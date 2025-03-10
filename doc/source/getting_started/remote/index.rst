.. _ref_creating_remote_service:

Launch a remote service
=======================

If a remote server is running Ansys Release 2025 R1 or later and is also running PIM (Product
Instance Manager), you can use PIM to start a SpeosRPC server Session that PySpeos
can connect to.

A usage example of the remote service can be accessed via AnsysLAB.

.. warning::

   **This option is only available for Ansys employees.**

   Only Ansys employees with credentials to the Artifact Repository Browser
   can download ZIP files for PIM.


Use PySpeos launcher
--------------------

To launch a remote Speos service:

.. code:: python

    from ansys.speos.core import launcher

    speos = launcher.launch_speos("251")

The preceding commands launch a remote Speos service (version 2025 R1).
You receive a ``Speos`` object in return that you then use as a Speos session.


End the session
---------------

The session can be ended via the object ``SpeosClient`` like this:

.. code:: python

    speos.client.close()

This closes the channel to the Speos service and also shuts down the remote Speos service.

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started