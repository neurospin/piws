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


CONNECTOMIST = [
    "CONNECTOMIST"]

RQL_MORPHOLOGIST = (
    "Any SC Where S is Subject, S code_in_study '{0}', "
    "S subject_processing_runs P, P in_assessment A, A timepoint '{1}', "
    "P label 'MORPHOLOGIST'")
RQL_DWI = (
    "Any SC ORDERBY T ASC Where S is Subject, S code_in_study '{0}', "
    "S subject_scans SC, SC in_assessment A, A timepoint '{1}', "
    "SC label REGEXP '^DWI*', SC type T")


def connectomist(condirs, study_name, subject_pattern, tool_version,
                 tool_parameters=None, savedir=None,
                 rql_template_morphologist=RQL_MORPHOLOGIST,
                 rql_template_dwi=RQL_DWI):
    """ Parse the connectomist files and create a structure that
    fulfill the processing importer synthax.

    Parameters
    ----------
    condirs: dict (mandatory)
        the location of the Morphologist directory with the
        timepoints as key.
    study_name: str (mandatory)
        the name of the study.
    subject_pattern: str (mandatory)
        a pattern used to extract the subject name from the Connectomist
        directories names.
    tool_version: str (mandatory)
        the Connectomist tool version.
    tool_parameters: object (optional, defafult None)
        a structure describing the used options.
    savedir: str (optional, defafult None)
        if a valid directory is specified write the generated structure as
        a json file.
    rql_template_morphologist: str (optional, default RQL_MORPHOLOGIST)
        the rql used to retrieve the Morphologist processing.
    rql_template_dwi: str str (optional, default RQL_DWI)
        the rql used to retrieve the diffusion scans.

    Returns
    -------
    processings: dict
        the generated structure with the Morphologist files information.
    """
    # Go through timepoints
    processings = {}
    for timepoint, condir in condirs.items():

        # Create an assessment
        assessment_id = u"{0}_CONNECTOMIST_{1}".format(
            timepoint, study_name.upper())
        assessment_struct = {
            "age_of_subject": 0,
            "identifier": assessment_id,
            "timepoint": unicode(timepoint)
        }

        # Go through subjects
        for subject in os.listdir(condir):

            # Get the subject code
            subjectcondir = os.path.join(condir, subject)
            if len(re.findall(subject_pattern, subject)) != 1:
                print("Skip '{0}' since no valid subject can be extracted "
                      "with pattern '{1}'.".format(subjectcondir,
                                                   subject_pattern))
                continue

            # Build a RQL to get the input T1
            rql_morphologist = rql_template_morphologist.format(subject, timepoint)
            rql_dwi = rql_template_dwi.format(subject, timepoint)

            # Create the processingrun: multiple filsets
            processingrun_id = u"{0}_{1}".format(assessment_id, subject)
            processingrun_struct = {
                "identifier": processingrun_id,
                "label": u"Connectomist",
                "tool": u"Connectomist",
                "version": unicode(tool_version),
                "parameters": unicode(json.dumps(tool_parameters))
            }
            fileset_structs = []
            extresources_structs = []

            # Go through Connectomist subdirectories
            dataset = {}
            dtidir = os.path.join(subjectcondir, "dtifit")
            if os.path.isdir(dtidir):
                dataset["SCALARS"] = glob.glob(
                    os.path.join(dtidir, "*.nii.gz"))
            preprocdir = os.path.join(subjectcondir, "preproc")
            if os.path.isdir(preprocdir):
                dataset["CORRECTED DWI"] = [
                    os.path.join(preprocdir, "dwi.nii.gz"),
                    os.path.join(preprocdir, "dwi.bvec"),
                    os.path.join(preprocdir, "dwi.bval")]
                dataset["QCFAST"] = glob.glob(
                    os.path.join(preprocdir, "*.pdf"))
            tractdir = os.path.join(subjectcondir, "tract")
            if os.path.isdir(tractdir):
                dataset["TRACTOGRAPHY MASK"] = os.path.join(
                    tractdir, "mask.nii.gz")
                scalars = glob.glob(os.path.join(tractdir, "*_*.nii.gz"))
                if "SCALARS" in dataset:
                    dataset["SCALARS"].extend(scalars)
                else:
                    dataset["SCALARS"] = scalars
                bundledir = os.path.join(tractdir, "bundles")
                if os.path.isdir(bundledir):
                    for region_name in os.listdir(bundledir):
                        dataset[region_name.upper()] = glob.glob(
                            os.path.join(bundledir, region_name, "*.trk"))

            # Get all the files associated with each file set
            for fset_name, files in dataset.items():

                # Filter files
                files = [path for path in files if os.path.isfile(path)]

                # Create a fileset
                fset_name = "Connectomist {0}".format(fset_name)
                fset_id = u"{0}_{1}".format(processingrun_id, fset_name)
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
                    "Inputs": [rql_morphologist, rql_dwi],
                    "ExternalResources": extresources_structs,
                    "FileSets": fileset_structs,
                    "ProcessingRun": processingrun_struct
                }]
            }
            processings.setdefault(subject, []).append(processing_struct)

    # Save the generated structure
    if savedir is not None and os.path.isdir(savedir):
        date = datetime.date.today()
        save_file = os.path.join(savedir, "connectomist_{0}.json".format(
            date.isoformat()))
        with open(save_file, "w") as openfile:
            json.dump(processings, openfile, indent=4, sort_keys=True)

    return processings
