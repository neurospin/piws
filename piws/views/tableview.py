##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from packaging import version

# Cubicweb import
import cubicweb
cw_version = version.parse(cubicweb.__version__)
if cw_version >= version.parse("3.21.0"):
    from cubicweb import _

from cubicweb.predicates import any_rset
from cubicweb.web.views import tableview
from logilab.common.decorators import monkeypatch
from cubicweb.view import AnyRsetView
from cubicweb.web.views.csvexport import CSVMixIn


@monkeypatch(tableview.TableLayout)
def render_table_headers(self, w, colrenderers):
    """ Render table and add a button to export rset data in CSV format.
    """
    # Export table in CSV
    labels = []
    for colrenderer in colrenderers:
        labels.append(colrenderer.header)
    # > all labels must be different than None:
    if self.cw_rset is not None and None not in labels:
        href = self._cw.build_url(rql=self.cw_rset.printable_rql(),
                                  vid="tablecsvexport", labels=labels)
        w(u'<a class="btn btn-default" role="button" id="table_csv_button" '
          u'href="{0}">CSV Export &#187</a>'.format(href))

    # Default rendering + get the header labels
    w(u'<thead><tr>')
    for colrenderer in colrenderers:
        if colrenderer.sortable:
            w(u'<th class="sortable">')
        else:
            w(u'<th>')
        colrenderer.render_header(w)
        w(u'</th>')
    w(u'</tr></thead>\n')


class CSVRsetView(CSVMixIn, AnyRsetView):
    """ Dumps table rset in CSV.
    """
    __regid__ = "tablecsvexport"
    __select__ = any_rset()
    title = _("CSV export")

    def call(self):
        """ This method expect a 'labels' form attribute that will be dumped
        as the first row of the CSV file.
        """
        writer = self.csvwriter()
        writer.writerow(self._cw.form["labels"])
        rset, descr = self.cw_rset, self.cw_rset.description
        eschema = self._cw.vreg.schema.eschema
        for rowindex, row in enumerate(rset):
            csvrow = []
            for colindex, val in enumerate(row):
                etype = descr[rowindex][colindex]
                if val is not None and not eschema(etype).final:
                    # csvrow.append(val) # val is eid in that case
                    content = self._cw.view('textincontext', rset,
                                            row=rowindex, col=colindex)
                else:
                    content = self._cw.view('final', rset,
                                            format='text/plain',
                                            row=rowindex, col=colindex)
                csvrow.append(content)
            writer.writerow(csvrow)

