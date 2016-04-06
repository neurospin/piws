##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import json

# Cubicweb import
from cubicweb.view import View


class QuestionnaireLongitudinalView(View):
    """ Create a view that summarized the longitudinal material for a subject.
    """
    __regid__ = "questionnaire-longitudinal-measures"
    title = _("Longitudinal")
    paginable = False
    div_id = "questionnaire-longitudinal-measures"

    def call(self, rset=None, patient_id="", **kwargs):
        """ Method that will create the subject longitudinal views.

        If no resultset are passed to this method, the current resultset is
        used.

        Only digits answers are considered.

        Parameters
        ----------
        rset: resultset (optional, default None)
            a  cw resultset
        patient_id: string (optional, default None)
            the patient identifier.
        """
        # Get the cw resultset
        rset = rset or self.cw_rset

        # Get the method parameters: if we use 'build_url' method, the data
        # are in the firm dictionary
        patient_id = patient_id or self._cw.form.get("patient_id", "")

        # Add some js resources
        self._cw.add_js(
            ("highcharts-4.0.4/js/highcharts.js",
             "highcharts-4.0.4/js/modules/exporting.js")
        )

        # Get the data from the result set
        questionnaires = {}
        for line_number in range(rset.rowcount):

            # Get the questionnaire run entity
            qr_entity = rset.get_entity(line_number, 0)

            # Get the questionnaire run timepoint
            timepoint = qr_entity.in_assessment[0].timepoint

            # Get the associated questionnaire/questions
            q_entity = qr_entity.questionnaire[0]
            if q_entity.name not in questionnaires:
                questionnaires[q_entity.name] = dict(
                    (entity.text, {})
                    for entity in q_entity.questions)

            # Get the questionnaire run associated answers and fill the
            # 'questionnaires' structure
            # > case 1: one line of answers inserted per subject (File)
            # > case 2: the answers are inserted in the database (OpenAnswer).
            if len(qr_entity.file) > 0:
                answers = json.loads(qr_entity.file[0].data.getvalue())
                for qname, answer in answers.items():
                    questionnaires[q_entity.name][qname][timepoint] = str(
                        answer)
            else:
                answer_entities = qr_entity.open_answers
                for entity in answer_entities:
                    questionnaires[q_entity.name][entity.question[0].text][
                        timepoint] = entity.value




        # Create a selector
        html = ("<h1>Please select a measure to follow accross the timepoints "
                "in this list:</h1>")
        html += "<select class='selectpicker' data-live-search='true'>"
        html += "<option></option>"
        for questionnaire_name, questions in questionnaires.iteritems():
            html += "<optgroup label='{0}' data-icon='glyphicon-heart'>".format(
                questionnaire_name)
            for question_name, question_item in questions.iteritems():

                # Get the plot data
                data = sorted(question_item.items())
                values = [p[1] for p in data]

                # Check if we are dealing with numbers
                control_value = values[0].replace(".", "", 1)
                if control_value.isdigit():
                    html += "<option value='{0}'>{0}</option>".format(
                        question_name)
            html += "</optgroup>"
        html += "</select>"

        # Ceate a div to display the plots
        html += ("<div id='longitudinal-plot' style='min-width: 310px; "
                 "height: 400px; max-width: 600px; margin: 0 auto'></div>")

        # Convert the input data
        html += "<script type='text/javascript'>"
        html += "var jdata = {};"
        for q_name, q_item in questionnaires.iteritems():
            for question_name, question_item in q_item.iteritems():

                # Get the plot data
                data = sorted(question_item.items())
                values = [p[1] for p in data]

                # Check if we are dealing with numbers
                control_value = values[0].replace(".", "", 1)
                if control_value.isdigit():
                    html += "var sdata = {};"
                    html += "sdata['x'] = [];".format(question_name)
                    html += "sdata['grid'] = [];".format(question_name)
                    html += "sdata['related_question'] = '{0}';".format(question_name)
                    html += "sdata['related_questionnaire'] = '{0}';".format(q_name)
                    for p in data:
                        html += "sdata['x'].push('{0}');".format(p[0])
                        html += "sdata['grid'].push({0});".format(p[1])
                    html += "jdata['{0}'] = sdata;".format(question_name)

        # Add an event when the selection change
        html += "$(function() {"
        html += "$('.selectpicker').on('change', function(){"
        html += "var selected = $(this).find('option:selected').val();"
        html += "if (selected != ''){"
        html += "$('#longitudinal-plot').highcharts({"
        html += "credits : {enabled : false}, "
        html += ("title: {{text: jdata[selected]['related_questionnaire'] + "
                 "'-' + jdata[selected]['related_question'] + "
                 "': {0}'}},".format(patient_id))
        html += "xAxis: {categories: jdata[selected]['x']},"
        html += "yAxis: {title: {text: ''}},"
        html += "legend: {layout: 'vertical', align: 'right', verticalAlign:"
        html += "'middle', borderWidth: 0},"
        html += "series: [{name: 'longitudinal', data: jdata[selected]['grid']}]"
        html += "});"
        html += "}"
        html += "});"
        html += "});"
        html += "</script>"

        # Display the page content
        self.w(unicode(html))
