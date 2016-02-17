##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import collections

# Cubicweb import
from cubicweb.predicates import is_instance
from cubicweb.view import EntityView

# Brainomics import
from cubes.brainomics.views.outofcontext import ScanOutOfContextView
from cubes.brainomics.views.outofcontext import AssessmentOutOfContextView
from cubes.brainomics.views.outofcontext import QuestionnaireRunOutOfContextView
from cubes.brainomics.views.outofcontext import SubjectOutOfContextView

# PIWS import
from components import AUTHORIZED_IMAGE_EXT


###############################################################################
# Base
###############################################################################

class BaseOutOfContextView(EntityView):
    __regid__ = "outofcontext"
    __select__ = False

    def entity_description(self, entity):
        """ Generate a dictionary with the entity description.
        """
        return {}

    def cell_call(self, row, col):
        """ Create the out of context view template
        """
        # Get the entity
        entity = self.cw_rset.get_entity(row, col)

        # Get the associated images
        imagefiles = []
        if entity.cw_etype == "Scan":
            if hasattr(entity, "results_files"):
                for efentries in entity.results_files:
                    imagefiles.extend(
                        [e.filepath for e in efentries.file_entries
                         if e.filepath.endswith(tuple(AUTHORIZED_IMAGE_EXT))])

        # Create a viewer if some images has been detected
        limagefiles = len(imagefiles)
        if limagefiles > 0:
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer", imagefiles=imagefiles,
                __message=(u"Found {0} image(s) that can be "
                            "displayed.".format(limagefiles)))

        # Get the associated documentation if available
        if hasattr(entity, "label"):
            tooltip_name = entity.label
            tooltip = self._cw.vreg.docmap.get(entity.label, None)
        else:
            tooltip = None

        # Get the subjects/study/center related entities
        if hasattr(entity, "subjects"):
            nbsubjects = len(entity.subjects)
        elif entity.__class__.__name__ == "Subject":
            nbsubjects = 1
        else:
            nbsubjects = "nc"
        study = entity.study[0]

        # Get the entity symbol
        image = u"<img alt='' src='{0}'>".format(
            self._cw.data_url(entity.symbol))

        # Create the div that will contain the list item
        self.w(u"<div class='ooview'><div class='well'>")

        # Create a bootstrap row item
        self.w(u"<div class='row'>")
        # > first element: the image
        self.w(u"<div class='col-md-2'><p class='text-center'>{0}</p>"
               "</div>".format(image))
        # > second element: the entity description + link
        self.w(u"<div class='col-md-6'><h4>{0}</h4>".format(
            entity.view("incontext")))
        entity_desc = u"Study <em>{0}</em>".format(study.name)
        if nbsubjects not in [1, 'nc']:
            entity_desc += u" - Number of subjects <em>{0}</em>".format(
                nbsubjects)
        self.w(entity_desc)
        self.w(u"</div>")
        # > third element: the see more button
        self.w(u"<button class='btn btn-danger' type='button' "
               "style='margin-top:8px' data-toggle='collapse' "
               "data-target='#info-{0}'>".format(row))
        self.w(u"See more")
        self.w(u"</button>")
        # > fourth element: the show button
        if limagefiles > 0:
            self.w(u"<a href='{0}' target=_blank class='btn btn-success' "
                   "type='button' style='margin-top:8px'>".format(href))
            self.w(u"Show &#9735;")
            self.w(u"</a>")
        # > fifth element: the doc button
        if tooltip is not None:
            tiphref = self._cw.build_url("view", vid="piws-documentation",
                                         tooltip_name=tooltip_name,
                                         _notemplate=True)
            self.w(u"<button href='{0}' class='btn btn-warning' type='button' "
                   "style='margin-top:8px' data-toggle='collapse' "
                   "data-target='#doc-{0}'>".format(row))
            self.w(u"Doc")
            self.w(u"</button>")
            self.w(u"<a href='{0}' target=_blank class='btn btn-warning' "
                   "type='button' style='margin-top:8px'>".format(tiphref))
            self.w(u"&#9735;")
            self.w(u"</a>")

        # Close row item
        self.w(u'</div>')

        # Get the entity description
        entity_desc = collections.OrderedDict(
            sorted(self.entity_description(entity).items()))

        # Create a div that will be show or hide when the see more button is
        # clicked
        self.w(u"<div id='info-{0}' class='collapse'>".format(row))
        self.w(u"<dl class='dl-horizontal'>")
        for key, value in entity_desc.items():
            self.w(u"<dt>{0}</dt><dd>{1}</dd>".format(key, value))
        self.w(u"</div>")

        # Create a div that will be show or hide when the doc button is
        # clicked
        self.w(u"<div id='doc-{0}' class='collapse'>".format(row))
        self.w(unicode(tooltip))
        self.w(u"</div>")

        # Close list item
        self.w(u"</div></div>")


###############################################################################
# Scans
###############################################################################

