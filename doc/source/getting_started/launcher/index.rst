.. _ref_creating_local_service:

Launch a service
================

To launch a Speos service you have several options:

* Use python launch method to start it locally
* Use Bash to start it yourself
* Rely on Ansys PIM to start a service

Python Launcher
---------------

to launch a local Speos RPC server instance use:

.. code:: python

    from ansys.speos.core.launcher import launch_local_speos_rpc_server

    speos = launch_local_speos_rpc_server(version='251')

You receive a ``Speos`` object in return that you then use as a Speos session.
For more information you can look at the API Reference.

.. button-ref:: ../../api/ansys/speos/core/launcher/index
    :ref-type: doc
    :color: primary
    :shadow:


The session can be ended via the object ``Speos`` like this:

.. code:: python

    speos.close()

Launch a local service by command line
--------------------------------------

To launch the service you need to use the following commands:

.. tab-set::

    .. tab-item:: Windows

        .. code-block:: bash

            "%AWP_ROOT251%\Optical Products\SPEOS_RPC\SpeosRPC_Server.exe"

    .. tab-item:: Linux

        .. code-block:: bash

            $AWP_ROOT251/OpticalProducts/SPEOS_RPC/SpeosRPC_Server.x


Use PySpeos launcher with PIM
-----------------------------

If a remote server is running Ansys Release 2025 R1 or later and is also running PIM (Product
Instance Manager), you can use PIM to start a SpeosRPC server Session that PySpeos
can connect to.

A usage example of the remote service can be accessed via AnsysLAB.

.. warning::

   **This option is only available for Ansys employees.**

   Only Ansys employees with credentials to the Artifact Repository Browser
   can download ZIP files for PIM.

To launch a remote Speos service:

.. code:: python

    from ansys.speos.core import launcher

    speos = launcher.launch_speos("251")

The preceding commands launch a remote Speos service (version 2025 R1).
You receive a ``Speos`` object in return that you then use as a Speos session.

The session can be ended via the object ``Speos`` like this:

.. code:: python

    speos.close()

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started