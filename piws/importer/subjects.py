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
    # Define the relations involved
    relations = [
        ("Subjects", "study", "Study"),
        ("Study", "subjects", "Subjects"),
        ("Subjects", "subjectgroups", "SubjectGroup"),
        ("SubjectGroup", "subjects", "Subjects"),
        ("Subjects", "dignostic", "Diagnostic"),
        ("Diagnostic", "subjects", "Subjects"),
        ("Subjects", "subject_protocol", "Protocol"),
        ("Protocol", "subjects", "Subjects"),
        ("Protocol", "study", "Study"),
        ("Study", "protocols", "Protocol")]

    def __init__(self, session, project_name, subjects, data_filepath=None,
                 store_type=None):
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
        store_type: str (optional, default None)
            store_type that must be None to use session, 'sql' to use
            SQLGenObjectStore, or 'massive' to use MassiveObjectStore.

        Notes
        -----
        Here is an axemple of the definiton of the 'subjects' parameter

        ::

            subjects = {
                "subject1": {
                    "code_in_study": "subject1",
                    "identifier": "toy_subject1",
                    "gender": "male",
                    "handedness": "right",
                    "groups": ["grp1", "grp2"],
                    "diagnostic": "normal",
                    "protocols": ["proto1", "proto2"]
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
        super(Subjects, self).__init__(
            session=session,
            can_read=True,
            can_update=True,
            store_type=store_type,
            piws_security_model=False)

        # Class parameters
        self.subjects = subjects
        self.project_name = project_name
        self.data_filepath = data_filepath or ""

        # Speed up parameters
        self.inserted_groups = {}
        self.inserted_diagnostics = {}
        self.inserted_protocol = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the subjects in the db.

        .. note::

            Below the schema used to insert the subject data:

            |

            .. image:: ../schemas/subjects.png
                :width: 600px
                :align: center
                :alt: schema

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
            data_filepath=unicode(self.data_filepath)
        )
        study_eid = study_entity.eid

        #######################################################################
        # Then create all the subjects
        #######################################################################

        # Go through the subject names
        nb_of_subjects = float(len(self.subjects))
        maxsize = max([len(name) for name in self.subjects])
        cnt_subject = 1
        for subject_name, subject_parameter in self.subjects.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject / nb_of_subjects,
                               title="{0}(subjects)".format(subject_name),
                               bar_length=40, maxsize=maxsize + 9)
            cnt_subject += 1.

            # Remove relation arguments from the subject structure
            diagnostic = subject_parameter.pop("diagnostic", None)
            groups = subject_parameter.pop("groups", None)
            protocols = subject_parameter.pop("protocols", None)

            # Create the subject if necessary
            subject_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Subject, X code_in_study "
                     "'{0}'".format(subject_parameter["code_in_study"])),
                check_unicity=True,
                entity_name="Subject",
                **subject_parameter)
            subject_eid = subject_entity.eid

            # If we just create the scan, specify and relate the entity
            if is_created:
                # > add relation with the study
                self._set_unique_relation(
                    subject_entity.eid, "study", study_eid, check_unicity=False)
                self._set_unique_relation(
                    study_eid, "subjects", subject_eid, check_unicity=False)

                # > add relation with groups (optional)
                if groups is not None:
                    self._create_subject_groups(groups, subject_eid, study_eid)

                # > add relation with diagnostic (optional)
                if diagnostic is not None:
                    self._create_subject_diagnostic(diagnostic, subject_eid)

                # > add relation with protocols (optional)
                if protocols is not None:
                    self._create_subject_protocols(
                        protocols, subject_eid, study_eid)

        print  # new line after last progress bar update

    ###########################################################################
    #   Private Methods
    ###########################################################################

    def _create_subject_groups(self, groups, subject_eid, study_eid):
        """ Link the subject with different groups.
        """
        # Go through each group
        for group_name in groups:

            # create the group if necessary
            if group_name in self.inserted_groups:
                subjectgroup_eid = self.inserted_groups[group_name]
            else:
                subjectgroup_entity, is_created = self._get_or_create_unique_entity(
                    rql=("Any X Where X is SubjectGroup, X name "
                         "'{0}'".format(group_name)),
                    check_unicity=True,
                    entity_name="SubjectGroup",
                    name=unicode(group_name))
                subjectgroup_eid = subjectgroup_entity.eid
                self.inserted_groups[group_name] = subjectgroup_eid

                # add relation with study
                if is_created:
                    self._set_unique_relation(
                        subjectgroup_eid, "study", study_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        study_eid, "study_subjectgroups", subjectgroup_eid,
                        check_unicity=False)

            # add relation with subject
            self._set_unique_relation(
                subject_eid, "subjectgroups", subjectgroup_eid,
                check_unicity=False)
            self._set_unique_relation(
                subjectgroup_eid, "subjects", subject_eid,
                check_unicity=False)

    def _create_subject_diagnostic(self, diagnostic, subject_eid):
        """ Link the subject with a diagnostic.
        """

        # Create the diagnostic if necessary
        if diagnostic in self.inserted_diagnostics:
            diagnostic_eid = self.inserted_diagnostics[diagnostic]
        else:
            diagnostic_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Diagnostic, X conclusion '{0}'".format(
                    diagnostic)),
                check_unicity=True,
                entity_name="Diagnostic",
                conclusion=unicode(diagnostic))
            diagnostic_eid = diagnostic_entity.eid
            self.inserted_diagnostics[diagnostic] = diagnostic_eid

        # Add relation with subject
        self._set_unique_relation(
            subject_eid, "diagnostic", diagnostic_eid, check_unicity=False)
        self._set_unique_relation(
            diagnostic_eid, "subjects", subject_eid, check_unicity=False)


    def _create_subject_protocols(self, protocols, subject_eid, study_eid):
        """ Link the subject with different protocols.
        """
        # Go through each protocol
        for protocol_name in protocols:

            # protocol in memory
            if protocol_name in self.inserted_protocol:
                protocol_eid = self.inserted_protocol[protocol_name]

            # create the protocol if necessary
            else:
                protocol_entity, is_created = self._get_or_create_unique_entity(
                    rql=("Any X Where X is Protocol, X name "
                         "'{0}'".format(protocol_name)),
                    check_unicity=True,
                    entity_name="Protocol",
                    name=unicode(protocol_name))
                protocol_eid = protocol_entity.eid
                self.inserted_protocol[protocol_name] = protocol_eid

                # add relation with study
                if is_created:
                    self._set_unique_relation(
                        protocol_eid, "study", study_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        study_eid, "protocols", protocol_eid,
                        check_unicity=False)

            # add relation with subject
            self._set_unique_relation(
                subject_eid, "subject_protocol", protocol_eid,
                check_unicity=False)
            self._set_unique_relation(
                protocol_eid, "subjects", subject_eid,
                check_unicity=False)

