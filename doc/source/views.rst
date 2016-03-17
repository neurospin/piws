:orphan:

.. _views_guide:

###################
Views documentation
###################

Documentation regarding views defined on the cube.

:mod:`piws.views.highcharts_views`: HighChartsBasicPieView
==========================================================

.. currentmodule:: cubes.piws.views

All the views designed in this section are based on the 'highcharts' JavaScript
library. The aim here is to propose a bunch of views to summarize the
database content.

User Views
----------

.. autosummary::
    :toctree: generated/highcharts/
    :template: class.rst

    highcharts_views.HighChartsBasicPieView
    highcharts_views.HighChartsRelationSummaryView
    highcharts_views.HighChartsBasicPlotView


:mod:`piws.views.longitudinal_views`: Longitudinal views
========================================================

When dealing with multiple timepoints, it is crucial to display the scores
of a subject at these timepoints.

.. automodule:: cubes.piws.views.longitudinal_views


:mod:`piws.views.table_views`: Table views
==========================================

All the views designed in this section are based on the 'datatables' JavaScript
library. Such views are convenient to display questionnaires associated answers
or huge dataset as we may be confronted when treating genetic data.

.. currentmodule:: cubes.piws.views

User Views
----------

The 'JhugetableView' class will send a single request to the server and then
everything will be deported to the client. The 'JtableView' will interact
with the server each time the user interact with the JavaScript table (ie,
paging, sorting, ....).

|

.. autosummary::
    :toctree: generated/table/
    :template: class.rst

    table_views.JHugetableView
    table_views.JtableView

Derived Views
-------------

.. autosummary::
    :toctree: generated/table/
    :template: class.rst

    table_views.FileAnswerTableView

Export Views
------------

.. autosummary::
    :toctree: generated/table/
    :template: class.rst

    table_views.PIWSCSVView


Ajax inner callbacks
--------------------

.. autosummary::
    :toctree: generated/table/
    :template: function.rst

    table_views.get_open_answers_data
    table_views.get_questionnaires_data



:mod:`piws.views.primary`: Primary views
============================================

Each entity content is displayed with a primary view. 


.. automodule:: cubes.piws.views.primary
    :private-members:


:mod:`piws.views.secondary`: Secondary views
============================================

A request may returns a bunch of results that are displayed in a list where
each returned entity is displayed with a secondary view. 


.. automodule:: cubes.piws.views.secondary
    :private-members:
