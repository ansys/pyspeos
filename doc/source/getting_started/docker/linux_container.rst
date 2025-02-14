.. _ref_linux_docker:

Linux Docker container
======================

.. contents::
   :backlinks: none

.. _ref_running_linux_containers:

Docker for Linux containers
---------------------------

To run the Linux Docker container for the Speos service, you need to install Docker.
You can choose one of the following possibilities:

* Install `Docker Engine <https://docs.docker.com/engine/install/>`_ (only for Linux environment).
  In this case you, can interact with docker by command line.

* Install `Docker Desktop <https://docs.docker.com/desktop/install/windows-install/>`_. (for all environments).
  In this case you, can have a GUI and can also interact with docker by command line.


Install the Speos service image
-------------------------------

The Speos service image can be downloaded from the GitHub Container Registry

.. note::

   This option is only available for users who are members of the ansys-internal organization.

Once Docker is installed on your machine, follow these steps to download the Linux Docker
container for the Speos service and install this image.

#. Use a GitHub personal access token with permission for reading packages to authorize Docker
   to access this repository. For more information, see `Managing your personal access tokens
   <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`_
   in the GitHub documentation.

#. Save the token to a file with this command:

   .. code-block:: bash

       echo XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX > GH_TOKEN.txt

#. Authorize Docker to access the repository and run the commands for your OS. To see these commands, click the tab corresponding to your OS.

   .. tab-set::

       .. tab-item:: Linux/Mac

           .. code-block:: bash

               export GH_USERNAME=<my-github-username>
               cat GH_TOKEN.txt | docker login ghcr.io -u $GH_USERNAME --password-stdin

       .. tab-item:: Powershell

           .. code-block:: pwsh

               $env:GH_USERNAME=<my-github-username>
               cat GH_TOKEN.txt | docker login ghcr.io -u $env:GH_USERNAME --password-stdin

       .. tab-item:: Windows CMD

           .. code-block:: bash

               SET GH_USERNAME=<my-github-username>
               type GH_TOKEN.txt | docker login ghcr.io -u %GH_USERNAME% --password-stdin


.. START - Include the common text for launching the service from a Docker container

.. include:: common_docker.rst

.. END - Include the common text for launching the service from a Docker container

.. button-ref:: index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Docker containers

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started