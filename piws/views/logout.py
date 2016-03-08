#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views.sessions import InMemoryRepositorySessionManager
from cubicweb.web import LogOut, DirectResponse, Redirect
from cubicweb.etwist.http import HTTPResponse
from cubicweb.web.controller import Controller
from cubes.trustedauth.views import LogoutController


class PiwsLogoutController(Controller):
    """
    Override the default logout controller (<base url>/logout).
    Sends invalid http credentials from clientside javascript to deauthenticate
    from Apache.
    """
    __regid__ = "logout"
    title = _("Logout")

    def publish(self, rset=None):
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
        html += "$.ajax({"
        html += "url: 'index.php',"
        html += "async: false,"
        html += "username: '*',"
        html += "password: '*'"
        html += "}).fail(function() {"
        html += "window.location.replace('{0}');".format(
            self._cw.vreg.config['deauthentication-redirection-url'])
        html += "});"
        html += "});"
        html += "</script>"
        html += "<noscript>"
        html += ("Javascript is not activated. Please activate "
                 "javascript and restart your web-browser.")
        html += "</noscript>"
        html += "</body>"
        html += "</html>"
        return u"{0}".format(html)


class PiwsExpirationLogoutController(Controller):
    """
    Override the default logout controller (<base url>/logout).
    If the user wants to logout, adds its sessionid in the expired session list.
    Then redirects the user to an inside page (e.g. the welcome page) to trigger
    the deauthentication mechanism from PiwsExpirationInMemoryRepositorySessionManager.
    """
    __regid__ = 'logout'
    title = _("Logout")

    def publish(self, rset=None):
        sessionid = self._cw.session.sessionid
        if sessionid not in self.appli.repo._piws_expired_sessionids:
            self.appli.repo._piws_expired_sessionids.add(sessionid)
            self.appli.repo.info('session {0} has logged out'.format(sessionid))
        raise Redirect(self._cw.base_url())


class PiwsExpirationUnloadController(Controller):
    """
    Restricted javascript access controller called just before redirection
    to external url in order to destroy session.
    """
    __regid__ = 'piws-unload'
    title = _("Unload")

    def publish(self, rset=None):
        req = self._cw
        if (req._headers_in.getRawHeaders(
                'x-requested-with') == ['XMLHttpRequest']):
            session_handler = self.appli.session_handler
            session_handler.session_manager.close_session(req.session)
            req.remove_cookie(session_handler.session_cookie(req))
            # Will raise a proper AuthenticationError
            raise LogOut()
        else:
            # Redirect unauthorised attempts to close the session to the logout
            # controller
            raise Redirect(self._cw.base_url() + 'logout')


class PiwsExpirationInMemoryRepositorySessionManager(InMemoryRepositorySessionManager):
    """
    Called on any http request to get user's session before its execution.
    If session has expired, sends a direct http response to short the request
    processing and logout the user.
    """

    def __init__(self, *args, **kwargs):
        super(PiwsExpirationInMemoryRepositorySessionManager,
              self).__init__(*args, **kwargs)
        self.repo = kwargs['repo']
        self.deauth_html = "<!DOCTYPE html>"
        self.deauth_html += "<html lang='en'>"
        self.deauth_html += "<head>"
        self.deauth_html += "<meta charset='utf-8'>"
        self.deauth_html += "<title>Loading</title>"
        self.deauth_html += ("<script src='//code.jquery.com/"
                             "jquery-1.11.3.min.js'></script>")
        self.deauth_html += "</head>"
        self.deauth_html += "<body>"
        self.deauth_html += "<script>"
        self.deauth_html += "$(document).ready(function() {"
        self.deauth_html += "$(window).unload(function() {"
        self.deauth_html += "$.ajax({"
        self.deauth_html += "url: 'piws-unload',"
        self.deauth_html += "async: false"
        self.deauth_html += "}).always(function() {"
        self.deauth_html += "$.ajax({"
        self.deauth_html += "url: 'index.php',"
        self.deauth_html += "async: false,"
        self.deauth_html += "username: '*',"
        self.deauth_html += "password: '*'"
        self.deauth_html += "});"
        self.deauth_html += "});"
        self.deauth_html += "});"
        self.deauth_html += "window.location.replace('{0}');".format(
            self.repo.config['deauthentication-redirection-url'])
        self.deauth_html += "});"
        self.deauth_html += "</script>"
        self.deauth_html += "<noscript>"
        self.deauth_html += ("Javascript is not activated. Please activate "
                             "javascript and restart your web-browser.")
        self.deauth_html += "</noscript>"
        self.deauth_html += "</body>"
        self.deauth_html += "</html>"

    def get_session(self, req, sessionid):
        if sessionid in self.repo._piws_expired_sessionids:
            logout_url = req.base_url() + 'piws-unload'
            # Allow access to piws-unload controller only to destroy session
            # (last step of deauthentication).
            if req.url() != logout_url:
                response = HTTPResponse(code=req.status_out,
                                        headers=req.headers_out,
                                        stream=u'{0}'.format(self.deauth_html),
                                        twisted_request=req._twreq)
                raise DirectResponse(response)
        return super(PiwsExpirationInMemoryRepositorySessionManager,
                     self).get_session(req, sessionid)


def registration_callback(vreg):
    """
    Update registry.
    """
    if vreg.config.get("enable-apache-logout", "no") == "yes":
        vreg.register_and_replace(PiwsLogoutController, LogoutController)
    else:
        if vreg.config.get('apache-cleanup-session-time', None) is not None:
            raise NotImplementedError("Session expiration with Apache is not yet "
                                      "available due to cross browsers "
                                      "compatibility issues")
            vreg.register_and_replace(
                PiwsExpirationInMemoryRepositorySessionManager,
                InMemoryRepositorySessionManager)
            vreg.register_and_replace(
                PiwsExpirationLogoutController,
                LogoutController)
            vreg.register(PiwsExpirationUnloadController)
