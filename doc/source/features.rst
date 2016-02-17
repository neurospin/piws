:orphan:

.. _features_guide:

######################
Features documentation
######################

Documentation regarding all other features implemented in this cube,
especially access rights and facets

:mod:`piws.views.facets`
------------------------

CubicWeb has a builtin facet system to define restrictions filters.
A number of criteria have been set up to restrict searches in this cube.

.. automodule:: cubes.piws.views.facets

The access rights management
----------------------------

All entities that requires access rights management are linked to 
one 'Assessment' entity by the relation 'in_assessment'.
As the access rights are set on the 'Assessment' entity through the
'can_read' and 'can_update' relations, the concerned entity are accessible
only by authorized users. See schema below:

|

.. figure:: _static/rights.png
    :width: 500px
    :alt: Access rights management
    :align: center

    Cube access rights management

Uplad functionnality
--------------------

The upload functionality is derived from the `rql_upload cube
<https://github.com/neurospin/rql_upload>`_.

Download functionnality
-----------------------

The download functionality is derived from the `rql_download cube
<https://github.com/neurospin/rql_download>`_

