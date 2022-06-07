PyOptics Library
########################

Project Overview
----------------
``PyOptics`` is a library that gathers functionalities and tools for ``Speos``, ``Zemax`` and ``Lumerical``.

On ``Speos`` side, this is a way to use ``exposed gRPC APIs`` and add some functionalities or post processing in python.

Installation
------------

Install ``PyOptics Library`` with:

.. code::

   pip install ansys-pyoptics

Alternatively, clone and install in development mode with:

.. code::

   git clone https://github.com/pyansys/pyoptics.git
   cd pyoptics
   pip install -r requirements_style.txt
   pre-commit install
   pip install -e .


Documentation
-------------
Include a link to the full sphinx documentation.  For example `PyAnsys <https://docs.pyansys.com/>`_


Usage
-----
It's best to provide a sample code or even a figure demonstrating the usage of your library.  For example:

.. code:: python

   >>> from ansys.<product/service> import <library>
   >>> my_object.<library>()
   >>> my_object.foo()
   'bar'


Testing
-------
``Input data`` for the tests are stored in ``tests/assets`` folder

Configuration file
~~~~~~~~~~~~~~~~~~
The configuration file ``local_config.json`` located in tests folder contains several parameters that can be changed according to your needs, for example:
 * SpeosServerOnDocker - boolean - Speos Server launched in a docker container
 * SpeosServerPort - integer - to modify the port where you send requests to Speos Server

Start gRPC Servers
~~~~~~~~~~~~~~~~~~
Create and launch the ``docker container`` (containing SpeosRPC_Server) with:

.. code::

   cd pyoptics
   docker-compose up -d

In case you are launching the SpeosRPC_Server by yourself, modify in the local_config.json:
 * SpeosServerOnDocker to false
 * SpeosServerPort to your current configuration (ie the port where the SpeosRPC_Server is listening)

Launch unit tests
~~~~~~~~~~~~~~~~~

.. code::

   cd pyoptics
   pip install -r requirements_test.txt
   pytest -vx


License
-------
``PyOptics`` is licensed under the MIT license.

The full license can be found in the root directory of the repository.
