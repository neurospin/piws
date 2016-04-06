##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CubicWeb import
from yams.buildobjs import SubjectRelation
from yams.buildobjs import RelationDefinition
from cubicweb.schema import ERQLExpression
from yams.buildobjs import RelationDefinition
from yams.buildobjs import RelationType
from cubicweb.entities.authobjs import CWUser
from cubicweb.entities.authobjs import CWGroup

# Cubes import
from cubes.brainomics2.schema.medicalexp import Assessment
from cubes.brainomics2.schema.medicalexp import Subject
from cubes.brainomics2.schema.medicalexp import FileSet
from cubes.brainomics2.schema.medicalexp import ExternalFile
from cubes.brainomics2.schema.medicalexp import ScoreDefinition
from cubes.brainomics2.schema.medicalexp import ScoreValue
from cubes.brainomics2.schema.medicalexp import ProcessingRun
from cubes.brainomics2.schema.medicalexp import Center
from cubes.brainomics2.schema.medicalexp import Study
from cubes.brainomics2.schema.neuroimaging import Scan
from cubes.brainomics2.schema.neuroimaging import DMRIData
from cubes.brainomics2.schema.neuroimaging import EEGData
from cubes.brainomics2.schema.neuroimaging import ETData
from cubes.brainomics2.schema.neuroimaging import PETData
from cubes.brainomics2.schema.neuroimaging import MRIData
from cubes.brainomics2.schema.neuroimaging import FMRIData
from cubes.brainomics2.schema.questionnaire import QuestionnaireRun
from cubes.brainomics2.schema.questionnaire import OpenAnswer
from cubes.brainomics2.schema.questionnaire import Questionnaire
from cubes.brainomics2.schema.questionnaire import Question
from cubes.brainomics2.schema.genomics import GenomicMeasure
from cubes.brainomics2.schema.file import RestrictedFile
from cubes.brainomics2.schema.card import Card
from cubes.rql_download.schema import CWSearch
from cubes.rql_download.schema import File
from cubes.rql_upload.schema import CWUpload
from cubes.rql_upload.schema import UploadForm
from cubes.rql_upload.schema import UploadFile


###############################################################################
# Define permission relations
###############################################################################

# CWGROUP
class can_read(RelationDefinition):
    """ Link a group to an assessment with this relation to give the group
    users read access to the assessment related entities.
    """
    inlined = False
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "*+"


class can_update(RelationDefinition):
    """ Link a group to an assessment with this relation to give the group
    users write access to the assessment related entities.
    """
    inlined = False
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "**"


class in_assessment(RelationType):
    """ Relate entities to an assessment with this relation in order to apply
    the proposed simplified rights management mechanism.
    """
    inlined = True
    cardinality = "1*"
    subject = "*"
    object = "Assessment"


###############################################################################
# Set permissions
###############################################################################

RESTRICTED_ENTITIES = [
    Scan, FMRIData, DMRIData, PETData, MRIData, EEGData, ETData, FileSet,
    ExternalFile, ScoreDefinition, ScoreValue, ProcessingRun, QuestionnaireRun, OpenAnswer,
    GenomicMeasure, RestrictedFile]

PUBLIC_ENTITIES = [
    Subject, Center, Study, Questionnaire, Question, Card]

ENTITIES = RESTRICTED_ENTITIES + PUBLIC_ENTITIES + [
    Assessment, CWSearch, File, CWUpload, UploadForm, UploadFile]


PUBLIC_PERMISSIONS = {
    "read": ("managers", "users"),
    "add": ("managers",),
    "update": ("managers",),
    "delete": ("managers",),
}

ASSESSMENT_PERMISSIONS = {
    "read": (
        "managers",
        ERQLExpression("U in_group G, G can_read X")),
    "add": (
        "managers",
        ERQLExpression("U in_group G, G can_update X")),
    "update": (
        "managers",
        ERQLExpression("U in_group G, G can_update X")),
    "delete": (
        "managers",
        ERQLExpression("U in_group G, G can_update X")),
}

RESTRICTED_PERMISSIONS = {
    "read": (
        "managers",
        ERQLExpression("X in_assessment A, U in_group G, G can_read A")),
    "add": (
        "managers",
        ERQLExpression("X in_assessment A, U in_group G, G can_update A")),
    "update": (
        "managers",
        ERQLExpression("X in_assessment A, U in_group G, G can_update A")),
    "delete": (
        "managers",
        ERQLExpression("X in_assessment A, U in_group G, G can_update A")),
}

MANAGER_PERMISSIONS = {
    "read": ("managers",),
    "add": ("managers",),
    "update": ("managers",),
    "delete": ("managers",),
}

UNTRACK_ENTITIES = ["CWUser", "CWGroup", "CWSource", "Study", "Center",
                    "Device", "Question", "Questionnaire", "Subject",
                    "GenomicPlatform", "Snp", "CWDataImport", "CWProperty",
                    "Workflow", "State", "BaseTransition", "Transition",
                    "Card", "EmailAddress"]
UNTRACK_ENTITIES += ["Assessment", "CWSearch", "File", "CWUpload",
                     "UploadForm", "UploadFile"]


# Set known entities permissions
for entity in PUBLIC_ENTITIES:
    entity.__permissions__ = PUBLIC_PERMISSIONS
for entity in RESTRICTED_ENTITIES:
    entity.__permissions__ = RESTRICTED_PERMISSIONS

# Set Assessment permissions
Assessment.__permissions__ = ASSESSMENT_PERMISSIONS


def post_build_callback(schema):

    # Get the schema
    entities = schema.entities()

    # Remove 'in_asessment' to untrack entities
    for entity in entities:
        if entity.type in UNTRACK_ENTITIES or entity.final:
            schema.del_relation_def(entity.type, "in_assessment", "Assessment")

    # Set strict default permissions for unknown entities
    entity_names = [e.__name__ for e in ENTITIES]
    for entity in entities:
        if entity.type not in entity_names:
            entity.permissions = MANAGER_PERMISSIONS

