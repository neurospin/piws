##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from cubicweb.server.sources.ldapfeed import LDAPFeedSource


# If the LDAP source ends with '/', it producesses a crash in LDAP 3 version
# <= 1.4

LDAPFeedSource._connection_info = LDAPFeedSource.connection_info
def connection_info(*args, **kwargs):
    """ Make sure the LDAP source does not finished by '/'.
    """
    protocol, host, port = LDAPFeedSource._connection_info(*args, **kwargs)
    if host.endswith("/"):
        host = host[:-1]
    return protocol, host, port
LDAPFeedSource.connection_info = connection_info
