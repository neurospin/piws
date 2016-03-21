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


FREESURFER_QUESTIONNAIRES = [
    "LH.APARC.FOLDIND", "LH.APARC.AREA", "RH.APARC.CURVIND",
    "LH.APARC.THICKNESSSTD", "MEASURE:VOLUME", "LH.APARC.MEANCURV",
    "RH.APARC.THICKNESSSTD", "LH.APARC.VOLUME", "RH.APARC.MEANCURV",
    "RH.APARC.VOLUME", "LH.APARC.CURVIND", "LH.APARC.THICKNESS",
    "RH.APARC.FOLDIND", "RH.APARC.GAUSCURV", "RH.APARC.AREA",
    "LH.APARC.GAUSCURV", "RH.APARC.THICKNESS"]
FREESURFER = [
    "FREESURFER"]

RQL_T1 = ("Any SC Where S is Subject, S code_in_study '{0}', "
          "S scans SC, SC in_assessment A, A timepoint '{1}', "
          "SC label 'ADNI_MPRAGE'")


def freesurfer_stats(fsstatdirs, study_name, subject_age_map, savedir=None):
    """ Parse the freesurfer stats files and create a structure that
    fulfill the questionnaire importer synthax.

    Parameters
    ----------
    fsstatdirs: dict (mandatory)
        the location of the FreeSurfer stats directories with the timepoints
        as key.
    study_name: str (mandatory)
        the name of the study.
    subject_age_map: dict (mandatory)
        a map between subject ids as keys and subject ages as
        values with the time points as a fist key.
    savedir: str (optional, defafult None)
        if a valid directory is specified write the generated structure as
        a json file.

    Returns
    -------
    questionnaires: dict
        the generated structure with the stat files information.
    """
    # Go through timepoints
    questionnaires = {}
    for timepoint, statdir in fsstatdirs.items():

        # List all csv stat files
        files = glob.glob(os.path.join(statdir, "*.csv"))

        # Go through stat files
        for filepath in files:

            # Parse the stat file
            with open(filepath, "rb") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read())
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                rows = [row for row in reader]
                headers = rows[0]
                qname = headers[0]
                for row in rows[1:]:
                    subject = row[0]
                    age = subject_age_map[timepoint][subject]
                    qstruct = {
                        "Questionnaires": {
                            qname: {k: v for k, v in zip(headers[1:], row[1:])}
                        },
                        "Assessment": {
                            "age_of_subject": float(age),
                            "identifier": u"{0}_{1}_{2}_{3}".format(
                                    timepoint, qname.upper(),
                                    study_name.upper(), subject),
                            "timepoint": unicode(timepoint)
                        }
                    }
                    questionnaires.setdefault(subject, []).append(qstruct)

    # Save the generated structure
    if savedir is not None and os.path.isdir(savedir):
        date = datetime.date.today()
        save_file = os.path.join(savedir, "freesurfer_stats_{0}.json".format(
            date.isoformat()))
        with open(save_file, "w") as openfile:
            json.dump(questionnaires, openfile, indent=4, sort_keys=True)

    return questionnaires


def freesurfer(fsdirs, study_name, subject_pattern, tool_version,
               tool_parameters=None, savedir=None, rql_template=RQL_T1):
    """ Parse the freesurfer files and create a structure that
    fulfill the processing importer synthax.

    Parameters
    ----------
    fsdirs: dict (mandatory)
        the location of the FreeSurfer directory with the
        timepoints as key.
    study_name: str (mandatory)
        the name of the study.
    subject_pattern: str (mandatory)
        a pattern used to extract the subject name from the FreeSurfer
        directories names.
    tool_version: str (mandatory)
        the FreeSurfer tool version.
    tool_parameters: object (optional, defafult None)
        a structure describing the used options.
    savedir: str (optional, defafult None)
        if a valid directory is specified write the generated structure as
        a json file.
    rql_template: str (optional, default RQL_T1)
        the rql used to retrieve the t1 scan attached to a FreeSurfer
        processing.

    Returns
    -------
    processings: dict
        the generated structure with the FreeSurfeer files information.
    """
    # Go through timepoints
    processings = {}
    for timepoint, fsdir in fsdirs.items():

        # Create an assessment
        assessment_id = u"{0}_FREESURFER_{1}".format(
            timepoint, study_name.upper())
        assessment_struct = {
            "age_of_subject": 0,
            "identifier": assessment_id,
            "timepoint": unicode(timepoint)
        }

        # Go through subjects
        for subject in os.listdir(fsdir):

            # Get the subject code
            subjectfsdir = os.path.join(fsdir, subject)
            if len(re.findall(subject_pattern, subject)) != 1:
                print("Skip '{0}' since no valid subject can be extracted "
                      "with pattern '{1}'.".format(subjectfsdir,
                                                   subject_pattern))
                continue

            # Build a RQL to get the input T1
            rql_t1 = rql_template.format(subject, timepoint)

            # Create the processingrun: multiple filsets
            processingrun_id = u"{0}_{1}".format(assessment_id, subject)
            processingrun_struct = {
                "identifier": processingrun_id,
                "label": u"FreeSurfer",
                "tool": u"FreeSurfer",
                "version": unicode(tool_version),
                "parameters": unicode(json.dumps(tool_parameters))
            }
            fileset_structs = []
            extresources_structs = []

            # Go through FreeSurfer subdirectories
            for dirname in os.listdir(subjectfsdir):
                fsetpath = os.path.join(subjectfsdir, dirname)

                # If subdirectory not empty
                if os.path.isdir(fsetpath) and len(os.listdir(fsetpath)) > 0:

                    # Create a fileset
                    fset_id = u"{0}_{1}".format(processingrun_id, dirname)
                    fileset_structs.append({
                        "identifier": fset_id,
                        "name": u"FreeSurfer {0}".format(dirname.upper())})
                    extresources_structs.append([])

                    # Create the external files
                    for root, dirs, files in os.walk(fsetpath):
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            file_struct = {
                                "identifier": unicode(fpath),
                                "absolute_path": True,
                                "name": unicode(fname),
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
        save_file = os.path.join(savedir, "freesurfer_{0}.json".format(
            date.isoformat()))
        with open(save_file, "w") as openfile:
            json.dump(processings, openfile, indent=4, sort_keys=True)

    return processings


