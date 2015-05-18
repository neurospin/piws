#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from cubicweb.server import hook

# PIWS import
from cubes.piws.docgen.rst2html import create_html_doc


class CreateDocumentation(hook.Hook):
    """ On startup create the documentation.
    """
    __regid__ = "piws.create_documentation"
    events = ("server_startup", )

    def __call__(self):
        """ The documantation is stored in repo.vreg.docmap and thus will
        be accessible in any CW pages.
        The docmap is a dictionary with the input rst documentation file
        basenames as keys. The values contain the corresponding html codes.
        """
        # Get the data url
        with self.repo.internal_cnx() as cnx:
            data_url = cnx.base_url() + "/data/"

        # Get the documentation
        doc_folder = self.repo.vreg.config["documentation_folder"]
        if doc_folder:
            self.repo.vreg.docmap = create_html_doc(doc_folder, data_url)
        else:
            self.repo.vreg.docmap = {}
