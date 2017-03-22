#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


# System imports
from urlparse import urlsplit

# Cubicweb imports
from cubicweb.web.views.sessions import InMemoryRepositorySessionManager
from cubicweb.web import DirectResponse, Redirect
from cubicweb.web.controller import Controller
from cubicweb.web.request import _CubicWebRequestBase
from cubicweb.web.views.ajaxcontroller import ajaxfunc
from logilab.common.decorators import monkeypatch


@monkeypatch(_CubicWebRequestBase)
def base_url_path(self):
    """
    Returns the absolute path of the base url.
    Monkeypatched to ensure session cookie path is '{base url}/domain'
    and not '{base url}/domain/'.
    """
    path = urlsplit(self.base_url())[2]
    if path.endswith("/"):
        path = path[:-1]
    return path


@ajaxfunc(output_type="json")
def sessionid_unload(self):
    """
    Ajax callback to remove user's sessionid from the expired list when the
    deauthentication javascript has been triggered.
    """
    req = self._cw
    is_success = False
    form_session_id = req.form.get("sessionid", "")
    sessionid = req.session.sessionid
    if (req._headers_in.getRawHeaders(
            'x-requested-with') == ['XMLHttpRequest']):
        if form_session_id == sessionid:
            if sessionid in req.session.repo._expired_sessionids:
                self._cw.session.repo._expired_sessionids[sessionid] = False
            is_success = True
    return {"unloaded": repr(is_success)}


class PiwsLogoutController(Controller):
    """
    Override the default logout controller (<base url>/logout).
    Sends invalid http credentials from clientside javascript to deauthenticate
    from Apache.
    """
    __regid__ = "logout"

    def publish(self, rset=None):
        session = self._cw.session
        sessionid = session.sessionid
        session.repo.info('session {0} logged out'.format(sessionid))
        if hasattr(session.repo, "_expired_sessionids"):
            self._cw.session.repo._expired_sessionids[sessionid] = True
            raise Redirect(self._cw.base_url())
        else:
            html = "<!DOCTYPE html>"
            html += "<html lang='en'>"
            html += "<head>"
            html += "<meta charset='utf-8'>"
            html += "<title>Loading</title>"
            html += ("<script src='//code.jquery.com/"
                     "jquery-1.11.3.min.js'></script>")
            html += "</head>"
            html += "<body>"
            html += "<script>"
            html += "$(document).ready(function() {"
            # Ajax callback to flush browser Apache http credentials
            html += "$.ajax({"
            html += "url: 'index.php',"
            html += "async: false,"
            html += "username: '*',"
            html += "password: '*'"
            # Last step : redirection to the specified url
            html += "}).fail(function() {"
            html += "window.location.replace('{0}');".format(
                self._cw.vreg.config["deauth-redirect-url"])
            html += "});"
            html += "});"
            html += "</script>"
            # Warning diplayed if Javascript s disabled
            html += "<noscript>"
            html += ("Javascript is not activated. Please activate "
                     "javascript and restart your web-browser.")
            html += "</noscript>"
            html += "</body>"
            html += "</html>"
            return "{0}".format(html)


def registration_callback(vreg):
    """
    Update registry.
    """
    if vreg.config["enable-apache-logout"]:
        from cubes.trustedauth.views import LogoutController
        vreg.register_and_replace(PiwsLogoutController, LogoutController)
        if vreg.config["apache-cleanup-session-time"] is not None:
            vreg.register(sessionid_unload)
