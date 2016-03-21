:orphan:

.. _scripts_guide:

######################
Importation procedures
######################

Python classes are provided to insert neuroimaging genetic data in a cubicweb
database. The major advantage of this module is to guarantee a unified schema
that in turn enables us to design common views.

.. _scripts_class:

:mod:`piws.scripts`: Unified importation methods
================================================

.. currentmodule:: cubes.piws.importer

.. autosummary::
    :toctree: generated/scripts/
    :template: class.rst

    base.Base
    subjects.Subjects
    genetics.Genetics
    scans.Scans
    questionnaires.Questionnaires
    processings.Processings
    groups.CWGroups
    users.CWUsers


.. _scripts_demo:

:mod:`piws.demo`: Demonstration
===============================

To exemplify the proposed unified importation methods, a demonstrator has been
leveraged. By executing the 'generate_toy_dataset.py' function, a toy neuroimaging
genetic data is created on your local file system.

The 'import_to_dataset.py' then inserts the generated data in a cubicweb
database using the previously presented unified insertion procedures.
    


