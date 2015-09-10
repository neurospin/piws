# coding: utf-8
#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from string import maketrans
from collections import OrderedDict
import json
import re
import datetime
import time

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc


###############################################################################
# Jtable
###############################################################################

class JhugetableView(View):
    """ Create a table view with Jtable.
    """
    __regid__ = "jtable-hugetable-clientside"
    paginable = False
    div_id = "jhugetable-table"

    mandatory_params = ["vid", "rql_labels", "ajaxcallback", "labels",
                        "title", "csvcallback"]

    def __init__(self, *args, **kwargs):
        """ Initialize the JtableView class.

        If you want to construct the table manually in your view pass the
        parent view in the 'parent_view' attribute.
        """
        super(JhugetableView, self).__init__(*args, **kwargs)
        if "parent_view" in kwargs:
            self._cw = kwargs["parent_view"]._cw
            self.w = kwargs["parent_view"].w

    def call(self, rql_labels=None, labels=None, ajaxcallback=None,
             title="", csvcallback=False, use_scroller=False, **kwargs):
        """ Method that will create a table for huge datasets (million of
        entries).

        An Ajax call is emulated within the JavaScript so this function is
        client side only.

        When left clicking on a row, the row is selected (highlighted) Click
        again on this row to deselect it.

        1) Extra parameters will be passed to the Ajax callback that is called
        one time

        2) Column labels must not contain space ' ' and they need to be
        replaced: use the 'label_cleaner' function.

        3) A special 'ID' column must be specified in the Ajax callback that
        contains the row string description.

        Parameters
        ----------
        rql_labels: string (rql_labels)
            a rql that will be executed to get the columns labels.
        labels: list of string (xor rql_labels)
            the columns labels.
        ajaxcallback: @func (mandatory)
            a function thaty will be called by jtable to create dynamically the
            data to display: do not foget the decorator @ajaxfunc.
        title: string (optional, default '')
            the title of the table.
        csvcallback: bool (optional)
            if True an export button will be available.
        use_scroller: bool (optional default False)
            if True do not use pagination.
        """
        # Get the parameters
        for key in sorted(self._cw.form.keys()):
            if key not in self.mandatory_params:
                kwargs[key] = self._cw.form[key]
        title = title or self._cw.form.get("title", "")
        rql_labels = rql_labels or self._cw.form.get("rql_labels", None)
        labels = labels or self._cw.form.get("labels", None)
        if labels is not None and not isinstance(labels, list):
            labels = [labels]
        ajaxcallback = ajaxcallback or self._cw.form.get("ajaxcallback", "")
        if self._cw.form.get("csvcallback", None) is not None:
            csvcallback = self._cw.form.get("csvcallback")
        if "use_scroller" in self._cw.form:
            use_scroller = eval(self._cw.form.get("use_scroller"))

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Add css resources
        self._cw.add_css("datatables-1.10.5/media/css/jquery.dataTables.min.css")
        self._cw.add_css("datatables-1.10.5/extensions/FixedColumns/css/"
                         "dataTables.fixedColumns.css")
        self._cw.add_css("datatables-1.10.5/extensions/Scroller/css/"
                         "dataTables.scroller.css")
        self._cw.add_css(
            "https://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css",
            localfile=False)

        # Add js resources
        self._cw.add_js("datatables-1.10.5/media/js/jquery.js")
        self._cw.add_js("datatables-1.10.5/media/js/jquery.dataTables.min.js")
        self._cw.add_js("datatables-1.10.5/extensions/FixedColumns/js/"
                        "dataTables.fixedColumns.js")
        self._cw.add_js("datatables-1.10.5/extensions/fnSetFilteringDelay.js")
        self._cw.add_js("datatables-1.10.5/extensions/Scroller/js/"
                        "dataTables.scroller.js")
        self._cw.add_js("https://code.jquery.com/ui/1.11.4/jquery-ui.js",
                        localfile=False)

        # Get table meta information
        if rql_labels is not None:
            labels = [item[0] for item in self._cw.execute(rql_labels)]
            labels.insert(0, u"ID")
        if labels is None:
            raise Exception("No labels can be selected while creating the "
                            "hugejtable")

        # Get the instance questionnaire map
        qmap = self._cw.vreg.docmap

        # Associate a tooltip to each label
        tooltips = []
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

        # Table column headers
        headers = []
        for label_text in labels:
            if label_text in qmap:
                tiphref = self._cw.build_url(
                    "view", vid="piws-documentation",
                    tooltip_name=label_text, _notemplate=True)
                headers.append(
                    {"sTitle": "<a href='{0}' target=_blank>"
                               "<span class='fake-link'>{1} &#9735"
                               "</span></a>".format(tiphref, label_text)})
            else:
                headers.append({"sTitle": label_text})

        post_data = kwargs
        if 'sSortDir_0' not in post_data:
            post_data['sSortDir_0'] = 'ASC'
        if 'iDisplayStart' not in post_data:
            post_data['iDisplayStart'] = '0'
        if 'iDisplayLength' not in post_data:
            post_data['iDisplayLength'] = '-1'
        if 'sSearch' not in post_data:
            post_data['sSearch'] = ''
        if 'labels' not in post_data:
            post_data['labels'] = '{0}'.format(json.dumps(labels))

        # Generate the script
        html = "<script type='text/javascript'> "
        html += "$(document).ready(function() {"

        # > call the ajax callback to get the data and display a processing
        # > message
        html += "$('#loadingmessage').show();"
        html += "var post = $.ajax({"
        html += "url: 'ajax?fname={0}', ".format(ajaxcallback)
        html += "type: 'POST', "
        html += "dataType: 'json', "
        html += "data: {0}".format(json.dumps(post_data))
        html += "});"

        # > start post: when data are loaded, hide the processing message
        html += "post.done(function(p){"
        html += "$('#loadingmessage').hide();"

        # > global variable with the data
        html += "var jdata = p['aaData'];"

        # > create the table
        html += "var table = $('#the_table').dataTable( { "

        # > set table display options
        html += "serverSide: true, "
        html += "ordering: false, "
        html += "searching: true, "
        html += "scrollX: '100%',"
        html += "scrollY: 600,"
        html += "scrollCollapse: true,"
        html += "aoColumns: {0}, ".format(json.dumps(headers))
        if use_scroller:
            if csvcallback:
                html += "dom: 'T<\"clear\"><\"toolbar\">frtiS', "
            else:
                html += "dom: 'T<\"clear\">frtiS', "
            html += "scroller: {loadingIndicator: true}, "
        else:
            if csvcallback:
                html += "dom: 'T<\"clear\">l<\"toolbar\">frtip', "
            else:
                html += "dom: 'T<\"clear\">lfrtip', "
            html += "lengthMenu: [ [25, 50, 100, 200], [25, 50, 100, 200] ],"
            html += "pagingType: 'full_numbers',"
            html += "bProcessing: true, "

        # > build the inner ajax call
        html += "ajax: function ( data, callback, settings ) {"
        # >> inner parameters
        html += "var out = [];"
        html += "var filtered_jdata = [];"
        # >> filter the dataset using a regex
        html += "if (data.search.value != '') {"
        html += "for ( var i=0, ien=jdata.length ; i<ien ; i++ ) {"
        html += "var reg = new RegExp(data.search.value);"
        html += "if (jdata[i][0].match(reg)) {"
        html += "filtered_jdata.push( jdata[i] );"
        html += "}"
        html += "}"
        html += "}"
        html += "else {"
        html += "filtered_jdata = jdata;"
        html += "}"
        # >> display only a subset of the filtered dataset
        html += ("for ( var i=data.start, ien=Math.min(data.start+data.length, "
                 "filtered_jdata.length) ; i<ien ; i++ ) {")
        html += "out.push( filtered_jdata[i] );"
        html += "}"
        # >> return the generated subset and add a timeout
        html += "setTimeout( function () {"
        html += "callback( {"
        html += "draw: data.draw, "
        html += "data: out, "
        html += "recordsTotal: jdata.length, "
        html += "recordsFiltered: filtered_jdata.length"
        html += "} );"
        html += "}, 50 );"
        # >> close ajax
        html += "}"

        # > close table
        html += "} );"

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

        if csvcallback:

            # > create a new csv download button
            csv_button_html = (u'<p><a class="btn btn-default" role="button" '
                               u'id="csv_button">CSV Export »</a></p>')
            html += u"$('div.toolbar').html('{0}');".format(csv_button_html)

            # > center the search-bar
            html += ("$('#the_table_filter').css({'float': 'none', "
                     "'text-align': 'center'});")

            # > assign ajax callback to csv button : start function click
            html += "$( '#csv_button' ).click(function() {"
            # # > display a processing message
            html += "$('#loadingmessage').show();"
            #
            html += "headers = {0};".format(json.dumps(labels))
            html += "var csvRows = [headers.join(';')];"
            html += "csvRows.push({0}.join(';'));".format(json.dumps(tooltips))
            html += "for(var i=0, l=jdata.length; i<l; ++i){"
            html += "csvRows.push(jdata[i].join(';'));"
            html += "}"

            # > create a download link
            html += "var csvString = csvRows.join('\\r\\n');"
            html += "var a = document.createElement('a');"
            html += ("a.href = 'data:application/csv;charset=utf-8,' "
                     "+ encodeURIComponent(csvString);")
            html += "a.target = '_blank';"
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S")
            if "timepoint" in kwargs:
                csv_file_name = "{0}_{1}_{2}.csv".format(
                    title, kwargs["timepoint"], st)
            else:
                csv_file_name = "{0}_{1}".format(title, st)
            html += "a.download = '{0}';".format(csv_file_name)

            # > hide the processing message
            html += "document.body.appendChild(a);"
            html += "a.click();"
            html += "$('#loadingmessage').hide();"

            # > end fct click
            html += "});"

        # > post done
        html += "});"

        # > error when loading the data
        html += "post.fail(function(){"
        html += " alert('Error : Download Failed!');"
        html += "});"

        # > close function
        html += "} );"

        # > close script
        html += "</script>"

        # > set a title
        html += "<h1>{0}</h1>".format(title)

        # > create a div for the in progress resource
        html += ("<div id='loadingmessage' style='display:none' "
                 "align='center'><img src='{0}'/></div>".format(wait_image_url))

        # > display the table in the body
        html += "<table id='the_table' class='cell-border display'>"
        html += "<thead></thead>"
        html += "</table>"

        # Creat the corrsponding html page
        self.w(unicode(html))


