.. _ref_getting_started:

Getting started
###############

``PySpeos`` is a Python client library that gathers functionalities and tools based on
remote API of ansys software `Speos <https://www.ansys.com/fr-fr/products/optics-vr>`_ .

Installation
============
You can use `pip <https://pypi.org/project/pip/>`_ to install PySpeos.

.. code:: bash

    pip install ansys-speos-core

Available modes
===============

This client library works with a Speos service backend. There are several ways of
running this backend, although the preferred and high-performance mode is using Docker
containers. Select the option that suits your needs best.

.. grid:: 2
   :gutter: 3 3 4 4

   .. grid-item-card:: Docker containers
            :link: docker/index
            :link-type: doc

            Launch the Speos service as a Docker container
            and connect to it from PySpeos.

   .. grid-item-card:: Local service
            :link: local/index
            :link-type: doc

            Launch the Speos service locally on your machine
            and connect to it from PySpeos.

   .. grid-item-card:: Remote service
            :link: remote/index
            :link-type: doc

            Launch the Speos service on a remote machine and
            connect to it using PIM (Product Instance Manager).

   .. grid-item-card:: Connect to an existing service
            :link: existing/index
            :link-type: doc

            Connect to an existing Speos service locally or remotely.

Development installation
========================

In case you want to support the development of PySpeos, install the repository
in development mode. For more information, refer to the `README`_.

Frequently asked questions
==========================

Any questions? Refer to :ref:`Q&A <ref_faq>` before submitting an issue.

.. toctree::
   :hidden:
   :maxdepth: 2

   docker/index
   local/index
   remote/index
   existing/index
   faq


.. Links
.. _README: https://github.com/ansys-internal/pyspeos