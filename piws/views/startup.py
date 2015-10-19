#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views.startup import IndexView
from cubicweb.predicates import is_instance
from cubicweb.web.views.primary import PrimaryView

# Cubes import
from cubes.brainomics.views.startup import BrainomicsIndexView


class NSIndexView(IndexView):
    """ Class that defines the piws index view.
    """

    def call(self, **kwargs):
        """ Create the 'index' like page of our site.
        """
        # Get the card that contains some text description about this site
        rset = self._cw.execute("Any X WHERE X is Card, X title 'index'")
        self.wview("primary", rset=rset)


###############################################################################
# Card View
###############################################################################

class NSCardView(PrimaryView):
    """ Class that that defines how we print card entities.
    """
    __select__ = PrimaryView.__select__ & is_instance("Card")

    def call(self, rset=None, **kwargs):
        """ Format the card entity content.
        """
        # Get the rset
        rset = self.cw_rset or rset

        # Get additional resources links
        resources = {
            "demo-url": "http://mart.intra.cea.fr/senior/",
            "license-url": self._cw.build_url("license"),
            "connect-image": self._cw.data_url("images/dreamstime_s_33211444.jpg"),
            "database-image": self._cw.data_url("images/dreamstime_s_32994616.jpg"),
            "nsap-image": self._cw.data_url("images/nsap.png"),
            "nsap-url": "https://bioproj.extra.cea.fr/redmine/projects/nsap",
        }

        # Update card links links to content
        content = rset.get_entity(0, 0).content
        content = content % resources
        self.w(content)


def registration_callback(vreg):
    vreg.register_and_replace(NSIndexView, BrainomicsIndexView)
    vreg.register(NSCardView)
