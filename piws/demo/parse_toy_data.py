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
import logging
import glob
import nibabel
import json


# Global parameters
raw_datatypes = {
    "t1": "MRIData",
    "fmri": "FMRIData"
}


def subject_parser(root, project_name):
    """ Method to get the subject elements.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.
    project_name: str (mandatory)
        the name of the project.

    Returns
    -------
    unique_subjects: dict of dict
        the first dictionnaries contains the subject name as keys and then
        the entity description.
    """
    # Initialize the output structure
    unique_subjects = {}

    # Get all the subjects
    subjects = set([
        os.path.basename(d) for d in glob.glob(os.path.join(root, "*", "*"))
        if os.path.basename(d) != "genetic"])

    # Go through each subject
    for subject in subjects:

        id_path = glob.glob(os.path.join(root, "*", subject, "questionnaires", 
                                         "ID.json"))[0]
        with open(id_path) as open_file:
            subject_info = json.load(open_file)
            unique_subjects[subject] = {
                "identifier": u"{0}_{1}".format(project_name, subject),
                "code_in_study": unicode(subject),
                "gender": unicode(subject_info["gender"]),
                "handedness": unicode(subject_info["handedness"])
            }

    return unique_subjects
    

def scan_parser(root, project_name):  
    """ Method to get the nifti scan elements.

    Special modalities:
        * "fmri": try to find the assoiated paradigm,
                  raise an Exception otherwise.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.
    project_name: str (mandatory)
        the name of the project.

    Returns
    -------
    scans: dict of list of dict
        the scan description: the first dictionary contains the subject
        name as keys and then a list of dictionaries with four keys (Scans -
        (Scan - TypeData - FileSet - ExternalResource - ScoreValue) -
        Assessment) that contains the entities parameter decriptions.
    """
    # Get all the timepoints
    timepoints = os.listdir(root)

    # Get all the subjects
    subjects = set([
        os.path.basename(d) for d in glob.glob(os.path.join(root, "*", "*"))
        if os.path.basename(d) != "genetic"])

    # Initialize the output structure
    scans = dict((subject_name, []) for subject_name in subjects)

    # Go through each subject
    for subject in subjects:

        # Go through each timepoint
        for timepoint in timepoints:

            # Get all the scan data
            dscans = {}
            for item in glob.glob(os.path.join(root, timepoint, subject,
                                               "images", "*", "*")):
                if os.path.isfile(item):
                    dscans.setdefault(item.split(os.sep)[-2], []).append(item) 

            # If we have some scans
            if len(dscans) > 0:

                # Create an assessment
                assessment_id = u"{0}_{1}_{2}".format(project_name, timepoint,
                                                      subject)
                id_path = os.path.join(
                    root, timepoint, subject, "questionnaires", "ID.json")
                with open(id_path) as open_file:
                    age_of_subject = json.load(open_file)["age"]
                assessment_struct = {
                    "identifier": assessment_id,
                    "age_of_subject": age_of_subject,
                    "timepoint": unicode(timepoint)
                }

                # Build the subject scans structure for this timepoint
                subj_scans = {
                    "Scans": [],
                    "Assessment": assessment_struct
                }

                # Try all the modalities
                for mod_name, mod_type in raw_datatypes.iteritems():

                    # Check that this subject has a scan match
                    if mod_name in dscans:

                        # Create a scan tag
                        scan_id = assessment_id + u"_{0}".format(mod_name)

                        # Load the nifti image to get metainformation
                        image_path = [item for item in dscans[mod_name]
                                      if item.endswith(".nii.gz")][0]
                        image = nibabel.load(image_path)
                        shape = image.shape
                        spacing = image.get_header()["pixdim"][1:]

                        # Create a structure with the image metainformation
                        scantype_struct = {
                            "type": unicode(mod_type),
                            "shape_x": int(shape[0]),
                            "shape_y": int(shape[1]),
                            "shape_z": int(shape[2]),
                            "voxel_res_x": float(spacing[0]),
                            "voxel_res_y": float(spacing[1]),
                            "voxel_res_z": float(spacing[2]),
                            "fov_x": 0,
                            "fov_y": 0,
                            "tr": 2.5,
                            "te": 0,
                            "field": "3T"
                        }

                        # Create the scan entity structure
                        scan_struct = {
                            "identifier": scan_id,
                            "type": unicode(mod_type),
                            "label": unicode(mod_name.upper()),
                            "format": u"Nifti"
                        }

                        # Create the file set entity structure
                        fset_struct = {
                            "identifier": scan_id,
                            "name": unicode(mod_name.upper())
                        }

                        # Create the external files
                        extfiles_item = []
                        for cnt, fname in enumerate(dscans[mod_name]):

                            # Create the external file structure
                            extfiles_item.append({
                                "identifier": scan_id + u"_{0}".format(cnt + 1),
                                "name": unicode(
                                    os.path.basename(fname).split(".")[0]),
                                "absolute_path": True,
                                "filepath": unicode(fname)
                            })                          
                            
                        # Update the subject scan structure
                        subj_scans["Scans"].append( {
                            "Scan": scan_struct,
                            "TypeData": scantype_struct,
                            "FileSet": fset_struct,
                            "ExternalResources": extfiles_item })

                scans[subject].append(subj_scans)

    return scans

