##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from packaging import version
import os

# Cubicweb import
import cubicweb
cw_version = version.parse(cubicweb.__version__)
if cw_version >= version.parse("3.21.0"):
    from cubicweb import _

from cubicweb.predicates import is_instance
from cubicweb.predicates import anonymous_user
from cubicweb.predicates import authenticated_user
from cubicweb.web.views.startup import IndexView
from cubicweb.web.views.primary import PrimaryView
from cubicweb.web.views.startup import IndexView
from cubicweb.web.views.basetemplates import LoggedOutTemplate
from cubicweb.view import StartupView
from cubicweb.web.views.baseviews import NullView


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


class History(NullView):
    """ Create a view to display the history.
    """
    __regid__ = "piws-history"
    __select__ = authenticated_user()
    templatable = False
    div_id = "piws-history"
    default_message = "Hostory has not been provided yet."

    def __init__(self, *args, **kwargs):
        """ Initialize the History class.
        """
        super(History, self).__init__(*args, **kwargs)

    def call(self, **kwargs):
        """ Create the history page.
        """

        # Get additional resources links
        resources = {
            "euaims-image": self._cw.data_url(
                "startup/images/euaims.png"),
            "pi-image": self._cw.data_url(
                "startup/images/pi.png"),
            "imagen-image": self._cw.data_url(
                "startup/images/imagen.png"),
            "fmri-image": self._cw.data_url(
                "startup/images/fmri.png"),
            "piws-image": self._cw.data_url(
                "startup/images/piws-small.png"),
            "nsap-image": self._cw.data_url(
                "startup/images/nsap.png")
        }

        # Get local html startup
        startup_html = os.path.join(os.path.dirname(__file__), "startup.html")
        if os.path.isfile(startup_html):
            links = (
                u'<link rel="stylesheet" type="text/css" href="{0}"/>'.format(
                    self._cw.data_url("startup/css/style.css")))
            for path in ("startup/js/jquery.js",
                         "startup/js/jquery-migrate.js",
                         "startup/js/mezr.js",
                         "startup/js/public.js"):
                links += (
                    u'<script type="text/javascript" src="{0}"></script>'.format(
                        self._cw.data_url(path)))
            with open(startup_html, "rt") as open_file:
                html = open_file.readlines()
            html = "\n".join(html[:8] + [links] + html[8:])
            for key, value in resources.items():
                html = html.replace("%({0})s".format(key), value)
            self.w(unicode(html))
        else:
            self.w(unicode(self.default_message))


def registration_callback(vreg):
    vreg.register_and_replace(PIWSIndexView, IndexView)
    vreg.register_and_replace(PIWSLoggedOutTemplate, LoggedOutTemplate)
    vreg.register(PIWSCardView)
    vreg.register(History)
