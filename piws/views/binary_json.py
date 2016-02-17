##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import json

# Cubicweb import
from cubicweb.utils import json_dumps
from cubicweb import Binary
from cubicweb.web.views.json import JsonMixIn
from logilab.common.decorators import monkeypatch


@monkeypatch(JsonMixIn)
def wdata(self, udata):
    """ Mixin class for json views.

    Handles the following optional request parameters:

    - '_indent': must be an integer. If found, it is used to pretty print
      json output.
    - '_binary': must be an integer. If found, it will decode binary fields.
    """
    # Select indentation
    if "_indent" in self._cw.form:
        indent = int(self._cw.form["_indent"])
    else:
        indent = None

    # Convert binary if requested
    if "_binary" in self._cw.form:
        data = []
        for row in udata:
            for index, item in enumerate(row):
                if isinstance(item, Binary):
                    row[index] = json.loads(item.getvalue())
            data.append(row)
    else:
        data = udata

    # Dump in html page
    self.w(json_dumps(data, indent=indent))