def questionnaire_parser(root, project_name):
    """ Method to get the questionnaires.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.
    project_name: str (mandatory)
        the name of the project.

    Returns
    -------
    questionnaires: dict of dict
        the first dictionnaries contains the subject name as keys and then
        the entity description.
    """
    # Get all the timepoints
    timepoints = os.listdir(root)

    # Get all the subjects
    subjects = set([
        os.path.basename(d) for d in glob.glob(os.path.join(root, "*", "*"))
        if os.path.basename(d) != "genetic"])

    # Initialize the output structure
    questionnaires = dict((subject_name, []) for subject_name in subjects)

    # Go through each subject
    for subject in subjects:

        # Go through each timepoint
        for timepoint in timepoints:

            # Get all the questionnaires data
            lquestionnaires = glob.glob(
                os.path.join(root, timepoint, subject, "questionnaires", "*.json"))

            # If we have some questionnaires
            if len(lquestionnaires) > 0:

                # Create an assessment
                assessment_id = u"{0}_{1}_{2}".format(project_name, timepoint,
                                                      subject)
                id_path = os.path.join(
                    root, timepoint, subject, "questionnaires", "ID.json")
                with open(id_path) as open_file:
                    age_of_subject = json.load(open_file)["age"]
                assessment_struct = {
                    "identifier": assessment_id,
                    "age_of_subject": age_of_subject,
                    "timepoint": unicode(timepoint)
                }

                # Build the subject questionnaires structure for this timepoint
                subj_questionnaires = {
                    "Questionnaires": {},
                    "Assessment": assessment_struct
                }

                # Go through all the current questionnaires
                for questionnaire_fname in lquestionnaires:

                    # Define the questionnaire name
                    qname = os.path.splitext(
                        os.path.basename(questionnaire_fname))[0]
                
                    # Load the questionnaire
                    with open(questionnaire_fname) as open_file:
                        data = json.load(open_file)  

                    subj_questionnaires["Questionnaires"][qname] = data
            
                questionnaires[subject].append(subj_questionnaires)               

    return questionnaires


def genetic_parser(root, project_name):  
    """ Method to get the genetic measure elements.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.
    project_name: str (mandatory)
        the name of the project.

    Returns
    -------
    genetics: dict of list of dict
        the genetic measure description: the first dictionary contains the
        timepoint as keys and then a list of dictionaries with two keys
        (GenomicMeasures - Assessment) that contains the entities parameter
        decriptions.
    """
    # Get all the timepoints
    timepoints = os.listdir(root)

    # Initialize the output structure
    genetics = dict((t, []) for t in timepoints)

    # Go through each timepoint
    for timepoint in timepoints:

        # Get all the genetic data
        dgenetics = []
        for item in glob.glob(os.path.join(root, timepoint, "genetic", "*.json")):
            if os.path.isfile(item):
                dgenetics.append(item) 

        # If we have some data
        if len(dgenetics) > 0:

            # Create an assessment
            assessment_id = u"{0}_{1}_{2}".format(project_name, timepoint,
                                                  "genetic")
            assessment_struct = {
                "identifier": assessment_id,
                "timepoint": unicode(timepoint)
            }

            # Build the genetic structure for this timepoint
            genetic_struct = {
                "GenomicMeasures": [],
                "Assessment": assessment_struct
            }

            # Go through all genetic resource for this timepoint
            for genetic_path in dgenetics:

                # Create the scan entity structure
                gmeasure_struct = {
                    "identifier": assessment_id + "_Illumina_raw_json",
                    "label": "Illumina_raw_json",
                    "type": u"raw",
                    "format": u"json"
                }

                # Build the platform associated to this measure
                with open(genetic_path) as open_file:
                    json_struct = json.load(open_file)
                    related_subjects = json_struct.keys()
                    related_snps = json_struct[related_subjects[0]].keys()
                platform_struct = {
                    "name": u"Illumina",
                    "related_subjects": related_subjects,
                    "related_snps": related_snps
                }

                # Create the file set entity structure
                fset_struct = {
                    "identifier": assessment_id,
                    "name": u"raw genetic measure"
                }

                # Create the external file
                extfiles_item = [{
                    "identifier": assessment_id + u"_{0}".format(1),
                    "name": unicode(
                        os.path.basename(genetic_path).split(".")[0]),
                    "absolute_path": True,
                    "filepath": unicode(genetic_path)
                }]
                       
                    
                # Update the subject scan structure
                genetic_struct["GenomicMeasures"].append({
                    "GenomicMeasure": gmeasure_struct,
                    "GenomicPlatform": platform_struct,
                    "FileSet": fset_struct,
                    "ExternalResources": extfiles_item
                })

        genetics[timepoint].append(genetic_struct)

    return genetics



if __name__ == "__main__":
    scans = scan_parser("/tmp/demo", "toy")
    print scans["subject1"]
    subjects = subject_parser("/tmp/demo", "toy")
    print subjects["subject1"]
    questionnaires = questionnaire_parser("/tmp/demo", "toy")
    print questionnaires["subject1"]
    genetics = genetic_parser("/tmp/demo", "toy")
    print genetics["V1"]