class OutOfContextScanView(BaseOutOfContextView):
    __select__ = EntityView.__select__ & is_instance("Scan")

    def entity_description(self, entity):
        """ Generate a dictionary with the Scan description.
        """
        dtype_entity = entity.has_data[0]
        study = entity.study[0]
        desc = {}
        desc["Image Shape (x)"] = dtype_entity.shape_x
        desc["Image Shape (y)"] = dtype_entity.shape_y
        desc["Image Shape (z)"] = dtype_entity.shape_z
        desc["Voxel resolution (x)"] = dtype_entity.voxel_res_x
        desc["Voxel resolution (y)"] = dtype_entity.voxel_res_y
        desc["Voxel resolution (z)"] = dtype_entity.voxel_res_z
        desc["Repetition time"] = dtype_entity.tr
        desc["Echo time"] = dtype_entity.te
        desc["Scanner field"] = dtype_entity.field
        #desc["Related subject"] = subject.view("incontext")
        desc["Related study"] = study.view("incontext")
        return desc


###############################################################################
# Assessment
###############################################################################

class OutOfContextAssessmentView(BaseOutOfContextView):
    __select__ = EntityView.__select__ & is_instance("Assessment")

    def entity_description(self, entity):
        """ Generate a dictionary with the Assessment description.
        """
        center = entity.center[0]
        subjects = entity.subjects
        run_items = []
        run_items.extend(entity.processing_runs)
        run_items.extend(entity.scans)
        run_items.extend(entity.questionnaire_runs)
        run_items.extend(entity.genomic_measures)
        desc = {}
        desc["Acquisition center"] = center.name
        if len(subjects) == 1:
            subject = subjects[0]
            desc["Gender"] = subject.gender
            desc["Handedness"] = subject.handedness
            desc["Age"] = entity.age_of_subject
        desc["Related runs"] = " - ".join(
            [x.view("incontext") for x in run_items])
        return desc


###############################################################################
# Subject
###############################################################################

class OutOfContextSubjectView(BaseOutOfContextView):
    __select__ = EntityView.__select__ & is_instance("Subject")

    def entity_description(self, entity):
        """ Generate a dictionary with the Subject description.
        """
        desc = {}
        desc["Gender"] = entity.gender
        desc["Handedness"] = entity.handedness
        desc["Related assessments"] = "".join(
            ["<li><a href='{0}'>{1}</a></li>".format(item.absolute_url(), item.identifier)
             for item in entity.assessments])
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any A WHERE S eid '{0}', S assessments A".format(entity.eid),
            relations=["scans", "questionnaire_runs", "genomic_measures"],
            subject_attr="timepoint", object_attr="label",
            title="Acquisition status: {0}".format(entity.code_in_study))
        desc["Acquisition summary"] = "<a href='{0}'>status</a>".format(href)
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any A WHERE S eid '{0}', S assessments A".format(entity.eid),
            relations="related_processing", subject_attr="timepoint",
            object_attr="tool", title="Processing status: {0}".format(
                entity.code_in_study))
        desc["Processing summary"] = "<a href='{0}'>status</a>".format(href)
        href = self._cw.build_url(
            "view", vid="questionnaire-longitudinal-measures",
            rql=("Any QR WHERE S eid '{0}', S assessments A, "
                 "A questionnaire_runs QR".format(entity.eid)),
            patient_id=entity.code_in_study)
        desc["Measure summary"] = "<a href='{0}'>status</a>".format(href)
        return desc


###############################################################################
# ProcessingRun
###############################################################################

class OutOfContextProcessingRunView(BaseOutOfContextView):
    __select__ = EntityView.__select__ & is_instance("ProcessingRun")

    def entity_description(self, entity):
        """ Generate a dictionary with the ProcessingRun description.
        """
        desc = {}
        desc["Name"] = entity.name
        desc["Tool"] = entity.tool
        desc["Parameters"] = entity.parameters
        return desc


###############################################################################
# QuestionnaireRun
###############################################################################


class OutOfContextQuestionnaireRunView(BaseOutOfContextView):
    __select__ = EntityView.__select__ & is_instance("QuestionnaireRun")

    def entity_description(self, entity):
        """ Generate a dictionary with the QuestionnaireRun description.
        """
        questionnaire = entity.instance_of[0]
        desc = {}
        desc["Related questionnaire"] = questionnaire.view("incontext")
        return desc


###############################################################################
# Default
###############################################################################

class OutOfContextDefaultView(EntityView):
    __regid__ = "outofcontext"
    __select__ = EntityView.__select__ & is_instance("CWSearch", "CWUpload")

    def cell_call(self, row, col):
        """ Create the default view line by line.
        """
        # Get the processing run entity
        entity = self.cw_rset.get_entity(row, col)

        # Create the div that will contain the list item
        self.w(u'<div class="ooview"><div class="well">')

        # Create a bootstrap row item
        self.w(u'<div class="row">')
        # > add the scan description + link
        self.w(u'<div class="col-md-4"><h4>{0}</h4>'.format(
            entity.view("incontext")))
        self.w(u'</div>')
        # Close row item
        self.w(u'</div>')

        # Close list item
        self.w(u'</div></div>')


###############################################################################
# Register views
###############################################################################

def registration_callback(vreg):
    """ Update outofcontext views.
    """
    vreg.register(OutOfContextDefaultView)
    vreg.register(OutOfContextProcessingRunView)
    vreg.register_and_replace(OutOfContextScanView, ScanOutOfContextView)
    vreg.register_and_replace(OutOfContextSubjectView, SubjectOutOfContextView)
    vreg.register_and_replace(
        OutOfContextAssessmentView, AssessmentOutOfContextView)
    vreg.register_and_replace(
        OutOfContextQuestionnaireRunView, QuestionnaireRunOutOfContextView)
