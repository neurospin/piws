#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from yams.buildobjs import SubjectRelation
from yams.buildobjs import RelationType
from yams.buildobjs import EntityType
from yams.buildobjs import String
from yams.buildobjs import Float
from yams.buildobjs import RelationDefinition
from yams.buildobjs import Datetime
from yams.constraints import BoundaryConstraint
from yams.constraints import Attribute
from cubicweb.schema import RRQLExpression
from cubicweb.schema import ERQLExpression

# Cubes import
from cubes.medicalexp.schema import Assessment
from cubes.medicalexp.schema import Subject
from cubes.medicalexp.schema import FileSet
from cubes.medicalexp.schema import ExternalFile
from cubes.medicalexp.schema import ScoreValue
from cubes.medicalexp.schema import ProcessingRun
from cubes.medicalexp.schema import Center
from cubes.medicalexp.schema import Study
from cubes.neuroimaging.schema import Scan
from cubes.neuroimaging.schema import DMRIData
from cubes.neuroimaging.schema import PETData
from cubes.neuroimaging.schema import MRIData
from cubes.questionnaire.schema import QuestionnaireRun
from cubes.questionnaire.schema import Questionnaire
from cubes.questionnaire.schema import Question
from cubes.genomics.schema import GenomicMeasure
from cubes.genomics.schema import ColumnRef
from cubes.genomics.schema import GenomicPlatform
from cubes.genomics.schema import Snp


###############################################################################
# Modification of the schema
###############################################################################

# It seems it's the only way to remove inlined relations
def post_build_callback(schema):
    # Remove inlined relations
    schema.del_relation_def('Answer', 'question', 'Question')
    # Add relation container with inlined=False
    schema.add_relation_type(RelationType('question', inlined=False))
    # Add again the deleted relation
    schema.add_relation_def(
        RelationDefinition(subject='Answer',
                           name='question',
                           object='Question',
                           cardinality='1*',
                           composite='object')
    )
    # Add a new relation
    schema.add_relation_def(
        RelationDefinition(subject='OpenAnswer',
                           name='question',
                           object='Question',
                           cardinality='1*')
    )

# ATTRIBUTES

# Add label to QuestionnaireRun entity
QuestionnaireRun.add_relation(
    String(maxsize=64), name="label")
# Add identifier to QuestionnaireRun entity
QuestionnaireRun.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add label to ProcessingRun entity
ProcessingRun.add_relation(
    String(maxsize=64), name="label")

# Add code_in_study to Subject entity
Subject.add_relation(
    String(maxsize=64, fulltextindexed=True), name="code_in_study")

# Add identifier to Assessment entity
Assessment.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

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

# Add label to GenomicMeasure entity
GenomicMeasure.add_relation(
    String(maxsize=64), name="label")
# Add identifier to GenomicMeasure entity
GenomicMeasure.add_relation(
    String(maxsize=128, fulltextindexed=True), name="identifier")

# Add chromset to Genomicmeasure
GenomicMeasure.add_relation(
    String(maxsize=64), name="chromset")

# Add shape to DMRIData entity
DMRIData.add_relation(
    Float(), name="shape_x")
DMRIData.add_relation(
    Float(), name="shape_y")
DMRIData.add_relation(
    Float(), name="shape_z")

# Add field to *Data entity
DMRIData.add_relation(
    String(maxsize=10, indexed=True), name="field")
MRIData.add_relation(
    String(maxsize=10, indexed=True), name="field")


# RELATIONS

# SCAN
Scan.remove_relation(name="related_study")
Scan.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")
Scan.remove_relation(name="concerns")
Scan.add_relation(
    SubjectRelation("Subject", cardinality="1*", inlined=False),
    name="subject")
Scan.remove_relation(name="measure")
Scan.add_relation(
    SubjectRelation("ScoreValue", cardinality="*1", inlined=False),
    name="score_values")
Scan.add_relation(
    SubjectRelation("ProcessingRun", cardinality="**", inlined=False),
    name="processing_runs")

# CENTER
Center.remove_relation(name="holds")
Center.add_relation(
    SubjectRelation("Assessment", cardinality="*1", inlined=False),
    name="assessments")

# ASSESSMENT
Assessment.add_relation(
    SubjectRelation("Center", cardinality="1*", inlined=False),
    name="center")
Assessment.remove_relation(name="related_study")
Assessment.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")
Assessment.remove_relation(name="uses")
Assessment.add_relation(
    SubjectRelation("Scan", cardinality="*1", inlined=False),
    name="scans")
Assessment.add_relation(
    SubjectRelation("QuestionnaireRun", cardinality="*1", inlined=False),
    name="questionnaire_runs")
Assessment.add_relation(
    SubjectRelation("GenomicMeasure", cardinality="*1", inlined=False),
    name="genomic_measures")
Assessment.remove_relation(name="concerns")
Assessment.add_relation(
    SubjectRelation("Subject", cardinality="**", inlined=False),
    name="subjects")
Assessment.remove_relation(name="related_processing")
Assessment.add_relation(
    SubjectRelation("ProcessingRun", cardinality="**", inlined=False),
    name="processing_runs")

# STUDY
Study.add_relation(
    SubjectRelation("Assessment", cardinality="*1", inlined=False),
    name="assessments")
Study.add_relation(
    SubjectRelation("Subject", cardinality="*1", inlined=False),
    name="subjects")
Study.add_relation(
    SubjectRelation("GenomicMeasure", cardinality="*1", inlined=False),
    name="genomic_measures")
Study.add_relation(
    SubjectRelation("Scan", cardinality="*1", inlined=False),
    name="scans")
