..  NSAp documentation master file, created by
    sphinx-quickstart on Wed Sep  4 12:18:01 2013.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.


Neurospinweb
============

Summary
-------

* Address neuroimaging genetic datasets.
* Propose a unified insertion procedure in a cubicweb database.
* Propose user-friendly views.
* Contain a demonstrator that can be generated from scratch.

Description
-----------

The cube address the
:ref:`insertion of neuroimaging genetic datasets <scripts_class>`. Scans,
questionnaires and genetic measures are inserted using the following schema:

|

.. figure:: generated/schemas/scan.png
    :width: 600px
    :align: center
    :alt: scan

    The scans insertion associated schema.

.. figure:: generated/schemas/questionnaire.png
    :width: 600px
    :align: center
    :alt: questionnaire

    The questionnaires insertion associated schema.

.. figure:: generated/schemas/genetic.png
    :width: 600px
    :align: center
    :alt: genetic

    The genetic data insertion associated schema.

A :ref:`demonstrator <scripts_demo>` is also proposed to illustrate the
proposed unified insertion procedure. Some :ref:`views <views_guide>` are also
proposed in the cube to visualize properly or summarize the database content.
Finally some :ref:`features of the cube <features_guide>` are presented.
Indeed, the cube tune the cubicweb rights mechanism and custom facets are
proposed to filter request result sets send on a database containing
neuroimaging genetic data.

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
