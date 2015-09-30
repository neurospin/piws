from cubicweb.web.views.sessions import InMemoryRepositorySessionManager
from cubicweb.web import LogOut, DirectResponse, Redirect
from cubicweb.etwist.http import HTTPResponse
from cubicweb.web.controller import Controller
from cubes.trustedauth.views import LogoutController


class PiwsLogoutController(Controller):
    """
    /logout controller.
    """
    __regid__ = 'logout'

    def publish(self, rset=None):
        sessionid = self._cw.session.sessionid
        if sessionid not in self.appli.repo._piws_expired_sessionids:
            self.appli.repo._piws_expired_sessionids.add(sessionid)
            self.appli.repo.info('session {0} has logged out'.format(sessionid))
        raise Redirect(self._cw.base_url())


class PiwsUnloadController(Controller):
    """
    Restricted javascript access controller called just before redirection
    to account manager url in order to destroy session.
    """
    __regid__ = 'piws-unload'

    def publish(self, rset=None):
        req = self._cw
        if req._headers_in.\
                getRawHeaders('x-requested-with') == ['XMLHttpRequest']:
            session_handler = self.appli.session_handler
            session_handler.session_manager.close_session(req.session)
            req.remove_cookie(session_handler.session_cookie(req))
            raise LogOut()


class PiwsInMemoryRepositorySessionManager(InMemoryRepositorySessionManager):
    """
    Called on any http request to get user's session. If session has expired,
     sends a direct http response to logout the user.
    """

    def __init__(self, *args, **kwargs):
        super(PiwsInMemoryRepositorySessionManager,
              self).__init__(*args, **kwargs)
        self.repo = kwargs['repo']
        self.deauth_html = "<!DOCTYPE html>"
        self.deauth_html += "<html lang='en'>"
        self.deauth_html += "<head>"
        self.deauth_html += "<meta charset='utf-8'>"
        self.deauth_html += "<title>Loading</title>"
        self.deauth_html += "<script src='//code.jquery.com/" \
                            "jquery-1.11.3.min.js'></script>"
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
            self.repo.config['account-manager-url'])
        self.deauth_html += "});"
        self.deauth_html += "</script>"
        self.deauth_html += "<noscript>"
        self.deauth_html += "Javascript is not activated. Please activate " \
                            "javascript and restart your web-browser."
        self.deauth_html += "</noscript>"
        self.deauth_html += "</body>"
        self.deauth_html += "</html>"

    def get_session(self, req, sessionid):
        if sessionid in self.repo._piws_expired_sessionids:
            logout_url = req.base_url() + 'piws-unload'
            if req.url() != logout_url:
                response = HTTPResponse(code=req.status_out,
                                        headers=req.headers_out,
                                        stream=u'{0}'.format(self.deauth_html),
                                        twisted_request=req._twreq)
                raise DirectResponse(response)
        return super(PiwsInMemoryRepositorySessionManager,
                     self).get_session(req, sessionid)


def registration_callback(vreg):
    """
    Update registry.
    """
    if vreg.config.get('enable-apache-deauth', 'no') == 'yes':
        vreg.register_and_replace(PiwsInMemoryRepositorySessionManager,
                                  InMemoryRepositorySessionManager)
        vreg.register_and_replace(PiwsLogoutController, LogoutController)
        vreg.register(PiwsUnloadController)
