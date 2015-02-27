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

# Neurospinweb import
from cubes.neurospinweb.scripts.base import Base


class Questionnaires(Base):
    """ This class enables us to load the questionnaire to CW.
    """
    def __init__(self, session, project_name, center_name, questionnaires,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True):
        """ Initialize the Questionnaires class.

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
        Here is an axemple of the definiton of the 'questionnaires' parameter:

        questionnaires = [ 
            {
                "Questionnaires": {
                    "Personal": {u"mood": 5}
                    "ID": {u"gender": u"male", u"age": 27, u"handedness": u"right"}
                }
                "Assessment": {
                    "age_of_subject": 27, "identifier": u"toy_V1_subject1",
                    "timepoint": u"V1'"
                }
            }, 
            {
                "Questionnaires": {
                    "Personal": {u"mood": 5}
                    "ID": {u"gender": u"male", u"age": 27, u"handedness": u"right"}
                }
                "Assessment": {
                    "age_of_subject": 27, "identifier": u"toy_V0_subject1",
                    "timepoint": u"V0"
                }
            }
        ]
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

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import some questionnaires in the db.
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
            data_filepath=unicode(self.data_path))
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
        for dquestionnaires in self.questionnaires:
            for qname, question_struct in dquestionnaires[
                                            "Questionnaires"].iteritems():
                qstructure.setdefault(qname, ()).union(
                    set(question_struct.keys()))

        # Then fill the questionnaire form
        questionnaire_eids = {}
        question_eids = {}
        for qname, question_names in self.qstructure.iteritems():

            # Create a questionnaire form
            questionnaire_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Questionnaire, X name "
                     "'{0}'".format(qname)),
                check_unicity=True,
                entity_name = "Questionnaire",
                identifier=unicode(questionnaire_name),
                name=unicode(questionnaire_name),
                type=u"unknown")
            questionnaire_eids[qname] = questionnaire_entity.eid
            question_eids[qname] = {}

            # Create corresponding questions
            for question in question_names:
                question_entity, _ = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Question, X text "
                         "'{0}'".format(question_name)),
                    check_unicity=True,
                    entity_name = "Question",
                    identifier=unicode(question_name),
                    text=unicode(question_name),
                    type=u"text")
                question_eids[qname][question] = question_entity.eid
                # > add relation with the questionnaire form
                self._set_unique_relation(question_entity.eid, "questionnaire",
                                          questionnaire_entity.eid)

        #######################################################################
        # Insert each subject answers
        #######################################################################

        # Information to create a progress bar
        nb_of_subjects = float(len(self.dataset["Subject"]))
        cnt_subject = 1.

        # Add the data
        for subject_struct, measure_item in zip(
            self.dataset["Subject"], self.dataset["Measure"]):

            # Print a progress bar
            self._progress_bar(
                cnt_subject/nb_of_subjects,
                title="{0}(measures)".format(subject_struct["code_in_study"]),
                bar_length=40)
            cnt_subject += 1

            # Create subject
            subject_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Subject, X identifier "
                     "'{0}'".format(subject_struct["identifier"])),
                entity_name="Subject",
                **subject_struct)

            # Create all measures
            for sub_exam_name, answer_item in measure_item.iteritems():

                ##############################################################
                # Create assessment
                ##############################################################

                assessment_struct = answer_item["Assessment"]
                assessment_entity, is_created = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Assessment, X identifier "
                         "'{0}'".format(assessment_struct["identifier"])),
                    entity_name="Assessment",
                    **assessment_struct)
                if is_created:
                    # > add relation with the study
                    self._set_unique_relation(assessment_entity.eid,
                        "related_study", study_entity.eid, check_unicity=False)
                    # > add relation with the subject
                    self._set_unique_relation(subject_entity.eid,
                        "concerned_by", assessment_entity.eid, check_unicity=False)
                    self._set_unique_relation(assessment_entity.eid,
                        "concerns", subject_entity.eid, check_unicity=False)
                    # > add relation with the center
                    self._set_unique_relation(center_entity.eid,
                        "holds", assessment_entity.eid, check_unicity=False)

                    # Set the permissions
                    # Create/get the related assessment groups
                    assessment_id = assessment_struct["identifier"].split("_")
                    related_groups = [
                        assessment_id[0],
                        assessment_id[1],
                        "_".join(assessment_id[:2]),
                        "_".join(assessment_id[1:3]),
                    ]
                    for group_name in related_groups:

                        # Create/get the entity
                        group_entity, is_created = self._get_or_create_unique_entity(
                            rql=("Any X Where X is CWGroup, X name "
                                 "'{0}'".format(group_name)),
                            entity_name="CWGroup",
                            name=unicode(group_name))
                        # > add relation with group
                        if self.can_read:
                            self._set_unique_relation(group_entity.eid,
                                "can_read", assessment_entity.eid)
                        if self.can_update:
                            self._set_unique_relation(group_entity.eid,
                                "can_update", assessment_entity.eid) 

                ###############################################################
                # Insert the patient answers in the db
                ###############################################################

                for q_name, q_items in answer_item["Answers"].iteritems():

                    # Unpack questionnaire items
                    qr_struct, answer_items = q_items

                    # Get the corresponding questionnaire name
                    questionnaire_name = qr_struct["user_ident"].split("_")[0]

                    # Create a questionnaire run
                    print qr_struct
                    qr_entity, is_created = self._get_or_create_unique_entity(
                        rql=("Any X Where X is QuestionnaireRun, X user_ident "
                             "'{0}'".format(qr_struct["user_ident"])),
                        entity_name="QuestionnaireRun",
                        **qr_struct)
                    if is_created:
                        # > add relation with the questionnaire
                        self._set_unique_relation(qr_entity.eid, "instance_of",
                            questionnaire_entities[questionnaire_name].eid,
                            check_unicity=False)
                        # > add relation with the assessment
                        self._set_unique_relation(
                            assessment_entity.eid, "uses",
                            qr_entity.eid, check_unicity=False)
                        self._set_unique_relation(qr_entity.eid,
                            "in_assessment", assessment_entity.eid,
                            check_unicity=False)
                        # > add relation with the study
                        self._set_unique_relation(qr_entity.eid, "related_study",
                            study_entity.eid, check_unicity=False)
                        # > add relation with the subject
                        self._set_unique_relation(qr_entity.eid, "concerns",
                            subject_entity.eid, check_unicity=False)

                        # Go through all answers
                        for answer_struct in answer_items:

                            # Get the corresponding question name
                            question_name = answer_struct[
                                "identifier"].split("_")[1]
                            # Get the question entity
                            question_entity = questions_entities[
                                questionnaire_name][question_name]

                            # Create an open answer
                            answer_entity, _ = self._get_or_create_unique_entity(
                                rql="",
                                entity_name="OpenAnswer",
                                check_unicity=False,
                                **answer_struct)
                            # > add relation with the question
                            self._set_unique_relation(answer_entity.eid, "question",
                                question_entity.eid)
                            # > add relation with the questionnaire run
                            self._set_unique_relation(answer_entity.eid,
                                "questionnaire_run", qr_entity.eid)
                            # > add relation with the assessment
                            self._set_unique_relation(answer_entity.eid,
                                "in_assessment", assessment_entity.eid,
                                check_unicity=False)
