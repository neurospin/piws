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
import sys
import glob
import json


def metagen_parser(root):
    """ Method to get the bioresource data elements.

    Parameters
    ----------
    root: str (mandatory)
        the path to the dataset.

    Returns
    -------
    metadata: dict of dict
        the first dictionary contains the chromosme name as keys and then
        the associated 'genes', 'snps' and 'cpgs' JSON files.
    """
    # Initialize the output structure
    metadata = {}

    # Get all the datasets
    for chr_name in range(1, 22) + ["X", "Y"]:
        metadata[chr_name] = {
            "genes": os.path.join(root,
                                  "genes_of_chr{0}.json".format(chr_name)),
            "snps": os.path.join(root,
                                 "snps_of_chr{0}.json".format(chr_name)),
            "cpgs": os.path.join(root,
                                 "cpgs_of_chr{0}.json".format(chr_name))}
        for key, path in metadata[chr_name].items():
            with open(path, "rt") as open_file:
                metadata[chr_name][key] = json.load(open_file)

    return metadata

