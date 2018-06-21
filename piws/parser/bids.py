##########################################################################
# NSAp - Copyright (C) CEA, 2018
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System imports
from __future__ import print_function
from collections import defaultdict
from collections import OrderedDict
import os
import csv
import json
import glob
import hashlib
import datetime
import progressbar

# Third party import
import nibabel


# Global parameters
DEFAULT_CENTER = "AnonCenter"
DEFAULT_TIMEPOINT = "TimeLess"
ALLOWED_MODALITY = ("T1w", "T2w", "FLAIR", "dwi", "asl", "GRE", "PD")


def md5_sum(string):
    """ Create a md5 sum of a string.

    Parameters
    ----------
    string: str
        a string to hash.

    Returns
    -------
    out: str
        the input hashed string.
    """
    m = hashlib.md5()
    m.update(string.encode("utf-8"))
    return m.hexdigest()


def save_parsing(parsing_struct, outputdir, study, dtype):
    """ Save the parsing result to file.

    Parameters
    ----------
    parsing_struct: dict
        The parser output structure.
    outputdir: str
        The output directory.
    study: str
        The study name.
    dtype: str
        The nature of the parsed data (e.g. 'scans').
    """
    date = datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
    outfname = os.path.join(
        outputdir, "{0}_{1}_{2}.json".format(dtype, study, date))
    with open(outfname, "wt") as open_file:
        json.dump(parsing_struct, open_file, indent=4, sort_keys=True)
    print("[{0}] save parsing: {1}".format(dtype, outfname))


