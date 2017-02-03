# coding: utf-8
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from collections import OrderedDict, defaultdict
import json
import re
import time

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc
from cubicweb.web.views.csvexport import CSVMixIn
from logilab.common.registry import yes


###############################################################################
# ScoreValue
###############################################################################

class ScoreValueTableViewSecondary(View):
    """ Generate an intermediate table to select the score values base on
    the item type and parameters.
    """
    __regid__ = "score-value-table-secondary"
    title = _("QC Scores")

    def call(self):
        """ Generate the table view.
        """
        # Get the view paremeters
        study = self._cw.form["study"]
        rtype = self._cw.form["rtype"]
        etype = self._cw.form["etype"]
        pname = self._cw.form["pname"]
        title = self._cw.form["title"]
        elts_to_sort = self._cw.form["elts_to_sort"]
        tooltip_name = self._cw.form["tooltip_name"]

        # Get the row and column labels
        if study == "":
            rql = ("DISTINCT Any L, P, T Where X is {0}, X type '{1}', "
                   "X in_assessment A, A timepoint T, "
                   "X label L, X {2} P".format(etype, rtype, pname))
        else:
            rql = ("DISTINCT Any L, P, T Where X is {0}, X study ST, "
                   "ST name '{1}', X type '{2}', X in_assessment A, "
                   "A timepoint T, X label L, "
                   "X {3} P".format(etype, study, rtype, pname))
        rset = self._cw.execute(rql)
        data = {}
        for row in rset:
            data.setdefault(row[2] + ": " + row[1], []).append(row)
        headers = sorted(set([row[0] for row in rset]))

        # Build the record
        records = []
        for processing_label, sequences in data.items():
            record = [processing_label] + [""] * len(headers)
            for sequence_name, pvalue, timepoint in sequences:
                index = headers.index(sequence_name) + 1
                href = self._cw.build_url(
                    "view", vid="score-value-table-primary", study=study,
                    etype=etype, rtype=rtype, pname=pname,
                    title=title, tooltip_name=tooltip_name,
                    timepoint=timepoint, pvalue=pvalue, label=sequence_name,
                    elts_to_sort=elts_to_sort, csv_export=True)
                record[index] = (
                    "<a href='{0}'>"
                    "<img src='data/images/blue-arrow.png' "
                    "alt='Open QC' width='20' "
                    "height='20' border='0'></a>").format(href)
            records.append(record)

        # Call JhugetableView for html generation of the table
        self.wview("jtable-hugetable-clientside", None, "null", labels=headers,
                   records=records, csv_export=False, title=title,
                   timepoint="", elts_to_sort=["ID"],
                   use_scroller=False, tooltip_name=tooltip_name)


class ScoreValueTableViewPrimary(View):
    """
    """
    __regid__ = "score-value-table-primary"
    title = _("QC Scores")
    default_error_message = "No score value has been provided yet."

    def call(self):
        """ Get all the score values and associated subjects.
        """
        # Get the view parameters
        study = self._cw.form["study"]
        rtype = self._cw.form["rtype"]
        etype = self._cw.form["etype"]
        pname = self._cw.form["pname"]
        timepoint = self._cw.form["timepoint"]
        pvalue = self._cw.form["pvalue"]
        label = self._cw.form["label"]
        csv_export = self._cw.form["csv_export"]
        title = self._cw.form["title"]
        elts_to_sort = self._cw.form["elts_to_sort"]
        tooltip_name = self._cw.form["tooltip_name"]

        # Get the score value
        if study == "":
            rql = ("Any SID, SCT, SCV Where X is {0}, X type '{1}', "
                   "X in_assessment A, A timepoint '{2}', X label '{3}', "
                   "X {4} '{5}', X score_values SC, SC text SCT, "
                   "SC value SCV, X subjects S, S code_in_study SID".format(
                        etype, rtype, timepoint, label,  pname, pvalue))
        else:
            rql = ("Any SID, SCT, SCV Where X is {0}, X study ST, "
                   "ST name '{1}', X type '{2}', X in_assessment A, "
                   "A timepoint '{3}', X label '{4}', X {5} '{6}', "
                   "X score_values SC, SC text SCT, "
                   "SC value SCV, X subjects S, S code_in_study SID".format(
                        etype, study, rtype, timepoint, label,  pname, pvalue))
        rset = self._cw.execute(rql)
        data = {}
        for row in rset:
            data.setdefault(row[0], []).append(row[1:])
        headers = sorted(set([row[1] for row in rset]))

        # Empty rset
        image_url = self._cw.data_url("images/error.png")
        self.w(u'<div style="align: left; text-align:center;">')
        self.w(u'<img src="{0}"/>'.format(image_url))
        self.w(u'<div class="caption"><font size="7">{0}</font>'
           '</div>'.format(self.default_error_message))
        self.w(u'</div>')
        return

        # Build the record
        records = []
        for sid, score_data in data.items():
            record = [sid] + [""] * len(headers)
            for text, value in score_data:
                index = headers.index(text) + 1
                record[index] = value
            records.append(record)

        # Call JhugetableView for html generation of the table
        self.wview("jtable-hugetable-clientside", None, "null", labels=headers,
                   records=records, csv_export=csv_export, title=title,
                   timepoint=timepoint, elts_to_sort=elts_to_sort,
                   use_scroller=False, tooltip_name=tooltip_name)


