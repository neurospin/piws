#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.baseviews import NullView


class DisplayDocumentation(NullView):
    """ Create a view to display the documentation.
    """
    __regid__ = "piws-documentation"
    templatable = False
    div_id = "piws-documentation"
    default_message = "Documentation has not been provided yet."

    def __init__(self, *args, **kwargs):
        """ Initialize the DisplayDocumentation class.
        """
        super(DisplayDocumentation, self).__init__(*args, **kwargs)

    def call(self, tooltip=None, tooltip_name=None, **kwargs):
        """ Create the documentation page.

        Parameters
        ----------
        tooltip: str
            a html formated string.
        tooltip_name: str
            the key of the item containing the html formated documentation.
        """
        # Get the parameters
        tooltip_name = tooltip_name or self._cw.form.get("tooltip_name", None)
        if tooltip_name is not None:
            tooltip = self._cw.vreg.docmap.get(tooltip_name, "")
            page_title = tooltip_name
        else:
            tooltip = tooltip or self._cw.form.get("tooltip", "")
            page_title = "Documentation"

        # Set a default message if documentation is empty
        tooltip = tooltip or "<div class='body'>{0}</div>".format(
            self.default_message)

        # Display documentation
        self.w(u"<!DOCTYPE html>")
        self.w(u"<html xmlns:cubicweb='http://www.cubicweb.org' lang='en'>")
        self.w(u"<head>")
        self.w(u"<meta http-equiv='content-type' content='text/html; charset=UTF-8'/>")
        self.w(u"<meta http-equiv='X-UA-Compatible' content='IE=8' />")
        self.w(u'<link rel="stylesheet" type="text/css" href="{0}"/>'.format(
            self._cw.data_url("doc.css")))
        self.w(u'<title>{0}</title>'.format(page_title))
        self.w(u'<link rel="icon" href="{0}" />'.format(
            self._cw.data_url("favicon.ico")))
        self.w(u"</head>")
        self.w(u"<body>")
        tooltip = tooltip.replace('class="document"', 'class="body"')
        self.w(unicode(tooltip))
        self.w(u"</body>")
        self.w(u"</html>")


###############################################################################
# Update CW registery
###############################################################################

def registration_callback(vreg):
    vreg.register(DisplayDocumentation)