Study.add_relation(
    SubjectRelation("QuestionnaireRun", cardinality="*1", inlined=False),
    name="questionnaire_runs")
Study.add_relation(
    SubjectRelation("ProcessingRun", cardinality="*1", inlined=False),
    name="processing_runs")

# SUBJECT
Subject.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")
Subject.add_relation(
    SubjectRelation("GenomicMeasure", cardinality="**", inlined=False),
    name="genomic_measures")
Subject.remove_relation(name="concerned_by")
Subject.add_relation(
    SubjectRelation("Assessment", cardinality="**", inlined=False),
    name="assessments")
Subject.add_relation(
    SubjectRelation("Scan", cardinality="*1", inlined=False),
    name="scans")
Subject.add_relation(
    SubjectRelation("QuestionnaireRun", cardinality="*1", inlined=False),
    name="questionnaire_runs")
Subject.add_relation(
    SubjectRelation("ProcessingRun", cardinality="*1", inlined=False),
    name="processing_runs")

# QUESTIONNAIRE RUN
QuestionnaireRun.add_relation(
    SubjectRelation("OpenAnswer", cardinality="*1", inlined=False),
    name="open_answers")
QuestionnaireRun.remove_relation(name="related_study")
QuestionnaireRun.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")
QuestionnaireRun.remove_relation(name="concerns")
QuestionnaireRun.add_relation(
    SubjectRelation("Subject", cardinality="1*", inlined=False),
    name="subject")

# QUESTION
Question.add_relation(
    SubjectRelation("OpenAnswer", cardinality="*1", inlined=False),
    name="open_answers")

# QUESTIONNAIRE
Questionnaire.add_relation(
    SubjectRelation("Question", cardinality="*1", inlined=False),
    name="questions")
Questionnaire.add_relation(
    SubjectRelation("QuestionnaireRun", cardinality="*1", inlined=False),
    name="questionnaire_runs")

# GENOMIC MEASURE
GenomicMeasure.add_relation(
    SubjectRelation("Subject", cardinality="**", inlined=False),
    name="subjects")
GenomicMeasure.remove_relation(name="related_study")
GenomicMeasure.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")
GenomicMeasure.add_relation(
    SubjectRelation("ProcessingRun", cardinality="**", inlined=False),
    name="processing_runs")

# ProcessingRun
ProcessingRun.add_relation(
    SubjectRelation("Subject", cardinality="**", inlined=False),
    name="subjects")
ProcessingRun.add_relation(
    SubjectRelation("Study", cardinality="1*", inlined=False),
    name="study")

# GENOMIC PLATFORM
GenomicPlatform.add_relation(
    SubjectRelation("GenomicMeasure", cardinality="*1", inlined=False),
    name="genomic_measures")
GenomicPlatform.remove_relation(name="related_snps")
GenomicPlatform.add_relation(
    SubjectRelation("Snp", cardinality="**", inlined=False),
    name="snps")

# SNP
Snp.add_relation(
    SubjectRelation("GenomicPlatform", cardinality="**", inlined=False),
    name="platforms")

# CWGROUP
class can_read(RelationDefinition):
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "*+"

class can_update(RelationDefinition):
    subject = "CWGroup"
    object = "Assessment"
    cardinality = "*+"

# RIGHTS
class in_assessment(RelationDefinition):
    subject = ("ProcessingRun", "ExternalFile")
    object = "Assessment"
    cardinality = "1*"
    inlined = True

# ENTITIES

# OPENANSWER
class OpenAnswer(EntityType):
    value = String(required=True)
    identifier = String(maxsize=64, indexed=True, unique=True)
    questionnaire_run = SubjectRelation("QuestionnaireRun", cardinality="1*",
                                        inlined=True)

# FMRIDATA
class FMRIData(EntityType):
    shape_x = Float()
    shape_y = Float()
    shape_z = Float()
    voxel_res_x = Float(required=True)
    voxel_res_y = Float(required=True)
    voxel_res_z = Float(required=True)
    fov_x = Float()
    fov_y = Float()
    tr = Float(required=True)
    te = Float()
    field = String(maxsize=10, indexed=True)
Scan.add_relation(SubjectRelation("FMRIData", cardinality='?1',
                                  composite="subject", inlined=True), name="has_data")


###############################################################################
# Set permissions
###############################################################################

ENTITIES = [
    Scan, FMRIData, DMRIData, PETData, MRIData, FileSet, ExternalFile,
    ScoreValue, ProcessingRun, QuestionnaireRun, OpenAnswer, GenomicMeasure]


DEFAULT_PERMISSIONS = {
    "read": ("managers", "users", "guests"),
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

# Set the subject/center/study/questionnaire/question entities permissions
Subject.set_permissions(DEFAULT_PERMISSIONS)
Center.set_permissions(DEFAULT_PERMISSIONS)
Study.set_permissions(DEFAULT_PERMISSIONS)
Questionnaire.set_permissions(DEFAULT_PERMISSIONS)
Question.set_permissions(DEFAULT_PERMISSIONS)

# Set the permissions on the used entities only
for entity in ENTITIES:
    entity.__permissions__ = ENTITY_PERMISSIONS

# Update the entities list to set relation permissions
ENTITIES.extend([Assessment, Subject, Center, Study, Questionnaire, Question])

# Set the permissions on the ised entities relations only
for entity in ENTITIES:

    # Get the subject relations
    for relation in entity.__relations__:
        if relation.__class__ is SubjectRelation:
            relation.__permissions__ = RELATION_PERMISSIONS