###############################################################################
# QuestionnaireRun
###############################################################################

class FileAnswerTableView(View):
    """ QuestionnaireRuns table view when subject questionnaires are inserted
    using the QuestionnaireRun -> file ->  File strategy, ie. one File
    per questionnaire.
    """
    __regid__ = "file-answer-table"
    title = _("Jtable")

    def call(self):
        """Get all the questionnaire runs and associated subjects"""

        # Retrieve form parameters from the url built by the ajax callback
        # get_questionnaires_data
        qname = self._cw.form['qname']
        csv_export = self._cw.form['csv_export']
        title = self._cw.form['title']
        timepoint = self._cw.form['timepoint']
        tooltip_name = self._cw.form['tooltip_name']
        elts_to_sort = self._cw.form['elts_to_sort']

        # Execute the rql to get all subjects QuestionnaireRuns
        rql = ("Any ID, D ORDERBY ID ASC WHERE QR is QuestionnaireRun, "
               "QR questionnaire Q, Q name '{0}', QR in_assessment A, "
               "A timepoint '{1}', QR file F, F data D, QR subject S, "
               "S code_in_study ID".format(qname, timepoint))
        rset = self._cw.execute(rql)

        # Load the dicts {question: answer, ..} per subject
        loaded_rset = [(sid, json.loads(sdata.getvalue()))
                       for sid, sdata in rset]

        # Get the table labels (ie headers) that corresponds to the questions
        rql_labels = ("Any QUT, P ORDERBY QUT WHERE Q is Questionnaire, "
                      "Q name '{0}', Q questions QU, QU text QUT, "
                      "QU position P".format(qname))
        labels = set()
        for sid, sdata in loaded_rset:
            labels |= set(sdata.keys())
        positions = {}
        rset_positions = self._cw.execute(rql_labels)
        for row in rset_positions:
            positions[row[0]] = row[1]
        labels = sorted(labels, key=lambda x: positions[x])

        # Construct all table rows
        records = []
        for sid, sdata in loaded_rset:
            record = [sid]
            for label in labels:
                try:
                    if isinstance(sdata[label], basestring):
                        record.append(sdata[label])
                    else:
                        record.append(repr(sdata[label]))
                except KeyError:
                    record.append(u"")
            records.append(record)

        # Call JhugetableView for html generation of the table
        self.wview('jtable-hugetable-clientside', None, 'null', labels=labels,
                   records=records, csv_export=csv_export, title=title,
                   timepoint=timepoint, elts_to_sort=elts_to_sort,
                   tooltip_name=tooltip_name, use_scroller=False)


###############################################################################
# Datatables
###############################################################################

