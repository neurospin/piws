##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import inspect
import copy

# CubicWeb import
from yams import BASE_GROUPS
from yams.buildobjs import SubjectRelation
from yams.buildobjs import RelationDefinition
from cubicweb.schema import ERQLExpression
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
from cubes.brainomics2.schema.medicalexp import Device
from cubes.brainomics2.schema.medicalexp import SubjectGroup
from cubes.brainomics2.schema.medicalexp import Protocol
from cubes.brainomics2.schema.medicalexp import Diagnostic
from cubes.brainomics2.schema.neuroimaging import Scan
from cubes.brainomics2.schema.neuroimaging import DMRIData
from cubes.brainomics2.schema.neuroimaging import EEGData
from cubes.brainomics2.schema.neuroimaging import ETData
from cubes.brainomics2.schema.neuroimaging import PETData
from cubes.brainomics2.schema.neuroimaging import MRIData
from cubes.brainomics2.schema.neuroimaging import FMRIData
from cubes.brainomics2.schema.neuroimaging import SPECTROData
from cubes.brainomics2.schema.questionnaire import QuestionnaireRun
from cubes.brainomics2.schema.questionnaire import OpenAnswer
from cubes.brainomics2.schema.questionnaire import Questionnaire
from cubes.brainomics2.schema.questionnaire import Question
from cubes.brainomics2.schema.genomics import GenomicMeasure
from cubes.brainomics2.schema.genomics import Snp
from cubes.brainomics2.schema.genomics import CpG
from cubes.brainomics2.schema.genomics import Gene
from cubes.brainomics2.schema.genomics import Chromosome
from cubes.brainomics2.schema.file import RestrictedFile
from cubes.brainomics2.schema.card import Card
from cubes.rql_download.schema import CWSearch
from cubes.rql_download.schema import File
from cubes.rql_upload.schema import CWUpload
from cubes.rql_upload.schema import UploadField
from cubes.rql_upload.schema import UploadFile
from cubes.rql_upload.schema import UPLOAD_PERMISSIONS
from cubes.rql_upload.schema import UPLOAD_RELATION_PERMISSIONS


###############################################################################
# Deal with upload
###############################################################################

# TODO: try to get the configuration directly from cubicweb.cwconfig
# For the moment use inspect to get the config from a parent frame.
import inspect
for cnt, frame in enumerate(inspect.stack()):
    _, _, _, values = inspect.getargvalues(frame[0])
    if "config" in values:
        config = values["config"]
        break
instance_name = config.appid
enable_upload = config["enable-upload"]
share_group_uploads = config["share_group_uploads"]
authorized_upload_groups = config["authorized-upload-groups"]
authorized_upload_groups = set(authorized_upload_groups)
for group_name in authorized_upload_groups:
    BASE_GROUPS.add(group_name)
authorized_upload_groups.add("managers")
UPLOAD_PERMISSIONS["add"] = tuple(authorized_upload_groups)
UPLOAD_RELATION_PERMISSIONS["add"] = UPLOAD_PERMISSIONS["add"]
UPLOAD_PUBLIC_ENTITIES = []
if enable_upload:
    UPLOAD_PUBLIC_ENTITIES = ["CWUser", "CWGroup"]
if share_group_uploads:
    UPLOAD_PERMISSIONS["read"] = (
        "managers",
        ERQLExpression(("X created_by Y, Y in_group GY, NOT GY name 'users', "
                        "U in_group GY")))


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
    ExternalFile, ScoreDefinition, ScoreValue, ProcessingRun, QuestionnaireRun,
    OpenAnswer, GenomicMeasure, RestrictedFile, SPECTROData]

PUBLIC_ENTITIES = [
    Device, Subject, Center, Study, Questionnaire, Question, Card, Snp,
    CpG, Gene, Chromosome, SubjectGroup, Diagnostic, Protocol]

ENTITIES = RESTRICTED_ENTITIES + PUBLIC_ENTITIES + [
    Assessment, CWSearch, File, CWUpload, UploadField, UploadFile]


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
                    "Question", "Questionnaire", "Subject", "Device",
                    "GenomicPlatform", "Snp", "CWDataImport", "CWProperty",
                    "Workflow", "State", "BaseTransition", "Transition",
                    "Card", "EmailAddress", "TrInfo", "Protocol",
                    "SubjectGroup", "Diagnostic"]
UNTRACK_ENTITIES += ["Assessment", "CWSearch", "File", "CWUpload",
                     "UploadField", "UploadFile"]
UNTRACK_ENTITIES += ["Snp", "CpG", "Gene", "Chromosome"]


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

    # Set strict default permissions for unknown entities and more permissive
    # permission on subject and study when the service is used as an
    # upload platform
    entity_names = [e.__name__ for e in ENTITIES] + UPLOAD_PUBLIC_ENTITIES
    for entity in entities:
        if entity.type not in entity_names:
            entity.permissions = MANAGER_PERMISSIONS
        if enable_upload and entity.type == "Subject":
            entity.permissions = UPLOAD_PERMISSIONS
        elif enable_upload and entity.type == "Study":
            perms = copy.deepcopy(UPLOAD_PERMISSIONS)
            perms["read"] = ("managers", "users")
            entity.permissions = perms

