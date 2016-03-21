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


class Genetics(Base):
    """ This class enables us to load the genetic data to CW.
    """
    # Define the relations involved
    relations = (
        Base.fileset_relations + Base.assessment_relations + [
            ("GenomicMeasure", "study", "Study"),
            ("Study", "study_genomic_measures", "GenomicMeasure"),
            ("GenomicMeasure", "subjects", "Subject"),
            ("Subject", "subject_genomic_measures", "GenomicMeasure"),
            ("Assessment", "genomic_measures", "GenomicMeasure"),
            ("GenomicMeasure", "in_assessment", "Assessment"),
            ("GenomicMeasure", "genomic_platform", "GenomicPlatform"),
            ("GenomicPlatform", "genomic_platform_genomic_measures", "GenomicMeasure"),
            ("GenomicPlatform", "snps", "Snp")]
    )
    relations[0][0] = "GenomicMeasure"

    def __init__(self, session, project_name, center_name, genetics,
                 can_read=True, can_update=True, data_filepath=None,
                 use_store=True, piws_security_model=True):
        """ Initialize the Genetics class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        project_name: str (mandatory)
            the name of the project
        center_name: str (mandatory)
            the center name
        genetics: dict of list of dict (mandatory)
            the genetic measure description: the first dictionary contains the
            timepoint as keys and then a list of dictionaries with two keys
            (GenomicMeasures - Assessment) that contains the entities parameter
            descriptions.
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
        Here is an example of the definition of the 'genetics' parameter:

        ::

            genetics = {
                "V1": [{
                    "GenomicMeasures": [{
                        "GenomicPlatform": {
                            "related_snps": [
                                u"rs325623", u"rs272569", u"rs400",
                                u"rs1053026"
                            ],
                            "name": u"Illumina",
                            "related_subjects": [
                                u"subject0", u"subject1", u"subject2",
                                u"subject3", u"subject4", u"subject5",
                                u"subject6", u"subject7", u"subject8",
                                u"subject9"
                            ]
                        },
                        "GenomicMeasure": {
                            "identifier": u"toy_V1_genetic_Illumina_raw_json",
                            "label": u"toy_V1_genetic_Illumina_raw_json",
                            "type": u"raw",
                            "format": u"json"
                        },
                        "FileSet": {
                            "identifier": u"toy_V1_genetic",
                            "name": u"raw genetic measure"
                        },
                        "ExternalResources": [{
                            "absolute_path": True,
                            "identifier": u"toy_V1_genetic_1",
                            "name": u"genetic",
                            "filepath": u"/tmp/demo/V1/genetic/genetic.json"
                        }]
                    }],
                    "Assessment": {
                        "identifier": u"toy_V1_genetic",
                        "timepoint": u"V1"}
                }]
            }

        """
        # Inheritance
        super(Genetics, self).__init__(session, use_store,
                                       piws_security_model)

        # Parse the file system
        self.genetics = genetics
        self.data_filepath = data_filepath or ""
        self.project_name = project_name
        self.center_name = center_name
        self.can_read = can_read
        self.can_update = can_update

        # Speed up parameters
        self.inserted_assessments = {}
        self.inserted_measures = {}
        self.inserted_platforms = {}
        self.inserted_snps = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import some genetic data in the db.

        .. note::

            Below the schema used to insert the genetic data:

            |

            .. image:: ../schemas/genetics.png
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
        subjects_eid_map = dict((row[1], row[0]) for row in rset
                                if row[2].startswith(self.project_name))

        #######################################################################
        # Get all the groups
        #######################################################################

        rset = self.session.execute(
            "Any G, N Where G is CWGroup, G name N")
        groups = dict((row[1], row[0]) for row in rset)

        #######################################################################
        # Insert each genetic measure
        #######################################################################

        # Add the data
        for timepoint, timepoint_genetics in self.genetics.iteritems():

            # Information to create a progress bar
            nb_of_measures = float(len(timepoint_genetics))
            cnt_measure = 1.

            # Select a platform
            for tgenetic_item in timepoint_genetics:

                # Print a progress bar
                self._progress_bar(
                    cnt_measure / nb_of_measures,
                    title="{0}(genetics)".format(
                        tgenetic_item["Assessment"]["identifier"]),
                    bar_length=40)
                cnt_measure += 1

                ###############################################################
                # Check all the subjects exist in the database
                ###############################################################

                timepoint_subjects = set()
                for tgenetic_measure in tgenetic_item["GenomicMeasures"]:
                    platform_struct = tgenetic_measure["GenomicPlatform"]
                    related_subjects = platform_struct["related_subjects"]
                    for subject_id in related_subjects:
                        if subject_id not in subjects_eid_map:
                            raise ValueError(
                                "The subject '{0}' in not known by the "
                                "database.".format(subject_id))
                        timepoint_subjects.add(subjects_eid_map[subject_id])
                timepoint_subjects = list(timepoint_subjects)

                ###############################################################
                # Create the assessment
                ###############################################################

                # Get the assessment identifier
                assessment_struct = tgenetic_item["Assessment"]
                assessment_id = assessment_struct["identifier"]

                # Check if this item has already been inserted
                if assessment_id in self.inserted_assessments:
                    assessment_eid = self.inserted_assessments[assessment_id]

                # Create the assessment
                else:
                    assessment_eid = self._create_assessment(
                        assessment_struct, timepoint_subjects, study_eid,
                        center_eid, groups)
                    self.inserted_assessments[assessment_id] = assessment_eid

                ###############################################################
                # Insert all the genetic measure at this timepoint
                ###############################################################

                for tgenetic_measure in tgenetic_item["GenomicMeasures"]:

                    platform_struct = tgenetic_measure["GenomicPlatform"]
                    related_subjects = platform_struct.pop("related_subjects")

                    ############################################################
                    # Create the genomic platform
                    ############################################################

                    # Check if this item has already been inserted
                    platform_name = platform_struct["name"]
                    if platform_name in self.inserted_platforms:
                        platform_eid = self.inserted_platforms[platform_name]

                    # Create the platform
                    else:
                        related_snps = platform_struct.pop("related_snps")
                        platform_eid = self._create_platform(
                            platform_struct, related_snps)
                        self.inserted_platforms[platform_name] = platform_eid

                    ############################################################
                    # Create the genomic measure
                    ############################################################

                    measure_struct = tgenetic_measure["GenomicMeasure"]
                    fset_struct = tgenetic_measure.get("FileSet", None)
                    extfiles = tgenetic_measure.get("ExternalResources", None)
                    measure_eid = self._create_measure(
                        measure_struct, fset_struct, extfiles, related_subjects,
                        subjects_eid_map, study_eid, assessment_eid, platform_eid)

        print  # new line after last progress bar update

    def _create_measure(self, measure_struct, fset_struct, extfiles,
                        related_subjects, subjects_eid_map, study_eid,
                        assessment_eid, platform_eid):
        """ Create a genomic measure and its associated relations.
        """
        # Create the measure
        measure_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is GenomicMeasure, X identifier "
                 "'{0}'".format(measure_struct["identifier"])),
            check_unicity=True,
            entity_name="GenomicMeasure",
            **measure_struct)
        measure_eid = measure_entity.eid

        # If we just create the measure, add relations
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                measure_eid, "study", study_eid, check_unicity=False)
            self._set_unique_relation(
                study_eid, "study_genomic_measures", measure_eid,
                check_unicity=False)
            # > add relation with the subjects
            for subject_id in related_subjects:
                self._set_unique_relation(
                    measure_eid, "subjects", subjects_eid_map[subject_id],
                    check_unicity=False)
                self._set_unique_relation(
                    subjects_eid_map[subject_id], "subject_genomic_measures",
                    measure_eid, check_unicity=False)
            # > add relation with the assessment
            self._set_unique_relation(
                assessment_eid, "genomic_measures", measure_eid,
                check_unicity=False)
            self._set_unique_relation(
                measure_eid, "in_assessment", assessment_eid,
                check_unicity=False, subjtype="GenomicMeasure")
            # > add relation with the platform
            self._set_unique_relation(
                measure_eid, "genomic_platform", platform_eid,
                check_unicity=False)
            self._set_unique_relation(
                platform_eid, "genomic_platform_genomic_measures", measure_eid,
                check_unicity=False)

            # Add the file set attached to a genomic measure
            if fset_struct:
                self._import_file_set(fset_struct, extfiles, measure_eid,
                                      assessment_eid)

        return measure_eid

    def _create_platform(self, platform_struct, related_snps):
        """ Create a genomic platform and its associated relations.
        """
        # Create the platform
        platform_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is GenomicPlatform, X name '{0}'".format(
                                                    platform_struct["name"])),
            check_unicity=True,
            entity_name="GenomicPlatform",
            **platform_struct)
        platform_eid = platform_entity.eid

        # If we just create the platform, relate the platform with the measured
        # snps
        if is_created:
            # > add relation with the snps
            nb_of_snps = float(len(related_snps))
            for cnt_snps, rs_id in enumerate(related_snps):

                # Print a progress bar
                if (cnt_snps % 100) == 0:
                    self._progress_bar(
                        cnt_snps / nb_of_snps,
                        title="{0}:{1}/{2}(snps)".format(
                            rs_id, cnt_snps, nb_of_snps),
                        bar_length=40)

                # Check if this item has already been inserted
                if rs_id in self.inserted_snps:
                    snp_eid = self.inserted_snps[rs_id]

                # Create the Snp
                else:
                    snp_entity, is_created = self._get_or_create_unique_entity(
                        rql=("Any X Where X is Snp, S rs_id '{0}'".format(
                            rs_id)),
                        check_unicity=True,
                        entity_name="Snp",
                        rs_id=unicode(rs_id),
                        position=-9)
                    snp_eid = snp_entity.eid
                    self.inserted_snps[rs_id] = snp_eid
                self._set_unique_relation(
                    platform_eid, "snps", snp_eid, check_unicity=False)

        return platform_eid