class JHugetableView(View):
    """ Create a table view with DataTables.
    """
    __regid__ = "jtable-hugetable-clientside"
    title = _("Jtable")
    paginable = False
    div_id = "jhugetable-table"

    def call(self, labels, records, csv_export=True, title="", timepoint="",
             elts_to_sort=None, tooltip_name=None, use_scroller=False,
             index=0):
        """ Method that will create a table with client-side processing only.
         It is useful for huge datasets (million of entries).

        An Ajax call is emulated within the JavaScript so this function is
        client side only.

        A special 'ID' label will be added to the given labels to provide the
        row string description. Thus the first column of the records array must
        contain the corresponding 'ID' values.

        Parameters
        ----------
        labels: list of string
            the columns labels.
        records: list of list
            the table data.
        csv_export: bool (optional)
            if True an export button will be available.
        title: string (optional, default '')
            the title of the table.
        timepoint: string (optional, default '')
            the timepoint.
        elts_to_sort: list (optional, default [])
            labels of the columns to be sorted
        tooltip_name: string (optional, default None)
            the piws documentation tooltip name.
        use_scroller: bool (optional default False)
            if True do not use pagination.
        index: int (optional, default 0)
            increment this parameter to insert multiple tables in the same
            page.
        """

        if elts_to_sort is None:
            elts_to_sort = []

        # Add css resources
        self._cw.add_css(
            "DataTables-1.10.10/media/css/jquery.dataTables.min.css")
        self._cw.add_css("DataTables-1.10.10/extensions/FixedColumns/css/"
                         "fixedColumns.dataTables.min.css")
        self._cw.add_css("DataTables-1.10.10/extensions/Scroller/css/"
                         "scroller.dataTables.min.css")
        self._cw.add_css(
            ("https://code.jquery.com/ui/1.11.4/themes/smoothness/"
             "jquery-ui.css"), localfile=False)

        # Add js resources
        #self._cw.add_js("DataTables-1.10.10/media/js/jquery.js")
        self._cw.add_js("DataTables-1.10.10/media/js/jquery.dataTables.min.js")
        self._cw.add_js("DataTables-1.10.10/extensions/FixedColumns/js/"
                        "dataTables.fixedColumns.js")
        self._cw.add_js("DataTables-1.10.10/extensions/Scroller/js/"
                        "dataTables.scroller.min.js")
        self._cw.add_js("DataTables-1.10.10/extensions/fnSetFilteringDelay.js")
        #self._cw.add_js("https://code.jquery.com/ui/1.11.4/jquery-ui.js",
        #                localfile=False)

        # Get the instance questionnaire map
        qmap = self._cw.vreg.docmap

        # Associate a tooltip to each label
        tooltips = [""]
        for label_text in labels:
            if label_text in qmap:
                matches = re.findall("<!--.*tooltip:.*-->", qmap[label_text])
                if len(matches) == 1:
                    match = matches[0][matches[0].index("tooltip:") + 8:-3]
                    tooltips.append(match)
                else:
                    tooltips.append("")
            else:
                tooltips.append("")

        # Generate the script
        # > table column headers and sort option
        headers = [{"sTitle": "ID"}]
        hide_sort_indices = []
        if "ID" not in elts_to_sort:
            hide_sort_indices.append(0)
        for cnt, label_text in enumerate(labels):
            # >> select if we can sort this column
            if label_text not in elts_to_sort:
                hide_sort_indices.append(cnt + 1)
            # >> add this column to the table definition parameters
            if label_text in qmap:
                tiphref = self._cw.build_url(
                    "view", vid="piws-documentation",
                    tooltip_name=label_text, _notemplate=True)
                headers.append(
                    {"sTitle": "<a href='{0}' target=_blank>"
                               "<span class='fake-link'>{1} &#9735;"
                               "</span></a>".format(tiphref, label_text)})
            else:
                headers.append({"sTitle": label_text})

        # > begin the script
        html = "<script type='text/javascript'> "
        html += "$(document).ready(function() {"

        # > dumps the answers rset into javascript
        html += "var all_data = {0};".format(json.dumps(records))
        html += "var nbrecordstotal = {0};".format(len(records))
        # > create a cache for search patterns filtering
        html += "var filtered_indices = ['', undefined];"
        # > set the default sorting direction
        html += "var sort_dir = 'asc';"

        # > create the table
        html += "var table = $('#the_table_{0}').dataTable( {{ ".format(index)
        html += "serverSide: true,"

        # > set the ajax callback to fill dynamically the table
        html += "ajax: function ( data, callback, settings ) {"
        # > get the table sorting direction
        html += "var current_sort_dir = data.order[0].dir.toLowerCase();"
        html += "if ( current_sort_dir != sort_dir) {"
        html += "all_data = all_data.reverse();"
        html += "sort_dir = current_sort_dir;"
        html += "}"
        # > create the records array for the page being displayed
        html += "var out = [];"
        # > get the ID search field
        html += "var search_pattern = data.search.value.toLowerCase().trim();"
        html += "var nbrecordsfiltered = nbrecordstotal;"
        # > if the search field is not empty
        html += "if (search_pattern != '') {"
        # check the filtered indicies cache
        html += "if (filtered_indices[0] != search_pattern) {"
        html += "filtered_indices[0] = search_pattern;"
        html += "filtered_indices[1] = [];"
        # fill the filtered indicies cache
        html += "for ( var i=0; i<nbrecordstotal ; i++ ) {"
        html += ("if (all_data[i][0].toLowerCase()"
                 ".indexOf(search_pattern) >= 0) {")
        html += "filtered_indices[1].push(i);"
        # close the 'if some occurence of the search pattern is found' loop
        html += "}"
        # close the for loop
        html += "}"
        # > close the filtered indices cache verification
        html += "}"
        html += "nbrecordsfiltered = filtered_indices[1].length;"
        # fill the records array based on the filtered indicies
        html += ("for (var i=data.start, ien=Math.min(data.start+data.length, "
                 "nbrecordsfiltered) ; i<ien ; i++) {")
        html += "out.push( all_data[ filtered_indices[1][i] ] );"
        html += "}"
        # > close the 'if the search field is not empty' condition
        html += "}"
        # > if the search field is empty
        html += "else {"
        # fill the records array without filtering
        html += ("for ( var i=data.start, ien=Math.min(data.start+data.length,"
                 " nbrecordstotal) ; i<ien ; i++ ) {")
        html += "out.push( all_data[i] );"
        # > close the for loop
        html += "}"
        # > close the 'else if the search field is empty' condition
        html += "}"
        # register the ajax callback
        html += "setTimeout( function () {"
        html += "callback( {"
        html += "draw: data.draw,"
        html += "data: out,"
        html += "recordsTotal: nbrecordstotal,"
        html += "recordsFiltered: nbrecordsfiltered"
        html += "} );"
        # > close the ajax callback registration
        html += "}, 50 );"
        # > close the ajax callback
        html += "},"

        # > set table display options
        html += '"sScrollX": "100%",'
        html += '"sScrollXInner": "150%",'
        html += '"bScrollCollapse": true,'
        html += "'sPaginationType': 'bootstrap',"
        if use_scroller:
            html += "'scrollY': '200px',"
            if csv_export:
                html += "dom: 'T<\"clear\"><\"toolbar\">frtiS', "
            else:
                html += "dom: 'T<\"clear\">frtiS', "
            html += "scroller: {loadingIndicator: true}, "
        else:
            html += "'processing': true,"
            html += "'scrollY': '600px',"
            if csv_export:
                html += "'dom': 'T<\"clear\">l<\"toolbar\">frtip',"
            else:
                html += "'dom': 'T<\"clear\">lfrtip',"
        html += "'oLanguage': {'sSearch': 'ID search'},"
        html += "'pagingType': 'full_numbers',"

        # > set table header
        html += "'aoColumns': {0},".format(json.dumps(headers))

        # > set sort widget on column
        html += "'aoColumnDefs': [ "
        html += "{{ 'bSortable': false, 'aTargets': {0} }}".format(
            str(hide_sort_indices))
        html += "],"

        # > close table
        html += "} );"

        # > the first column is static in the display
        html += "var fc = new $.fn.dataTable.FixedColumns( "
        html += "table, {leftColumns: 1} "
        html += ");"
        html += "table.fnSetFilteringDelay(1000);"

        # Add tooltip in table column header
        html += "var question_text = {0};".format(json.dumps(tooltips))
        html += "$('thead th').each(function(index, value){"
        html += "var sTitle = question_text[index];"
        html += "this.setAttribute('title', sTitle);"
        html += "} );"
        html += "$( table.fnGetNodes() ).tooltip( {"
        html += "'delay': 0,"
        html += "'track': true,"
        html += "'fade': 250"
        html += "} );"

        if csv_export:

            # > create a new csv download button
            csv_button_html = (u'<p><a class="btn btn-default" role="button" '
                               u'id="csv_button">CSV Export »</a></p>')
            html += u"$('div.toolbar').html('{0}');".format(csv_button_html)

            # > center the search-bar
            html += ("$('#the_table_filter').css({'float': 'none', "
                     "'text-align': 'center'});")

            # > set csv file name
            timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
            filename_items = [title, timepoint, timestamp]
            filename = "_".join([x for x in filename_items if x])

            # > assign ajax callback to csv button : start function click
            html += "$('#csv_button').click(function() {"

            # > create the csv string
            html += "var csv_headers = {0};".format(
                    json.dumps([u"ID"] + labels))
            html += "var csv_tooltips = {0};".format(
                json.dumps([tooltip.replace(";", "") for tooltip in tooltips]))
            html += ("var csv_rows = [csv_headers.join(';'), "
                     "csv_tooltips.join(';')];")
            html += "for(var i=0, l=all_data.length; i<l; ++i){"
            html += "csv_rows.push(all_data[i].join(';'));"
            html += "}"
            html += "var csv_string = csv_rows.join('\\r\\n');"

            # > create a web-browser download object
            html += "var a = window.document.createElement('a');"
            html += ("a.href = window.URL.createObjectURL("
                     "new Blob([csv_string], {type: 'text/csv'}));")
            html += "a.download = '{0}.csv';".format(filename)
            html += "document.body.appendChild(a);"
            html += "a.click();"
            html += "document.body.removeChild(a);"

            # > end fct click
            html += "});"

        # > close document section
        html += "} );"

        # Close script div
        html += "</script>"

        # > set a title
        if tooltip_name is not None:
            tiphref = self._cw.build_url(
                "view", vid="piws-documentation", tooltip_name=tooltip_name,
                _notemplate=True)
            title = (u"<a class='btn btn-warning' href='{0}' target=_blanck>"
                     "{1} &#9735;</a>".format(tiphref, title))
        html += "<h1>{0}</h1>".format(title)

        # > display the table in the body
        html += "<table id='the_table_{0}' class='cell-border display'>".format(index)
        html += "<thead></thead>"
        html += "<tbody></tbody>"
        html += "</table>"

        # Creat the corrsponding html page
        self.w(unicode(html))


