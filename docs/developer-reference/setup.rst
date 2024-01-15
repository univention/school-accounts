.. Copyright (C) 2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

*****
Setup
*****

Reproducible environment with Vagrant
=====================================

This project provides a Vagrantfile to create reproducible development environments with
`Vagrant <https://developer.hashicorp.com/vagrant/>`_. Installation instructions can be found
`here <https://developer.hashicorp.com/vagrant/docs/installation>`_. On a debian based system, Vagrant and kvm/libvirt
can be installed with:

.. code-block:: bash

    sudo apt-get install -y vagrant qemu-kvm libvirt-clients libvirt-daemon-system bridge-utils virtinst libvirt-daemon

.. note::

   More information about the installation and configuration of libvirt on a Ubuntu system can be found at the
   `Ubuntu libvirt documentation <https://ubuntu.com/server/docs/virtualization-libvirt>`_.

The Vagrant box used in the Vagrantfile supports both `libvirt <https://github.com/vagrant-libvirt/vagrant-libvirt>`_ and
`virtualbox <https://developer.hashicorp.com/vagrant/docs/providers/virtualbox>`_ as providers.

After installing Vagrant and a suitable provider on your system, you can create your environment with ``vagrant up``.

The Vagrantfile allows for some configuration via environmental variables:

.. envvar:: VAGRANT_PROVISION_SSH_KEY

If set (any value will do), your ssh key is copied from the host to the guest machine.

.. envvar:: VAGRANT_GIT_SSH_PRIVATE_KEY_SOURCE

Set this variable to your private ssh key, if it is not located at ``$HOME/.ssh/id_rsa``.

.. envvar:: VAGRANT_GIT_SSH_PRIVATE_KEY_DESTINATION

Set this variable to the path, the ssh key should be copied to in the guest.
If unset, the key will be copied to the same location within the guest, as specified in the source variable. This
might be necessary to accommodate some specific ssh config.

.. envvar:: VAGRANT_PROVISION_SSH_CONFIG

If set (any value will do), your ssh config, assumed to be located at ``$HOME/.ssh/config``, is copied
from the host to the guest.

.. envvar:: VAGRANT_PROVISION_GIT_CONFIG

If set (any value will do), your global git config, assumed to be located at ``$HOME/.gitconfig``,
is copied from the host to the guest.

.. envvar:: VAGRANT_NUM_CPU_CORES

This defines the number of CPU cores you want to allocate for the VM. It defaults to 2

.. envvar:: VAGRANT_AMOUNT_RAM

This defines the amount of RAM to allocate for the VM. It defaults to 2048

In addition, you can create the script ``vagrant_custom_provisioning.sh`` in the repositories root directory to run
custom code within the guest during the provisioning. This script runs as the ``vagrant`` user within the guest.

With all that you might set up your development environment like this:

.. code-block:: bash

   VAGRANT_PROVISION_SSH_KEY=1 VAGRANT_GIT_SSH_PRIVATE_KEY_SOURCE='~/.ssh/work' VAGRANT_PROVISION_GIT_CONFIG=1 VAGRANT_PROVISION_SSH_CONFIG=1 vagrant up

.. note::

   The environment variables do not have to be set for consecutive calls to ``vagrant up``. It is only necessary
   for provisioning during the first startup.

.. note::

   You might have to provide your password during the startup of the vagrant box. This is due to the NFS share that
   is created to pass through the project directory to the virtual machine.

.. warning::

   Vagrant uses ssh keys during the ``vagrant up`` procedure. It is possible that the following problem occurs:

   .. code-block:: bash

      $ vagrant up
      Bringing machine 'default' up with 'libvirt' provider...
      ==> default: Checking if box 'debian/bookworm64' version '12.20231211.1' is up to date...
      ==> default: Starting domain.
      ==> default: Waiting for domain to get an IP address...
      ==> default: Waiting for machine to boot. This may take a few minutes...
          default: SSH address: 192.168.121.87:22
          default: SSH username: vagrant
          default: SSH auth method: private key
          default: Warning: Authentication failure. Retrying...
          default: Warning: Authentication failure. Retrying...
      ^C==> default: Waiting for cleanup before exiting...

   It seems there can be some conflict with a running ssh agent. By clearing the agent with ``ssh-add -D`` the
   problem could be solved reliably.

Using the development environment
=================================

You can now enter your development environment with ``vagrant ssh``. If you want to shut down the development VM, use
``vagrant halt`` and to completely purge it, use ``vagrant destroy``.

The vagrant environment has the following features:

* Python and node are installed in the correct version
* git is installed
* pre-commit is installed in the correct version
* There is a python virtualenv in ``~/venv``
* The repository is mounted on the path ``/vagrant``
* The VM is a regular debian bookworm that can be further modified


.. note::

   Most instructions are expected to be executed within the vagrant development environment. Others on the host machine
   directly. Commands will be marked with either :guilabel:`VAGRANT` or :guilabel:`HOST` to specify where the commands
   should be executed.

   If you do not want to use Vagrant for development, you have to make sure that all tools are available on your
   development machine in the correct versions. Please derive the necessary steps from the ``Vagrantfile``.