def subjects_parser(root, study, outdir):
    """ Parse the subjects in a BIDS dataset.

    This parsing is based on the participants tsv file.

    Parameters
    ----------
    root: str
        The BIDS organized directory to be parsed (the one conataining the
        'participants.tsv' file).
    study: str
        The study name.
    outdir: str
        The output directory.

    Returns
    -------
    subjects: dict
        The PIWS-like structure containg the parsed data.
    """
    # Welcome
    print("Starting subjects parsing...")

    # Parameters
    subjects = defaultdict(
        lambda: defaultdict(dict))
    participants_file = os.path.join(root, "participants.tsv")

    # Parse the paticipants tsv file
    with open(participants_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            subject = row["participant_id"].replace("sub-", "")
            center = row.get("site", DEFAULT_CENTER)
            subjects[center][subject] = {
                "identifier": md5_sum(subject),
                "code_in_study": subject,
                "handedness": row.get("handedness", "unknown"),
                "gender": row.get("gender", "unknown")}

    # Save the results
    print("Saving data in '{0}'...".format(outdir))
    save_parsing(subjects, outdir, study, "subjects")

    # Goodbye
    print("Done.")

    return subjects


def nifti_typedata(filepath, scan_type, desc_file=None, read_nifti=False):
    """ Return nifti file metadata.

    Parameters
    ----------
    filepath: str
        The path to the nifti file.
    scan_type: str
        Scan entity datatype (CW entity name).
    desc_file: str, default None
        The BIDS niftiimage associated description file.
    read_nifti: bool, default False
        If True retrieves some metadata from the file (eg. the shape, spacing,
        ...), else uses default values.

    Returns
    -------
    typedata: dict
        The structure containing the scan metadata.
    device: dict
        The structure containing the device information.
    """
    # Load the description and create the device description
    if desc_file is not None:
        with open(desc_file, "rt") as open_file:
            data_desc = json.load(open_file)
        manufacturer = data_desc.get("Manufacturer", None)
        software_version = data_desc.get("SoftwareVersions", "unkwnown")
        serialnum = data_desc.get("DeviceSerialNumber", "unkwnown")
        identifier = "{0}_{1}_{2}".format(
            manufacturer, software_version, serialnum)
        if manufacturer is not None:
            device = {
                "identifier": md5_sum(identifier),
                "manufacturer": manufacturer,
                "model": data_desc.get("ManufacturersModelName", "unkwnown"),
                "serialnum": serialnum,
                "software_version": software_version}
        else:
            device = None
    else:
        data_desc = {}
        device = None
    typedata_kwargs = {
        "te": data_desc.get("EchoTime", 0),
        "tr": data_desc.get("RepetitionTime", 0)}
    field = data_desc.get("MagneticFieldStrength", None)
    if field is not None:
        typedata_kwargs["field"] = "{0}T".format(field)

    # Load the nifti image and generate the type description
    if read_nifti:
        image = nibabel.load(filepath)
        shape = image.shape
        spacing = image.get_header().get_zooms()
        typedata = {
            "type": scan_type,
            "shape_x": int(shape[0]),
            "shape_y": int(shape[1]),
            "shape_z": int(shape[2]),
            "voxel_res_x": float(spacing[0]),
            "voxel_res_y": float(spacing[1]),
            "voxel_res_z": float(spacing[2])}
    else:
        typedata = {
            "type": scan_type,
            "shape_x": 0,
            "shape_y": 0,
            "shape_z": 0,
            "voxel_res_x": 0.,
            "voxel_res_y": 0.,
            "voxel_res_z": 0.}
    typedata.update(typedata_kwargs)

    return typedata, device


def scans_parser(root, study, outdir, read_nifti=False):
    """ Parse the sourcedata nifti files in a BIDS dataset.

    Try to detect the nifti files associeted DICOM tarballs, making the
    assumption that only the extension differs '.nii' or '.nii.gz' ->
    '.dicom.tar.gz'.

    Parameters
    ----------
    root: str
        The BIDS organized directory to be parsed (the one containing the
        'sourcedata' directory).
    study: str
        The study name.
    outdir: str
        The output directory.
    read_nifti: bool, default False
        If True retrieves some metadata from the file (eg. the shape, spacing,
        ...), else uses default values.

    Returns
    -------
    scans: dict
        The PIWS-like structure containg the parsed data.
    """
    # Welcome
    print("Starting scans parsing...")

    # Parameters
    sourcedir = os.path.join(root, "sourcedata")
    pattern = os.path.join(
        sourcedir, "sub-*", "ses-*", "*", "sub-*_ses-*.nii*")
    # TODO: remove when reorganized
    pattern = os.path.join(
        sourcedir, "sub-*", "ses-*", "*", "*", "sub-*_ses-*.nii*")
    scans = defaultdict(lambda: defaultdict(list))

    # Parse the session files
    participants_sessions = {}
    all_subjects = os.listdir(sourcedir)
    with progressbar.ProgressBar(max_value=len(all_subjects),
                                 redirect_stdout=True) as bar:
        for cnt, subject in enumerate(all_subjects):
            session_file = os.path.join(
                sourcedir, subject, "{0}_sessions.tsv".format(subject))
            if os.path.isfile(session_file):
                with open(session_file) as open_file:
                    reader = csv.DictReader(open_file, delimiter="\t")
                    participants_sessions[subject.replace("sub-", "")] = {}
                    for row in reader:
                        participants_sessions[subject.replace("sub-", "")][
                            row["session_id"]] = row
            bar.update(cnt)

    # Parse the sourcedata directory
    all_files = glob.glob(pattern)
    with progressbar.ProgressBar(max_value=len(all_files),
                                 redirect_stdout=True) as bar:
        for cnt, path in enumerate(all_files):

            # Get acquisition information
            split = path.split(os.sep)
            subject = split[-4].replace("sub-", "")
            session_id = split[-3]
            session = split[-3].replace("ses-", "")
            dtype = split[-2]
            # TODO: remove when reorganized
            subject = split[-5].replace("sub-", "")
            session_id = split[-4]
            session = split[-4].replace("ses-", "")
            dtype = split[-3]
            name, ext = split[-1].split(".", 1)
            label = name.split("_")[-1]
            if label not in ALLOWED_MODALITY:
                # Deal with multiple conversions
                label = label[:-1]
                if label not in ALLOWED_MODALITY:
                    print("Unsupported BIDS modality label '{0}'.".format(path))
                    continue
            if subject in participants_sessions:
                session_info = participants_sessions[subject][session_id]
                center = session_info.get("site", DEFAULT_CENTER)
                age_of_subject = session_info.get("age", None)
                if not isinstance(age_of_subject, float):
                    age_of_subject = None
                timepoint_label = session_info.get("label", None)
            else:
                center = DEFAULT_CENTER
                age_of_subject = None

            # Get all associated files
            resources = [path]
            desc_file = os.path.join(os.path.dirname(path), name + ".json")
            if not os.path.isfile(desc_file):
                desc_file = None
            else:
                resources.append(desc_file)
            tarball_file = os.path.join(os.path.dirname(path),
                                        name + ".dicom.tar.gz")
            if not os.path.isfile(tarball_file):
                tarball_file = None          
            if dtype == "dwi":
                bvec_file = os.path.join(os.path.dirname(path), name + ".bvec")
                bval_file = os.path.join(os.path.dirname(path), name + ".bval")
                if not os.path.isfile(bvec_file):
                    print("No diffusion bvecs, skipping '{0}'...".format(path))
                    continue
                if not os.path.isfile(bval_file):
                    print("No diffusion bvals, skipping '{0}'...".format(path))
                    continue
                resources.extend([bvec_file, bval_file])

            # Type the input nifti dataset
            if dtype in ("swi", "anat"):
                scan_type = "MRIData"
            elif dtype == "func":
                scan_type = "FMRIData"
            elif dtype == "dwi":
                scan_type = "DMRIData"
            else:
                raise ValueError(
                    "'{0}' data type not yet supported.".format(dtype))
            typedata_struct, device_struct = nifti_typedata(
                path, scan_type, desc_file, read_nifti=read_nifti)

            # Convert timepoint
            if timepoint_label is not None:
                if age_of_subject is None:
                    age_of_subject = session
                session = timepoint_label

            # Generate the scan struct
            assessment_id = "{0}_{1}_{2}_{3}".format(
                study.lower(), label, session, subject)
            scans[center][subject].append({
                "Assessment": {
                    "identifier": assessment_id,
                    "timepoint": session},
                "Scans": [{
                    "TypeData": typedata_struct,
                    "ExternalResources": [],
                    "FileSet": {
                      "identifier": md5_sum(path),
                      "name": label},
                    "Scan": {
                      "format": "NIFTI",
                      "label": label,
                      "identifier": md5_sum(path),
                      "type": label}
                }]
            })
            if tarball_file is not None:
                scans[center][subject][-1]["Scans"].append({
                    "TypeData": typedata_struct,
                    "ExternalResources": [{
                        "identifier": md5_sum(tarball_file),
                        "absolute_path": True,
                        "name": name,
                        "filepath": tarball_file}],
                    "FileSet": {
                      "identifier": md5_sum(tarball_file),
                      "name": label},
                    "Scan": {
                      "format": "DICOM",
                      "label": label,
                      "identifier": md5_sum(tarball_file),
                      "type": label}
                })
            if device_struct is not None:
                scans[center][subject][-1]["Device"] = device_struct
            if age_of_subject is not None:
                scans[center][subject][-1]["Assessment"][
                    "age_of_subject"] = age_of_subject
            for _path in resources:
                name, ext = os.path.basename(_path).split(".", 1)
                scans[center][subject][-1]["Scans"][0][
                    "ExternalResources"].append({
                        "identifier": md5_sum(_path),
                        "absolute_path": True,
                        "name": name,
                        "filepath": _path})

            # Update progress bar
            bar.update(cnt)

    # Save the results
    print("Saving data in '{0}'...".format(outdir))
    save_parsing(scans, outdir, study, "scans")

    # Goodbye
    print("Done.")

    return scans


def table_parser(table_files, study, outdir, timepoint=None, dtype="wide",
                 auto_type=False):
    """ Parse the TSV table files of a BIDS dataset.

    Parameters
    ----------
    table_files: list of str
        The BIDS organized TSV table files with the first column beeing the
        participant ID.
    study: str
        The study name.
    outdir: str
        The output directory.
    timepoint: str, default None
        In longitudinal studies this parameter represents the table acquisition
        timestamp.
    dtype: str, default 'wide'
        The table format: 'wide' or 'long'. In the long format, participant IDs
        are unique.
    auto_type: bool, default False
        if True try to guess the table column data type.

    Returns
    -------
    tables: list of str
        Saved PIWS-like structure containg the parsed data in JSON format.
    """
    # Welcome
    print("Starting tables parsing...")

    # Check inputs
    if dtype not in ("wide", "long"):
        raise ValueError("Unexpected data type '{0}'.".format(dtype))

    # Parse all the tables
    tables = []
    with progressbar.ProgressBar(max_value=len(table_files),
                                 redirect_stdout=True) as bar:
        for cnt, path in enumerate(table_files):

            # Open the TSV table
            with open(path, "rt") as open_file:
                raw_table = open_file.readlines()
            header = raw_table[0].rstrip("\n").split("\t")
            table_content = []
            for row in raw_table[1:]:
                row = row.rstrip("\n").split("\t")
                if auto_type:
                    raise NotImplementedError(
                        "The automatic typing of columns has not been yet "
                        "implemented.")
                table_content.append(row)

            # Generate the final structure
            table = {}
            qname = os.path.basename(path).replace(".tsv", "")
            center = DEFAULT_CENTER
            if timepoint is None:
                timepoint = DEFAULT_TIMEPOINT
            for row_cnt, row in enumerate(table_content):
                assessment_id = "{0}_q{1}_{2}".format(
                    study.lower(), qname, timepoint)
                subject = row[0].replace("sub-", "")
                if dtype == "wide":
                    assessment_id = "{0}_{1}".format(
                        assessment_id, row_cnt + 1)
                assessment_id = "{0}_{1}".format(assessment_id, subject)

                # Create assessment structure
                assessment_struct = {
                    "identifier": assessment_id,
                    "timepoint": timepoint}

                # Build the subject questionnaires structure for this timepoint
                subj_questionnaires = {
                    "Questionnaires": OrderedDict(),
                    "Assessment": assessment_struct
                }

                # Fill the questionnaire structure
                qdata = OrderedDict()
                for question, answer in zip(header, row):
                    question = question.decode("utf-8", "ignore").encode(
                        "utf-8")
                    answer = answer.decode("utf-8", "ignore").encode("utf-8")
                    qdata[question] = answer
                subj_questionnaires["Questionnaires"][qname] = qdata

                # Add this questionnaire to the patient data
                if center not in table:
                    table[center] = {}
                if subject not in table[center]:
                    table[center][subject] = []
                table[center][subject].append(subj_questionnaires)

            # Saving result
            save_parsing(table, outdir, study, "tables-{0}".format(qname))
            tables.extend(glob.glob(
                os.path.join(outdir, "tables-{0}*.json".format(qname))))

            # Update progress bar
            bar.update(cnt)

    # Goodbye
    print("Done.")

    return tables

