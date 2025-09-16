.. _ref_getting_started:

Getting started
###############

``PySpeos`` is a Python client library that gathers functionalities and tools based on
remote API of Ansys software `Speos <https://www.ansys.com/products/optics/ansys-speos>`_ .

Installation
============
You can use `pip <https://pypi.org/project/pip/>`_ to install PySpeos.

.. code:: bash

    pip install ansys-speos-core

Available modes
===============

This client library works with a Speos service backend. There are several ways of
running this backend, although the preferred and high-performance mode is using Docker
containers. Select the option that best suits your needs.

.. grid:: 2
   :gutter: 3 3 4 4

   .. grid-item-card:: Docker containers
            :link: docker/index
            :link-type: doc

            Launch the Speos service as a Docker container
            and connect to it from PySpeos.

   .. grid-item-card:: Launch a service
            :link: launcher/index
            :link-type: doc

            Launch the Speos service locally or remotely on a Computer
            and connect to it from PySpeos.

   .. grid-item-card:: Use an existing service
            :link: existing/index
            :link-type: doc

            Connect to an existing Speos service locally or remotely.

Development installation
========================

In case you want to support the development of PySpeos, install the repository
in development mode. For more information, refer to the `README`_.

.. _ref_security_consideration:

Security considerations
=======================

This section provides information on security considerations for the use
of PySpeos. It is important to understand the capabilities which PySpeos
provides, especially when using it to build applications or scripts that
accept untrusted input.

If a function displays a warning that redirects to this page, it indicates
that the function may expose security risks when used improperly.
In such cases, it is essential to pay close attention to:

- **Function arguments**: Ensure that arguments passed to the function are
  properly validated and do not contain untrusted content such as arbitrary
  file paths, shell commands, or serialized data.
- **Environment variables**: Be cautious of environment variables that can
  influence the behavior of the function, particularly if they are user-defined
  or inherited from an untrusted execution context.

Always validate external input, avoid executing arbitrary commands or code,
and follow the principle of least privilege when developing with PySpeos.

Launching local Speos RPC server
--------------------------------

The :py:func:`.local_speos_rpc_server` function can be used to launch Speos RPC
server locally. The executable which is launched is configured with the function
parameters and environment variables. This may allow an attacker to launch
arbitrary executables on the system. When exposing the launch function to
untrusted users, it is important to validate that the executable path,
environment variables (for example ``AWP_ROOT``) are safe.
Otherwise, hard-code them in the app.

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
.. _README: https://github.com/ansys/pyspeos