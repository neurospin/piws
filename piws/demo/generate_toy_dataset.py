#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import os
import random
import numpy
import nibabel
import json


# Ask for a folder where we can put the demo dataset
dir_name = raw_input("Enter a valid folder [default: /tmp]:")
if not dir_name:
    dir_name = "/tmp"
if not os.path.isdir(dir_name):
    raise ValueError("'{0}' is not a valid folder.".format(dir_name))
dir_name = os.path.join(dir_name, "demo")
if os.path.isdir(dir_name):
    raise ValueError(
        "'{0}' already exists, please specify another root directory or "
        "remove manually this folder.".format(dir_name))
else:
    os.makedirs(dir_name)

# Ask for the number of subjects to insert
nb_of_subjects = raw_input("Enter the number of subject for the demo [10, 50]:")
nb_of_subjects = int(nb_of_subjects)
if nb_of_subjects < 10 or nb_of_subjects > 50:
    raise ValueError("The number of subjects must be in range [10, 50].")


# Global variables
SUBJECTS = ["subject{0}".format(cnt) for cnt in range(nb_of_subjects)]
MODALITITES = ["fmri", "t1"]
GENDERS = ["male", "female"]
HANDEDNESSES = ["right", "left", "ambidextrous"]
TIMEPOINTS = ["V0", "V1"]
QUESTIONNAIRES = {}
for subject in SUBJECTS:
    QUESTIONNAIRES[subject] = {}
    QUESTIONNAIRES[subject]["ID"] = {
        "gender": GENDERS[random.randint(0, len(GENDERS) - 1)],
        "handedness": HANDEDNESSES[random.randint(0, len(HANDEDNESSES) - 1)],
        "age": random.randint(20, 30)
    }
SNP_VALUES = [0, 1, 2]
PLATFORM = {
    "name": "Illumina",
    "measured_snps": ["rs272569", "rs400", "rs325623", "rs1053026"]
}


# Generate the demo scans questionnaires processings datasets for all
# timepoints
fsdirs = ["label", "mri", "scripts", "stats", "surf", "touch"]
for timepoint in TIMEPOINTS:

    # Go through all subjects
    for subject in SUBJECTS:

        # Create the scans and t1 associated freesurfer processings
        for cnt, modality in enumerate(MODALITITES):
            if random.randint(0, 4) != 2:

                # Generate scan
                modality_path = os.path.join(
                    dir_name, timepoint, subject, "images", modality)
                os.makedirs(modality_path)
                data = numpy.ones((2, 2, 2)) * (cnt + 1)
                affine = numpy.eye(4)
                affine[:3, :3] += numpy.eye(3)
                image = nibabel.Nifti1Image(data, affine)
                nibabel.save(
                    image, os.path.join(modality_path, modality + ".nii.gz"))
                if modality == "fmri":
                    fname = os.path.join(modality_path, "paradigm.json")
                    with open(fname, "w") as open_file:
                        json.dump(["My Paradigm"], open_file, indent=4)

                # Generate freesurfer like processing
                if modality == "t1":
                    subject_fsdir = os.path.join(
                        dir_name, timepoint, "processed", "freesurfer", subject)
                    for dirname in fsdirs:
                        datadir = os.path.join(subject_fsdir, dirname)
                        os.makedirs(datadir)
                        data = numpy.ones((2, 2, 2))
                        affine = numpy.eye(4)
                        affine[:3, :3] += numpy.eye(3)
                        image = nibabel.Nifti1Image(data, affine)
                        nibabel.save(
                            image, os.path.join(datadir, dirname + ".nii.gz"))

        # Create the questionnaires
        questionnaires_path = os.path.join(
            dir_name, timepoint, subject, "questionnaires")
        os.makedirs(questionnaires_path)
        for questionnaire_name, questionnaire in QUESTIONNAIRES[subject].items():
            fname = os.path.join(
                questionnaires_path, questionnaire_name + ".json")
            with open(fname, "w") as open_file:
                json.dump(questionnaire, open_file, indent=4)

        # Update the questionnaires with a Personal temporal question
        if random.randint(0, 4) != 2:
            questionnaire_name = "Personal"
            questionnaire = {
                "mood": random.randint(1, 10)
            }
            fname = os.path.join(
                questionnaires_path, questionnaire_name + ".json")
            with open(fname, "w") as open_file:
                json.dump(questionnaire, open_file, indent=4)


# Generate the demo genetic dataset
for timepoint in TIMEPOINTS:

    # Generate dataset
    genetics = {}
    for subject in SUBJECTS:
        genetics[subject] = {}
        for snp in PLATFORM["measured_snps"]:
            if random.randint(0, 6) != 2:
                genetics[subject][snp] = SNP_VALUES[
                    random.randint(0, len(SNP_VALUES) - 1)]
            else:
                genetics[subject][snp] = -9

    genetic_path = os.path.join(dir_name, timepoint, "genetic")
    os.makedirs(genetic_path)
    fname = os.path.join(genetic_path, "genetic" + ".json")
    with open(fname, "w") as open_file:
        json.dump(genetics, open_file, indent=4)
