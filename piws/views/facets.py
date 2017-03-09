##########################################################################
# NSAp - Copyright (C) CEA, 2013
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

from cubicweb.web import facet
from cubicweb.predicates import is_instance
from cubicweb.web.views.facets import FacetFilterMixIn
from cubicweb.web.views.facets import HasTextFacet


############################################################################
# Hide facet while filtering
############################################################################

FacetFilterMixIn._generate_form = FacetFilterMixIn.generate_form


def generate_form(self, w, rset, divid, vid, vidargs=None, mainvar=None,
                  paginate=False, cssclass='', hiddens=None, **kwargs):

        FacetFilterMixIn._generate_form(self, w, rset, divid, vid, vidargs=None,
                                        mainvar=None, paginate=False,
                                        cssclass='', hiddens=None, **kwargs)

        html = "<script>"
        html += "function onFacetFiltering(event, divid /* ... */) {"
        html += "$('#facet_filterbox').hide();"
        html += "showFacetLoading(divid);"
        html += "}"
        html += ("function onFacetContentLoaded"
                 "(event, divid, rql, vid, extraparams) {")
        html += "$('#facetLoading').hide();"
        html += "$('#facet_filterbox').show();"
        html += "}"
        html += "</script>"

        w(u'{0}'.format(html))

FacetFilterMixIn.generate_form = generate_form


############################################################################
# FACETS
############################################################################


class StatusFacet(facet.RQLPathFacet):
    """ Filter on status.

    This filter is applied on 'CWUpload'.
    """
    __regid__ = "status-facet"
    __select__ = is_instance("CWUpload")
    path = ["X status S"]
    order = 1
    filter_variable = "S"
    title = _("Status")


class TimepointFacet(facet.RQLPathFacet):
    """ Filter on timepoint (form the 'Assessment' entity).

    This filter is applied on 'Scan', 'ProcessingRun',
    'QuestionnaireRun' and 'GenomicMeasure' entities.
    """
    __regid__ = "timepoint-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun",
                             "GenomicMeasure")
    path = ["X in_assessment A", "A timepoint T"]
    order = 1
    filter_variable = "T"
    title = _("Timepoints")


class LabelFacet(facet.RQLPathFacet):
    """ Filter on label.

    This filter is applied on 'Scan', 'ProcessingRun',
    'QuestionnaireRun' and 'GenomicMeasure' entities.
    """
    __regid__ = "label-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun",
                             "GenomicMeasure")
    path = ["X label L"]
    order = 1
    filter_variable = "L"
    title = _("Labels")


class NameFacet(facet.RQLPathFacet):
    """ Filter on name.

    This filter is applied on 'FileSet'.
    """
    __regid__ = "name-facet"
    __select__ = is_instance("FileSet")
    path = ["X name N"]
    order = 1
    filter_variable = "N"
    title = _("Name")


class StudyFacet(facet.RQLPathFacet):
    """ Filter on study name (from the 'Study' entity).

    This filter is applied on 'Scan', 'ProcessingRun',
    'QuestionnaireRun' and 'GenomicMeasure' entities.
    """
    __regid__ = "study-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun",
                             "GenomicMeasure")
    path = ["X in_assessment A", "A study S", "S name N"]
    order = 2
    filter_variable = "N"
    title = _("Studies")


class SubjectFacet(facet.RQLPathFacet):
    """ Filter on subject code (from the 'Subject' entity).

    This filter can is applied on 'Scan', 'QuestionnaireRun' entities.
    """
    __regid__ = "subject-facet"
    __select__ = is_instance("Scan", "QuestionnaireRun")
    path = ["X subject S", "S code_in_study C"]
    order = 3
    filter_variable = "C"
    title = _("Subjects")


class SubjectsFacet(facet.RQLPathFacet):
    """ Filter on subject code (from the 'Subject' entity).

    This filter can is applied on 'GenomicMeasure' entity.
    """
    __regid__ = "subjects-facet"
    __select__ = is_instance("GenomicMeasure")
    path = ["X subjects S", "S code_in_study C"]
    order = 3
    filter_variable = "C"
    title = _("Subjects")


class ScanFieldFacet(facet.RQLPathFacet):
    """ Filter the scan fields.

    This filter is applied on 'Scan'.
    """
    __regid__ = "scan-field-facet"
    __select__ = is_instance("Scan")
    path = ["X has_data D", "D field F"]
    order = 1
    filter_variable = "F"
    title = _("Scanner Field")


class ScanFormatFacet(facet.RQLPathFacet):
    """ Filter the scan formats.

    This filter is applied on 'Scan'.
    """
    __regid__ = "scan-format-facet"
    __select__ = is_instance("Scan")
    path = ["X format F"]
    order = 2
    filter_variable = "F"
    title = _("Image Format")


class AssessmentTimepointFacet(facet.RQLPathFacet):
    """ Filter the assessment timepoints.

    This filter is applied on 'Assessment'.
    """
    __regid__ = "assessment-timepoint-facet"
    __select__ = is_instance("Assessment")
    path = ["X timepoint T"]
    order = 1
    filter_variable = "T"
    title = _("Timepoints")


class AssessmentSubjectFacet(facet.RQLPathFacet):
    """ Filter the assessment subjects.

    This filter is applied on 'Assessment'.
    """
    __regid__ = "assessment-subject-facet"
    __select__ = is_instance("Assessment")
    path = ["X subjects S", "S code_in_study C"]
    order = 3
    filter_variable = "C"
    title = _("Subjects")


class GenomicMeasureTypeFacet(facet.RQLPathFacet):
    """ Filter the genomic measure types.

    This filter is applied on 'GenomicMeasure'.
    """
    __regid__ = "genomicmeasure-type-facet"
    __select__ = is_instance("GenomicMeasure")
    path = ["X type T"]
    order = 1
    filter_variable = "T"
    title = _("Type")


class ProcessingRunNameFacet(facet.RQLPathFacet):
    """ Filter the ProcessingRun FileSets by name.

    This filter is applied on 'ProcessingRun'.
    """
    __regid__ = "processingrun-name-facet"
    __select__ = is_instance("ProcessingRun")
    path = ["X filesets F", "F name N"]
    order = 1
    filter_variable = "N"
    title = _("Type")


class ProcessingRunSubjectFacet(facet.RQLPathFacet):
    """ Filter on subject code (from the 'Subject' entity).

    This filter can is applied on 'ProcessingRun'.
    """
    __regid__ = "processingrun-subject-facet"
    __select__ = is_instance("ProcessingRun")
    path = ["X subjects S", "S code_in_study C"]
    order = 2
    filter_variable = "C"
    title = _("Subjects")


###############################################################################
# Registration callback
###############################################################################

def registration_callback(vreg):

    vreg.unregister(HasTextFacet)

    for eclass in [GenomicMeasureTypeFacet, TimepointFacet, StudyFacet,
                   SubjectFacet, ScanFieldFacet, ScanFormatFacet,
                   AssessmentTimepointFacet, AssessmentSubjectFacet,
                   ProcessingRunNameFacet, LabelFacet, NameFacet,
                   ProcessingRunSubjectFacet, StatusFacet]:
        vreg.register(eclass)
