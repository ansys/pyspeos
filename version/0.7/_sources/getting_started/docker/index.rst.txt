.. _ref_docker:

Docker containers
=================

What is Docker?
---------------

Docker is an open platform for developing, shipping, and running apps in a
containerized way.

Containers are standard units of software that package the code and all its dependencies
so that the app runs quickly and reliably across different computing environments.

Ensure that Docker is installed on the machine where the Speos service is running. Otherwise,
see `Install Docker Engine <https://docs.docker.com/engine/install/>`_ in the Docker documentation.

Select your Docker container
----------------------------

Currently, the Speos service backend is delivered as a **Linux** Docker container.

Select the kind of Docker container you want to build:

.. grid:: 2
   :gutter: 3 3 4 4

   .. grid-item-card:: Linux Docker container
      :link: linux_container
      :link-type: doc

      Build a Windows Docker container for the Speos service
      and use it from PySpeos.

..   .. grid-item-card:: Windows Docker container
..            :link: windows_container
..            :link-type: doc

..            Build a Windows Docker container for the Speos service
..            and use it from PySpeos.

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started

.. toctree::
   :hidden:
   :maxdepth: 2

   linux_container
..   windows_container