class JtableView(View):
    """ Create a table view with DataTables.
    """
    __regid__ = "jtable-table"
    title = _("Jtable")
    paginable = False
    div_id = "jtable-table"

    mandatory_params = ["vid", "rql_labels", "ajaxcallback", "labels",
                        "title", "elts_to_sort", "csv_export",
                        "use_server"]

    def __init__(self, *args, **kwargs):
        """ Initialize the JtableView class.

        If you want to construct the table manually in your view pass the
        parent view in the 'parent_view' attribute.
        """
        super(JtableView, self).__init__(*args, **kwargs)
        if "parent_view" in kwargs:
            self._cw = kwargs["parent_view"]._cw
            self.w = kwargs["parent_view"].w

    def call(self, rql_labels=None, labels=None, ajaxcallback=None,
             csv_export=False, title="", elts_to_sort=None,
             use_server=True, tooltip_name=None, **kwargs):
        """ Method that will create a table.

        When left clicking on a row, the row is selected (highlighted) Click
        again on this row to deselect it.

        On the right side of each herder box, you can decide to sort the
        the row if the option is available.

        1) Extra parameters will be passed to the ajax callback.

        2) Column labels must not contain space ' ' and they need to be
        replaced: use the 'label_cleaner' function.

        3) A special 'ID' column must be specified in the ajax callback that
        contains the row string description.

        4) All the sortable items must be handle in the ajax callback.

        Parameters
        ----------
        rql_labels: string (rql_labels)
            a rql that will be executed to get the columns labels.
        labels: list of string (xor rql_labels)
            a rql that will be executed to get the columns labels.
        ajaxcallback: @func (mandatory)
            a function that will be called by jtable to create dynamically the
            data to display: do not forget the decorator @ajaxfunc.
        csv_export: bool (optional)
            if True an export button will be available.
        title: string (optional, default '')
            the title of the table.
        elts_to_sort: list of str (optional)
            the colums label that can be sortable.
        use_server: bool (optional, default True)
            if True, use server-side processing.
        """
        # Get the parameters
        for key in sorted(self._cw.form.keys()):
            if key not in self.mandatory_params:
                kwargs[key] = self._cw.form[key]
        title = title or self._cw.form.get("title", None)
        tooltip_name = tooltip_name or self._cw.form.get("tooltip_name", "")
        rql_labels = rql_labels or self._cw.form.get("rql_labels", None)
        labels = labels or self._cw.form.get("labels", None)
        if labels is not None and not isinstance(labels, list):
            labels = [labels]
        ajaxcallback = ajaxcallback or self._cw.form.get("ajaxcallback", "")
        if self._cw.form.get("csv_export", None) is not None:
            csv_export = self._cw.form.get("csv_export")
        elts_to_sort = elts_to_sort or self._cw.form.get("elts_to_sort", [])
        if not isinstance(elts_to_sort, list):
            elts_to_sort = [elts_to_sort]
        if "use_server" in self._cw.form:
            use_server = eval(self._cw.form.get("use_server"))

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Add css resources
        self._cw.add_css(
            "DataTables-1.10.10/media/css/jquery.dataTables.min.css")
        self._cw.add_css("DataTables-1.10.10/extensions/FixedColumns/css/"
                         "fixedColumns.dataTables.min.css")
        self._cw.add_css("DataTables-1.10.10/extensions/Scroller/css/"
                         "scroller.dataTables.min.css")
        self._cw.add_css(
            ("https://code.jquery.com/ui/1.11.4/themes/smoothness/"
             "jquery-ui.css"), localfile=False)

        # Add js resources
        #self._cw.add_js("DataTables-1.10.10/media/js/jquery.js")
        self._cw.add_js("DataTables-1.10.10/media/js/jquery.dataTables.min.js")
        self._cw.add_js("DataTables-1.10.10/extensions/FixedColumns/js/"
                        "dataTables.fixedColumns.js")
        self._cw.add_js("DataTables-1.10.10/extensions/fnSetFilteringDelay.js")
        #self._cw.add_js("https://code.jquery.com/ui/1.11.4/jquery-ui.js",
        #                localfile=False)

        # Get table meta information
        if labels is None:
            if rql_labels is not None:
                labels_rset = self._cw.execute(rql_labels)
                labels = [item[0] for item in labels_rset]
        if labels is None:
            raise Exception("No labels can be selected while creating the "
                            "jtable")

        # Get the instance questionnaire map
        qmap = self._cw.vreg.docmap

        # Associate a tooltip to each label
        tooltips = [""]
        for label_text in labels:
            if label_text in qmap:
                matches = re.findall("<!--.*tooltip:.*-->", qmap[label_text])
                if len(matches) == 1:
                    match = matches[0][matches[0].index("tooltip:") + 8:-3]
                    tooltips.append(match)
                else:
                    tooltips.append("")
            else:
                tooltips.append("")

        # Generate the script
        # > table column headers and sort option
        headers = [{"sTitle": "ID"}]
        hide_sort_indices = []
        if "ID" not in elts_to_sort:
            hide_sort_indices.append(0)
        for cnt, label_text in enumerate(sorted(labels)):

            # >> select if we can sort this column
            if label_text not in elts_to_sort:
                hide_sort_indices.append(cnt + 1)

            # >> add this column to the table definition parameters
            if label_text in qmap:
                tiphref = self._cw.build_url(
                    "view", vid="piws-documentation",
                    tooltip_name=label_text, _notemplate=True)
                headers.append(
                    {"sTitle": "<a href='{0}' target=_blank>"
                               "<span class='fake-link'>{1} &#9735;"
                               "</span></a>".format(tiphref, label_text)})
            else:
                headers.append({"sTitle": label_text})

        # > begin the script
        html = "<script type='text/javascript'> "
        html += "$(document).ready(function() {"

        # > create the table
        html += "var table = $('#the_table').dataTable( { "

        # > set table display options
        html += '"sScrollX": "100%",'
        html += '"sScrollXInner": "150%",'
        html += '"bScrollCollapse": true,'
        html += "'scrollCollapse': true,"
        html += "'sPaginationType': 'bootstrap',"
        if csv_export:
            html += "'dom': 'T<\"clear\">l<\"toolbar\">frtip',"
        else:
            html += "'dom': 'T<\"clear\">lfrtip',"
        html += "'sServerMethod': 'POST',"
        html += "'oLanguage': {'sSearch': 'ID search'},"
        html += "'pagingType': 'full_numbers',"
        html += "'bProcessing': true,"
        if use_server:
            html += "'bServerSide': true,"
        else:
            html += "'bServerSide': false,"

        # > set table header
        html += "'aoColumns': {0},".format(json.dumps(headers))

        # > set sort widget on column
        html += "'aoColumnDefs': [ "
        html += "{{ 'bSortable': false, 'aTargets': {0} }}".format(
            str(hide_sort_indices))
        html += "],"

        # > set the ajax callback to fill dynamically the table
        html += "'sAjaxSource':'ajax?fname={0}',".format(ajaxcallback)
        html += "'fnServerParams': function (aoData) {"
        html += "aoData.push("
        html += "{ name: 'labels', "
        html += "value: '{0}'".format(json.dumps(["ID"] + labels))
        html += "}, "
        for key, value in kwargs.items():
            if isinstance(value, basestring):
                html += "{{name: '{0}', value: '{1}'}}, ".format(
                    key, str(value))
            else:
                html += "{{name: '{0}', value: {1}}}, ".format(key, value)

        # Remove extre comma
        html = html[:-2]

        # > close push data
        html += ");"

        # > close function fnServerParams
        html += "},"

        # > close table
        html += "} );"

        # > the first column is static in the display
        html += "var fc = new $.fn.dataTable.FixedColumns( "
        html += "table, {leftColumns: 1} "
        html += ");"
        html += "table.fnSetFilteringDelay(1000);"

        # Add tooltip in table column header
        html += "var question_text = {0};".format(json.dumps(tooltips))
        html += "$('thead th').each(function(index, value){"
        html += "var sTitle = question_text[index];"
        html += "this.setAttribute('title', sTitle);"
        html += "} );"
        html += "$( table.fnGetNodes() ).tooltip( {"
        html += "'delay': 0,"
        html += "'track': true,"
        html += "'fade': 250"
        html += "} );"

        if csv_export:

            # > create a new csv download button
            csv_button_html = (u'<p><a class="btn btn-default" role="button" '
                               u'id="csv_button">CSV Export »</a></p>')
            html += u"$('div.toolbar').html('{0}');".format(csv_button_html)

            # > center the search-bar
            html += ("$('#the_table_filter').css({'float': 'none', "
                     "'text-align': 'center'});")

            # > set options to retrieve all the full result set from the ajax
            # callback
            post_data = {'qname': kwargs['qname'],
                         'timepoint': kwargs['timepoint'],
                         'labels': json.dumps(["ID"] + labels)}

            # > set csv file name
            timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
            filename_items = [title, kwargs.get("timepoint", ""), timestamp]
            filename = "_".join([x for x in filename_items if x])

            # > assign ajax callback to csv button : start function click
            html += "$('#csv_button').click(function() {"

            # > display a processing message
            html += "$('#loadingmessage').show();"

            # > execute the ajax callback
            html += "var request = $.ajax({"
            html += "url: 'view?vid=jtable-table-csv-export',"
            html += "method: 'POST',"
            html += "data: {0},".format(json.dumps(post_data))
            html += "dataType: 'html'"
            html += "});"

            # > the ajax callback is done, get the result set
            html += "request.done(function( result ) {"
            # > create a download link
            html += "var a = window.document.createElement('a');"
            html += ("a.href = window.URL.createObjectURL(new Blob([result], "
                     "{type: 'text/csv'}));")
            html += "a.download = '{0}.csv';".format(filename)
            html += "document.body.appendChild(a);"
            html += "a.click();"
            html += "document.body.removeChild(a);"
            # > hide the processing message
            html += "$('#loadingmessage').hide();"
            html += "});"

            # > if the ajax callback failed display an alert
            html += "request.fail(function(){"
            html += "$('#loadingmessage').hide();"
            html += "alert('Error : Download Failed!');"
            html += "});"

            # > end fct click
            html += "});"

        # > close script
        html += "} );"

        # Close script div
        html += "</script>"

        # > set a title
        if tooltip_name is not None:
            tiphref = self._cw.build_url(
                "view", vid="piws-documentation", tooltip_name=tooltip_name,
                _notemplate=True)
            title = (u"<a class='btn btn-warning' href='{0}' target=_blanck>"
                     "{1} &#9735;</a>".format(tiphref, title))
        html += "<h1>{0}</h1>".format(title)

        # > create a div for the in progress resource
        html += ("<div id='loadingmessage' style='display:none' "
                 "align='center'><img src='{0}'/></div>".format(
                     wait_image_url))

        # > display the table in the body
        html += "<table id='the_table' class='cell-border display'>"
        html += "<thead></thead>"
        html += "<tbody></tbody>"
        html += "</table>"

        # Creat the corrsponding html page
        self.w(unicode(html))


