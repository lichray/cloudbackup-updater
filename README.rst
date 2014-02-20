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

  1. Download the latest rpm package;
  2. ``sudo yum install cloudbackup-updater-<version>-2.noarch.rpm``

- Debian flavors

  1. Download the latest deb package;
  2. ``sudo dpkg -i cloudbackup-updater_<version>-2_all.deb``


Behaviors
=========

This section describes the expected behavior of the auto-updater after the
installation under different scenarios.  Scenarios are the valid combinations
of all the conditions.  The exact behaviors are different with different
package management systems, but the logic are the same.

Conditions:

1. The agent repository is correctly configured.

2. An agent is installed.

3. The installed agent is updated.  Requires 2).

4. The installed agent is running.  Requires 2).

5. The running agent is performing a backup, a restore, or a cleanup.
   Requires 4).

Behaviors:

If 1) is not true, then agent repository is configured.

Debian: `/etc/apt/sources.list.d/driveclient.list` is created and the command line output of ``sudo apt-key list`` contains the agent repo key.

Redhat: `/etc/yum.repos.d/drivesrvr.repo` is created.

*[Note:* A better approach to verify the existence of the repositories is
to remove the installed agent then install it:

Debian: ``sudo apt-get remove driveclient``, ``sudo apt-get install driveclient``

Redhat: ``sudo yum remove driveclient``, ``sudo yum install driveclient``

Since there is no local package involved, the installation sources must be the
repositories.

*-- end note]*

If 2) is not true, then the newest agent is installed from the repository.

*[Note:* The installation or upgrade of the agent does not block the
installation of the auto-updater itself, so user might experience that the
agent is installed or upgraded **shortly after** the auto-updater being
installed.  *-- end note]*

Debian: ``sudo dpkg-query -W driveclient`` shows the installed version.

Redhat: ``sudo yum info driveclient`` shows the installed version.

If 3) is true, do nothing.

Otherwise, if 4) is not true, the installed agent is updated to the latest
version from the repository.

Use the command showing the installed version to compare the agent version
before and after the installation of the auto-updater.

*[Note:* To create a situation of "an old version of the agent is installed
without a configured agent repository", download an old deb or rpm agent
package and install them.  To create a situation of "an old version of the
agent is installed from the repository", you can downgrade the agent:

Debian: ``sudo apt-get install driveclient=<an old version>`` (Does not work unless you have the old version installed before.  Use the usual way to get this situation (i.e., install a local package).

Redhat: ``sudo yum downgrade driveclient``

*-- end note]*

Otherwise, if 5) is not true, then stop the agent daemon, upgrade the agent,
and start the new agent daemon.

ALL: If the logging level is set to `verbose` (already set in init script. See `Other Options`_ for details), the detailed steps will be logged (defaults to `/var/log/cloudbackup-updater.log`).  System log (`/var/log/messages`) may also contains the information about how the agent daemon is stopped and started, but the info text various on different system.

Otherwise, the auto-updater waits for the agent to finish the current backup,
restore, or cleanup task, stop the agent daemon, upgrade the agent, and start
the new agent daemon.

ALL: The agent holds a lock file, `/var/cache/driveclient/backup-running.lock`, when performing these tasks, so do the auto-updater, when performing **agent upgrade**.


Usage
=====

The auto-updater can be used in two ways:

1. As a command line tool.  Execute ``cloudbackup-updater`` from the command
   line without the **-d** option, then ``driveclient`` is installed or updated
   to the latest version.

2. As a daemon.  Execute ``cloudbackup-updater -d``, then ``driveclient`` is
   installed or updated to the latest version.  The auto-updater checks for the
   new agent version (as specified in `release/windows/version.txt` under the
   remote agent repository) every hour after it starts and keep the agent
   installed and updated.  The interval of the checking can be changed.  See
   `Other Options`_.

Only one ``cloudbackup-updater`` can run at the same time.  The attempt to
start a second daemon will fail with an error.

The command line ``cloudbackup-updater`` can be safely used when the daemon is
running.  One of them will perform the actual agent upgrade.  User can use the
command line to update the agent immediately without waiting for the next
checking.


Other Options
=============
