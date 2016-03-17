# -*- coding: utf-8 -*-
##########################################################################
# NSAp - Copyright (C) CEA, 2014
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""cubicweb-piws postcreate script, executed at instance creation time or when
the cube is added to an existing instance.

You could setup site properties or a workflow here for example.
"""

# Change the site name
set_property("ui.site-title", "")

# Change pagination properties
set_property("navigation.page-size", "20")

# Set cards
from cubes.piws.migration.cards import create_or_update_static_cards
create_or_update_static_cards(session)
