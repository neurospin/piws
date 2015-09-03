#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os

# CW import
from cubicweb.server import hook

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

        # Go to the virtualenv root folder
        #if "VIRTUAL_ENV" in os.environ:
        #    os.chdir(os.environ["VIRTUAL_ENV"])

        # Get the documentation
        doc_folder = self.repo.vreg.config["documentation_folder"]
        if doc_folder:
            self.repo.vreg.docmap = create_html_doc(doc_folder, data_url)
        else:
            self.repo.vreg.docmap = {}


class RemoveUserStatusHook(hook.Hook):
    __regid__ = "piws.remove_userstatus"
    __select__ = hook.Hook.__select__
    events = ('server_startup', 'server_maintenance')

    def __call__(self):

        show_user_status = self.repo.vreg.config.get("show_user_status", 'yes')

        if show_user_status not in ['yes', 'no']:
            raise Exception('Only :yes or :no values are allowed for '
                            'all-in-one.conf property :show_user_status.')

        with self.repo.internal_cnx() as cnx:

            if 'ctxcomponents' in cnx.vreg:

                cw_properties_list = [
                    {'pkey': u'ctxcomponents.userstatus.visible',
                     'value': u"'1'"},
                    {'pkey': u'ctxcomponents.userstatus.order',
                     'value': u'5'},
                    {'pkey': u'ctxcomponents.userstatus.context',
                     'value': u'header-right'}
                ]

                if show_user_status == 'no':
                    cw_properties_list[0]['value'] = 'NULL'

                for item in cw_properties_list:
                    cnx.execute(u"DELETE Any X WHERE X is CWProperty, "
                                u"X pkey '%(pkey)s'" % item)

                cnx.execute(u"INSERT CWProperty X: X value %(value)s, "
                            u"X pkey '%(pkey)s'" % cw_properties_list[0])
                cnx.execute(u"INSERT CWProperty X: X value '%(value)s', "
                            u"X pkey '%(pkey)s'" % cw_properties_list[1])
                cnx.execute(u"INSERT CWProperty X: X value '%(value)s', "
                            u"X pkey '%(pkey)s'" % cw_properties_list[2])

                cnx.commit()
