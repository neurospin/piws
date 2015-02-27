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

# Neurospinweb import
from cubes.neurospinweb.scripts.base import Base


class Subjects(Base):
    """ This class enables us to add new subjects in CW.
    """
    def __init__(self, session, subjects, use_store=True):
        """ Initialize the Subjects class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        subjects: dict (mandatory)
            the user names as keys and a dict with the group_names, login and
            password.
        use_store: bool (optional, default True)    
            if True use an SQLGenObjectStore, otherwise the session.

        Notes
        -----
        Here is an axemple of the definiton of the 'subjects' parameter:

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

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the subjects in cw.
        """
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
            subject_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Subject, X identifier "
                     "'{0}'".format(subject_parameter["identifier"])),
                check_unicity=True,
                entity_name="Subject",
                **subject_parameter)
