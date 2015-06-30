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
import re

# Docutils import
from docutils.core import publish_parts


def rst2html(rstfile, data_url):
    """ Create a html documentation from a rst description.

    Parameters
    ----------
    rstfile: str (mandatory)
        the documentation rst description.
    data_url: str (mandatory)
        the server data url.

    Returns
    -------
    doc: str
        the corresponding html documentation.
    """
    with open(rstfile, "r") as openfile:
        rststr = "".join(openfile.readlines())
        doc = publish_parts(rststr, writer_name="html")["html_body"]
    doc = set_data_url(data_url, doc)
    return doc


def create_html_doc(directory, data_url):
    """ Create the html documentation from the rst files available in the
    input directory.

    The mapping between each file and each CW entity is performed based on the
    file name and entity label.

    Parameters
    ----------
    directory: str (mandatory)
        the input documentation directory: where we are looking for rst files.
    data_url: str (mandatory)
        the server data url.

    Returns
    -------
    docmap: dict
        a mapping with the expected CW entity label as key, associated with the
        html documentation.
    """
    docmap = dict((rstfile.split(".")[0], rst2html(os.path.join(directory, rstfile), data_url))
                  for rstfile in os.listdir(directory)
                  if rstfile.endswith(".rst"))
    return docmap


def set_data_url(data_url, doc):
    """ Transform the image source.

    Note that all the images or resources have to be placed in the cube data
    folder.

    Parameters
    ----------
    data_url: str (mandatory)
        the server data url.
    doc: str
        an html documentation.

    Returns
    -------
    doc: str
        the formatted html documentation.
    """
    matches = re.findall("<img.*/>", doc)
    for imgtag in matches:
        index = imgtag.index("src=") + 5
        newimgtag = imgtag[:index] + data_url + imgtag[index:]
        doc = doc.replace(imgtag, newimgtag)
    return doc
