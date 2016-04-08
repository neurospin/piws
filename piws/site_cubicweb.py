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
        "default": None,
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
        "default": None,
        "help": "LDAP base dn for synchronisation",
        "group": "piws",
        "level": 1,
    }),
    ('apache-cleanup-session-time',
     {'type': 'time',
      'default': None,
      'help': ('Duration of inactivity after which an apache de-authentication'
               'will be triggered'),
      'group': 'piws',
      'level': 1,
      }),
    ('deauthentication-redirection-url',
     {'type': 'string',
      'default': None,
      'help': 'Redirection url after apache deauthentication occured.',
      'group': 'piws',
      'level': 1,
      }),
    ("enable-cwusers-watcher", {
        "type": "string",
        "default": 'no',
        "help": ("If 'yes', an email is sent (this email address has to be "
                 "set in the [MAIL] all-in-one section) when a CW user is "
                 "created or deleted."),
        "group": "piws",
        "level": 1,
    }),
    ('enable-apache-logout',
     {'type': 'string',
      'default': 'no',
      'help': 'Enable Apache logout',
      'group': 'piws',
      'level': 1,
      }),
    ('logo',
     {'type': 'string',
      'default': 'images/nsap.png',
      'help': 'Navigation bar logo',
      'group': 'piws',
      'level': 1,
      }),
)
