Launch the Speos service
------------------------

Manually launch the Speos service.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

The Speos service requires this mandatory environment variable to function properly:

* ``ANSYSLMD_LICENSE_FILE``: License server (port and IP address or DNS) the Speos service connects to.
  For example, ``1055@127.0.0.1``.

You can also specify other optional environment variables:

* ``SPEOS_LOG_LEVEL``: Sets the Speos service logging level. The default is ``2``, in which case
  the logging level is ``INFO``.

Here are some terms to keep in mind:

* **host**: Machine that hosts the Speos service. It is typically on ``localhost``.
  But if you are deploying the service on a remote machine, then the machine's IP address is expected.
  By default, PySpeos assumes it is on ``localhost``.

* **port**: Port that exposes the Speos service on the host machine. Its
  value is assumed to be ``50098``, but users can deploy the service on preferred ports.


Docker for Speos service
^^^^^^^^^^^^^^^^^^^^^^^^

This method allows you to start the Speos service based on predefined environment variables and properties.
Afterwards, see the next section to understand how to connect to this service instance from PySpeos.

The following snippet shows how to run Speos service 2025.2.
To use another product version, please modify the image label from `252` to the corresponding product version.

.. tab-set::

    .. tab-item:: Linux/Mac

        .. code-block:: bash

            export LICENSE_SERVER="1055@XXX.XXX.XXX.XXX"
            docker run --detach --name speos-rpc -p 127.0.0.1:50098:50098 -e ANSYSLMD_LICENSE_FILE=$LICENSE_SERVER --entrypoint /app/SpeosRPC_Server.x ghcr.io/ansys/speos-rpc:252 --transport_insecure --host 0.0.0.0

    .. tab-item:: Powershell

        .. code-block:: pwsh

            $env:LICENSE_SERVER="1055@XXX.XXX.XXX.XXX"
            docker run --detach --name speos-rpc -p 127.0.0.1:50098:50098 -e ANSYSLMD_LICENSE_FILE=$env:LICENSE_SERVER --entrypoint /app/SpeosRPC_Server.x ghcr.io/ansys/speos-rpc:252 --transport_insecure --host 0.0.0.0

    .. tab-item:: Windows CMD

        .. code-block:: bash

            set LICENSE_SERVER="1055@XXX.XXX.XXX.XXX"
            docker run --detach --name speos-rpc -p 127.0.0.1:50098:50098 -e ANSYSLMD_LICENSE_FILE=%LICENSE_SERVER% --entrypoint /app/SpeosRPC_Server.x ghcr.io/ansys/speos-rpc:252 --transport_insecure --host 0.0.0.0

Connect to the Speos service
----------------------------

After the Speos service is launched, connect to it with these commands:

.. code-block:: python

   from ansys.speos.core import Speos

   speos = Speos()

By default, the ``Speos`` instance connects to ``"localhost"`` on
port ``50098``.

You can change this by modifying the ``host`` and ``port``
parameters of ``default_docker_channel``, but note that you must also modify
your ``docker run`` command by changing the ``<HOST-PORT>:50098`` argument.

The following tabs show the commands that set the ``host`` and ``port``
parameters of ``default_docker_channel``.

.. code-block:: python

    from ansys.speos.core import Speos, default_docker_channel
    speos = Speos(channel = default_docker_channel(host="127.0.0.1", port=50098))

Use secure transport channel
----------------------------

Whether with a local server or a Docker image, you can configure the transport mode to use Mutual TLS, Unix Domain Socket, Windows Named User Authentication or Insecure.
Of course, server and client must be aligned on the transport mode.
On server side, transport is defined by command line option:

* ``--transport_tls SERVER_KEY,SERVER_CERTIFICATE,SERVER_CLIENT_CA``
gRPC transport, using TLS encryption, must provide paths to the server's private key, certificate and server/client Certificate Authority files.

* ``--transport_uds UDSPATH(=C:\tmp\speosrpc_sock_50098)``
Unix Domain Socket transport for local server/client communications, can pass an optional path for the socket.

* ``--transport_wnua``
Run the server with Windows named user authentication, only available on Windows and set by default if no transport selected, host must be localhost.

* ``--transport_insecure``
Run the server in gRPC insecure mode.

On client side, please use ``ansys.speos.core.kernel.grpc.transport_options`` to create the grpc channel with same mode than the server.
Here is an example with WNUA transport mode:

.. code-block:: python

  import grpc
  from ansys.speos.core import Speos
  from ansys.speos.core.kernel.grpc.transport_options import TransportOptions, WNUAOptions
  transport = TransportOptions(mode=TransportMode.WNUA, options=WNUAOptions(host="127.0.0.1", port=50098))
  channel = transport.create_channel(grpc_options=[("grpc.max_receive_message_length", message_size)]
  speos = Speos(channel=channel)


