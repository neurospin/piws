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


class Samples(Base):
    """ This class enables us to parse and load the sapmle data
    to the cubicweb database
    """
    def __init__(self, session, project_name, center_name, data_path, parser,
                 can_read=True, can_update=True):
        """ Initialize the Measures class

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project
        center_name: str (mandatory)
            the center name
        data_path: str (mandatory)
            the 'parser' function input that specify where the data are
        parser: @function (mandatory)
            the function to parse the filesystem
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        """
        # Inheritance
        super(Samples, self).__init__(session)

        # Parameters
        self.data_path = data_path
        self.project_name = project_name
        self.center_name = center_name
        self.can_read = can_read
        self.can_update = can_update

        # Parse the file system
        self.dataset = parser(project_name, center_name, data_path)

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import some measures in the db.
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
        study_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Study, X name "
                 "'{0}'".format(self.project_name)),
            entity_name="Study",
            name=unicode(self.project_name),
            data_filepath=unicode(self.data_path))

        #######################################################################
        # Insert each subject samples
        #######################################################################

        # Information to create a progress bar
        nb_of_subjects = float(len(self.dataset.keys()))
        cnt_subject = 1.

        # Add the data
        for subject_id, sample_item in self.dataset.iteritems():

            # Print a progress bar
            self._progress_bar(cnt_subject/nb_of_subjects,
                               title="{0}(samples)".format(subject_id),
                               bar_length=40)
            cnt_subject += 1

            ###################################################################
            # Create the subject
            ###################################################################

            esubject_id = u"{0}_{1}".format(self.project_name, subject_id)
            subject_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is Subject, X identifier "
                     "'{0}'".format(esubject_id)),
                entity_name="Subject",
                identifier=subject_id,
                code_in_study=unicode(subject_id),
                gender=u"unknown",
                handedness=u"unknown")

            ###################################################################
            # Insert all the bio samples
            ###################################################################

            for sample in sample_item:

                ##############################################################
                # Create assessment
                ##############################################################

                assessment_struct = sample["Assessment"]
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
                # Insert the patient samples in the db
                ###############################################################

                for sample_struct, extfile_struct in sample["BioSamples"]:

                    # Create a bio sample
                    sample_entity, is_created = self._get_or_create_unique_entity(
                        rql=("Any X Where X is BioSample, X identifier "
                             "'{0}'".format(sample_struct["identifier"])),
                        entity_name="BioSample",
                        **sample_struct)
                    if is_created:
                        # > add relation with the assessment
                        self._set_unique_relation(
                            assessment_entity.eid, "uses",
                            sample_entity.eid, check_unicity=False)
                        self._set_unique_relation(sample_entity.eid,
                            "in_assessment", assessment_entity.eid,
                            check_unicity=False)
                        # > add relation with the study
                        self._set_unique_relation(sample_entity.eid, "related_study",
                            study_entity.eid, check_unicity=False)
                        # > add relation with the subject
                        self._set_unique_relation(sample_entity.eid, "concerns",
                            subject_entity.eid, check_unicity=False)

                        # Create the attached file if the 'filepath' is not
                        # 'unknown'
                        if extfile_struct["filepath"] != "unknown":

                            # Create the external file
                            file_entity, is_created = self._get_or_create_unique_entity(
                                rql="",
                                entity_name="ExternalFile",
                                check_unicity=False,
                                **extfile_struct)
                            # > add relation with the bio sample
                            self._set_unique_relation(sample_entity.eid,
                                "results_files", file_entity.eid,
                                check_unicity=False)
                            # > add relation with the assessment
                            self._set_unique_relation(file_entity.eid,
                                "in_assessment", assessment_entity.eid,
                                check_unicity=False)
