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
import glob
import json
import numpy


def metagen_parser(root):
    """ Method to get the bioresource data elements.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.

    Returns
    -------
    metadata: dict of dict
        the first dictionary contains the chromosme name as keys and then
        the associated 'genes', 'snps' and 'cpgs' JSON files.
    """
    # Initialize the output structure
    metadata = {}

    # Get all the datasets
    for chr_name in range(1, 23) + ["X", "Y"]:
        metadata[chr_name] = {
            "genes": os.path.join(root,
                                  "genes_of_chr{0}.json".format(chr_name)),
            "snps": os.path.join(root,
                                 "snps_of_chr{0}.json".format(chr_name)),
            "cpgs": os.path.join(root,
                                 "cpgs_of_chr{0}.json".format(chr_name))}
        for key, path in metadata[chr_name].items():
            with open(path, "rt") as open_file:
                metadata[chr_name][key] = json.load(open_file)

    return metadata


def genetic_parser(root, project_name, timepoint):
    """ Method to get the genetic plink measure elements.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset: expect bim, bam, bed files
    project_name: str (mandatory)
        the name of the project.
    timepoint: str (mandatory)
        the dataset acquisition timepoint.

    Returns
    -------
    genetics: dict of list of dict
        the genetic measure description: the first dictionary contains the
        timepoint as keys and then a list of dictionaries with two keys
        (GenomicMeasures - Assessment) that contains the entities parameter
        decriptions.
    """
    # Initialize the output structure
    genetics = {timepoint: []}

    # Get all the genetic data
    dataset = {}
    for ext in [".bim", ".fam", ".bed"]:
        dataset[ext] = root + ext
        if not os.path.isfile(dataset[ext]):
            raise valueError("{0} is not a file.".format(dataset[ext]))

    # Create an assessment
    assessment_id = u"{0}_{1}_{2}".format(project_name, timepoint, "plink")
    assessment_struct = {
        "identifier": assessment_id,
        "timepoint": unicode(timepoint)
    }

    # Build the genetic structure for this timepoint
    genetic_struct = {
        "GenomicMeasures": [],
        "Assessment": assessment_struct
    }

    # Create the genomic measure entity structure
    gmeasure_struct = {
        "identifier": assessment_id + u"_Chip1",
        "label": u"Chip1",
        "type": u"raw",
        "format": u"plink"
    }

    # Build the platform associated to this measure
    related_snps = numpy.loadtxt(dataset[".bim"], dtype=str)[:, 1]
    related_subjects = numpy.loadtxt(dataset[".fam"], dtype=str)[:, 1]
    platform_struct = {
        "name": u"Chip1",
        "related_subjects": related_subjects,
        "related_snps": related_snps
    }

    # Create the file set entity structure
    fset_struct = {
        "identifier": assessment_id,
        "name": u"plink genetic measure"
    }

    # Create the external file
    extfiles_item = []
    for ext in [".bim", ".fam", ".bed"]:
        path = dataset[ext]
        extfiles_item.append({
            "identifier": assessment_id + u"_{0}".format(ext[1:]),
            "name": unicode(os.path.basename(root)),
            "absolute_path": True,
            "filepath": unicode(path)
        })

    # Update the subject scan structure
    genetic_struct["GenomicMeasures"].append({
        "GenomicMeasure": gmeasure_struct,
        "GenomicPlatform": platform_struct,
        "FileSet": fset_struct,
        "ExternalResources": extfiles_item
    })

    genetics[timepoint].append(genetic_struct)

    return genetics


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
    subjects = set(numpy.loadtxt(root + ".fam", dtype=str)[:, 1])

    # Go through each subject
    for subject in subjects:

        unique_subjects[subject] = {
            "identifier": u"{0}_{1}".format(project_name, subject),
            "code_in_study": unicode(subject),
            "gender": unicode("unknown"),
            "handedness": unicode("unknown")}

    return unique_subjects

