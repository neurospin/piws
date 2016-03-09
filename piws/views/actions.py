##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.predicates import is_instance
from cubicweb.predicates import authenticated_user
from cubicweb.web.action import Action
from cubicweb.web.views.wdoc import HelpAction, AboutAction
from cubicweb.web.views.actions import PoweredByAction
from cubicweb.web.views.actions import UserPreferencesAction
from cubicweb.web.views.actions import UserInfoAction
from logilab.common.registry import yes


###############################################################################
# ACTIONS
###############################################################################

class PIWSPoweredByAction(Action):
    __regid__ = "poweredby"
    __select__ = yes()

    category = "footer"
    order = 3
    title = _("Powered by NSAp")

    def url(self):
        return "https://github.com/neurospin/piws"


def registration_callback(vreg):

    # Update the footer
    vreg.register_and_replace(PIWSPoweredByAction, PoweredByAction)
    vreg.unregister(HelpAction)
    vreg.unregister(AboutAction)
    vreg.unregister(UserPreferencesAction)
    vreg.unregister(UserInfoAction)