###############################################################################
# Export table data in CSV
###############################################################################

class PIWSCSVView(CSVMixIn, View):
    """ Dumps table data in CSV: used by 'jtable-table' view.
    """
    __regid__ = "jtable-table-csv-export"
    __select__ = yes()
    title = _("piws csv export")

    def call(self):
        """ Display the CSV formated table data.
        """

        qname = self._cw.form["qname"]
        timepoint = self._cw.form["timepoint"]
        labels = json.loads(self._cw.form["labels"])

        rql = ("Any ID, QT, OV Where S is Subject, S code_in_study ID, "
               "S subject_questionnaire_runs QR, QR questionnaire QU, "
               "QU name '{0}', QR open_answers O, O value OV, "
               "O in_assessment A, A timepoint '{1}', O question Q, "
               "Q text QT".format(qname, timepoint))
        rset = self._cw.execute(rql)

        table = defaultdict(lambda: OrderedDict.fromkeys(labels, ""))
        for item in rset:
            table[item[0]][item[1]] = item[2]
        for id, data in table.iteritems():
            table[id]["ID"] = id

        writer = self.csvwriter()
        writer.writerow(labels)
        for psc2, data in iter(sorted(table.iteritems())):
            writer.writerow(data.values())


###############################################################################
# Interact with jtable js
###############################################################################

