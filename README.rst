
==============================
Population Imaging Web Service
==============================


Summary
=======

Population Imaging Web Service cube.

Publish neuroimaging genetic datasets using the CubicWeb framework.
Check `this link <https://neurospin.github.io/piws/>`_ for the complete
documentation.

Content
=======

This cube contains most of the functionalities that have been developped by
the NeuroSpin platform in collaboration with Logilab to produce semantic web
population imaging databases.

This cube provides:
-------------------

- A database schema that supports any kind of data modality the PI projects can
  produce (MRI, EEG, Eye-Tracking, Questionnaires, Subjects and machines 
  meta-informations ...)

- A web-interface that allows users to navigate efficiently within the database
  content, consult data and select relevant subsets. Examples:

  - Online visualisation of MRI sequences (3D and 4D).
  - Online consultation of questionnaires, dynamic filtering of tables and 
    direct-download possibility
  - Multi-level documentation

- A fine security model
  - Login/logout possibility
  - Access rules on each data element

Synergy:
--------

This cube integrates the rql_download_ and rql_upload_ cubes 
which bring massive data download/upload functionalities.

.. _rql_upload: https://github.com/neurospin/rql_upload
.. _rql_download: https://github.com/neurospin/rql_download
