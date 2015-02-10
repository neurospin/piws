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

    mandatory_params = ["vid", "rql_rows", "rql_labels", "ajaxcallback",
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

    def call(self, rql_rows=None, rql_labels=None, ajaxcallback=None,
             csvcallback=None, title="", elts_to_sort=None, **kwargs):
        """ Method that will create a table.

        When right clicking on the table header, you can choose to hide some
        columns.

        When left clicking on a row, the row is selected (highlighted) Click
        again on this row to deselect it.

        On the right side of each herder box, you can decide to sort the the
        the row.

        1) Extra parameters will be sorted by names and passed to the ajax
        callback.

        2) Column labels must not contain space ' ' and they need to be
        replaced: use the 'label_cleaner' function.

        3) A special 'ID' column must be specified in the ajax callback that
        contains the row string description.

        4) All the sortable items must be handle in the ajax callback.

        Parameters
        ----------
        rql_rows: string (mandatory)
            a rql that will be executed to get the number of rows in the table.
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
        rql_rows = rql_rows or self._cw.form.get("rql_rows", "")
        rql_labels = rql_labels or self._cw.form.get("rql_labels", "")
        ajaxcallback = ajaxcallback or self._cw.form.get("ajaxcallback", "")
        csvcallback = csvcallback or self._cw.form.get("csvcallback", None)
        elts_to_sort = elts_to_sort or self._cw.form.get("elts_to_sort", [])
        if not isinstance(elts_to_sort, list):
            elts_to_sort = [elts_to_sort]

        # Add some js resources
        self._cw.add_js("jtable-2.4.0/jquery.jtable.min.js")
        self._cw.add_css("jtable-2.4.0/themes/lightcolor/blue/jtable.css")

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Get table meta information
        labels = self._cw.execute(rql_labels)
        nb_rows = self._cw.execute(rql_rows)[0][0]
        nb_cols = len(labels)

        # Generate the script

        # > table column headers
        headers_str = "ID@"
        fields_str = "{"
        sort_val = "false"
        if "ID" in elts_to_sort:
            sort_val = "true"
        fields_str += "ID:{{key:true,title:'> ID',sorting:{0}}},".format(
            sort_val)
        for label_text in labels:
            sort_val = "false"
            if label_text[0] in elts_to_sort:
                sort_val = "true"
            fields_str += "{0}:{{title:'{1}',sorting:{2}}},".format(
                label_cleaner(label_text[0]),
                "> " + label_text[0].replace(" ", ""), sort_val)
            headers_str += "{0}@".format(label_cleaner(label_text[0]))
        fields_str += "}"

        # > create a div for the in progress resource
        html = ("<div id='loadingmessage' style='display:none' "
                "align='center'><img src='{0}'/></div>".format(wait_image_url))

        # > create a div to display a scroll bar
        html += "<div style='overflow:auto;height: 100%; width: 90%;'>"
        html += "<div id='PatientTableContainer'></div>"

        # > create the table
        html += "<script type='text/javascript'> "
        html += "$(document).ready(function () { "
        html += "$('#PatientTableContainer').jtable({"

        # > set a title
        html += "title: '{0}',".format(title)

        # > set table display options
        html += "paging: true,"
        html += "pageSize: 10,"
        html += "selecting: true,"
        html += "multiselect: true,"
        html += "columnResizable: true,"
        html += "sorting: true,"
        html += "multiSorting: false,"
        html += "selectingCheckboxes: true,"
        html += "defaultSorting: 'undefined',"

        # > export csv options
        if csvcallback is not None:
            html += ("toolbar: {hoverAnimation: true, "
                     "hoverAnimationDuration: 5, "
                     "hoverAnimationEasing: undefined, items: [{icon: "
                     "'/images/excel.png', text: 'CSV export', "
                     "click: function() {")

            # > export csv callback
            html += "$('#loadingmessage').show();"
            html += "var post = $.ajax({"
            html += ("url: 'json?fname={0}'".format(csvcallback))
            html += " + '&arg=' + '\"{0}\"'".format(headers_str)
            for key, value in kwargs.items():
                if isinstance(value, basestring):
                    html += " + '&arg=' + '\"{0}\"'".format(str(value))
                else:
                    html += " + '&arg=' + {0}".format(value)
            html += ","
            html += "data: {json: JSON.stringify({dl_url: 'stringify'})},"
            html += "type: 'POST'});"

            # > export csv redirection: success
            html += "post.done(function(p){"
            html += "window.location = p.dl_url;"
            html += "$('#loadingmessage').hide();"
            html += "});"

            # > export csv redirection: success
            html += "post.fail(function(){"
            html += "$('#loadingmessage').hide();"
            html += "alert('Error : Download Failed!');"
            html += "});"

            # > export csv callback end
            html += "}"

            # > export csv options end
            html += "}]},"

        # > continue export csv options: callback to get the data dynamically
        html += "actions: {"
        html += "listAction: function (postData, jtParams) {"
        html += "return $.Deferred(function ($dfd) {"
        html += "$.ajax({"
        html += ("url: 'json?fname={0}&"
                 "arg=\"' + jtParams.jtSorting + "
                 "'\"&arg=' + jtParams.jtStartIndex + "
                 "'&arg=' + jtParams.jtPageSize + "
                 "'&arg=' + {1} + '&arg=' + {2}".format(ajaxcallback,
                                                        nb_rows, nb_cols))
        for key, value in kwargs.items():
            if isinstance(value, basestring):
                html += " + '&arg=' + '\"{0}\"'".format(str(value))
            else:
                html += " + '&arg=' + {0}".format(value)
        html += ","
        html += "type: 'POST',"
        html += "dataType: 'json',"
        html += "data: postData,"
        html += "success: function (data) {"
        html += "$dfd.resolve(data);"
        html += "},"
        html += "error: function () {"
        html += "$dfd.reject();"
        html += "}"
        html += "});"
        html += "});"
        html += "},"
        html += "},"

        # > continue export csv options: column labels
        html += "fields: "
        html += fields_str
        html += "});"

        # > load the table data
        html += "$('#PatientTableContainer').jtable('load');"
        html += "});"

        # Close script div
        html += "</script>"

        # Close scrollbar div
        html += "</div>"

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

    def call(self, rql=None, header=None):
        """ Dump a table in csv format.

        A rql is executed where the first returned element is expected to be
        the row identifier 'ID'.

        Parameters
        ----------
        rql: str (mandatory)
            the rql to execute in order to fill the desired table.
        header: list of str (mandatory)
            the jtable headers.
        """
        # Get function parameters
        rql = rql or self._cw.form.get("rql", "")
        header = header or self._cw.form.get("header", "")

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
def csv_open_answers_export(self, header, qname, timepoint):
    """ Export the answers in the database in csv format.

    Parameters
    ----------
    header: string (mandatory)
        the jtable header elements separated by the '@' character.
    qname: string (mandatory)
        the name of the questionnaire we want to export.
    timepoint: string (mandatory)
        filter request on a timepoint.

    Returns
    -------
    link: dict
        the jtable structure that contains the download link.
    """
    # Execute the full request
    rql = ("Any ID, QUT, OAV "
           "Where OA is OpenAnswer, OA questionnaire_run QR, "
           "OA question QU, QR in_assessment A, A timepoint '{0}', "
           "QR instance_of Q, Q name '{1}', OA value OAV, QU text QUT, "
           "QR concerns S, S code_in_study ID".format(timepoint, qname))

    # Split the headers
    header = header.split("@")

    # Build the download url
    url = self._cw.build_url("view", vid="jtable-csvexport", rql=rql,
                             header=header)

    # Create the export jtable structure
    link = {"dl_url": url}

    return link


@ajaxfunc(output_type="json")
def get_open_answers_data(self, jtsort, jtstartindex, jtpagesize,
                          nb_rows, nb_cols, qname, timepoint):
    """ Get the subject answer data formated for jtable.

    Parameters
    ----------
    jtsort: str
        the sorting option to use.
    jtstartindex: int
        the current index provided by jtable.
    jtpagesize: int
        the number of rows per page.
    nb_rows: int
        the total number of rao elements in the table.
    nb_cols: int
        if the rql request return multiple line that must be displayed in one
        row use this parameter as an offset.
    qname: string (mandatory)
        the name of the questionnaire we want to export.
    timepoint: string (mandatory)
        filter request on a timepoint.

    Returns
    -------
    data: dict
        the jtable content.
    """
    # Deal with sort options
    if jtsort not in ["undefined", "ID ASC", "ID DESC"]:
        raise ValueError("Unsupported sort key '{0}'.".format(jtsort))
    if jtsort == "undefined":
        jtsort = ""
    else:
        jtsort = "ORDERBY {0}".format(jtsort)

    # Get the all the answers and associated subjects
    rql_all = ("Any ID, QUT, OAV {0} LIMIT {1} OFFSET {2} "
               "Where OA is OpenAnswer, OA questionnaire_run QR, "
               "OA question QU, QR in_assessment A, A timepoint '{3}', "
               "QR instance_of Q, Q name '{4}', OA value OAV, QU text QUT, "
               "QR concerns S, S code_in_study ID".format(
                   jtsort, int(jtpagesize * nb_cols),
                   int(jtstartindex * nb_cols), timepoint, qname))
    rset_all = self._cw.execute(rql_all)

    # Create a structure to be able to sort by subject id
    sstruct = OrderedDict()
    for item in rset_all:
        sstruct.setdefault(item[0], []).append(
            (label_cleaner(item[1]), item[2]))

    # Build the dict that will be dumped in the jtable
    records = []
    for subject_id, answer_items in sstruct.iteritems():

        # Start filling the jtabel dataset
        dstruct = {"ID": subject_id}

        # Go through all answers
        for qname, answer in answer_items:
            dstruct[qname] = answer

        # Store the jtabel formated row
        records.append(dstruct)

    # Jtable formatting
    data = {"Result": "OK",
            "Records": records,
            "TotalRecordCount": nb_rows}

    return data


@ajaxfunc(output_type="json")
def get_questionnaires_data(self, jtsort, jtstartindex, jtpagesize, nb_rows,
                            nb_cols):
    """ Get the questionnaires data formated for jtable.

    Parameters
    ----------
    jtsort: str
        the sorting option to use.
    jtstartindex: int
        the current index provided by jtable.
    jtpagesize: int
        the number of rows per page.
    nb_rows: int
        the total number of rao elements in the table.
    nb_cols: int
        if the rql request return multiple line that must be displayed in one
        row use this parameter as an offset.

    Returns
    -------
    data: dict
        the jtable content.
    """
    # Deal with sort options
    if jtsort not in ["undefined", "ID ASC", "ID DESC"]:
        raise ValueError("Unsupported sort key '{0}'.".format(jtsort))
    if jtsort == "undefined":
        jtsort = ""
    else:
        jtsort = "ORDERBY {0}".format(jtsort)

    # Get the all the questionnaire and associated timepoints
    rql = ("DISTINCT Any ID, T {0} LIMIT {1} OFFSET {2} "
           "Where Q is Questionnaire, QR is QuestionnaireRun, "
           "QR instance_of Q, QR in_assessment A, Q name ID, "
           "A timepoint T".format(jtsort, int(jtpagesize * nb_cols),
                                  int(jtstartindex * nb_cols)))
    rset = self._cw.execute(rql)

    # Create a structure to be able to sort by questionnaire name
    qstruct = OrderedDict()
    for item in rset:
        qstruct.setdefault(item[0], []).append(
            label_cleaner(item[1]))

    # Open answer jtable parameters
    ajaxcallback = "get_open_answers_data"
    rql_rows = ("Any COUNT(SID) WHERE QR is QuestionnaireRun, "
                "QR concerns S, S code_in_study SID, "
                "QR instance_of Q, Q name '{0}', QR in_assessment A,"
                "A timepoint '{1}'")
    rql_labels = ("Any QUT ORDERBY QUT WHERE Q is Questionnaire, "
                  "QU questionnaire Q, QU text QUT, "
                  "Q name '{0}'")

    # Build the dict that will be dumped in the jtable
    records = []
    for qname in qstruct.keys():

        # Start filling the jtabel dataset
        dstruct = {"ID": qname}

        # Go through all decalred timepoints
        for timepoint in qstruct[qname]:

            # Construct the answer table view
            href = self._cw.build_url(
                "view", vid="jtable-table",
                rql_rows=rql_rows.format(qname, timepoint),
                rql_labels=rql_labels.format(qname),
                ajaxcallback=ajaxcallback, title=qname,
                qname=qname, timepoint=timepoint, elts_to_sort=["ID"],
                csvcallback="csv_open_answers_export")
            dstruct[timepoint] = "<a href='{0}'>link</a>".format(href)

        # Store the jtabel formated row
        records.append(dstruct)

    # Jtable formatting
    data = {"Result": "OK",
            "Records": records,
            "TotalRecordCount": nb_rows}

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