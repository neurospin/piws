##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import types
import smtplib
import time
import json
from email.mime.text import MIMEText

# CW import
from cubicweb.server import hook
from cubicweb.predicates import is_instance

# PIWS import
from cubes.piws.docgen.rst2html import create_html_doc


class ServerStartupHook(hook.Hook):
    """
        Update repository cache with groups from indexation to ease LDAP
        synchronisation
    """
    __regid__ = 'piws.update_cache_hook'
    events = ('server_startup', 'server_maintenance')

    def __call__(self):
        # get ldap base dn
        ldap_base_dn = self.repo.vreg.config.get("ldap_base_dn", None)
        # update repository cache
        if ldap_base_dn is not None:
            with self.repo.internal_cnx() as cnx:
                rset = cnx.execute("Any X WHERE X is CWGroup")
                for egroup in rset.entities():
                    if egroup.name in ["guests", "managers", "users", "owners"]:
                        continue
                    self.repo._extid_cache['cn={0},{1}'.format(
                        egroup.name, ldap_base_dn)] = egroup.eid


class CreateDocumentation(hook.Hook):
    """ On startup create the documentation.
    """
    __regid__ = "piws.create_documentation"
    events = ("server_startup", )

    def __call__(self):
        """ The documantation is stored in repo.vreg.docmap and thus will
        be accessible in any CW pages.
        The docmap is a dictionary with the input rst documentation file
        basenames as keys. The values contain the corresponding html codes.
        """
        # Get the data url
        with self.repo.internal_cnx() as cnx:
            data_url = os.path.join(cnx.base_url(), "data/")

        # Get the documentation
        doc_folder = self.repo.vreg.config["documentation_folder"]
        if doc_folder:
            self.repo.vreg.docmap = create_html_doc(doc_folder, data_url)
        else:
            self.repo.vreg.docmap = {}


def piws_clean_sessions(self):
    """tags sessions not used since an amount of time specified in the
    configuration
    """
    # Remove zombies from expired sessions
    self._piws_expired_sessionids &= set(self._sessions)
    # System import
    from time import time, strftime, localtime
    mintime = time() - self.piws_cleanup_session_time
    self.debug('cleaning session unused since %s',
               strftime('%H:%M:%S', localtime(mintime)))
    nbclosed = 0
    for sessionid, session in self._sessions.iteritems():
        if session.timestamp < mintime:
            if sessionid not in self._piws_expired_sessionids:
                self._piws_expired_sessionids.add(sessionid)
                self.info('session {0} has expired'.format(sessionid))
                nbclosed += 1
    return nbclosed


class PiwsApacheDeauthenticationHook(hook.Hook):
    """
        Add piws_clean_sessions to server looping tasks
    """
    __regid__ = 'piws.apache_deauthentication'
    events = ('server_startup', 'server_maintenance')

    def __call__(self):
        """
        Register session clean up task.
        Adapted from cubicweb.server.repository @ _prepare_startup
        """
        if not (self.repo.config.creating or self.repo.config.repairing
                or self.repo.config.quick_start):
            piws_cleanup_session_time = self.repo.config.get(
                'apache-cleanup-session-time', None)
            if piws_cleanup_session_time is not None:
                raise NotImplementedError("Session expiration with Apache "
                                          "is not yet available due to "
                                          "cross browsers compatibility "
                                          "issues")
                assert piws_cleanup_session_time > 0
                self.repo.piws_cleanup_session_time = piws_cleanup_session_time
                self.repo._piws_expired_sessionids = set()
                self.repo.piws_clean_sessions = types.MethodType(
                    piws_clean_sessions, self.repo)
                # Arbitrary define the period to clean sessions as a third
                # of the specified cleanup time T. This implies a maximum
                # uncertainty in each session expiration of T/3.
                # If T > 3h we arbitrary fix this period to 1h.
                cleanup_session_interval = min(60 * 60,
                                               self.repo.
                                               piws_cleanup_session_time / 3)
                assert self.repo._tasks_manager is not None, ("This Repository "
                                                              "is not intended "
                                                              "to be used as a "
                                                              "server")
                self.repo._tasks_manager.add_looping_task(
                    cleanup_session_interval, self.repo.piws_clean_sessions)


class PiwsCWUsersWatcher(hook.Hook):
    """
        Sends an email message on CWUser creation/deletion, using all-in-one
        parameters of the [MAIL] section.
    """
    __regid__ = 'piws.cwusers_watcher'
    __select__ = hook.Hook.__select__ & is_instance('CWUser')
    events = ('after_add_entity', 'before_delete_entity')
    mandatory_params = ['sender-name', 'sender-addr', 'supervising-addrs',
                        'smtp-host', 'smtp-port']

    def sendmail(self, sender_name, sender_email, recipients_list, subject,
                 body, smtp_host, smtp_port):
        """
        Sends an email

        Parameters
        ----------
        sender_name: string (mandatory)
            The sender name (ie the database name)
        sender_email: string (mandatory)
            The sender email address
        recipients_list: list of str (mandatory)
            List of the recipients emails addresses
        subject: string (mandatory)
            The email subject
        body: string (mandatory)
            The email body
        smtp_host: string (mandatory)
            The SMTP server address
        smtp_port: int (mandatory)
            The SMTP server port
        """
        msg = MIMEText(body)
        msg['Subject'] = "[CubicWeb] {0} : {1}".format(sender_name, subject)
        msg['To'] = ", ".join(recipients_list)
        s = smtplib.SMTP(smtp_host, smtp_port)
        s.sendmail(sender_email, recipients_list, msg.as_string())
        s.quit()

    def __call__(self):
        """
        If the CW server is in production, create an admin message on CWUser
        entity creation or deletion.
        """
        config = self._cw.vreg.config
        if not (config.creating or config.repairing or config.quick_start):
            if config.get('enable-cwusers-watcher', 'no') == 'yes':
                if any(len(config.get(item, '')) == 0 for item
                       in self.mandatory_params):
                    raise Exception("In all-in-one section [MAIL] please fill "
                                    "the fields  'sender-name', 'sender-addr', "
                                    "'supervising-addrs', 'smtp-host', "
                                    "'smtp-port'")
                user_login = self.entity.login
                if self.event == 'after_add_entity':
                    creation_date = self.entity.creation_date.strftime(
                        '%d %b %Y - %H:%M:%S')
                    email_subject = "New user {0}".format(user_login)
                    email_body = "Creation date: {0}\n".format(creation_date)
                    email_body += "Login: {0}".format(user_login)
                else:
                    email_subject = "Deleted user {0}".format(user_login)
                    email_body = "Deletion date: {0}\n".format(
                        time.strftime('%d %b %Y - %H:%M:%S'))
                    email_body += "Login: {0}".format(user_login)
                self.sendmail(config['sender-name'], config['sender-addr'],
                              config['supervising-addrs'], email_subject,
                              email_body, config['smtp-host'],
                              config['smtp-port'])
