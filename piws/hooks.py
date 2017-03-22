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
from packaging import version

# CW import
import cubicweb
from cubicweb.server import hook
from cubicweb.predicates import is_instance
from logilab.common.decorators import monkeypatch

# PIWS import
_docutils_initial_cwd = os.getcwd()  # work around docutils bug
from cubes.piws.docgen.rst2html import create_html_doc


cw_version = version.parse(cubicweb.__version__)


# Sync the CW and LDAP chache properly
if cw_version < version.parse("3.24.0"):

    class ServerStartupHook(hook.Hook):
        """ Update repository cache with groups from indexation to ease LDAP
        synchronisation.
        """
        __regid__ = 'piws.update_cache_hook'
        events = ('server_startup', 'server_maintenance')

        def __call__(self):
            # get ldap base dn
            ldap_groups_dn = self.repo.vreg.config.get("ldap_groups_dn", None)
            # update repository cache
            if ldap_groups_dn is not None:
                with self.repo.internal_cnx() as cnx:
                    rset = cnx.execute("Any X WHERE X is CWGroup")
                    for egroup in rset.entities():
                        if egroup.name in ["guests", "managers", "users",
                                           "owners"]:
                            continue
                        self.repo._extid_cache['cn={0},{1}'.format(
                            egroup.name, ldap_groups_dn)] = egroup.eid

else:

    from cubicweb.dataimport.importer import ExtEntitiesImporter

    @monkeypatch(ExtEntitiesImporter)
    def _import_entities(self, ext_entities, queue):
        """ LDAP synch import groups as external entities and thus the
        'ExtEntitiesImporter' importer is used.

        To synch LDAP with existing CW groups, check the group existance in
        CW.
        """
        extid2eid = self.extid2eid
        deferred = {}  # non inlined relations that may be deferred
        self.import_log.record_debug("importing entities")
        for ext_entity in self.iter_ext_entities(ext_entities, deferred, queue):

            # Case of groups for LDAP Sync: check group existance
            if ext_entity.etype == "CWGroup":
                group_name = ext_entity.values["name"]
                rql = "Any G Where G is CWGroup, G name '{0}'".format(
                    group_name)
                if self.store.rql(rql).rowcount > 0:
                    continue

            try:
                eid = extid2eid[ext_entity.extid]
            except KeyError:
                self.prepare_insert_entity(ext_entity)
            else:
                if ext_entity.values:
                    self.prepare_update_entity(ext_entity, eid)
        return deferred


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
            site_url = cnx.base_url()

        # Docutils initializes paths relatively to the current directory.
        # Relative paths are nonsensical in a library because any subsequent
        # os.chdir() will result in crashes in the library. This bug has been
        # recently fixed but current releases still lack the fix (latest
        # release is 0.12 at the time of this writing):
        #   https://sourceforge.net/p/docutils/code/7795/
        # Unless started in debug mode, CubicWeb calls a daemonize() function
        # that resets the current directory using os.chdir('/'). It also
        # imports docutils early on. Subsequent use of docutils results in
        # crashes unless we os.chdir() back to the initial directory.
        os.chdir(_docutils_initial_cwd)

        # Get the documentation
        doc_folder = self.repo.vreg.config["documentation_folder"]
        if doc_folder:
            self.repo.vreg.docmap = create_html_doc(doc_folder, site_url)
        else:
            self.repo.vreg.docmap = {}


def apache_clean_sessions(self):
    """ Tags sessions not used since an amount of time specified in the
    configuration.
    """
    # Remove zombies from expired sessions
    for sessionid, _ in self._expired_sessionids.iteritems():
        if sessionid not in self._sessions:
            del self._expired_sessionids[sessionid]

    # System import
    from time import time, strftime, localtime
    mintime = time() - self.a_cleanup_session_time
    self.debug('cleaning session unused since %s',
               strftime('%H:%M:%S', localtime(mintime)))
    nbclosed = 0
    for sessionid, session in self._sessions.iteritems():
        if session.timestamp < mintime:
            if sessionid not in self._expired_sessionids:
                self._expired_sessionids[sessionid] = True
                self.info('session {0} expired'.format(sessionid))
                nbclosed += 1
    return nbclosed


class PiwsApacheDeauthenticationHook(hook.Hook):
    """ Add apache_clean_sessions to server looping tasks
    """
    __regid__ = 'apache_logout.apache_deauthentication'
    events = ('server_startup', 'server_maintenance')

    def __call__(self):
        """
        Register session clean up task.
        Adapted from cubicweb.server.repository @ _prepare_startup
        """
        if not (self.repo.config.creating or self.repo.config.repairing
                or self.repo.config.quick_start):
            a_cleanup_session_time = self.repo.config[
                'apache-cleanup-session-time']
            if a_cleanup_session_time:
                assert a_cleanup_session_time > 0
                self.repo.a_cleanup_session_time = a_cleanup_session_time
                self.repo._expired_sessionids = {}
                self.repo.apache_clean_sessions = types.MethodType(
                    apache_clean_sessions, self.repo)
                # Arbitrary define the period to clean sessions as a third
                # of the specified cleanup time T. This implies a maximum
                # uncertainty in each session expiration of T/3.
                # If T > 3h we arbitrary fix this period to 1h.
                cleanup_session_interval = min(60 * 60,
                                               self.repo.
                                               a_cleanup_session_time / 3)
                assert self.repo._tasks_manager is not None, (
                    "This Repository is not intended to be used as a server.")
                self.repo._tasks_manager.add_looping_task(
                    cleanup_session_interval, self.repo.apache_clean_sessions)


class PiwsCWUsersWatcher(hook.Hook):
    """ Sends an email message on CWUser creation/deletion, using all-in-one
    parameters of the [MAIL] section.
    """
    __regid__ = "piws.cwusers_watcher"
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
