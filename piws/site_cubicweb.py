#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


options = (
    ("documentation_folder", {
        "type": "string",
        "default": "",
        "help": "the folder containing the documentation of the project.",
        "group": "piws",
        "level": 1,
    }),
    ("show_user_status", {
        "type": "string",
        "default": "yes",
        "help": "Show or not the user status link on the website.",
        "group": "piws",
        "level": 1,
    }),
    ("ldap_base_dn", {
        "type": "string",
        "default": "",
        "help": "LDAP base dn for synchronisation",
        "group": "piws",
        "level": 1,
    }),
)