class JtableView(View):
    """ Create a table view with Jtable.
    """
    __regid__ = "jtable-table"
    paginable = False
    div_id = "jtable-table"

    mandatory_params = ["vid", "rql_labels", "ajaxcallback", "labels",
                        "title", "elts_to_sort", "csvcallback",
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
             csvcallback=False, title="", elts_to_sort=None,
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
            a function thaty will be called by jtable to create dynamically the
            data to display: do not foget the decorator @ajaxfunc.
        csvcallback: bool (optional)
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
        if self._cw.form.get("csvcallback", None) is not None:
            csvcallback = self._cw.form.get("csvcallback")
        elts_to_sort = elts_to_sort or self._cw.form.get("elts_to_sort", [])
        if not isinstance(elts_to_sort, list):
            elts_to_sort = [elts_to_sort]
        if "use_server" in self._cw.form:
            use_server = eval(self._cw.form.get("use_server"))

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Add css resources
        self._cw.add_css("datatables-1.10.5/media/css/jquery.dataTables.min.css")
        self._cw.add_css("datatables-1.10.5/extensions/FixedColumns/css/"
                         "dataTables.fixedColumns.css")
        self._cw.add_css(
            "https://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css",
            localfile=False)

        # Add js resources
        self._cw.add_js("datatables-1.10.5/media/js/jquery.js")
        self._cw.add_js("datatables-1.10.5/media/js/jquery.dataTables.min.js")
        self._cw.add_js("datatables-1.10.5/extensions/FixedColumns/js/"
                        "dataTables.fixedColumns.js")
        self._cw.add_js("datatables-1.10.5/extensions/fnSetFilteringDelay.js")
        self._cw.add_js("https://code.jquery.com/ui/1.11.4/jquery-ui.js",
                        localfile=False)

        # Get table meta information
        if rql_labels is not None:
            labels = self._cw.execute(rql_labels)
        if rql_labels is None and labels is not None:
            labels = [[str(item)] for item in labels]
        if labels is None:
            raise Exception("No labels can be selected while creating the "
                            "jtable")

        # Get the instance questionnaire map
        qmap = self._cw.vreg.docmap

        # Associate a tooltip to each label
        tooltips = [""]
        for label_text in labels:
            label_text = label_text[0]
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
        label_list = ["ID"]
        if "ID" not in elts_to_sort:
            hide_sort_indices.append(0)
        for cnt, label_text in enumerate(labels):

            # >> select if we can sort this column
            if label_text[0] not in elts_to_sort:
                hide_sort_indices.append(cnt + 1)

            # >> add this column to the table definition parameters
            label_list.append(label_cleaner(label_text[0]))
            if label_text[0] in qmap:
                tiphref = self._cw.build_url(
                    "view", vid="piws-documentation",
                    tooltip_name=label_text[0], _notemplate=True)
                headers.append(
                    {"sTitle": "<a href='{0}' target=_blank>"
                               "<span class='fake-link'>{1} &#9735"
                               "</span></a>".format(tiphref, label_text[0])})
            else:
                headers.append({"sTitle": label_text[0]})

        # > begin the script
        html = "<script type='text/javascript'> "
        html += "$(document).ready(function() {"

        # > create the table
        html += "var table = $('#the_table').dataTable( { "

        # > set table display options
        html += "'scrollX': '100%',"
        html += "'scrollY': '600px',"
        html += "'scrollCollapse': true,"
        html += "'sPaginationType': 'bootstrap',"
        if csvcallback:
            html += "'dom': 'T<\"clear\">l<\"toolbar\">frtip',"
        else:
            html += "'dom': 'T<\"clear\">lfrtip',"
        html += "'lengthMenu': [ [10, 25, 50, 100, -1], [10, 25, 50, 100, 'All'] ],"
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
        html += "value: '{0}'".format(json.dumps(label_list))
        html += "}, "
        for key, value in kwargs.items():
            if isinstance(value, basestring):
                html += "{{name: '{0}', value: '{1}'}}, ".format(key, str(value))
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

        if csvcallback:

            # > create a new csv download button
            csv_button_html = (u'<p><a class="btn btn-default" role="button" '
                               u'id="csv_button">CSV Export »</a></p>')
            html += u"$('div.toolbar').html('{0}');".format(csv_button_html)

            # > center the search-bar
            html += ("$('#the_table_filter').css({'float': 'none', "
                     "'text-align': 'center'});")

            # > assign ajax callback to csv button : start function click
            html += "$( '#csv_button' ).click(function() {"
            # # > display a processing message
            html += "$('#loadingmessage').show();"
            #
            # # > get information from the data table
            html += "var dt = new $.fn.dataTable.Api( table );"
            html += "var postData = dt.ajax.params() || {};"

            # > set options to retrieve all the full result set from the ajax
            # callback
            html += "postData.iDisplayStart = 0;"
            html += "postData.iDisplayLength = -1;"
            html += "postData.sSearch = '';"

            # > execute the ajax callback
            html += "var post = $.ajax({"
            html += "url: dt.ajax.url(),"
            html += "type: 'POST',"
            html += "data: postData"
            html += "});"

            # > the ajax callback is done, get the result set
            html += "post.done(function(p){"
            html += "var jdata = p.aaData;"
            html += "headers = JSON.parse(postData.labels);"
            html += "var csvRows = [headers.join(';')];"
            html += "csvRows.push({0}.join(';'));".format(json.dumps(tooltips))
            html += "for(var i=0, l=jdata.length; i<l; ++i){"
            html += "csvRows.push(jdata[i].join(';'));"
            html += "}"

            # > create a download link
            html += "var csvString = csvRows.join('\\r\\n');"
            html += "var a = document.createElement('a');"
            html += ("a.href = 'data:application/csv;charset=utf-8,' "
                     "+ encodeURIComponent(csvString);")
            html += "a.target = '_blank';"
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H:%M:%S")
            if "timepoint" in kwargs:
                csv_file_name = "{0}_{1}_{2}.csv".format(
                    title, kwargs["timepoint"], st)
            else:
                csv_file_name = "{0}_{1}".format(title, st)
            html += "a.download = '{0}';".format(csv_file_name)

            # > hide the processing message
            html += "document.body.appendChild(a);"
            html += "a.click();"
            html += "$('#loadingmessage').hide();"
            html += "});"

            # > if the ajax callback failed display an alert
            html += "post.fail(function(){"
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
                 "align='center'><img src='{0}'/></div>".format(wait_image_url))

        # > display the table in the body
        html += "<table id='the_table' class='cell-border display'>"
        html += "<thead></thead>"
        html += "<tbody></tbody>"
        html += "</table>"

        # Creat the corrsponding html page
        self.w(unicode(html))


