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

# Piws import
from .base import Base


class Processings(Base):
    """ This class enables us to load the processing data to CW.
    """
    def __init__(self, session, project_name, center_name, processings,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True, piws_security_model=True):
        """ Initialize the Processings class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project.
        center_name: str (mandatory)
            the center name.
        processings: dict of list of dict (mandatory)
            the processing description: the first dictionary contains the subject
            name as keys and then a list of dictionaries with two keys (
            Assessment - Processings) that contains the entities parameter
            decriptions.
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        data_filepath: str (optional, default None)
            the path to folder containing the current study dataset.
        use_store: bool (optional, default True)
            if True use an SQLGenObjectStore, otherwise the session.
        piws_security_model: bool (optional, default True)
            if True use the security model specific to PIWS.

        Notes
        -----
        Here is an axemple of the definiton of the 'processings' parameter:

        ::

            processings = {
                "subjects1": [ {
                    "Assessment": {
                        "identifier": u"toy_V1_subject1",
                        "timepoint": u"V1"},
                    "Processings": [ {
                        "Inputs": ["Any X Where X is Scan"],
                        "ExternalResources": [ {
                            "absolute_path": True, "name": u"p1",
                            "identifier": u"toy_V1_subject1_p1_1",
                            "filepath": u"/tmp/demo/V1/subject1/images/t1/t1.nii.gz"}],
                        "FileSet": {
                            "identifier": u"toy_V1_subject1_p1", "name": u"p1"},
                        "ProcessingRun": {
                            "identifier": u"toy_V1_subject1_p1",
                            "name": u"p1", "label": u"segmentation",
                            "tool": u"spm", "version": u"8.1",
                            "parameters": u"{'a': 1, 'r': 'mypath'}"}
                    }]
                } ]
            }
        """
        # Inheritance
        super(Processings, self).__init__(session, use_store)

        # Class parameters
        self.processings = processings
        self.data_filepath = data_filepath or ""
        self.project_name = project_name
        self.center_name = center_name
        self.can_read = can_read
        self.can_update = can_update
        self.piws_security_model = piws_security_model

        # Speed up parameters
        self.inserted_assessments = {}
        self.inserted_processings = {}

        # Define the relations involved
        self.relations = (
            self.fileset_relations + self.assessment_relations + [
                ("ProcessingRun", "study", "Study"),
                ("Study", "processing_runs", "ProcessingRun"),
                ("ProcessingRun", "subject", "Subject"),
                ("Subject", "processing_runs", "ProcessingRun"),
                ("Assessment", "processing_runs", "ProcessingRun"),
                ("ProcessingRun", "in_assessment", "Assessment"),
                ("ProcessingRun", "score_values", "ScoreValue"),
                ("ScoreValue", "in_assessment", "Assessment")]
        )
        self.relations[0][0] = "ProcessingRun"

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the processing data in the db.

        .. note::

            Below the schema used to insert the scans:

            |

            .. image:: ../schemas/processing.png
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
        # Start the processing insertion
        #######################################################################

        # Go through the data structure
        nb_of_subjects = float(len(self.processings))
        cnt_subject = 1.
        for subject_id, list_subj_processings in self.processings.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject / nb_of_subjects,
                               title="{0}(processings):".format(subject_id),
                               bar_length=40)
            cnt_subject += 1.

            ###################################################################
            # Check the subject exists in the database
            ###################################################################

            if subject_id in study_subjects:
                subject_eid = study_subjects[subject_id]
            else:
                raise ValueError("The subject '{0}' in not known by the "
                                 "database.".format(subject_id))

            ###################################################################
            # Insert all the subject processings
            ###################################################################

            for subj_processings in list_subj_processings:

                ###############################################################
                # Create the assessment
                ###############################################################

                # Get the assessment identifier
                assessment_struct = subj_processings["Assessment"]
                assessment_id = assessment_struct["identifier"]

                # Check if this item has already been inserted
                if assessment_id in self.inserted_assessments:
                    assessment_eid = self.inserted_assessments[assessment_id]

                    # > add relation with the subject if not already set
                    self._set_unique_relation(
                        subject_eid, "assessments", assessment_eid,
                        check_unicity=True)
                    self._set_unique_relation(
                        assessment_eid, "subjects", subject_eid,
                        check_unicity=True, subjtype="Assessment")

                # Create the assessment
                else:
                    assessment_eid = self._create_assessment(
                        assessment_struct, subject_eid, study_eid, center_eid,
                        groups, self.piws_security_model)
                    self.inserted_assessments[assessment_id] = assessment_eid

                ###############################################################
                # Go through the processings - scores
                ###############################################################

                for current_processing in subj_processings["Processings"]:

                    # Create the processing identifier
                    processing_struct = current_processing["ProcessingRun"]
                    processing_inputs = current_processing["Inputs"]
                    fset_struct = current_processing["FileSet"]
                    extfiles = current_processing["ExternalResources"]
                    scores = current_processing.get("Scores", None)
                    processing_id = processing_struct["identifier"]

                    # Check if this item has already been inserted
                    if processing_id in self.inserted_processings:
                        processing_eid = self.inserted_processings[processing_id]

                        # Deal with multi subject analysis
                        # > add relation with the subject
                        self._set_unique_relation(
                            processing_eid, "subjects", subject_eid,
                            check_unicity=True)
                        self._set_unique_relation(
                            subject_eid, "processing_runs", processing_eid,
                            check_unicity=True)

                    # Create the processing
                    else:
                        processing_eid = self._create_processing(
                            processing_struct, fset_struct, extfiles,
                            scores, processing_inputs, subject_eid, study_eid,
                            assessment_eid)

    def _create_processing(self, processing_struct, fset_struct, extfiles,
                           scores, processing_inputs, subject_eid, study_eid,
                           assessment_eid):
        """ Create a processing and its associated relations.
        """
        # Create the processing
        processing_id = processing_struct["identifier"]
        processing_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is ProcessingRun, X identifier '{0}'".format(
                processing_id)),
            check_unicity=True,
            entity_name="ProcessingRun",
            **processing_struct)
        processing_eid = processing_entity.eid
        self.inserted_processings[processing_id] = processing_eid

        # If we just create the processing, relate the entity
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                processing_eid, "study", study_eid, check_unicity=False)
            self._set_unique_relation(
                study_eid, "processing_runs", processing_eid, check_unicity=False)
            # > add relation with the subject
            self._set_unique_relation(
                processing_eid, "subjects", subject_eid, check_unicity=False)
            self._set_unique_relation(
                subject_eid, "processing_runs", processing_eid, check_unicity=False)
            # > add relation with the assessment
            self._set_unique_relation(
                assessment_eid, "processing_runs", processing_eid, check_unicity=False)
            self._set_unique_relation(
                processing_eid, "in_assessment", assessment_eid, check_unicity=False,
                subjtype="ProcessingRun")
            # > add relation with the inputs
            for rql in processing_inputs:
                for item in self.session.execute(rql):
                    input_eid = item[0]
                    self._set_unique_relation(
                        processing_eid, "inputs", input_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        input_eid, "processing_runs", processing_eid,
                        check_unicity=False)

            # Add the file set attached to a processing entity
            self._import_file_set(fset_struct, extfiles, processing_eid,
                                  assessment_eid)

        # Check if their is some scores attached to the current processing
        if scores is not None:

            # Go through all the scores attached to the scan
            for score_struct in scores:

                # Create the entity
                score_entity = self._get_or_create_unique_entity(
                    rql="",
                    check_unicity=False,
                    entity_name="ScoreValue",
                    **score_struct)
                # > add relation with the processing
                self._set_unique_relation(
                    processing_eid, "outputs", score_entity.eid)
                # > add relation with the assessment
                self._set_unique_relation(
                    score_entity.eid, "in_assessment", assessment_eid,
                    subjtype="ScoreValue")

        return processing_eid