@ajaxfunc(output_type="json")
def get_open_answers_data(self):
    """ Get the subject answer data.

    Parameters
    ----------
    jtsort: str
        the sorting option to use.
    jtstartindex: int
        the current index provided by jtable.
    jtpagesize: int
        the number of rows per page.
    id_pattern: str
        pattern to search in the ID column.
    labels: list of str
        the table column names.
    qname: string (mandatory)
        the name of the questionnaire we want to export.
    timepoint: string (mandatory)
        filter request on a timepoint.

    Returns
    -------
    data: dict
        the table content.
    """
    # Get parameters
    jtsort = self._cw.form['sSortDir_0']
    jtstartindex = int(self._cw.form['iDisplayStart'])
    jtpagesize = int(self._cw.form['iDisplayLength'])
    id_pattern = self._cw.form['sSearch']
    labels = json.loads(self._cw.form['labels'])
    qname = self._cw.form['qname']
    timepoint = self._cw.form['timepoint']

    # Deal with sort options
    jtsort = "ORDERBY ID {0}".format(jtsort)

    # Get all the questionnaire runs and associated subjects
    rql = ("Any ID, QR {0} "
           "Where QR is QuestionnaireRun, QR questionnaire Q, Q name '{1}', "
           "QR subject S, S code_in_study ID, QR in_assessment A, "
           "A timepoint '{2}'".format(jtsort, qname, timepoint))
    rset = self._cw.execute(rql)

    # Filter the rset with the ID pattern
    filtered_rset = []
    for item in rset:
        if id_pattern == "" or id_pattern in item[0]:
            filtered_rset.append([item[0], item[1]])

    # Set the appropriate range to access the data
    # > if the user want to show all the results
    if jtpagesize == -1 or jtpagesize > len(filtered_rset):
        rset_range = range(len(filtered_rset))
    # > otherwise
    else:
        rset_range = range(jtstartindex,
                           min(jtstartindex + jtpagesize, len(filtered_rset)))

    # Get the answers of the desired subset of subjects
    records = []
    for row_nb in rset_range:
        user_data = OrderedDict.fromkeys(labels, '')
        user_data['ID'] = filtered_rset[row_nb][0]

        # Execute an rql to get the subject answers
        questionnaire_run_eid = filtered_rset[row_nb][1]
        rql = ("Any QN, V Where QR eid '{0}', QR open_answers A, A question Q,"
               "Q text QN, A value V".format(questionnaire_run_eid))
        answer_rset = self._cw.execute(rql)

        # Go through all answers
        for qname, answer in answer_rset:
            user_data[qname] = answer

        # Store the tabel formated row
        records.append(user_data.values())

    # Table formatting
    data = {"iTotalRecords": rset.rowcount,
            "iTotalDisplayRecords": len(filtered_rset),
            "aaData": records}

    return data


