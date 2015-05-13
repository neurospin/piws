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

# CubicWeb import
from cubicweb import cwconfig
from cubicweb.dbapi import in_memory_repo_cnx

# Piws import
from cubes.piws.scripts.users import Users
from cubes.piws.scripts.subjects import Subjects
from cubes.piws.scripts.scans import Scans
from cubes.piws.scripts.questionnaires import Questionnaires
from cubes.piws.scripts.genetics import Genetics

# Define the output_directory
out_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       "source", "generated", "schemas")
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# Create a cw session
config = cwconfig.instance_configuration("toy_instance")
repo, cnx = in_memory_repo_cnx(config, login="anon", password="anon")
session = repo._get_session(cnx.sessionid)

# Generate the schemas
# > user
db_user_importer = Users(session, {})
db_user_importer.schema(outfname=os.path.join(out_dir, "user.png"))
# > scan
db_scan_importer = Scans(session, "", "", {})
db_scan_importer.schema(outfname=os.path.join(out_dir, "scan.png"))
# > questionnaire
db_questionnaire_importer = Questionnaires(session, "", "", {})
db_questionnaire_importer.schema(
    outfname=os.path.join(out_dir, "questionnaire.png"))
# > genetic
db_genetic_importer = Genetics(session, "", "", {}, )
db_genetic_importer.schema(outfname=os.path.join(out_dir, "genetic.png"))

