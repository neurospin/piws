
.. _install_guid:

=========================
Installing `Neurospinweb`
=========================

This tutorial will walk you through the process of installing Neurospinweb:

    * **neurospinweb**: a cube that can only be instanciated
      if `cubicweb is installed <https://docs.cubicweb.org/admin/setup>`_.


.. _install_neurospinweb:

Installing neurospinweb
=======================

Installing the current version
------------------------------

Install from *github*
~~~~~~~~~~~~~~~~~~~~~

**Clone the project**

>>> cd $CLONEDIR
>>> git clone https://github.com/neurospin/neurospinweb.git

**Update your CW_CUBES_PATH**

>>> export CW_CUBES_PATH=$CLONE_DIR/neurospinweb:$CW_CUBES_PATH

Make sure the cube is in CubicWeb's path
----------------------------------------

>>> cubicweb-ctl list

Create an instance of the cube
------------------------------

>>> cubicweb-ctl create neurospinweb toy_instance

You can then run the instance in debug mode:

>>> cubicweb-ctl start -D toy_instance

The last line of the prompt will indicate which url the 
instance can be reached by:

>>> (cubicweb.twisted) INFO: instance started on http://url:port/

Change configuration
--------------------

The configuration file is stored on your system:

>>> ...etc/cubicweb.d/toy_instance/all-in-one.conf
