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


class Scans(Base):
    """ This class enables us to load the scan data to CW.
    """
    def __init__(self, session, project_name, center_name, scans,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True):
        """ Initialize the Scans class.

        The cw groups are generated dynamically from the assessment
        identifiers:

            * we '_' split the string and create all the combinations.
            * the permissions 'can_read', 'can_update' relate the assessments
              with the corresponding group.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project
        center_name: str (mandatory)
            the center name
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

        Notes
        -----
        Here is an axemple of the definiton of the 'scans' parameter:

        scans = {
            "subjects1": [ {
                "Assessment": {
                    "age_of_subject": 27, "identifier": u"toy_V1_subject1",
                    "timepoint": u"V1"},
                "Scans": [ {
                    "TypeData": {
                        "fov_y": 0, "fov_x": 0, "voxel_res_y": 2.0,
                        "voxel_res_x": 2.0, "voxel_res_z": 2.0, "field": "3T",
                        "tr": 2.5, "shape_y": 2, "shape_x": 2, "shape_z": 2,
                        "te": 0, "type": u"MRIData"},
                    "ExternalResources": [ {
                        "absolute_path": True,
                        "identifier": u"toy_V1_subject1_t1_1", "name": u"t1",
                        "filepath": u"/tmp/demo/V1/subject1/images/t1/t1.nii.gz"}],
                    "FileSet": {
                        "identifier": u"toy_V1_subject1_t1", "name": u"T1"},
                    "Scan": {
                        "format": u"Nifti", "label": u"T1",
                        "identifier": u"toy_V1_subject1_t1", "type": u"MRIData"}
                }]
            } ]
        }
        """
        # Inheritance
        super(Scans, self).__init__(session, use_store)

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
        """

        #######################################################################
        # First get/create the study and the center
        #######################################################################

        center_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Center, X name "
                 "'{0}'".format(self.center_name)),
            entity_name="Center",
            identifier=unicode(self.center_name),
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
        # Start the scan insertion
        #######################################################################

        # Go through the data structure
        nb_of_subjects = float(len(self.scans))
        cnt_subject = 1.
        for subject_id, list_subj_scans in self.scans.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject / nb_of_subjects,
                               title="{0}(scans):".format(subject_id),
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
                scan_eid, "related_study", study_eid, check_unicity=False,
                subjtype="Scan")
            # > add relation with the subject
            self._set_unique_relation(
                scan_eid, "concerns", subject_eid, check_unicity=False,
                subjtype="Scan")
            # > add relation with the assessment
            self._set_unique_relation(
                assessment_eid, "uses", scan_eid, check_unicity=False)
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
                    scan_eid, "measure", score_entity.eid)
                # > add relation with the assessment
                self._set_unique_relation(
                    score_entity.eid, "in_assessment", assessment_eid,
                    subjtype="ScoreValue")

        return scan_eid

    def _create_assessment(self, assessment_struct, subject_eid, study_eid,
                           center_eid, groups):
        """ Create an assessment and its associated relations.
        """ 
        # Create the assessment
        assessment_id = assessment_struct["identifier"]
        assessment_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is Assessment, X identifier "
                 "'{0}'".format(assessment_id)),
            check_unicity=True,
            entity_name="Assessment",
            **assessment_struct)
        assessment_eid = assessment_entity.eid
        self.inserted_assessments[assessment_id] = assessment_eid

        # If we just create the assessment, relate the entity
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                assessment_eid, "related_study", study_eid, check_unicity=False,
                subjtype="Assessment")
            # > add relation with the subject
            self._set_unique_relation(
                subject_eid, "concerned_by", assessment_eid, check_unicity=False)
            self._set_unique_relation(
                assessment_eid, "concerns", subject_eid, check_unicity=False,
                subjtype="Assessment")
            # > add relation with the center
            self._set_unique_relation(
                center_eid, "holds", assessment_eid, check_unicity=False)

            # Set the permissions
            # Create/get the related assessment groups
            assessment_id = assessment_id.split("_")
            related_groups = [
                assessment_id[0],
                "_".join(assessment_id[:2])
            ]
            for group_name in related_groups:

                # Check the group is created
                if group_name in groups:
                    group_eid = groups[group_name]
                else:
                    raise ValueError(
                        "Please create first the group '{0}'.".format(group_name))

                # > add relation with group
                if self.can_read:
                    self._set_unique_relation(
                        group_eid, "can_read", assessment_eid)
                if self.can_update:
                    self._set_unique_relation(
                        group_eid, "can_update", assessment_eid)
    
        return assessment_eid   

    def _import_file_set(self, fset_struct, extfiles, parent_eid,
                         assessment_eid):
        """ Add the file set attached to a parent entity.
        """
        # Create the file set
        fset_entity, _ = self._get_or_create_unique_entity(
            rql="",
            check_unicity=False,
            entity_name="FileSet",
            **fset_struct)
        # > add relation with the parent
        self._set_unique_relation(parent_eid,
            "results_files", fset_entity.eid,
            check_unicity=False)
        # > add relation with the assessment
        self._set_unique_relation(fset_entity.eid,
            "in_assessment", assessment_eid,
            check_unicity=False, subjtype="FileSet")

        # Create the external files
        for extfile_struct in extfiles:
            file_entity, _ = self._get_or_create_unique_entity(
                rql="",
                check_unicity=False,
                entity_name="ExternalFile",
                **extfile_struct)
            # > add relation with the file set
            self._set_unique_relation(fset_entity.eid,
                "file_entries", file_entity.eid,
                check_unicity=False) 
            # > add relation with the assessment
            self._set_unique_relation(file_entity.eid,
                "in_assessment", assessment_eid,
                check_unicity=False, subjtype="ExternalFile")                     

