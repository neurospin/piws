##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.predicates import is_instance
from cubicweb.predicates import anonymous_user
from cubicweb.web.views.startup import IndexView
from cubicweb.web.views.primary import PrimaryView
from cubicweb.web.views.startup import IndexView
from cubicweb.web.views.basetemplates import LoggedOutTemplate
from cubicweb.view import StartupView


class PIWSIndexView(IndexView):
    """ Class that defines the piws index view.
    """
    title = _("Index")

    def call(self, **kwargs):
        """ Create the 'index' like page of our site.
        """
        # Get the card that contains some text description about this site
        rset = self._cw.execute("Any X WHERE X is Card, X title 'index'")
        self.wview("primary", rset=rset)


class PIWSLoggedOutTemplate(StartupView):
    __regid__ = "loggedout"
    __select__ = anonymous_user()
    title = "Logged out"

    def call(self):
        msg = self._cw._("You have been logged out:")
        if self._cw.cnx:
            comp = self._cw.vreg["components"].select("applmessages", self._cw)
            comp.render(w=self.w, msg=msg)
            self.wview("index")
        else:
            self.w(u"<div class='container'>")
            self.w(u"<h2>%s</h2>" % msg)
            self.w(u"<a href='{0}' class='btn btn-info btn-lg'>".format(
                self._cw.build_url("login")))
            self.w(u"<span class='glyphicon glyphicon-log-in'></span> Log in")
            self.w(u"</a>")
            self.w(u"</div>")


class PIWSCardView(PrimaryView):
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
            "demo-url": "http://piws.demo.logilab.fr/",
            "license-url": self._cw.build_url("license"),
            "connect-image": self._cw.data_url(
                "images/dreamstime_s_33211444.jpg"),
            "database-image": self._cw.data_url(
                "images/dreamstime_s_32994616.jpg"),
            "nsap-image": self._cw.data_url("images/nsap.png"),
            "nsap-url": "http://i2bm.cea.fr/drf/i2bm/Pages/NeuroSpin/UNATI/nsap.aspx",
        }

        # Update card links links to content
        content = rset.get_entity(0, 0).content
        content = content % resources
        self.w(content)


def registration_callback(vreg):
    vreg.register_and_replace(PIWSIndexView, IndexView)
    vreg.register_and_replace(PIWSLoggedOutTemplate, LoggedOutTemplate)
    vreg.register(PIWSCardView)
