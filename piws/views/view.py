##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import re

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.baseviews import SameETypeListView
from logilab.common.decorators import monkeypatch


@monkeypatch(View)
def page_title(self):
    """ Returns a title according to the result set - used for the
    title in the HTML header.
    """
    rset = self.cw_rset
    regex = "Any [a-zA-Z] Where [a-zA-Z] is [a-zA-Z]{1,20}"
    rql = ""
    if rset is not None:
        rql = rset.rql
    if rset is not None and rset.rowcount and rset.rowcount == 1:
        try:
            entity = rset.complete_entity(0, 0)
            title = entity.cw_etype
        except:
            title = _("NotAnEntity")
    elif hasattr(self, "title"):
        title = self.title
    elif len(re.findall(regex, rql)) == 1:
        title = rql.split()[-1]
    else:
        title = _("NoMatch")

    return title


def display_name(req, key, form="", context=None):
    """ Returns a internationalized string for the key (schema entity or
    relation name) in a given form.
    """
    assert form in ("", "plural", "subject", "object")
    if form == "subject":
        form = ""
    elif form == "plural":
        key = key + "s"
    elif form:
        key = key + "_" + form
    # ensure unicode
    if context is not None:
        return unicode(req.pgettext(context, key))
    else:
        return unicode(req._(key))


@property
def title(self):
    etype = iter(self.cw_rset.column_types(0)).next()
    return display_name(self._cw, etype, form='plural')

SameETypeListView.title = title
