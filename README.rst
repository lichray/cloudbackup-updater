===============================
Cloud Backup Agent Auto-Updater
===============================

Overview
========

Rackspace Cloud Backup Agent resides on a variety of different Linux
distributions, and may expand its support to FreeBSD in a near future.  Unlike
Windows (despite of Windows Store), these platforms all come with some form of
"package management" systems, so that user can upgrade the backup agents
through these systems.  However, such upgrade tasks involve user interactions,
while the practice we provide for Windows involves no user interactions, and
has been proven to be more user-friendly and still robust.  To delivery a more
consistent and comprehensive user-experience package, we launch the auto-
updater support on the Linux distributions.

In addition, due to the difference between the repository support of the
package management systems, the steps to install the agent from scratch on a
Linux box is even more complicated.  This is also a problem which the auto-
updater aims to solve.


Supported Platforms
===================

- Distributions

  1. Redhat flavors

     - Fedora 18, 19, 20
     - RHEL 5, 6
     - CentOS 5, 6
     - Scientific Linux 6

  2. Debian flavors

     - Debian 6, 7
     - Ubuntu 10, 12, 13

- Python versions

  The auto-updater runs on the default Python implementation on each
  distribution, and such an implementation is required to be py2x.  The
  following Python versions are supported:

  2.4, 2.5 [1]_, 2.6, 2.7

.. [1] However, no supported distribution comes with a default Python version
   of 2.5.


Installation
============

- Redhat flavors

- Debian flavors


Scenarios
=========


Usage
=====


Other Options
=============
