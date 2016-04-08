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
from cubes.piws.importer.users import CWUsers
from cubes.piws.importer.subjects import Subjects
from cubes.piws.importer.scans import Scans
from cubes.piws.importer.questionnaires import Questionnaires
from cubes.piws.importer.genetics import Genetics
from cubes.piws.importer.processings import Processings

# Define the output_directory
out_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       "source", "generated", "schemas")
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# Generate the schemas
# > user
CWUsers.schema(outfname=os.path.join(out_dir, "users.png"))
# > subjects
Subjects.schema(outfname=os.path.join(out_dir, "subjects.png"))
# > scan
Scans.schema(outfname=os.path.join(out_dir, "scans.png"))
# > questionnaire
Questionnaires.schema(outfname=os.path.join(out_dir, "questionnaires.png"))
# > genetic
Genetics.schema(outfname=os.path.join(out_dir, "genetics.png"))
# > processings
Processings.schema(outfname=os.path.join(out_dir, "processings.png"))
