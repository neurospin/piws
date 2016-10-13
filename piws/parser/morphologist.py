##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import os
import re
import csv
import copy
import glob
import datetime
import json


MORPHOLOGIST = [
    "MORPHOLOGIST"]

RQL_T1 = ("Any SC Where S is Subject, S code_in_study '{0}', "
          "S subject_scans SC, SC in_assessment A, A timepoint '{1}', "
          "SC label 'ADNI_MPRAGE'")

MPDIRS = {
    "Morphologist ACQUISITION": (
        os.path.join("t1mri", "default_acquisition"),
        False),
    "Morphologist ANALYSIS": (
        os.path.join("t1mri", "default_acquisition", "default_analysis"),
        False),
    "Morphologist FOLDS": (
        os.path.join("t1mri", "default_acquisition", "default_analysis",
                     "folds"),
        True),
    "Morphologist SEGMENTATION": (
        os.path.join("t1mri", "default_acquisition", "default_analysis",
                     "segmentation"),
        True),
    "Morphologist REGISTRATION": (
        os.path.join("t1mri", "default_acquisition", "registration"),
        True),
    "Morphologist TMP": (
        os.path.join("t1mri", "default_acquisition", "tmp"),
        True)
}


def morphologist(mpdirs, study_name, subject_pattern, tool_version,
                 tool_parameters=None, savedir=None, rql_template=RQL_T1):
    """ Parse the morphologist files and create a structure that
    fulfill the processing importer synthax.

    Parameters
    ----------
    mpdirs: dict (mandatory)
        the location of the Morphologist directory with the
        timepoints as key.
    study_name: str (mandatory)
        the name of the study.
    subject_pattern: str (mandatory)
        a pattern used to extract the subject name from the Morphologist
        directories names.
    tool_version: str (mandatory)
        the Morphologist tool version.
    tool_parameters: object (optional, defafult None)
        a structure describing the used options.
    savedir: str (optional, defafult None)
        if a valid directory is specified write the generated structure as
        a json file.
    rql_template: str (optional, default RQL_T1)
        the rql used to retrieve the t1 scan attached to a Morphologist
        processing.

    Returns
    -------
    processings: dict
        the generated structure with the Morphologist files information.
    """
    # Go through timepoints
    processings = {}
    for timepoint, mpdir in mpdirs.items():

        # Create an assessment
        assessment_id = u"{0}_MORPHOLOGIST_{1}".format(
            timepoint, study_name.upper())
        assessment_struct = {
            "age_of_subject": 0,
            "identifier": assessment_id,
            "timepoint": unicode(timepoint)
        }

        # Go through subjects
        for subject in os.listdir(mpdir):

            # Get the subject code
            subjectmpdir = os.path.join(mpdir, subject)
            if len(re.findall(subject_pattern, subject)) != 1:
                print("Skip '{0}' since no valid subject can be extracted "
                      "with pattern '{1}'.".format(subjectmpdir,
                                                   subject_pattern))
                continue

            # Build a RQL to get the input T1
            rql_t1 = rql_template.format(subject, timepoint)

            # Create the processingrun: multiple filsets
            processingrun_id = u"{0}_{1}".format(assessment_id, subject)
            processingrun_struct = {
                "identifier": processingrun_id,
                "label": u"Morphologist",
                "tool": u"Morphologist",
                "version": unicode(tool_version),
                "parameters": unicode(json.dumps(tool_parameters))
            }
            fileset_structs = []
            extresources_structs = []

            # Go through Morphologist subdirectories
            for fset_name, (rpath, walk) in MPDIRS.items():

                # Get all the files associated with this file set
                fsetpath = os.path.join(subjectmpdir, rpath)
                if not os.path.isdir(fsetpath):
                    continue
                if walk:
                    files = []
                    for root, dirs, fnames in os.walk(fsetpath):
                        files.extend([os.path.join(root, fname)
                                      for fname in fnames])
                else:
                    files = [os.path.join(fsetpath, bname)
                             for bname in os.listdir(fsetpath)
                             if os.path.isfile(os.path.join(fsetpath, bname))]
                if len(files) == 0:
                    continue

                # Create a fileset
                fset_id = u"{0}_{1}".format(processingrun_id,
                                            rpath.replace(os.sep, "_"))
                fileset_structs.append({
                    "identifier": fset_id,
                    "name": unicode(fset_name)})
                extresources_structs.append([])

                # Create the external files
                for fpath in files:
                    file_struct = {
                        "identifier": unicode(fpath),
                        "absolute_path": True,
                        "name": unicode(os.path.basename(fpath)),
                        "filepath": unicode(fpath)
                    }
                    extresources_structs[-1].append(file_struct)

            # Create the final structure
            processing_struct = {
                "Assessment": copy.deepcopy(assessment_struct),
                "Processings": [{
                    "Inputs": [rql_t1],
                    "ExternalResources": extresources_structs,
                    "FileSets": fileset_structs,
                    "ProcessingRun": processingrun_struct
                }]
            }
            processings.setdefault(subject, []).append(processing_struct)

    # Save the generated structure
    if savedir is not None and os.path.isdir(savedir):
        date = datetime.date.today()
        save_file = os.path.join(savedir, "morphologist_{0}.json".format(
            date.isoformat()))
        with open(save_file, "w") as openfile:
            json.dump(processings, openfile, indent=4, sort_keys=True)

    return processings
