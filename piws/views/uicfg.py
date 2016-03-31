##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views import uicfg

# Brainomics2 import
from cubes.brainomics2.schema.neuroimaging import SCAN_DATA
from cubes.piws.schema.security import RESTRICTED_ENTITIES


uicfg.primaryview_section.tag_subject_of(
    ("Question", "questionnaire", "Questionnaire"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("OpenAnswer", "question", "Question"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("OpenAnswer", "questionnaire_run", "QuestionnaireRun"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("QuestionnaireRun", "study", "Study"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("QuestionnaireRun", "subject", "Subject"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("QuestionnaireRun", "questionnaire", "Questionnaire"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("Questionnaire", "questions", "Question"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("Subject", "study", "Study"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("Assessment", "study", "Study"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("Scan", "study", "Study"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("Scan", "subject", "Subject"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("GenomicMeasure", "study", "Study"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("CWSearch", "result", "File"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("CWSearch", "rset", "File"), "sideboxes")
uicfg.primaryview_section.tag_subject_of(
    ("CWSearch", "owned_by", "CWUser"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("CWUpload", "uploaded_by", "CWUser"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("UploadForm", "upload", "CWUpload"), "sideboxes")

uicfg.primaryview_section.tag_subject_of(
    ("ProcessingRun", "study", "Study"), "sideboxes")

for dtype in SCAN_DATA:
    uicfg.primaryview_section.tag_subject_of(
        (dtype, "scan", "Scan"), "sideboxes")
    uicfg.primaryview_section.tag_subject_of(
        ("Scan", "has_data", dtype), "sideboxes")

for dtype in ("Scan", "ProcessingRun", "GenomicMeasure"):
    uicfg.primaryview_section.tag_subject_of(
        ("FileSet", "containers", dtype), "sideboxes")

for eclass in RESTRICTED_ENTITIES:
    uicfg.primaryview_section.tag_subject_of(
        (eclass.__name__, "in_assessment", "Assessment"), "sideboxes")

# uicfg.primaryview_section.tag_attribute(("File", "data_format"), "attributes")
