##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import time

# Cubicweb import
from cubicweb.web.views.sessions import InMemoryRepositorySessionManager
from cubicweb.etwist.http import HTTPResponse


class TimeoutInMemoryRepositorySessionManager(InMemoryRepositorySessionManager):
    """ Add a cookie to the session that trace the last server activity.
    """
    def get_session(self, req, sessionid):

        # Define the expiration cookie
        secure = req.https and req.base_url().startswith("https://")
        req.set_cookie("{}clock".format(sessionid), str(time.time()),
                       maxage=None, secure=secure, httponly=False)

        # Inheritance
        session = super(TimeoutInMemoryRepositorySessionManager,
                        self).get_session(req, sessionid)

        return session


class ApacheTimeoutInMemoryRepositorySessionManager(
        TimeoutInMemoryRepositorySessionManager):
    """
    Triggered on any http request to get user's session before its execution.
    If session expired, sends a direct http response to short the request
    processing and logout the user.
    """

    def __init__(self, *args, **kwargs):
        super(ApacheTimeoutInMemoryRepositorySessionManager,
              self).__init__(*args, **kwargs)
        # Get the 'repo' object
        self.repo = kwargs['repo']
        # Create the deauthentication html page
        self.logout_html = "<!DOCTYPE html>"
        self.logout_html += "<html lang='en'>"
        self.logout_html += "<head>"
        self.logout_html += "<meta charset='utf-8'>"
        self.logout_html += "<title>Loading</title>"
        self.logout_html += ("<script src='https://code.jquery.com/"
                             "jquery-1.11.3.min.js'></script>")
        self.logout_html += "</head>"
        self.logout_html += "<body>"
        self.logout_html += "<script>"
        self.logout_html += "$(document).ready(function() {"
        # First Ajax callback to remove the session id from the expired ones
        self.logout_html += "$.post('%(ajax_url)s', "
        self.logout_html += "{sessionid: '%(sessionid)s'})"
        self.logout_html += ".done(function() {"
        # Second Ajax callback to flush browser Apache http credentials
        self.logout_html += "$.ajax({"
        self.logout_html += "url: 'index.php',"
        self.logout_html += "async: false,"
        self.logout_html += "username: '*',"
        self.logout_html += "password: '*'"
        # Last step : redirection to the specified url
        self.logout_html += "}).fail(function() {"
        self.logout_html += "window.location.replace('{0}');".format(
            self.repo.config['deauth-redirect-url'])
        self.logout_html += "});"
        self.logout_html += "});"
        self.logout_html += "});"
        self.logout_html += "</script>"
        # Warning displayed if Javascript is disabled
        self.logout_html += "<noscript>"
        self.logout_html += ("Javascript is not activated. Please activate "
                             "javascript and restart your web-browser.")
        self.logout_html += "</noscript>"
        self.logout_html += "</body>"
        self.logout_html += "</html>"

    def get_session(self, req, sessionid):
        # If the session expired
        if sessionid in self.repo._expired_sessionids:
            if self.repo._expired_sessionids[sessionid]:
                # Intercept all requests except for 'sessionid_unload'
                # ajax controller
                unload_url = req.build_url("ajax", fname="sessionid_unload")
                if req.url() != unload_url:
                    parameters = {"ajax_url": unload_url,
                                  "sessionid": sessionid}
                    stream = self.logout_html % parameters
                    response = HTTPResponse(code=req.status_out,
                                            headers=req.headers_out,
                                            stream=u'{0}'.format(stream),
                                            twisted_request=req._twreq)
                    raise DirectResponse(response)
            else:
                del self.repo._expired_sessionids[sessionid]
        return super(ApacheTimeoutInMemoryRepositorySessionManager,
                     self).get_session(req, sessionid)


def registration_callback(vreg):
    """
    Update registry.
    """
    if vreg.config["apache-cleanup-session-time"] is not None:
        vreg.register_and_replace(
            ApacheTimeoutInMemoryRepositorySessionManager,
            InMemoryRepositorySessionManager)
    else:
        vreg.register_and_replace(
            TimeoutInMemoryRepositorySessionManager,
            InMemoryRepositorySessionManager)
