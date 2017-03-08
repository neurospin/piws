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
import sys
import getpass

# CW imports
from cubicweb.utils import admincnx

# Piws import
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from piws.importer.groups import CWGroups
from piws.importer.users import CWUsers
from piws.importer.subjects import Subjects
from piws.importer.scans import Scans
from piws.importer.questionnaires import Questionnaires
from piws.importer.genetics import Genetics
from cubes.piws.importer.processings import Processings
from parse_toy_data import freesurfer_parser
from parse_toy_data import subject_parser
from parse_toy_data import scan_parser
from parse_toy_data import questionnaire_parser
from parse_toy_data import genetic_parser
from cubes.piws.parser.freesurfer import RQL_T1


# Ask for instance & login information
instance_name = raw_input("\nEnter the instance name [default: toy_instance]: ")
if not instance_name:
    instance_name = "toy_instance"
demo_path = raw_input("\nEnter where are the demo data [default: /tmp/demo]: ")
if not demo_path:
    demo_path = "/tmp/demo"

# Select the insertion methode type
available_stores = ["RQL", "SQL", "MASSIVE"]
menu = "\nAvailable importation methods: "
for index, store in enumerate(available_stores):
    menu += "\n{} ---> {}".format(index, store)
menu += "\nPlease choose a store type: "
while True:
    store_index = raw_input(menu)
    if store_index in [str(i) for i in range(len(available_stores))]:
        break
    else:
        print("\nInvalid selection")
store_type = available_stores[int(store_index)]
print("\nStarting importation with '{}' store...\n".format(store_type))

# Gloabal parameters
USERS = {
    "user1": {
        "login": "user1",
        "password": "user1",
        "group_names": ["toy_V0", "users", "uploaders"]
    },
    "user2": {
        "login": "user2",
        "password": "user2",
        "group_names": ["toy_V1", "users"]
    },
    "user3": {
        "login": "user3",
        "password": "user3",
        "group_names": ["toy", "users"]
    }
}
STUDY_NAME = "toy"
CENTER_NAME = "home"

# Parse the file system
subjects = subject_parser(demo_path, STUDY_NAME)
scans = scan_parser(demo_path, STUDY_NAME)
questionnaires = questionnaire_parser(demo_path, STUDY_NAME)
genetics = genetic_parser(demo_path, STUDY_NAME)
processings = freesurfer_parser(demo_path, STUDY_NAME)

with admincnx(instance_name) as session:
    # Define all the importers
    db_grp_importer = CWGroups(session, ["toy_V0", "toy_V1", "toy", "uploaders"],
                               store_type=store_type)
    db_user_importer = CWUsers(session, USERS)
    db_subject_importer = Subjects(
        session, STUDY_NAME, subjects, store_type=store_type)
    db_scan_importer = Scans(
        session, STUDY_NAME, CENTER_NAME, scans, can_read=True, can_update=False,
        data_filepath=demo_path, store_type=store_type)
    db_questionnaire_importer = Questionnaires(
        session, STUDY_NAME, CENTER_NAME, questionnaires, "Clinical",
        can_read=True, can_update=False, data_filepath=demo_path, store_type=store_type,
        use_openanswer=True)
    db_genetic_importer = Genetics(
        session, STUDY_NAME, CENTER_NAME, genetics, can_read=True,
        can_update=False, data_filepath=demo_path, store_type=store_type)
    db_processings_importer = Processings(
        session, STUDY_NAME, CENTER_NAME, processings, "FreeSurfer", can_read=True,
        can_update=False, data_filepath=demo_path, store_type=store_type)

    # Execute in the appropriate order the importation scripts
    # > groups
    db_grp_importer.import_data()
    db_grp_importer.cleanup()
    # > users
    db_user_importer.import_data()
    db_user_importer.cleanup()
    # > subjects
    db_subject_importer.import_data()
    db_subject_importer.cleanup()
    # > scans
    db_scan_importer.import_data()
    db_scan_importer.cleanup()
    # > questionnaires
    db_questionnaire_importer.import_data()
    db_questionnaire_importer.cleanup()
    # > genetics
    db_genetic_importer.import_data()
    db_genetic_importer.cleanup()
    # > processings
    db_processings_importer.import_data()
    db_processings_importer.cleanup()

    # Commit
    session.commit()
