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
import os
import copy

# CUBICWEB import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc
from cubicweb.web.views.csvexport import CSVMixIn


###############################################################################
# Jtable
###############################################################################

class JtableView(View):
    """ Create a table view with Jtable.
    """
    __regid__ = "jtable-table"
    paginable = False
    div_id = "jtable-table"

    mandatory_params = ["vid", "rql_labels", "ajaxcallback",
                        "title", "elts_to_sort", "csvcallback"]

    def __init__(self, *args, **kwargs):
        """ Initialize the JtableView class.

        If you want to construct the table manually in your view pass the
        parent view in the 'parent_view' attribute.
        """
        super(JtableView, self).__init__(*args, **kwargs)
        if "parent_view" in kwargs:
            self._cw = kwargs["parent_view"]._cw
            self.w = kwargs["parent_view"].w

    def call(self, rql_labels=None, ajaxcallback=None,
             csvcallback=None, title="", elts_to_sort=None, **kwargs):
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
        rql_labels: string (mandatory)
            a rql that will be executed to get the columns labels.
        ajaxcallback: @func (mandatory)
            a function thaty will be called by jtable to create dynamically the
            data to display: do not foget the decorator @ajaxfunc.
        csvcallback: @func (optional)
            if an ajax callback is given then an export button will be
            available.
        title: string (optional, default '')
            the title of the table.
        """
        # Get the parameters
        for key in sorted(self._cw.form.keys()):
            if key not in self.mandatory_params:
                kwargs[key] = self._cw.form[key]
        title = title or self._cw.form.get("title", "")
        rql_labels = rql_labels or self._cw.form.get("rql_labels", "")
        ajaxcallback = ajaxcallback or self._cw.form.get("ajaxcallback", "")
        csvcallback = csvcallback or self._cw.form.get("csvcallback", None)
        elts_to_sort = elts_to_sort or self._cw.form.get("elts_to_sort", [])
        if not isinstance(elts_to_sort, list):
            elts_to_sort = [elts_to_sort]

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Add css resources
        self._cw.add_css("datatables-1.10.5/media/css/jquery.dataTables.min.css")
        self._cw.add_css("datatables-1.10.5/extensions/TableTools/css/"
                         "dataTables.tableTools.min.css")
        self._cw.add_css("datatables-1.10.5/extensions/FixedColumns/css/"
                         "dataTables.fixedColumns.css")

        # Add js resources
        self._cw.add_js("datatables-1.10.5/media/js/jquery.js")
        self._cw.add_js("datatables-1.10.5/media/js/jquery.dataTables.min.js")
        self._cw.add_js("datatables-1.10.5/extensions/TableTools/js/"
                         "dataTables.tableTools.min.js")
        self._cw.add_js("datatables-1.10.5/extensions/FixedColumns/js/"
                        "dataTables.fixedColumns.js")
        self._cw.add_js("datatables-1.10.5/extensions/fnSetFilteringDelay.js")

        # Add swf resources
        swf_export = self._cw.data_url("datatables-1.10.5/extensions/"
                                       "TableTools/swf/copy_csv_xls.swf")

        # Get table meta information
        labels = self._cw.execute(rql_labels)

        # Generate the script

        # > table column headers and sort option
        headers = [{"sTitle": "ID"}]
        hide_sort_indices = []
        label_list = ["ID"]
        for cnt, label_text in enumerate(labels):
            
            # >> select if we can sort this column
            if label_text[0] not in elts_to_sort:
                hide_sort_indices.append(cnt + 1)

            # >> add this column to the table definition parameters
            label_list.append(label_cleaner(label_text[0]))
            headers.append({"sTitle": label_text[0]})

        # > create the table
        html = "<script type='text/javascript'> "
        html += "$(document).ready(function() {"
        html += "var table = $('#the_table').dataTable( { "

        # > set table display options
        html += "'scrollX': '100%',"
        html += "'scrollY': '600px',"
        html += "'scrollCollapse': true,"
        html += "'sPaginationType': 'bootstrap',"
        html += "'dom': 'T<\"clear\">lfrtip',"
        html += "'lengthMenu': [ [10, 25, 50, 100, -1], [10, 25, 50, 100, 'All'] ],"
        html += "'sServerMethod': 'POST',"
        html += "'oLanguage': {'sSearch': 'ID'},"
        html += "'pagingType': 'full_numbers',"
        html += "'bProcessing': true,"
        html += "'bServerSide': true,"

        # > export csv options
        buttons = "'copy', 'print'"
        if csvcallback is not None:
            # >> create a custom button to download all the table
            export_button = (
                "{'sExtends': 'ajax', 'sButtonText': 'CSV - All results', ")
            # >> when you click the button display a processing message and
            # >> run the callback
            export_button += "'fnClick': function () { "
            export_button += "$('#loadingmessage').show();"
            export_button += "var post = $.ajax({ "
            export_button += "url: 'ajax?fname={0}', ".format(csvcallback)
            export_button += "type: 'POST', "
            export_button += "dataType: 'json', "
            csv_callback_parms = copy.deepcopy(kwargs)
            csv_callback_parms["rql_labels"] = rql_labels
            export_button += "data: {0}".format(json.dumps(csv_callback_parms))
            export_button += "}); "
            # >> handle sucess case
            export_button += "post.done(function(p){ "
            export_button += "window.location = p.dl_url; "
            export_button += "$('#loadingmessage').hide(); "
            export_button += "});"
            # >> handle error case
            export_button += "post.fail(function(){ "
            export_button += "$('#loadingmessage').hide(); "
            export_button += "alert('Error : Download Failed!'); "
            export_button += "}); "
            # >> end click event
            export_button += "}"
            # >> end custom button
            export_button += "} "
            buttons += ", 'csv', {0}".format(export_button)

        # > display the export buttons
        html += ("'tableTools': {{ "
                 "'sRowSelect': 'multi', "
                 "'sSwfPath': '{0}', "
                 "'aButtons': [{1}] }}, ".format(swf_export, buttons))

        # > set table header
        html += "'aoColumns': {0},".format(json.dumps(headers))

        # > set sort widget on column
        html += "'aoColumnDefs': [ "
        html += "{{ 'bSortable': false, 'aTargets': {0} }}".format(str(hide_sort_indices))
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

        # > close script
        html += "} );"

        # Close script div
        html += "</script>"

        # > set a title
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
# CW CSV tuned export
###############################################################################

class CSVJtableView(CSVMixIn, View):
    """ Dumps a jtable in a CSV.
    """
    __regid__ = "jtable-csvexport"
    title = _("csv export")

    def call(self, rql=None, rql_labels=None):
        """ Dump a table in csv format.

        A rql is executed where the first returned element is expected to be
        the row identifier 'ID'.

        Parameters
        ----------
        rql: str (mandatory)
            the rql to execute in order to fill the desired table.
        rql_labels: string (mandatory)
            a rql that will be executed to get the columns labels.
        """
        # Get function parameters
        rql = rql or self._cw.form.get("rql", "")
        rql_labels = rql_labels or self._cw.form.get("rql_labels", "")

        # Get the questionnaire associated questions
        header = [item[0] for item in self._cw.execute(rql_labels)]

        # Execute the full request
        rset = self._cw.execute(rql)

        # Create a structure to be able to sort by subject id
        jtable_data = OrderedDict()
        for item in rset:
            if item[0] not in jtable_data:
                jtable_data[item[0]] = OrderedDict((key, "nc")
                                                   for key in header)
            jtable_data[item[0]][item[1]] = item[2]

        # Create a CW csv writer
        writer = self.csvwriter()

        # Write a header row
        writer.writerow(header)

        # Write the jtable content row by row
        for rowid, data in jtable_data.iteritems():
            writer.writerow([rowid] + data.values())


###############################################################################
# Interact with jtable js
###############################################################################

@ajaxfunc(output_type="json")
def csv_open_answers_export(self):
    """ Export the answers in the database in csv format.

    Parameters
    ----------
    rql_labels: string (mandatory)
        a rql that will be executed to get the columns labels.
    qname: string (mandatory)
        the name of the questionnaire we want to export.
    timepoint: string (mandatory)
        filter request on a timepoint.

    Returns
    -------
    link: dict
        the table structure that contains the download link.
    """
    # Get parameters
    rql_labels = self._cw.form["rql_labels"]
    qname = self._cw.form["qname"]
    timepoint = self._cw.form["timepoint"]

    # Define the full request
    rql = ("Any ID, QUT, OAV "
           "Where OA is OpenAnswer, OA questionnaire_run QR, "
           "OA question QU, QR in_assessment A, A timepoint '{0}', "
           "QR instance_of Q, Q name '{1}', OA value OAV, QU text QUT, "
           "QR concerns S, S code_in_study ID".format(timepoint, qname))

    # Build the download url
    url = self._cw.build_url("view", vid="jtable-csvexport", rql=rql,
                             rql_labels=rql_labels)

    # Create the export jtable structure
    link = {"dl_url": url}

    return link


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

    # Get the all the questionnaire runs and associated subjects
    rql = ("Any ID, QR {0} "
           "Where QR is QuestionnaireRun, QR concerns S, S code_in_study ID, "
           "QR instance_of Q, Q name '{1}', QR in_assessment A, "
           "A timepoint '{2}'".format(jtsort, qname, timepoint))
    rset = self._cw.execute(rql)

    # Filter the rset with the ID pattern
    filtered_rset = []
    for item in rset:
        if id_pattern == "" or id_pattern in item[0]:
            filtered_rset.append([item[0], item[1]])

    # Set the appropriate range to access the data
    # > if the user want to show all the results
    if jtpagesize == -1 or jtpagesize > len(rset):
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
        rql = "Any QN, V Where QR eid '{0}', A is OpenAnswer, " \
              "A questionnaire_run QR, A question Q, Q text QN, " \
              "A value V".format(questionnaire_run_eid)
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
        the current index provided by jtable.
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

    # Get the all the questionnaire and associated timepoints
    rql = ("DISTINCT Any ID, T {0} "
           "Where Q is Questionnaire, QR is QuestionnaireRun, "
           "QR instance_of Q, QR in_assessment A, Q name ID, "
           "A timepoint T".format(jtsort))
    rset = self._cw.execute(rql)

    # Filter the rset with the ID pattern
    filtered_rset = []
    nb_of_rows = len(set([item[0] for item in rset]))
    for item in rset:
        if id_pattern == "" or id_pattern in item[0]:
            filtered_rset.append([item[0], item[1]])

    # Create a structure to be able to sort by questionnaire name
    qstruct = OrderedDict()
    for item in filtered_rset:
        qstruct.setdefault(item[0], []).append(
            label_cleaner(item[1]))

    # Open answer table parameters
    ajaxcallback = "get_open_answers_data"
    rql_labels = ("Any QUT ORDERBY QUT WHERE Q is Questionnaire, "
                  "QU questionnaire Q, QU text QUT, "
                  "Q name '{0}'")

    # Build the dict that will be dumped in the table
    records = []
    for qname in qstruct.keys():

        # Start filling the tabel dataset
        dstruct = [""] * len(labels)
        dstruct[0] = qname

        # Go through all decalred timepoints
        for timepoint in qstruct[qname]:

            # Construct the answer table view
            href = self._cw.build_url(
                "view", vid="jtable-table",
                rql_labels=rql_labels.format(qname),
                ajaxcallback=ajaxcallback, title=qname,
                qname=qname, timepoint=timepoint, elts_to_sort=["ID"],
                csvcallback="csv_open_answers_export")
            timepoint_index = labels.index(timepoint)
            dstruct[timepoint_index] = "<a href='{0}'>link</a>".format(href)

        # Store the tabel formated row
        records.append(dstruct)

    # Table formatting
    data = {"iTotalRecords": nb_of_rows,
            "iTotalDisplayRecords": len(qstruct),
            "aaData": records}

    return data


###############################################################################
# Update CW registery
###############################################################################

def registration_callback(vreg):
    vreg.register(JtableView)
    vreg.register(get_open_answers_data)
    vreg.register(get_questionnaires_data)
    vreg.register(csv_open_answers_export)
    vreg.register(CSVJtableView)
