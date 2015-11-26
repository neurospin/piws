==============================
Population Imaging Web Service
==============================


.. image:: ./piws/data/images/nsap.png 
   :scale: 50 %
   :alt: NeuroSpin Analysis Platform
   :align: center

Summary
=======

Population Imaging Web Service cube.

Publish neuroimaging genetic datasets using CubicWeb framework.

Content
=======

This cube contains most of the functionalities that have been developped by
the neurospin platform in collaboration with Logilab to produce wed-semantic 
population imaging databases.

This cube provides:
-------------------

- A database schema that supports any kind of data modality the PI projects can
  produce (MRI, EEG, Eye-Tracking, Questionnaires, Subjects and machines 
  meta-informations ...)

- A web-interface that allows users to navigate efficiently within the database
  content, consult data and select relevant subsets.
    - Online visualisation of MRI sequences (3D and 4D).
    - Online consultation of questionnaires, dynamic filtering of tables and direct
      download possibility
    - Multi-level documentation

- A fine security model
  - Login/logout possibility
  - Access rules on each data element

Synergy:
--------

This cube is perfectly compatible with the rql_download_ and rql_upload_ cubes 
which bring massive data download/upload functionalities.

.. _rql_upload: https://github.com/neurospin/rql_upload
.. _rql_download: https://github.com/neurospin/rql_download