@ajaxfunc(output_type="json")
def get_questionnaires_data(self):
    """ Get the questionnaires data.

    Attributes
    ----------
    jtsort: str
        the sorting option to use.
    jtstartindex: int
        the current index provided by the datatable.
    jtpagesize: int
        the number of rows per page.
    column_to_filter: int
        index of the column to filter.
    id_pattern: str
        pattern to search in the ID column.
    labels: list of str
        the table column names.
    qtype: str
        the requested questionnaires type.

    Returns
    -------
    data: dict
        the table content.
    """
    # Get parameters
    jtsort = self._cw.form['sSortDir_0']
    jtstartindex = int(self._cw.form['iDisplayStart'])
    jtpagesize = int(self._cw.form['iDisplayLength'])
    id_pattern = self._cw.form['sSearch']
    labels = json.loads(self._cw.form['labels'])
    qtype = self._cw.form['qtype']
    column_to_filter = int(self._cw.form['iSortCol_0'])

    # Only the ID column can be filtered
    if column_to_filter != 0:
        raise Exception("Only the 'ID' column can be filtered by "
                        "'get_questionnaires_data' ajax callback.")

    # Choose the questionnaire rendering view:
    # > case 1: one line of answers inserted per subject (File)
    # > case 2: the answers are inserted in the database (OpenAnswer).
    rql = "Any QR Where QR is QuestionnaireRun, EXISTS(QR file F)"
    rset = self._cw.execute(rql)
    if rset.rowcount > 0:
        vid = "file-answer-table"
    else:
        vid = "jtable-table"

    # Deal with sort options
    jtsort = "ORDERBY ID {0}".format(jtsort)

    # Get all the questionnaire and associated timepoints
    rql = ("DISTINCT Any ID, T {0} "
           "Where Q is Questionnaire, QR is QuestionnaireRun, "
           "QR questionnaire Q, Q type '{1}', QR in_assessment A, Q name ID, "
           "A timepoint T".format(jtsort, qtype))
    rset = self._cw.execute(rql)

    # Get the total number of rows (without filtering)
    total_nb_of_rows = len(set([item[0] for item in rset]))

    # Create a structure to be able to sort by questionnaire name
    qstruct = OrderedDict()
    for item in rset:
        qname = item[0]
        timepoint = item[1]
        # Filter the rset with the ID pattern
        if id_pattern == "" or id_pattern.lower() in qname.lower():
            qstruct.setdefault(qname, []).append(timepoint)

    # Open answer table parameters
    ajaxcallback = "get_open_answers_data"
    rql_labels = ("Any QUT ORDERBY QUT WHERE Q is Questionnaire, Q name '{0}',"
                  "Q questions QU, QU text QUT")

    # Define start and stop display index for pagination
    lower = jtstartindex
    # If ALL results are selected
    if jtpagesize == -1:
        higher = total_nb_of_rows
    else:
        higher = min(jtstartindex + jtpagesize, len(qstruct))

    # Build the list that will be dumped in the table
    records = []
    for item in qstruct.items()[lower:higher]:

        qname = item[0]
        timepoints = item[1]

        # Build the current row
        record = [qname] + [""] * (len(labels) - 1)

        # Start filling the table dataset
        # Go through all declared timepoints
        for timepoint in timepoints:
            # Construct the answer table view
            href = self._cw.build_url(
                "view", vid=vid,
                rql_labels=rql_labels.format(qname),
                ajaxcallback=ajaxcallback, title=qname, tooltip_name=qname,
                qname=qname, timepoint=timepoint, elts_to_sort=["ID"],
                csv_export=True)
            # Find the column index corresponding to this timepoint
            timepoint_index = [label.lower() for label in labels].index(
                timepoint.lower())
            # Fill the cells with hyperlinks to the questionnaire view
            record[timepoint_index] = (
                "<a href='{0}'>"
                "<img src='data/images/blue-arrow.png' "
                "alt='Open questionnaire' width='20' "
                "height='20' border='0'></a>").format(href)

        # Store the table formatted row
        records.append(record)

    # Table formatting
    data = {"iTotalRecords": total_nb_of_rows,
            "iTotalDisplayRecords": len(qstruct),
            "aaData": records}

    return data


###############################################################################
# Update CW registery
###############################################################################

def registration_callback(vreg):

    for tclass in [JtableView, JHugetableView, FileAnswerTableView,
                   PIWSCSVView, ScoreValueTableViewSecondary,
                   ScoreValueTableViewPrimary]:
        vreg.register(tclass)

    for ajax in [get_questionnaires_data, get_open_answers_data]:
        vreg.register(ajax)
