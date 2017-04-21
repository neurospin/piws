##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import sys
import hashlib
import json
from collections import OrderedDict

# CubicWeb import
from cubicweb import Binary
from cubes.brainomics2.schema.questionnaire import ANSWERS_RTYPE

# Piws import
from .base import Base


class Questionnaires(Base):
    """ This class enables us to load questionnaires into a CW instance.
    """
    # Define the relations involved
    relations = Base.assessment_relations + [
        ("Question", "questionnaire", "Questionnaire"),
        ("Questionnaire", "questions", "Question"),
        ("QuestionnaireRun", "questionnaire", "Questionnaire"),
        ("Questionnaire", "questionnaire_questionnaire_runs", "QuestionnaireRun"),
        ("Assessment", "questionnaire_runs", "QuestionnaireRun"),
        ("QuestionnaireRun", "in_assessment", "Assessment"),
        ("QuestionnaireRun", "study", "Study"),
        ("Study", "study_questionnaire_runs", "QuestionnaireRun"),
        ("QuestionnaireRun", "subject", "Subject"),
        ("Subject", "subject_questionnaire_runs", "QuestionnaireRun"),
        ("TextAnswer", "question", "Question"),
        ("Question", "question_text_answers", "TextAnswer"),
        ("TextAnswer", "questionnaire_run", "QuestionnaireRun"),
        ("QuestionnaireRun", "text_answers", "TextAnswer"),
        ("TextAnswer", "in_assessment", "Assessment"),
        ("IntAnswer", "question", "Question"),
        ("Question", "question_int_answers", "IntAnswer"),
        ("IntAnswer", "questionnaire_run", "QuestionnaireRun"),
        ("QuestionnaireRun", "int_answers", "IntAnswer"),
        ("IntAnswer", "in_assessment", "Assessment"),
        ("FloatAnswer", "question", "Question"),
        ("Question", "question_float_answers", "FloatAnswer"),
        ("FloatAnswer", "questionnaire_run", "QuestionnaireRun"),
        ("QuestionnaireRun", "float_answers", "FloatAnswer"),
        ("FloatAnswer", "in_assessment", "Assessment"),
        ("QuestionnaireRun", "file", "RestrictedFile")
    ]
    annotation_operator = ": "

    def __init__(self, session, project_name, center_name, questionnaires,
                 questionnaire_type, can_read=True, can_update=True,
                 data_filepath=None, store_type="RQL", piws_security_model=True,
                 use_openanswer=False):
        """ Initialize the 'Questionnaires' class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project
        center_name: str (mandatory)
            the center name
        questionnaires: dict of list of dict (mandatory)
            the scan description: the first dictionary contains the subject
            name as keys and then a list of dictionaries with four keys (Scans -
            (Scan - TypeData - FileSet - ExternalResource - ScoreValues) -
            Assessment) that contains the entities parameter decriptions.
        questionnaire_type: str (mandatory)
            a questionnaire type used to gather together similar
            questionnaires.
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        data_filepath: str (optional, default None)
            the path to folder containing the current study dataset.
        store_type: str (optional, default 'RQL')
            Must be in ['RQL', 'SQL', 'MASSIVE'].
            'RQL' to use session, 'SQL' to use SQLGenObjectStore, or 'MASSIVE'
            to use MassiveObjectStore.
        piws_security_model: bool (optional, default True)
            if True apply the PIWS security model.
        use_openanswer : bool (optional, default False)
            if True insert questionnaires using the {{RTYPE}}Answer entity,
            else using the File entity.

        Notes
        -----
        Here is an example of the definition of the 'questionnaires' parameter.
        Note that in the case of open answers, you can specify the type
        of a question with the ': ' annotation operator. The ': ' is thus
        reserved and must not be used in question mapings:

        ::

            questionnaires = {
                "subject1": [
                    {
                        "Questionnaires": {
                            "Personal": {u"mood": 5}
                            "ID": {u"gender": u"male", u"age: int": 27,
                                   u"handedness": u"right"}
                        }
                        "Assessment": {
                            "age_of_subject": 27,
                            "identifier": u"toy_V1_subject1",
                            "timepoint": u"V1'"
                        }
                    },
                    {
                        "Questionnaires": {
                            "Personal": {u"mood": 5}
                            "ID": {u"gender": u"male", u"age: int": 27,
                                   u"handedness": u"right"}
                        }
                        "Assessment": {
                            "age_of_subject": 27,
                            "identifier": u"toy_V0_subject1",
                            "timepoint": u"V0"
                        }
                    }
                ]
            }
        """
        # Inheritance
        super(Questionnaires, self).__init__(
            session=session,
            can_read=can_read,
            can_update=can_update,
            store_type=store_type,
            piws_security_model=piws_security_model)

        # Define QuestionnaireRuns insertion strategy
        self.use_openanswer = use_openanswer

        # Parse the file system
        self.questionnaires = questionnaires
        self.data_filepath = data_filepath or ""
        self.project_name = project_name
        self.center_name = center_name
        self.questionnaire_type = questionnaire_type

        # Speed up parameters
        self.inserted_assessments = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import some questionnaires in the db.

        .. note::

            Below the schema used to insert the questionnaires:

            |

            .. image:: ../schemas/questionnaires.png
                :width: 600px
                :align: center
                :alt: schema

        .. warning::

            This method assumes that all the subjects and groups have already
            been inserted in the database.
        """

        #######################################################################
        # First get/create the study and the center
        #######################################################################

        center_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Center, X name "
                 "'{0}'".format(self.center_name)),
            entity_name="Center",
            identifier=unicode(self._md5_sum(self.center_name)),
            name=unicode(self.center_name))
        center_eid = center_entity.eid
        study_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Study, X name "
                 "'{0}'".format(self.project_name)),
            entity_name="Study",
            name=unicode(self.project_name),
            data_filepath=unicode(self.data_filepath))
        study_eid = study_entity.eid

        #######################################################################
        # Get all the subjects
        #######################################################################

        rset = self.session.execute(
            "Any S, C, N Where S is Subject, S code_in_study C, S study E, "
            "E name N")
        study_subjects = dict((row[1], row[0]) for row in rset
                              if row[2].startswith(self.project_name))

        #######################################################################
        # Get all the groups
        #######################################################################

        rset = self.session.execute(
            "Any G, N Where G is CWGroup, G name N")
        groups = dict((row[1], row[0]) for row in rset)

        #######################################################################
        # Create the questionnaires and associated questions
        #######################################################################

        # Get the questionnaire structure
        qstructure = {}
        for subject_questionnaires in self.questionnaires.values():
            for list_of_questionnaires in subject_questionnaires:
                for qname, question_struct in list_of_questionnaires[
                                            "Questionnaires"].items():
                    if qname not in qstructure:
                        qstructure[qname] = OrderedDict()
                    for question_name in question_struct:
                        question_name, question_type = self._parse_annotation(
                            question_name)
                        qstructure[qname][question_name] = question_type

        # Then fill the questionnaire form
        questionnaire_eids = {}
        question_eids = {}
        for qname, questions_struct in qstructure.iteritems():

            # Create a questionnaire form
            questionnaire_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Questionnaire, X name "
                     "'{0}'".format(qname)),
                check_unicity=True,
                entity_name = "Questionnaire",
                identifier=unicode(self._md5_sum(qname)),
                name=unicode(qname),
                type=unicode(self.questionnaire_type))
            questionnaire_eids[qname] = questionnaire_entity.eid
            question_eids[qname] = {}

            # Create corresponding questions
            for index, (question_name, question_type) in enumerate(
                    questions_struct.items()):
                question_id = self._md5_sum(qname + "_" + question_name)
                question_entity, _ = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Question, X identifier "
                         "'{0}'".format(question_id)),
                    check_unicity=True,
                    entity_name = "Question",
                    identifier=unicode(question_id),
                    text=unicode(question_name),
                    position=index,
                    type=unicode(question_type))
                question_eids[qname][question_name] = question_entity.eid
                # > add relation with the questionnaire form
                self._set_unique_relation(question_entity.eid, "questionnaire",
                                          questionnaire_entity.eid)
                self._set_unique_relation(questionnaire_entity.eid, "questions",
                                          question_entity.eid)

        #######################################################################
        # Insert each subject answers
        #######################################################################

        # Information to create a progress bar
        nb_of_subjects = float(len(self.questionnaires))
        maxsize = max([len(name) for name in self.questionnaires])
        cnt_subject = 1.

        # Add the data
        for subject_id, list_questionnaires in self.questionnaires.iteritems():

            # Print a progress bar
            self._progress_bar(
                cnt_subject / nb_of_subjects,
                title="{0}(questionnaires)".format(subject_id),
                bar_length=40, maxsize=maxsize + 16)
            cnt_subject += 1

            ###################################################################
            # Check the subject exists in the database
            ###################################################################

            if subject_id in study_subjects:
                subject_eid = study_subjects[subject_id]
            else:
                raise ValueError("The subject '{0}' in not known by the "
                                 "database.".format(subject_id))

            ###################################################################
            # Insert all the subject questionnaires
            ###################################################################

            for timepoint_questionnaires in list_questionnaires:

                ##############################################################
                # Create the assessment
                ##############################################################

                # Get the assessment identifier
                assessment_struct = timepoint_questionnaires["Assessment"]
                assessment_id = assessment_struct["identifier"]

                # Create the assessment, check if this item has already been
                # inserted
                assessment_eid, is_created = self._create_assessment(
                    assessment_struct, subject_eid, study_eid, center_eid,
                    groups)

                ###############################################################
                # Insert the patient answers in the db
                ###############################################################

                for q_name, q_items in timepoint_questionnaires[
                                                "Questionnaires"].iteritems():

                    qr_eid = self._create_questionnaire(
                        q_name, q_items, assessment_id, subject_id, subject_eid,
                        study_eid, assessment_eid, questionnaire_eids,
                        question_eids)

        print  # new line after last progress bar update

    ###########################################################################
    #   Private Methods
    ###########################################################################

    def _create_questionnaire(self, questionnaire_name, q_items,
                              identifier_prefix, subject_id, subject_eid,
                              study_eid, assessment_eid, questionnaire_eids,
                              question_eids):
        """ Create a scans and its associated relations.
        """
        # Create a questionnaire run
        qr_id = self._md5_sum(identifier_prefix + "_" + questionnaire_name)
        qr_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is QuestionnaireRun, X identifier "
                 "'{0}'".format(qr_id)),
            check_unicity=True,
            entity_name="QuestionnaireRun",
            identifier=unicode(qr_id),
            label=unicode(questionnaire_name)
        )

        # If we just create the questionnaire run, specify and relate the entity
        if is_created:
            # > add relation with the questionnaire
            self._set_unique_relation(
                qr_entity.eid, "questionnaire",
                questionnaire_eids[questionnaire_name], check_unicity=False)
            self._set_unique_relation(
                questionnaire_eids[questionnaire_name],
                "questionnaire_questionnaire_runs", qr_entity.eid,
                check_unicity=False)
            # > add relation with the assessment
            self._set_unique_relation(
                assessment_eid, "questionnaire_runs", qr_entity.eid,
                check_unicity=False)
            self._set_unique_relation(
                qr_entity.eid, "in_assessment", assessment_eid,
                check_unicity=False, subjtype="QuestionnaireRun")
            # > add relation with the study
            self._set_unique_relation(
                qr_entity.eid, "study", study_eid, check_unicity=False)
            self._set_unique_relation(
                study_eid, "study_questionnaire_runs", qr_entity.eid,
                check_unicity=False)
            # > add relation with the subject
            self._set_unique_relation(
                qr_entity.eid, "subject", subject_eid, check_unicity=False)
            self._set_unique_relation(
                subject_eid, "subject_questionnaire_runs", qr_entity.eid,
                check_unicity=False)

            if self.use_openanswer:
                # Go through all answers
                for question_attribute, answer in q_items.iteritems():

                    # Parse question attribute
                    question_name, rtype = self._parse_annotation(
                        question_attribute)
                    etype = "{0}Answer".format(rtype.title())

                    # Get the question entity
                    question_eid = question_eids[questionnaire_name][
                        question_name]

                    # Create an answer of the good type
                    answer_entity, _ = self._get_or_create_unique_entity(
                        rql="",
                        check_unicity=False,
                        entity_name=etype,
                        identifier=unicode(self._md5_sum(
                            qr_id + "_" + question_name)),
                        value=answer)
                    # > add relation with the question
                    self._set_unique_relation(
                        answer_entity.eid, "question", question_eid,
                        check_unicity=False, subjtype=etype)
                    self._set_unique_relation(
                        question_eid, "question_{0}_answers".format(rtype),
                        answer_entity.eid, check_unicity=False)
                    # > add relation with the questionnaire run
                    self._set_unique_relation(
                        answer_entity.eid, "questionnaire_run", qr_entity.eid,
                        check_unicity=False, subjtype=etype)
                    self._set_unique_relation(
                        qr_entity.eid, "{0}_answers".format(rtype),
                        answer_entity.eid, check_unicity=False)
                    # > add relation with the assessment
                    self._set_unique_relation(
                        answer_entity.eid, "in_assessment", assessment_eid,
                        check_unicity=False, subjtype=etype)
            else:
                f_entity, _ = self._get_or_create_unique_entity(
                    rql="",
                    entity_name="RestrictedFile",
                    title=u"{0} ({1})".format(questionnaire_name, subject_id),
                    data=Binary(json.dumps(q_items)),
                    data_format=u"text/json",
                    data_name=u"result.json",
                    check_unicity=False)
                self._set_unique_relation(
                    qr_entity.eid, "file", f_entity.eid,
                    check_unicity=False, subjtype="QuestionnaireRun")
                self._set_unique_relation(
                    f_entity.eid, "in_assessment", assessment_eid,
                    check_unicity=False, subjtype="RestrictedFile")

        return qr_entity.eid

    def _parse_annotation(self, attribute_name):
        """ Parse an annotation.

        Parameters
        ----------
        attribute_name: str
            the input string to be parsed.

        Returns
        -------
        name: str
            the attribute name.
        type: str
            the attribute type.
        """
        attribute_split = attribute_name.split(self.annotation_operator)
        if len(attribute_split) > 2:
            raise ValueError("Invalid attribute name '{0}'. '{1}' is a "
                             "reserved operator.".format(
                                    attribute_name, self.annotation_operator))
        elif len(attribute_split) == 1:
            attribute_split.append("text")
        if attribute_split[1] not in ANSWERS_RTYPE:
            raise ValueError("Unsupported question type '{0}'. Defined types "
                             "are {1}.".format(
                                    attribute_split[1], ANSWERS_RTYPE))
        return attribute_split
