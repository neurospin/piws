
.. _install_guid:

=================
Installing `PIWS`
=================

This tutorial walk you through the process of installing a data sharing
service (DSS) based on the the Population Imaging Web Service (PIWS) cube.
Two strategies are proposed: create a demonstrator DSS by
:ref:`installing the CW environement from scratch <install_scratch>` or by
:ref:`running a virtual machine <install_vm>`. For testing, we recommand the
second option.


.. _install_scratch:

Installing a DSS from scratch
=============================

The CW environment needs to be installed in order to setup the demonstrator.
This tutorial was tested with CW 3.20.9. Please visit the 
`CW website <https://docs.cubicweb.org>`_ for a
detailed procedure on how to install CW.
In addition 'postgresql' and 'postgresql-plpython' must be installed. Notice
that a PostgreSQL account is required:

::

    >>> whoami
    me
    >>> sudo -u postgres createuser -P -s me

Then configure CW by changing the resource mode and augmenting the default
search path for cubes:

    >>> mkdir -p $HOME/cw/cubes
    >>> mkdir -p $HOME/cw/repositories
    >>> export CW_MODE=user
    >>> export CW_CUBES_PATH=$HOME/cw/cubes
    >>> export PYTHONPATH=$PYTHONPATH:$HOME/cw


Setup environment
-----------------

A CW instance is made of several base cubes. A helper package is proposed to
import the required PIWS cube dependencies. First install the helper package:

::

    >>> pip install --user piws_setup

Since the helper package has been installed using the user scheme in the
previous section, you may have to update the path to executable files:

::

    >>> export PATH=$PATH:$HOME/.local/bin

If you have root privileges on the machine, you may use a standard
installation (without the --user option) to avoid the previous step.
Then execute the setup script:

::

    >>> piws_setup -d $HOME/cw/repositories

Select the appropriate configuration depending on the installed version of CW.
This information can be accessed by typing:

::

    >>> cubicweb-ctl list


Instance creation and configuration
-----------------------------------

Create a PIWS instance named 'toy_instance':

::

    >>> cubicweb-ctl create piws toy_instance

To be compliant with following documentation, we recommend to authorize
anonymous access to the database.
Four specific items must be configured when a DSS is created: the WEB, PIWS,
RQL_UPLOAD and RQL_DOWNLOAD features.
They can be configured during the instance creation or by editing the instance
associated 'all-in-one.conf' configuration file (see its location below).
The different basic configurations are reviewed in the following paragraphs:

- **Web configuration:** In order to access the CW instance through a web
  browser, a port has to be defined. It is also possible to control the
  maximum length of an HTTP/HTTPS request. This latter option will be critical
  when large files are uploaded with the proposed system. To set up the previous
  options, modify the configuration file
  '$HOME/etc/cubicweb.d/toy_instance/all-in-one.conf' as follows:

  ::

      [WEB]

      # http server port number (default to 8080)
      port=8080

      # maximum length of HTTP request. Default to 100 MB.
      max-post-length=200MB

- **PIWS configuration:** In the instance configuration file located here
  '$HOME/etc/cubicweb.d/toy_instance/all-in-one.conf', set the following options
  to activate the login/logout:

  ::

      [PIWS]

      # Show or not the user status link on the website.
      show_user_status=yes

- **Upload configuration:** In the instance configuration file located here
  '$HOME/etc/cubicweb.d/toy_instance/all-in-one.conf', set the following options
  to activate the upload functionality:

  ::

      [RQL_UPLOAD]

      # base directory in which files are uploaded.
      upload_directory=/tmp/upload

      # JSON file describing the different upload entities.
      upload_structure_json=/home/me/cw/repositories/rql_upload/demo/demo.json

      [PIWS]

      # If true enable the upload, ie relax security on user and group entities.
      enable-upload=yes

      # A list of groups that will be able to upload data.
      authorized-upload-groups=uploaders

