.. _ref_creating_remote_service:

Launch a remote service
=======================

An example of usage of the remote service can be via AnsysLAB.

PIM (Product Instance Manager) is required to launch the remote Speos service.
PIM is configured in AnsysLAB.

Use PySpeos launcher
--------------------

To launch a remote Speos service:

.. code:: python

    from ansys.speos.core import launcher

    speos = launcher.launch_speos("242")

The preceding commands launch a remote Speos service (version 24.2).
You receive a ``Speos`` object back that you then use as a Speos session.


End the session
---------------

The session can be ended via the object ``SpeosClient`` like this:

.. code:: python

    speos.client.close()

This closes the channel to the Speos service and also shut down the remote Speos service.

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started