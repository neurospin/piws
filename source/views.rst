:orphan:

.. _views_guide:

###################
Views documentation
###################

Documentation regarding views defined on the cube.

:mod:`neurospinweb.views.highcharts_views`: HighChartsBasicPieView
==================================================================

.. currentmodule:: neurospinweb.views

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


:mod:`neurospinweb.views.table_views`: Table views
==================================================

All the views designed in this section are based on the 'datatables' JavaScript
library. Such views are convenient to display questionnaires associated answers
or huge dataset as we may be confronted when treating genetic data.

.. currentmodule:: neurospinweb.views

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

    table_views.JhugetableView
    table_views.JtableView

CSV inner exporter
------------------

.. autosummary::
    :toctree: generated/table/
    :template: class.rst

    table_views.CSVJtableView

Inner tools
-----------

.. autosummary::
    :toctree: generated/table/
    :template: function.rst

    table_views.label_cleaner

Ajax inner callbacks
--------------------

.. autosummary::
    :toctree: generated/table/
    :template: function.rst

    table_views.csv_open_answers_export
    table_views.get_open_answers_data
    table_views.get_questionnaires_data