###############################################################################
# Define a function that clean a string
###############################################################################

_ILLEGAL_CHARACTERS = "\\/:*%.()?\"'<>| \t\r\n\0"
_CLEANUP_TABLE = maketrans(_ILLEGAL_CHARACTERS, "_" * len(_ILLEGAL_CHARACTERS))


def label_cleaner(string_label):
    """ Get rid of illegal characters.

    Replace characters that are illegal in jtable labels.
    - Windows reserved characters
    - spaces, tab, newline and null character

    Parameters
    ----------
    string_label: str
        string to cleanup.

    Returns
    -------
    cleaned_label: str
        string with illegal characters replaced.
    """
    return str(string_label).translate(_CLEANUP_TABLE)


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
           "Where QR is QuestionnaireRun, QR instance_of Q, Q name '{1}', "
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

        # Start filling the tabel dataset
        dstruct = [""] * len(labels)
        dstruct[0] = filtered_rset[row_nb][0]

        # Execute an rql to get the subject answers
        questionnaire_run_eid = filtered_rset[row_nb][1]
        rql = ("Any QN, V Where QR eid '{0}', QR open_answers A, A question Q,"
               "Q text QN, A value V".format(questionnaire_run_eid))
        answer_rset = self._cw.execute(rql)

        # Go through all answers
        for qname, answer in answer_rset:
            answer_index = labels.index(label_cleaner(qname))
            dstruct[answer_index] = answer

        # Store the tabel formated row
        records.append(dstruct)

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
    column_to_filter = int(self._cw.form['iSortCol_0'])

    # Only the ID column can be filtered
    if column_to_filter != 0:
        raise Exception("Only the 'ID' column can be filtered by "
                        "'get_questionnaires_data' ajax callback.")

    # Deal with sort options
    jtsort = "ORDERBY ID {0}".format(jtsort)

    # Get all the questionnaire and associated timepoints
    rql = ("DISTINCT Any ID, T {0} "
           "Where Q is Questionnaire, QR is QuestionnaireRun, "
           "QR instance_of Q, QR in_assessment A, Q name ID, "
           "A timepoint T".format(jtsort))
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
            qstruct.setdefault(qname, []).append(
                label_cleaner(timepoint))

    # Open answer table parameters
    ajaxcallback = "get_open_answers_data"
    rql_labels = ("Any QUT ORDERBY QUT WHERE Q is Questionnaire, Q name '{0}', "
                  "Q questions QU, QU text QUT")

    # Define start and stop display index for pagination
    lower = jtstartindex
    # If ALL results are selected
    if jtpagesize == -1:
        higher = total_nb_of_rows
    else:
        higher = min(jtstartindex+jtpagesize, len(qstruct))

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
                "view", vid="jtable-table",
                rql_labels=rql_labels.format(qname),
                ajaxcallback=ajaxcallback, title=qname, tooltip_name=qname,
                qname=qname, timepoint=timepoint, elts_to_sort=["ID"],
                csvcallback=True)
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
    vreg.register(JtableView)
    vreg.register(JhugetableView)
    vreg.register(get_open_answers_data)
    vreg.register(get_questionnaires_data)
