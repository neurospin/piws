#! /usr/bin/env python
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

# Piws import
from .base import Base


class Questionnaires(Base):
    """ This class enables us to load the questionnaire to CW.
    """
    def __init__(self, session, project_name, center_name, questionnaires,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True):
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
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        data_filepath: str (optional, default None)
            the path to folder containing the current study dataset.
        use_store: bool (optional, default True)
            if True use an SQLGenObjectStore, otherwise the session.

        Notes
        -----
        Here is an example of the definition of the 'questionnaires' parameter:

        ::

            questionnaires = {
                "subject1": [
                    {
                        "Questionnaires": {
                            "Personal": {u"mood": 5}
                            "ID": {u"gender": u"male", u"age": 27,
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
                            "ID": {u"gender": u"male", u"age": 27,
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
        super(Questionnaires, self).__init__(session, use_store)

        # Parse the file system
        self.questionnaires = questionnaires
        self.data_filepath = data_filepath or ""
        self.project_name = project_name
        self.center_name = center_name
        self.can_read = can_read
        self.can_update = can_update

        # Speed up parameters
        self.inserted_assessments = {}

        # Define the relations involved
        self.relations = self.assessment_relations + [
            ("Question", "questionnaire", "Questionnaire"),
            ("Questionnaire", "questions", "Question"),
            ("QuestionnaireRun", "instance_of", "Questionnaire"),
            ("Questionnaire", "questionnaire_runs", "QuestionnaireRun"),
            ("Assessment", "questionnaire_runs", "QuestionnaireRun"),
            ("QuestionnaireRun", "in_assessment", "Assessment"),
            ("QuestionnaireRun", "study", "Study"),
            ("Study", "questionnaire_runs", "QuestionnaireRun"),
            ("QuestionnaireRun", "subject", "Subject"),
            ("Subject", "questionnaire_runs", "QuestionnaireRun"),
            ("OpenAnswer", "question", "Question"),
            ("Question", "open_answers", "OpenAnswer"),
            ("OpenAnswer", "questionnaire_run", "QuestionnaireRun"),
            ("QuestionnaireRun", "open_answers", "OpenAnswer"),
            ("OpenAnswer", "in_assessment", "Assessment"),
        ]

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import some questionnaires in the db.

        .. note::

            Below the schema used to insert the questionnaires:

            |

            .. image:: ../schemas/questionnaire.png
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
            "Any S, C, I Where S is Subject, S code_in_study C, S identifier I")
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
            for dquestionnaires in subject_questionnaires:
                for qname, question_struct in dquestionnaires[
                                            "Questionnaires"].iteritems():
                    qstructure.setdefault(qname, []).extend(
                        question_struct.keys())

        # Then fill the questionnaire form
        questionnaire_eids = {}
        question_eids = {}
        for qname, question_names in qstructure.iteritems():

            # Create a questionnaire form
            questionnaire_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Questionnaire, X name "
                     "'{0}'".format(qname)),
                check_unicity=True,
                entity_name = "Questionnaire",
                identifier=unicode(qname),
                name=unicode(qname),
                type=u"unknown")
            questionnaire_eids[qname] = questionnaire_entity.eid
            question_eids[qname] = {}

            # Create corresponding questions
            for question_name in set(question_names):
                question_id = qname + "_" + question_name
                question_entity, _ = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Question, X identifier "
                         "'{0}'".format(question_id)),
                    check_unicity=True,
                    entity_name = "Question",
                    identifier=unicode(question_id),
                    text=unicode(question_name),
                    type=u"text")
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
        cnt_subject = 1.

        # Add the data
        for subject_id, list_questionnaires in self.questionnaires.iteritems():

            # Print a progress bar
            self._progress_bar(
                cnt_subject / nb_of_subjects,
                title="{0}(questionnaires)".format(subject_id),
                bar_length=40)
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

                # Check if this item has already been inserted
                if assessment_id in self.inserted_assessments:
                    assessment_eid = self.inserted_assessments[assessment_id]

                # Create the assessment
                else:
                    assessment_eid = self._create_assessment(
                        assessment_struct, subject_eid, study_eid, center_eid,
                        groups)
                    self.inserted_assessments[assessment_id] = assessment_eid

                ###############################################################
                # Insert the patient answers in the db
                ###############################################################

                for q_name, q_items in timepoint_questionnaires[
                                                "Questionnaires"].iteritems():

                    qr_eid = self._create_questionnaire(
                        q_name, q_items, assessment_id, subject_id, subject_eid,
                        study_eid, assessment_eid, questionnaire_eids,
                        question_eids)

    def _create_questionnaire(self, questionnaire_name, q_items,
                              identifier_prefix, subject_id, subject_eid,
                              study_eid, assessment_eid, questionnaire_eids,
                              question_eids):
        """ Create a scans and its associated relations.
        """
        # Create a questionnaire run
        qr_id = identifier_prefix + "_" + questionnaire_name
        qr_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is QuestionnaireRun, X identifier "
                 "'{0}'".format(qr_id)),
            check_unicity=True,
            entity_name="QuestionnaireRun",
            user_ident=unicode(subject_id),
            identifier=unicode(qr_id),
            label=unicode(questionnaire_name))

        # If we just create the questionnaire run, specify and relate the entity
        if is_created:
            # > add relation with the questionnaire
            self._set_unique_relation(
                qr_entity.eid, "instance_of",
                questionnaire_eids[questionnaire_name], check_unicity=False)
            self._set_unique_relation(
                questionnaire_eids[questionnaire_name], "questionnaire_runs",
                qr_entity.eid, check_unicity=False)
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
                study_eid, "questionnaire_runs", qr_entity.eid,
                check_unicity=False)
            # > add relation with the subject
            self._set_unique_relation(
                qr_entity.eid, "subject", subject_eid, check_unicity=False)
            self._set_unique_relation(
                subject_eid, "questionnaire_runs", qr_entity.eid,
                check_unicity=False)

            # Go through all answers
            for question_name, answer in q_items.iteritems():

                # Get the question entity
                question_eid = question_eids[questionnaire_name][
                    question_name]

                # Create an open answer
                answer_entity, _ = self._get_or_create_unique_entity(
                    rql="",
                    check_unicity=False,
                    entity_name="OpenAnswer",
                    identifier=unicode(qr_id + "_" + question_name),
                    value=unicode(answer))
                # > add relation with the question
                self._set_unique_relation(
                    answer_entity.eid, "question", question_eid,
                    check_unicity=False, subjtype="OpenAnswer")
                self._set_unique_relation(
                    question_eid, "open_answers", answer_entity.eid,
                    check_unicity=False)
                # > add relation with the questionnaire run
                self._set_unique_relation(
                    answer_entity.eid, "questionnaire_run", qr_entity.eid,
                    check_unicity=False, subjtype="OpenAnswer")
                self._set_unique_relation(
                    qr_entity.eid, "open_answers", answer_entity.eid,
                    check_unicity=False)
                # > add relation with the assessment
                self._set_unique_relation(
                    answer_entity.eid, "in_assessment", assessment_eid,
                    check_unicity=False, subjtype="OpenAnswer")

        return qr_entity.eid
