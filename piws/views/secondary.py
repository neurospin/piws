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

# PIWS import
from components import AUTHORIZED_IMAGE_EXT


###############################################################################
# Base
###############################################################################

class BaseOutOfContextView(EntityView):
    """ Default secondary view rendering.
    """
    __regid__ = "outofcontext"
    __select__ = False
    title = _("Outofcontext")

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
        #if entity.cw_etype == "Scan":
        #    if hasattr(entity, "filesets"):
        #        for efentries in entity.filesets:
        #            imagefiles.extend(
        #                [e.filepath for e in efentries.external_files
        #                 if e.filepath.endswith(tuple(AUTHORIZED_IMAGE_EXT))])

        # Create a viewer if some images has been detected
        limagefiles = len(imagefiles)
        if limagefiles > 0:
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer", imagefiles=imagefiles,
                __message=(u"Found '{0}' image(s) that can be "
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
        study = None
        if hasattr(entity, "study") and len(entity.study) > 0:
            study = entity.study[0]

        # Get the entity symbol
        if hasattr(entity, "__bootstap_glyph__") and entity.__bootstap_glyph__:
            image = unicode(entity.symbol)
        else:
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
        entity_desc = u""
        if study is not None:
            entity_desc += u"Study <em>{0}</em>".format(study.name)
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
    """ Scan secondary rendering.
    """
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
        return desc


###############################################################################
# Assessment
###############################################################################

class OutOfContextAssessmentView(BaseOutOfContextView):
    """ Assessment secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("Assessment")

    def entity_description(self, entity):
        """ Generate a dictionary with the Assessment description.
        """
        center = entity.center[0]
        subjects = entity.subjects
        desc = {}
        desc["Acquisition center"] = center.name
        if len(subjects) == 1:
            subject = subjects[0]
            desc["Gender"] = subject.gender
            desc["Handedness"] = subject.handedness
            desc["Age"] = entity.age_of_subject
        return desc


###############################################################################
# Subject
###############################################################################

class OutOfContextSubjectView(BaseOutOfContextView):
    """ Subject secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("Subject")

    def entity_description(self, entity):
        """ Generate a dictionary with the Subject description.
        """
        desc = {}
        desc["Gender"] = entity.gender
        desc["Handedness"] = entity.handedness
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
            relations="processing_runs", subject_attr="timepoint",
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
    """ ProcessingRun secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("ProcessingRun")

    def entity_description(self, entity):
        """ Generate a dictionary with the ProcessingRun description.
        """
        desc = {}
        desc["Label"] = entity.label
        desc["Tool"] = entity.tool
        desc["Parameters"] = entity.parameters
        desc["Type"] = entity.type
        return desc


###############################################################################
# Genomic Measure
###############################################################################

class OutOfContextGenomicMeasureView(BaseOutOfContextView):
    """ GenomicMeasure secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("GenomicMeasure")

    def entity_description(self, entity):
        """ Generate a dictionary with the GenomicMeasure description.
        """
        desc = {}
        desc["Label"] = entity.label
        desc["Type"] = entity.type
        desc["Format"] = entity.format
        return desc


###############################################################################
# QuestionnaireRun
###############################################################################

class OutOfContextQuestionnaireRunView(BaseOutOfContextView):
    """ QuestionnaireRun secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("QuestionnaireRun")

    def entity_description(self, entity):
        """ Generate a dictionary with the QuestionnaireRun description.
        """
        questionnaire = entity.questionnaire[0]
        desc = {}
        desc["Related questionnaire"] = questionnaire.view("incontext")
        return desc


###############################################################################
# Question
###############################################################################

class OutOfContextQuestionView(BaseOutOfContextView):
    """ Question secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("Question")

    def entity_description(self, entity):
        """ Generate a dictionary with the Question description.
        """
        questionnaire = entity.questionnaire[0]
        desc = {}
        desc["Related questionnaire"] = questionnaire.view("incontext")
        return desc



###############################################################################
# Questionnaire
###############################################################################

class OutOfContextQuestionnaireView(BaseOutOfContextView):
    """ Questionnaire secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("Questionnaire")

    def entity_description(self, entity):
        """ Generate a dictionary with the Questionnaire description.
        """
        desc = {}
        desc["Name"] = entity.name
        desc["Nimber of questions"] = len(entity.questions)
        return desc


###############################################################################
# Snp
###############################################################################

class OutOfContextSnpView(BaseOutOfContextView):
    """ Snp secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("Snp")

    def entity_description(self, entity):
        """ Generate a dictionary with the Snp description.
        """
        desc = {}
        desc["Identifier"] = entity.rs_id
        desc["Position"] = entity.position
        return desc


###############################################################################
# GenomicPlatform
###############################################################################

class OutOfContextGenomicPlatformView(BaseOutOfContextView):
    """ GenomicPlatform secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("GenomicPlatform")

    def entity_description(self, entity):
        """ Generate a dictionary with the GenomicPlatform description.
        """
        desc = {}
        desc["Name"] = entity.name
        return desc


###############################################################################
# FileSet
###############################################################################

class OutOfContextFileSetView(BaseOutOfContextView):
    """ FileSet secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("FileSet")

    def entity_description(self, entity):
        """ Generate a dictionary with the FileSet description.
        """
        desc = {}
        desc["Name"] = entity.name
        return desc


###############################################################################
# ExternalFile
###############################################################################

class OutOfContextExternalFileView(BaseOutOfContextView):
    """ ExternalFile secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("ExternalFile")

    def entity_description(self, entity):
        """ Generate a dictionary with the ExternalFile description.
        """
        desc = {}
        desc["Name"] = entity.name
        desc["Abolute path"] = entity.absolute_path
        desc["Path"] = entity.filepath
        return desc


###############################################################################
# CWSearch
###############################################################################

class OutOfContextCWSearchView(BaseOutOfContextView):
    """ CWSearch secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("CWSearch")

    def entity_description(self, entity):
        """ Generate a dictionary with the CWSearch description.
        """
        desc = {}
        desc["Tile"] = entity.title
        desc["RQL"] = entity.path
        desc["Expiration data"] = entity.expiration_date
        desc["Type"] = entity.rset_type
        return desc


###############################################################################
# CWUpload
###############################################################################

class OutOfContextCWUploadView(BaseOutOfContextView):
    """ CWUpload secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("CWUpload")

    def entity_description(self, entity):
        """ Generate a dictionary with the CWUpload description.
        """
        desc = {}
        desc["Tile"] = entity.title
        desc["Form"] = entity.form_name
        return desc


###############################################################################
# File
###############################################################################

class OutOfContextFileView(BaseOutOfContextView):
    """ File secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("File")

    def entity_description(self, entity):
        """ Generate a dictionary with the File description.
        """
        desc = {}
        desc["Title"] = entity.title
        desc["Format"] = entity.data_format
        desc["SHA1"] = entity.data_sha1hex
        return desc


###############################################################################
# UploadFile
###############################################################################

class OutOfContextUploadFileView(BaseOutOfContextView):
    """ UploadFile secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("UploadFile")

    def entity_description(self, entity):
        """ Generate a dictionary with the UploadFile description.
        """
        desc = {}
        desc["Title"] = entity.title
        desc["Format"] = entity.data_extension
        desc["SHA1"] = entity.data_sha1hex
        return desc


###############################################################################
# RestrictedFile
###############################################################################

class OutOfContextRestrictedFileView(BaseOutOfContextView):
    """ RestrictedFile secondary rendering.
    """
    __select__ = EntityView.__select__ & is_instance("RestrictedFile")

    def entity_description(self, entity):
        """ Generate a dictionary with the RestrictedFile description.
        """
        desc = {}
        desc["Title"] = entity.title
        desc["Format"] = entity.data_format
        desc["SHA1"] = entity.data_sha1hex
        return desc


###############################################################################
# Register views
###############################################################################

def registration_callback(vreg):
    """ Update outofcontext views.
    """
    for klass in [OutOfContextQuestionView, OutOfContextGenomicPlatformView,
                  OutOfContextSnpView, OutOfContextFileSetView,
                  OutOfContextQuestionnaireView, OutOfContextCWUploadView,
                  OutOfContextProcessingRunView, OutOfContextScanView,
                  OutOfContextSubjectView, OutOfContextAssessmentView,
                  OutOfContextQuestionnaireRunView,
                  OutOfContextExternalFileView, OutOfContextCWSearchView,
                  OutOfContextFileView, OutOfContextUploadFileView,
                  OutOfContextRestrictedFileView,
                  OutOfContextGenomicMeasureView]:
        vreg.register(klass)

