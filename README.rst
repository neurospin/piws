
==============================
Population Imaging Web Service
==============================


Summary
=======

Population Imaging Web Service cube.

Publish neuroimaging genetic datasets using the CubicWeb framework.
Check `this link <https://neurospin.github.io/piws/>`_ for the complete
documentation.

Install
=======

Following the proposed instructions_, it is possible to create a
demonstrator DSS by installing the CW environement from scratch or by runing a
virtual machine.

.. _instructions: https://neurospin.github.io/piws/installation.html

Content
=======

This cube contains most of the functionalities that have been developped by
the NeuroSpin platform in collaboration with Logilab to produce population
imaging (PI), web semenatic data sharing services (DSS). Two services are
provided:

- a multi-center upload DSS.
- a publication DSS with massive-download features.

This cube provides:
-------------------

- A database schema:

  - supports any kind of data modality a PI projects can produce (MRI, EEG,
    Eye-Tracking, Questionnaires, Subjects and associated meta-data).

- An upload mechanism:

  - described in a JSON file.
  - synchronous and asynchronous validations possibilities.
  - only specific groups have the rights to upload.

- A shopping cart mechanism:

  - interact with facets to filter the content of the current search.
  - users only access their own searches.
  - a search has an expiration date.

- A shopping cart transfer mechanism:

  - delegate the download to sFTP.
  - serve searches using FUSE (need to create virtual folders).
  - serve searches using Twisted server.
  - share common local data organization.

- A fine security model

  - login/logout possibility.
  - access rules on each data element.

- A web-interface that allows users to navigate efficiently within the database
  content, consult data and select relevant subsets:

  - online visualisation of MRI sequences (3D and 4D).
  - online consultation of questionnaires, dynamic filtering of tables and 
    direct-download possibility.
  - online contextual multi-level documentation.

- A unified insertion procedure:

  - Python scripts to insert data from Python dictionaries.


Dependencies:
-------------

This cube integrates the brainomics2_, rql_download_ and rql_upload_ cubes 
which bring:

- the database schema that supports any kind of data modality a PI projects can
  produce (MRI, EEG, Eye-Tracking, Questionnaires, Subjects and machines 
  meta-informations ...)
- massive data download/upload functionalities.

.. _brainomics2: https://github.com/neurospin/brainomics2
.. _rql_upload: https://github.com/neurospin/rql_upload
.. _rql_download: https://github.com/neurospin/rql_download


Roadmap:
--------

- Work at the integration of emerging ontologies and standards
  (e.g. NIDM).
- Add operability with bioinformatics resources to request the (imputed) SNP
  data.
- Automatic logout based on the server activity using cookies.
- Add compatibility with CubicWeb 3.23.
