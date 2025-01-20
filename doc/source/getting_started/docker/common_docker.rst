Launch the Speos service
------------------------

Manually launch the Speos service.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

The Speos service requires this mandatory environment variable for its use:

* ``ANSYSLMD_LICENSE_FILE``: License server (port and IP address or DNS) that the Speos service is to
  connect to. For example, ``1055@127.0.0.1``.

You can also specify other optional environment variables:

* ``SPEOS_LOG_LEVEL``: Sets the Speos service logging level. The default is ``2``, in which case
  the logging level is ``INFO``.

Here are some terms to keep in mind:

* **host**: Machine that hosts the Speos service. It is typically on ``localhost``, but if
  you are deploying the service on a remote machine, you must pass in this host machine's
  IP address when connecting. By default, PySpeos assumes it is on ``localhost``.

* **port**: Port that exposes the Speos service on the host machine. Its
  value is assumed to be ``50098``, but users can deploy the service on preferred ports.


Docker compose for Speos service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This method allows you to start the Speos service based on predefined environment variables and properties. Afterwards,
see the next section to understand how to connect to this service instance from PySpeos.

.. tab-set::

    .. tab-item:: Linux/Mac

        .. code-block:: bash

            export LICENSE_SERVER=1055@XXX.XXX.XXX.XXX
            docker-compose up -d

    .. tab-item:: Powershell

        .. code-block:: pwsh

            $env:LICENSE_SERVER=1055@XXX.XXX.XXX.XXX
            docker-compose up -d

    .. tab-item:: Windows CMD

        .. code-block:: bash

            set LICENSE_SERVER=1055@XXX.XXX.XXX.XXX
            docker-compose up -d

Connect to the Speos service
----------------------------

After the Speos service is launched, connect to it with these commands:

.. code:: python

   from ansys.speos.core import Speos

   speos = Speos()

By default, the ``Speos`` instance connects to ``127.0.0.1`` (``"localhost"``) on
port ``50098``.

You can change this by modifying the ``host`` and ``port``
parameters of the ``Speos`` object, but note that you must also modify
your ``docker run`` command by changing the ``<HOST-PORT>-50098`` argument.

The following tabs show the commands that set the environment variables and ``Speos``
function.

.. code:: python

    from ansys.speos.core import Speos

    speos = Speos(host="127.0.0.1", port=50098)