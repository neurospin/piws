#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from cubicweb.web import facet
from cubicweb.selectors import is_instance


############################################################################
# FACETS 
############################################################################

class TimepointFacet(facet.RQLPathFacet):
    __regid__ = "timepoint-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun")
    path = ["X in_assessment A", "A timepoint T"]
    order = 1
    filter_variable = "T"
    title = _("Timepoints")


class StudyFacet(facet.RQLPathFacet):
    __regid__ = "study-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun")
    path = ["X in_assessment A", "A related_study S", "S name N"]
    order = 2
    filter_variable = "N"
    title = _("Studies")


class SubjectFacet(facet.RQLPathFacet):
    __regid__ = "subject-facet"
    __select__ = is_instance("Scan", "ProcessingRun", "QuestionnaireRun")
    path = ["X in_assessment A", "A concerns S", "S code_in_study C"]
    order = 3
    filter_variable = "C"
    title = _("Subjects")


class ScanFieldFacet(facet.RQLPathFacet):
    __regid__ = "scan-field-facet"
    __select__ = is_instance("Scan")
    path = ["X has_data D", "D field F"]
    order = 1
    filter_variable = "F"
    title = _("Scanner Field")


class ScanFormatFacet(facet.RQLPathFacet):
    __regid__ = "scan-format-facet"
    __select__ = is_instance("Scan")
    path = ["X format F"]
    order = 2
    filter_variable = "F"
    title = _("Image Format")


class AssessmentTimepointFacet(facet.RQLPathFacet):
    __regid__ = "assessment-timepoint-facet"
    __select__ = is_instance("Assessment")
    path = ["X timepoint T"]
    order = 1
    filter_variable = "T"
    title = _("Timepoints")


class AssessmentStudyFacet(facet.RQLPathFacet):
    __regid__ = "assessment-study-facet"
    __select__ = is_instance("Assessment")
    path = ["X related_study S", "S name N"]
    order = 2
    filter_variable = "N"
    title = _("Studies")


class AssessmentSubjectFacet(facet.RQLPathFacet):
    __regid__ = "assessment-subject-facet"
    __select__ = is_instance("Assessment")
    path = ["X concerns S", "S code_in_study C"]
    order = 3
    filter_variable = "C"
    title = _("Subjects")


def registration_callback(vreg):

    # Update the facets
    vreg.register(TimepointFacet)
    vreg.register(StudyFacet)
    vreg.register(SubjectFacet)
    vreg.register(ScanFieldFacet)
    vreg.register(ScanFormatFacet)
    vreg.register(AssessmentTimepointFacet)
    vreg.register(AssessmentStudyFacet)
    vreg.register(AssessmentSubjectFacet)