- **Twisted server (recommended):** In the instance configuration file located at
  '$HOME/etc/cubicweb.d/toy_instance/all-in-one.conf', set the following options
  to activate the Twisted sFTP server that will expose the content of each CW
  search:

  ::

      [RQL_DOWNLOAD]

      # specifies expiration delay of CWSearch (in days)
      default_expiration_delay=1

      # base directory in which files are stored (this option is given to the ftp
      # server and fuse processes)
      basedir=/tmp

      # if true cubicweb will start automatically sftp server (you need to set
      # properly the configuration file: see the documentation)
      start_sftp_server=yes

  A configuration file defining where the Twisted server is listening and which
  CW instance(s) is(are) concerned must be set at location
  '$HOME/.config/rsetftp':

  ::

      [rsetftp]

      cubicweb-instance=toy_instance
      port=9191
      private-key=/home/me/.ssh/id_rsa
      public-key=/home/me/.ssh/id_rsa.pub
      unix-username=me

  The authentication key can be generated with the 'ssh-keygen' command.

- **Fuse virtual folders:** In the instance configuration file located here
  '$HOME/etc/cubicweb.d/toy_instance/all-in-one.conf', set the following options
  to activate the Fuse virtual folders creation from CW searches:

  ::

      [RQL_DOWNLOAD]

      # specifies expiration delay of CWSearch (in days)
      default_expiration_delay=1

      # base directory in which files are stored (this option is given to the ftp
      # server and fuse processes)
      basedir=/tmp

      # base directory in which fuse will mount the user virtual directories
      mountdir=/home/me/tmp/fuse

      # if true cubicweb will start automatically a fuse mount per user when the user
      # has some CWSearch entities.
      start_user_fuse=yes

  In the 'mountdir', a specific hierarchy for each CW user (here 'me') has to be
  defined:

  ::

      - - me
          |
           - - toy_instance


Generating and importing a toy dataset
--------------------------------------

A script is proposed in the PIWS cube to create a toy dataset (use the proposed
default values):

::

    >>> python $HOME/cw/repositories/piws/piws/demo/generate_toy_dataset.py
    Enter a valid folder [default: /tmp]:
    Enter the number of subject for the demo [10, 50]: 10

The demonstration dataset has been generated in the '/tmp/demo' folder. This
latter can be imported in the previously created 'toy_instance' instance using
PIWS uniformed insertion procedure:

::

    >>> python $HOME/cw/repositories/piws/piws/demo/import_toy_dataset.py
    Enter the instance name [default: toy_instance]:
    Enter where are the demo data [default: /tmp/demo]:
    Enter the 'toy_instance' login [default: anon]:
    Enter the 'toy_instance' password [default: anon]:

The CW instance can be started and access via a web browser at the configured
port (here the default 8080 port):

::

    >>> cubicweb-ctl start toy_instance
    >>> firefox http://localhost:8080/


.. _install_vm:

Running a virtual machine
=========================

We propose an Oracle VirtualBox VDI image here_ with a PIWS DSS installed on
an Ubuntu 16.04LTS operating system.
This DSS highlights the collect and publication functionalities of the proposed
framework.
When the VM is started, a service start automatically the DSS.
Launch Firefox using the left launch bar to access the DSS login prompt.
Three users have been registered in the system with different access rights:

- login: user1 - password: user1:
    have an access to the timepoint V0 data and can upload some data to the
    system.

- login: user2 - password: user2:
    have an access to the timepoint V1 data.

- login: user3 - password: user3
    have an access to all the data.

The saved searches can be downloaded using FileZilla.
Launch FileZilla using the left launch bar.
On the FileZilla main frame, select the top left toolbar icon: 'Open the Site
Manager'.
Three sites have been registered to access the searches of each user.

.. _here: ftp://ftp.cea.fr/pub/unati/nsap/virtualbox/PIWS-DEMO.vdi



