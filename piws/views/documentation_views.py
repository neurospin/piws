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

    def __init__(self, *args, **kwargs):
        """ Initialize the DisplayDocumentation class.
        """
        super(DisplayDocumentation, self).__init__(*args, **kwargs)

    def call(self, tooltip=None, **kwargs):
        """
        """
        # Get the parameters
        tooltip = tooltip or self._cw.form.get("tooltip", "")

        # Display documentation
        self.w(u"<!DOCTYPE html>")
        self.w(u"<html xmlns:cubicweb='http://www.cubicweb.org' lang='en'>")
        self.w(u"<head>")
        self.w(u"<meta http-equiv='content-type' content='text/html; charset=UTF-8'/>")
        self.w(u"<meta http-equiv='X-UA-Compatible' content='IE=8' />")
        self.w(unicode(tooltip))


###############################################################################
# Update CW registery
###############################################################################

def registration_callback(vreg):
    vreg.register(DisplayDocumentation)
