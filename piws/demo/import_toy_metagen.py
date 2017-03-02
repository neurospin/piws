#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2016
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
from piws.importer.metagen import MetaGen
from piws.importer.genetics import Genetics
from piws.importer.subjects import Subjects
from piws.importer.groups import CWGroups
from piws.importer.users import CWUsers
from parse_toy_metagen import metagen_parser
from parse_toy_metagen import genetic_parser
from parse_toy_metagen import subject_parser


# Ask for instance & login information
instance_name = raw_input("\nEnter the instance name [default: toy_metagen]: ")
if not instance_name:
    instance_name = "toy_metagen"
meta_path = os.path.join(os.path.dirname(__file__), "metagen")
plink_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "plink", "test"))
login = raw_input("\nEnter the '{0}' login [default: anon]: ".format(
    instance_name))
if not login:
    login = "anon"
password = getpass.getpass("Enter the '{0}' password [default: anon]: ".format(
    instance_name))
if not password:
    password = "anon"

# Define users
USERS = {
    "anon": {
        "login": "anon",
        "password": "anon",
        "group_names": ["users"]}
}


# Create a cw session
config = cwconfig.instance_configuration(instance_name)
repo, cnx = in_memory_repo_cnx(config, login=login, password=password)
session = repo._get_session(cnx.sessionid)

# Parse the file system
subjects = subject_parser(plink_path, "TEST")
genetics = genetic_parser(plink_path, "TEST", "V1")
metagen = metagen_parser(meta_path)

# Define the importer
db_user_importer = CWUsers(session, USERS)
db_grp_importer = CWGroups(session, ["TEST_V1", "TEST"], store_type="None")
db_genetic_importer = MetaGen(session, store_type="None")
db_plink_importer = Genetics(
    session, "TEST", "NS", genetics, can_read=True,
    can_update=False, data_filepath=plink_path, store_type="None")
db_subject_importer = Subjects(
    session, "TEST", subjects, store_type="None")

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
# > meta genetics
for chr_name, meta_struct in metagen.items():
    db_genetic_importer.import_data(
        chromosome_name=chr_name,
        genes=meta_struct["genes"],
        cpgs=meta_struct["cpgs"],
        snps=meta_struct["snps"])
    db_genetic_importer.cleanup()
# > plink genetics
db_plink_importer.import_data()
db_plink_importer.cleanup()


# Commit
session.commit()
