##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
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


class Scans(Base):
    """ This class enables us to load the scan data to CW.
    """
    # Define the relations involved
    relations = (
        Base.fileset_relations + Base.assessment_relations + [
            ("Scan", "study", "Study"),
            ("Study", "scans", "Scan"),
            ("Scan", "subject", "Subject"),
            ("Subject", "scans", "Scan"),
            ("Assessment", "scans", "Scan"),
            ("Scan", "in_assessment", "Assessment"),
            ("Scan", "has_data", "PETData"),
            ("PETData", "in_assessment", "Assessment"),
            ("Scan", "has_data", "FMRIData"),
            ("FMRIData", "in_assessment", "Assessment"),
            ("Scan", "has_data", "DMRIData"),
            ("DMRIData", "in_assessment", "Assessment"),
            ("Scan", "has_data", "MRIData"),
            ("MRIData", "in_assessment", "Assessment"),
            ("Scan", "score_values", "ScoreValue"),
            ("ScoreValue", "in_assessment", "Assessment")]
    )
    relations[0][0] = "Scan"

    def __init__(self, session, project_name, center_name, scans,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True, piws_security_model=True):
        """ Initialize the Scans class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project.
        center_name: str (mandatory)
            the center name.
        scans: dict of list of dict (mandatory)
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
        piws_security_model: bool (optional, default True)
            if True apply the PIWS security model.

        Notes
        -----
        Here is an axemple of the definiton of the 'scans' parameter:

        ::

            scans = {
                "subjects1": [ {
                    "Assessment": {
                        "age_of_subject": 27, "identifier": u"toy_V1_subject1",
                        "timepoint": u"V1"},
                    "Scans": [ {
                        "TypeData": {
                            "fov_y": 0, "fov_x": 0, "voxel_res_y": 2.0,
                            "voxel_res_x": 2.0, "voxel_res_z": 2.0,
                            "field": "3T", "tr": 2.5, "shape_y": 2,
                            "shape_x": 2, "shape_z": 2, "te": 0,
                            "type": u"MRIData"},
                        "ExternalResources": [ {
                            "absolute_path": True, "name": u"t1",
                            "identifier": u"toy_V1_subject1_t1_1",
                            "filepath": u"/tmp/demo/V1/subject1/images/t1/t1.nii.gz"}],
                        "FileSet": {
                            "identifier": u"toy_V1_subject1_t1", "name": u"T1"},
                        "Scan": {
                            "format": u"Nifti", "label": u"T1",
                            "identifier": u"toy_V1_subject1_t1",
                            "type": u"MRIData"}
                    }]
                } ]
            }
        """
        # Inheritance
        super(Scans, self).__init__(session, use_store, piws_security_model)

        # Class parameters
        self.scans = scans
        self.data_filepath = data_filepath or ""
        self.project_name = project_name
        self.center_name = center_name
        self.can_read = can_read
        self.can_update = can_update

        # Speed up parameters
        self.inserted_assessments = {}
        self.inserted_scans = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the scan data in the db.

        .. note::

            Below the schema used to insert the scans:

            |

            .. image:: ../schemas/scans.png
                :width: 600px
                :align: center
                :alt: schema

        .. warning::

            In the 'scans' input structure, the 'TypeData' item contains a
            special key 'type' corresponding to the data type. The associated
            value is a string representing the entity name that must be in
            ['PETData', 'FMRIData', 'DMRIData', 'MRIData'].

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
        # Start the scan insertion
        #######################################################################

        # Go through the data structure
        nb_of_subjects = float(len(self.scans))
        maxsize = max([len(name) for name in self.scans])
        cnt_subject = 1.
        for subject_id, list_subj_scans in self.scans.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject / nb_of_subjects,
                               title="{0}(scans)".format(subject_id),
                               bar_length=40, maxsize=maxsize + 7)
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
            # Insert all the subject scans
            ###################################################################

            for subj_scans in list_subj_scans:

                ###############################################################
                # Create the assessment
                ###############################################################

                # Get the assessment identifier
                assessment_struct = subj_scans["Assessment"]
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
                # Go through the scans - processings - scores
                ###############################################################

                for current_scan in subj_scans["Scans"]:

                    # Create the scan identifier
                    scan_struct = current_scan["Scan"]
                    scantype_struct = current_scan["TypeData"]
                    fset_struct = current_scan["FileSet"]
                    extfiles = current_scan["ExternalResources"]
                    scores = current_scan.get("Scores", None)
                    scan_id = scan_struct["identifier"]

                    # Check if this item has already been inserted
                    if scan_id in self.inserted_scans:
                        scan_eid = self.inserted_scans[scan_id]

                    # Create the scan
                    else:
                        scan_eid = self._create_scan(
                            scan_struct, scantype_struct, fset_struct, extfiles,
                            scores, subject_eid, study_eid, assessment_eid)

        print  # new line after last progress bar update

    def _create_scan(self, scan_struct, scantype_struct, fset_struct, extfiles,
                     scores, subject_eid, study_eid, assessment_eid):
        """ Create a scans and its associated relations.
        """
        # Create the scan
        scan_id = scan_struct["identifier"]
        scan_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is Scan, X identifier '{0}'".format(scan_id)),
            check_unicity=True,
            entity_name="Scan",
            **scan_struct)
        scan_eid = scan_entity.eid
        self.inserted_scans[scan_id] = scan_eid

        # If we just create the scan, specify and relate the entity
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                scan_eid, "study", study_eid, check_unicity=False)
            self._set_unique_relation(
                study_eid, "scans", scan_eid, check_unicity=False)
            # > add relation with the subject
            self._set_unique_relation(
                scan_eid, "subject", subject_eid, check_unicity=False)
            self._set_unique_relation(
                subject_eid, "scans", scan_eid, check_unicity=False)
            # > add relation with the assessment
            self._set_unique_relation(
                assessment_eid, "scans", scan_eid, check_unicity=False)
            self._set_unique_relation(
                scan_eid, "in_assessment", assessment_eid, check_unicity=False,
                subjtype="Scan")

            # Add the file set attached to a scan entity
            self._import_file_set(fset_struct, extfiles, scan_eid, assessment_eid)

            # Specialize the scan: set the data type
            if "type" in scantype_struct:
                dtype = scantype_struct.pop("type")
                dtype_entity, _ = self._get_or_create_unique_entity(
                    rql="",
                    check_unicity=False,
                    entity_name=dtype,
                    **scantype_struct)
                # > add relation with the scan
                self._set_unique_relation(
                    scan_eid, "has_data", dtype_entity.eid, check_unicity=False)
                # > add relation with the assessment
                self._set_unique_relation(
                    dtype_entity.eid, "in_assessment", assessment_eid,
                    check_unicity=False, subjtype=dtype)

        # Check if their is some scores attached to the current scan
        if scores is not None:

            # Go through all the scores attached to the scan
            for score_struct in scores:

                # Create the entity
                score_entity = self._get_or_create_unique_entity(
                    rql="",
                    check_unicity=False,
                    entity_name="ScoreValue",
                    **score_struct)
                # > add relation with the scan
                self._set_unique_relation(
                    scan_eid, "score_values", score_entity.eid)
                # > add relation with the assessment
                self._set_unique_relation(
                    score_entity.eid, "in_assessment", assessment_eid,
                    subjtype="ScoreValue")

        return scan_eid
