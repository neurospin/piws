#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.predicates import is_instance, yes
from cubicweb.web.action import Action
from cubicweb.web.views.wdoc import HelpAction, AboutAction
from cubicweb.web.views.actions import PoweredByAction


###############################################################################
# ACTIONS
###############################################################################

class LicenseAction(Action):
    __regid__ = "license"
    __select__ = yes()
    category = "footer"
    order = 1
    title = _("License")

    def url(self):
        return self._cw.build_url("license")


class LegalAction(Action):
    __regid__ = "legal"
    __select__ = yes()
    category = "footer"
    order = 2
    title = _("Legal")

    def url(self):
        return self._cw.build_url("legal")


class NSPoweredByAction(Action):
    __regid__ = "poweredby"
    __select__ = yes()
    category = "footer"
    order = 3
    title = _("&#169 2014, Neurospin Analysis Platform developers")

    def url(self):
        return "http://www-centre-saclay.cea.fr/fr/NeuroSpin"


def registration_callback(vreg):

    # Update the footer
    vreg.register(LegalAction)
    vreg.register(LicenseAction)
    vreg.register(NSPoweredByAction)
    vreg.unregister(HelpAction)
    vreg.unregister(AboutAction)
    vreg.unregister(PoweredByAction)
