# -*- coding: utf-8 -*-
# copyright 2014 nsap, all rights reserved.
# contact http://www.logilab.fr -- mailto:antoine.grigis@cea.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""cubicweb-neurospinweb schema"""

from yams.buildobjs import (
    SubjectRelation, EntityType, String, Float, RelationDefinition, Datetime)
from yams.constraints import BoundaryConstraint, Attribute

from cubicweb.schema import RRQLExpression, ERQLExpression
from cubes.medicalexp.schema import (
    Assessment, Subject, FileSet, ExternalFile, ScoreValue, ProcessingRun,
    Center, Study)
from cubes.neuroimaging.schema import (
    Scan, DMRIData, PETData, MRIData)
from cubes.questionnaire.schema import (
    QuestionnaireRun, Questionnaire, Question)


###############################################################################
# Modification of the schema
###############################################################################

# Add label to QuestionnaireRun entity
QuestionnaireRun.add_relation(
    String(maxsize=128, fulltextindexed=True), name="label")

# Add code_in_study to Subject entity
Subject.add_relation(
    String(maxsize=64, fulltextindexed=True), name="code_in_study")

# Add identifier to Assessment entity
Assessment.add_relation(
    String(maxsize=64, fulltextindexed=True), name="identifier")

# Add identifier to ProcessingRun entity
ProcessingRun.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add identifier to Scan entity
Scan.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add identifier to FileSet entity
FileSet.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add identifier to ExternalFile entity
ExternalFile.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add shape to DMRIData entity
DMRIData.add_relation(Float(required=True, indexed=True), name="shape_x")
DMRIData.add_relation(Float(required=True, indexed=True), name="shape_y")
DMRIData.add_relation(Float(required=True, indexed=True), name="shape_z")

# Add field to *Data entity
DMRIData.add_relation(String(maxsize=64, indexed=True), name="field")
MRIData.add_relation(String(maxsize=64, indexed=True), name="field")


# Add entity to store some generic scores
class OpenAnswer(EntityType):
    value = String(required=True, indexed=True)
    identifier = String(maxsize=64, indexed=True)
    question = SubjectRelation("Question", cardinality="1*", inlined=True)
    questionnaire_run = SubjectRelation("QuestionnaireRun", cardinality="1*",
                                        inlined=True)


# Add entity to select fmri data
class FMRIData(EntityType):
    shape_x = Float(required=True, indexed=True)
    shape_y = Float(required=True, indexed=True)
    shape_z = Float(required=True, indexed=True)
    voxel_res_x = Float(required=True, indexed=True)
    voxel_res_y = Float(required=True, indexed=True)
    voxel_res_z = Float(required=True, indexed=True)
    fov_x = Float(indexed=True)
    fov_y = Float(indexed=True)
    tr = Float(required=True, indexed=True)
    te = Float(required=True, indexed=True)
    field = String(maxsize=64, indexed=True)
Scan.add_relation(SubjectRelation("FMRIData", cardinality='?1',
                  composite="subject", inlined=True), name="has_data")


# Add entity to store bio samples
class BioSample(EntityType):
    identifier = String(maxsize=64, indexed=True)
    label = String(maxsize=64, indexed=False)
    sample_creation_date = Datetime()
    box_id = String(maxsize=64, indexed=False)
    tube_name = String(maxsize=64, indexed=False)
    extraction_lab_name = String(maxsize=64, indexed=False)
    send_extraction_lab_date = Datetime()
#        constraints=[BoundaryConstraint('>=', Attribute("sample_creation_date"))])
    receive_extraction_lab_date = Datetime(
        constraints=[BoundaryConstraint('>=', Attribute("send_extraction_lab_date"))])
    destruction_date = Datetime()
    hybridation_lab_name = String(maxsize=64, indexed=False)
    send_hybridation_lab_date = Datetime(
        constraints=[BoundaryConstraint('>=', Attribute("sample_creation_date"))])
    receive_hybridation_lab_date = Datetime(
        constraints=[BoundaryConstraint('>=', Attribute("send_hybridation_lab_date"))])
    qc_nano = String(maxsize=64, indexed=False)
    qc_spectro = String(maxsize=64, indexed=False)
BioSample.add_relation(SubjectRelation(
    "Subject", cardinality="1*", inlined=True), name="concerns")
Assessment.add_relation(SubjectRelation(
    "BioSample", cardinality="**", composite="subject"), name="uses")
BioSample.add_relation(SubjectRelation(
    "Study", cardinality="1*", inlined=True, composite="object"),
    name="related_study")
BioSample.add_relation(SubjectRelation(
    ("File", "FileSet", "ExternalFile"), cardinality="**", composite="subject"),
    name="results_files")


# Add Assessment/CWGroup relations
class can_read(RelationDefinition):
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "**"


class can_update(RelationDefinition):
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "**"


# Add Assessment/Subject ralation
class concerns(RelationDefinition):
    subject = "Assessment"
    object = ("Subject", "SubjectGroup")
    cardinality = "1*"
    inlined = True


# Add Assessment/ProcessingRun relation
class in_assessment(RelationDefinition):
    subject = ("ProcessingRun", "ExternalFile", "BioSample")
    object = "Assessment"
    cardinality = "1*"
    inlined = True


###############################################################################
# Set permissions
###############################################################################

ENTITIES = [
    Scan, FMRIData, DMRIData, PETData, MRIData, FileSet, ExternalFile,
    ScoreValue, ProcessingRun, QuestionnaireRun, Questionnaire, Question,
    OpenAnswer]


DEFAULT_PERMISSIONS = {
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


RELATION_PERMISSIONS = {
    "read": (
        "managers",
        "users"),
    "add": (
        "managers",
        RRQLExpression("S in_assessment A, U in_group G, G can_update A")),
    "delete": (
        "managers",
        RRQLExpression("S in_assessment A, U in_group G, G can_update A"))
}


ENTITY_PERMISSIONS = {
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


# Set the assessment entity permissions
Assessment.set_permissions(ASSESSMENT_PERMISSIONS)

# Set the subject/center/study entities permissions
Subject.set_permissions(DEFAULT_PERMISSIONS)
Center.set_permissions(DEFAULT_PERMISSIONS)
Study.set_permissions(DEFAULT_PERMISSIONS)

# Set the permissions on the used entities only
for entity in ENTITIES:
    entity.__permissions__ = ENTITY_PERMISSIONS

# Update the entities list to set relation permissions
ENTITIES.extend([Assessment, Subject, Center, Study])

# Set the permissions on the ised entities relations only
for entity in ENTITIES:

    # Get the subject relations
    for relation in entity.__relations__:
        if relation.__class__ is SubjectRelation:
            relation.__permissions__ = RELATION_PERMISSIONS
