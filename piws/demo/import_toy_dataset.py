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

# CubicWeb import
from cubicweb import cwconfig
from cubicweb.dbapi import in_memory_repo_cnx

# Piws import
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from piws.scripts.groups import Groups
from piws.scripts.users import Users
from piws.scripts.subjects import Subjects
from piws.scripts.scans import Scans
from piws.scripts.questionnaires import Questionnaires
from piws.scripts.genetics import Genetics
from parse_toy_data import subject_parser
from parse_toy_data import scan_parser
from parse_toy_data import questionnaire_parser
from parse_toy_data import genetic_parser


# Ask for instance & login information
instance_name = raw_input("\nEnter the instance name [default: toy_instance]: ")
if not instance_name:
    instance_name = "toy_instance"
demo_path = raw_input("\nEnter where are the demo data [default: /tmp/demo]: ")
if not demo_path:
    demo_path = "/tmp/demo"
login = raw_input("\nEnter the '{0}' login [default: anon]: ".format(
    instance_name))
if not login:
    login = "anon"
password = getpass.getpass("Enter the '{0}' password [default: anon]: ".format(
    instance_name))
if not password:
    password = "anon"

# Gloabal parameters
USERS = {
    "user1": {
        "login": "user1",
        "password": "user1",
        "group_names": ["toy_V0", "users"]
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

# Create a cw session
config = cwconfig.instance_configuration(instance_name)
repo, cnx = in_memory_repo_cnx(config, login=login, password=password)
session = repo._get_session(cnx.sessionid)

# Parse the file system
subjects = subject_parser(demo_path, STUDY_NAME)
scans = scan_parser(demo_path, STUDY_NAME)
questionnaires = questionnaire_parser(demo_path, STUDY_NAME)
genetics = genetic_parser(demo_path, STUDY_NAME)

# Define all the importers
db_grp_importer = Groups(session, ["toy_V0", "toy_V1", "toy"],
                         use_store=True)
db_user_importer = Users(session, USERS, use_store=True)
db_subject_importer = Subjects(
    session, STUDY_NAME, subjects, use_store=True)
db_scan_importer = Scans(
    session, STUDY_NAME, CENTER_NAME, scans, can_read=True, can_update=False,
    data_filepath=demo_path, use_store=True)
db_questionnaire_importer = Questionnaires(
    session, STUDY_NAME, CENTER_NAME, questionnaires, can_read=True,
    can_update=False, data_filepath=demo_path, use_store=True)
db_genetic_importer = Genetics(
    session, STUDY_NAME, CENTER_NAME, genetics, can_read=True,
    can_update=False, data_filepath=demo_path, use_store=True)

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

# Commit
session.commit()
