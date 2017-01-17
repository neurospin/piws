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
from parse_toy_metagen import metagen_parser


# Ask for instance & login information
instance_name = raw_input("\nEnter the instance name [default: toy_metagen]: ")
if not instance_name:
    instance_name = "toy_metagen"
demo_path = os.path.join(os.path.dirname(__file__), "metagen")
login = raw_input("\nEnter the '{0}' login [default: anon]: ".format(
    instance_name))
if not login:
    login = "anon"
password = getpass.getpass("Enter the '{0}' password [default: anon]: ".format(
    instance_name))
if not password:
    password = "anon"


# Create a cw session
config = cwconfig.instance_configuration(instance_name)
repo, cnx = in_memory_repo_cnx(config, login=login, password=password)
session = repo._get_session(cnx.sessionid)

# Parse the file system
metagen = metagen_parser(demo_path)

# Define the importer
db_genetic_importer = MetaGen(session, use_store=False)

# Execute in the appropriate order the importation scripts
# > genetics
for chr_name, meta_struct in metagen.items():
    db_genetic_importer.import_data(
        chromosome_name=chr_name,
        genes=meta_struct["genes"],
        cpgs=meta_struct["cpgs"],
        snps=meta_struct["snps"])
    db_genetic_importer.cleanup()


# Commit
session.commit()
