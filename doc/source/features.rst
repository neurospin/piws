:orphan:

.. _features_guide:

###################################
Neurospinweb features documentation
###################################

Documentation regarding all other features implemented in this cube,
especially access rights and facets

:mod:`neurospinweb.views.facets`
--------------------------------

CubicWeb has a builtin facet system to define restrictions filters.
A number of criteria have been set up to restrict searches in this cube.

.. automodule:: neurospinweb.views.facets

The access rights management
----------------------------

All entities that requires access rights management are linked to 
one 'Assessment' entity by the relation 'in_assessment'.
As the access rights are set on the 'Assessment' entity through the
'can_read' and 'can_update' relations, the concerned entity are accessible
only by authorized users. See schema below:

|

.. figure:: _static/Image1.png
    :width: 500px
    :alt: Access rights management
    :align: center

    Cube access rights management

