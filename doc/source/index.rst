..  NSAp documentation master file, created by
    sphinx-quickstart on Wed Sep  4 12:18:01 2013.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.


Population Imaging Web Service: PIWS
====================================

Summary
-------

* Address neuroimaging genetic datasets.
* Propose a unified insertion procedure in a CubicWeb database.
* Propose a download strategy for images and associated metadata.
* Propose dynamic filters: what you see is what you get.
* Propose simplified data collection tools.
* Propose user-friendly views.
* Contain a demonstrator that can be generated from scratch.


Description
-----------

The cube address the
:ref:`insertion of neuroimaging genetic datasets <scripts_class>`. Scans,
questionnaires, processsings and genetic measures are inserted using the
following schema:

|

.. figure:: generated/schemas/scans.png
    :width: 600px
    :align: center
    :alt: scan

    The scans insertion associated schema.

.. figure:: generated/schemas/questionnaires.png
    :width: 600px
    :align: center
    :alt: questionnaire

    The questionnaires insertion associated schema.

.. figure:: generated/schemas/genetics.png
    :width: 600px
    :align: center
    :alt: genetic

    The genetic data insertion associated schema.

.. figure:: generated/schemas/processings.png
    :width: 600px
    :align: center
    :alt: genetic

    The processed data insertion associated schema.

A :ref:`demonstrator <scripts_demo>` is also proposed to illustrate the
proposed unified insertion procedure. Some :ref:`views <views_guide>` are also
proposed in the cube to visualize properly or summarize the database content.
Finally some :ref:`features of the cube <features_guide>` are presented.
Indeed, the cube tunes the CubicWeb rights mechanism and custom facets are
proposed to filter request result sets.

The proposed tool also proposes upload and download functionalties. It has been
setup to collect and serve data of two european projects
(IMAGEN and EUAIMS). Some capabilities of the tool are illustrated in these
videos:

* `Download tutorial <ftp://ftp.cea.fr/pub/unati/brainomics/euaims/download_euaims_data.mp4>`_
* `Navigation tutorial <ftp://ftp.cea.fr/pub/unati/brainomics/euaims/navigate_euaims_database.mp4>`_

|

Contents
========
.. toctree::
    :maxdepth: 1

    installation
    documentation


Search
=======

:ref:`search`
