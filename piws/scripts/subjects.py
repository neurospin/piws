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
import logging

# Piws import
from .base import Base


class Subjects(Base):
    """ This class enables us to add new subjects in CW.
    """
    def __init__(self, session, project_name, subjects, data_filepath=None,
                 use_store=True):
        """ Initialize the Subjects class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project.
        subjects: dict (mandatory)
            the user names as keys and a dict with the group_names, login and
            password.
        data_filepath: str (optional, default None)
            the path to folder containing the current study dataset.
        use_store: bool (optional, default True)    
            if True use an SQLGenObjectStore, otherwise the session.

        Notes
        -----
        Here is an axemple of the definiton of the 'subjects' parameter

        ::

            subjects = {
                "subject1": {
                    "code_in_study": "subject1",
                    "identifier": "toy_subject1",
                    "gender": "male",
                    "handedness": "right"
                },
                "subject2": {
                    "code_in_study": "subject2",
                    "identifier": "toy_subject2",
                    "gender": "female",
                    "handedness": "ambidextrous"
                }
            }
        """
        # Inheritance
        super(Subjects, self).__init__(session, use_store)

        # Class parameters
        self.subjects = subjects
        self.project_name = project_name
        self.data_filepath = data_filepath or ""

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the subjects in cw.

        .. note::

            This procedure create a 'Subject' entity for each input subject
            name.

        .. warning::

            The dictionary associated to each subject name in the 'subjects'
            parameter must match the entity attributes defined by
            the cubicweb schema (it may depends on the version of the cubes
            you are using).
        """
        #######################################################################
        # First get/create the study
        #######################################################################

        study_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Study, X name "
                 "'{0}'".format(self.project_name)),
            entity_name="Study",
            check_unicity=True,
            name=unicode(self.project_name),
            data_filepath=unicode(self.data_filepath))
        study_eid = study_entity.eid

        #######################################################################
        # Then create all the subjects
        #######################################################################

        # Go through the subject names
        nb_of_subjects = float(len(self.subjects))
        cnt_subject = 1
        for subject_name, subject_parameter in self.subjects.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject / nb_of_subjects,
                               title="Import {0}:".format(subject_name),
                               bar_length=40)
            cnt_subject += 1.

            # Create the subject if necessary
            subject_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Subject, X identifier "
                     "'{0}'".format(subject_parameter["identifier"])),
                check_unicity=True,
                entity_name="Subject",
                **subject_parameter)

            # If we just create the scan, specify and relate the entity
            if is_created:
                # > add relation with the study
                self._set_unique_relation(
                    subject_entity.eid, "study", study_eid, check_unicity=False)
                self._set_unique_relation(
                    study_eid, "subjects", subject_entity.eid,
                    check_unicity=False)
