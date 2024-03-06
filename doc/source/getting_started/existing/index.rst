.. _ref_existing_service:

Use an existing service
=======================

If a Speos service is already running, PySpeos can be used to connect to it.

Information to know for a successful connection are the host and also the port.

Establish the connection
------------------------

From Python, establish a connection to the existing Speos service by creating a ``Speos`` object:

.. code:: python

    from ansys.speos.core import Speos

    speos = Speos(host="127.0.0.1", port=50051)

If no error messages are received, your connection is established successfully.

Verify the connection
---------------------
If you want to verify that the connection is successful, request the status of the client
connection inside your ``Speos`` object:

.. code:: pycon

   >>> speos.client
   Ansys Speos client (...)
   Target:     localhost:50051
   Connection: Healthy

.. button-ref:: ../index
    :ref-type: doc
    :color: primary
    :shadow:
    :expand:

    Go to Getting started