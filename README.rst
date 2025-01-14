PySpeos library
================
|pyansys| |GH-CI| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |GH-CI| image:: https://github.com/ansys-internal/pyspeos/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys-internal/pyspeos/actions/workflows/ci_cd.yml

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


Project overview
----------------
``PySpeos`` is a Python library that gathers functionalities and tools based on remote API of Ansys software `Speos <https://www.ansys.com/products/optics>`_ .

Installation
------------
Installation can be done using the published `package`_ or the repository `sources`_.

Package
~~~~~~~
.. warning:: Release is in process it might take some time till available. Until then, please use `Sources`_.

This repository is deployed as the Python packages `ansys-speos <https://pypi.org/project/ansys-speos>`_.
As usual, installation is done by running:

.. code::

   pip install ansys-speos

Sources
~~~~~~~
**Prerequisite**: user needs to have a GitHub account and a valid Personal Access Token
(see GitHub Settings/Developer settings/Personal access tokens/Generate new token).

Clone and install
^^^^^^^^^^^^^^^^^

.. code::

   git clone https://github.com/ansys/pyspeos.git
   cd pyspeos
   python -m pip install --upgrade pip
   pip install -U pip tox
   tox -e style
   pip install -e .


Functionalities
^^^^^^^^^^^^^^^
All sources are located in `<src/>`_ folder.

.. code:: python

   from ansys.speos.core.speos import Speos

   speos = Speos(host="localhost", port=50098)

Documentation
-------------

Documentation for the latest stable release of PySpeos is hosted at
`PySpeos Documentation <https://speos.docs.pyansys.com>`_.

Documentation is stored in `<doc>`_ folder and generated using `Sphinx`_.
To build it manually :

.. code::

   pip install -U pip tox
   pip install .[doc]
   tox -e doc && your_browser_name .tox/doc_out/index.html


.. note::

      Include a link to the full sphinx documentation. For example `PyAnsys`_

Testing
-------
Tests and assets are in `<tests>`_ and `<tests/assets>`_ folder.
Running PySpeos tests requires a running SpeosRPC server.
A configuration file allows to choose between a local server and a Docker server (by default).

Test configuration file
~~~~~~~~~~~~~~~~~~~~~~~
The configuration file `<tests/local_config.json>`_ located in tests folder contains several parameters that can be changed according to your needs, for example:

 - **SpeosServerOnDocker** (Boolean): Speos server launched in a Docker container.
 - **SpeosServerPort** (integer): Port used by Speos server for HTTP transfer.

Start server
~~~~~~~~~~~~
First option is to use the Docker container of `SpeosRPC_Server <https://github.com/orgs/ansys-internal/packages/container/package/pyspeos%2Fspeos-rpc>`_.
It can be started using `<docker-compose.yml>`_ (if needed, please provide GitHub username and PAT as password).
Since the Docker image contains no license server, you will need to enter your license server IP address in the `LICENSE_SERVER` environment variable.
Then, you can launch SpeosRPC server with:

.. code::

   export LICENSE_SERVER=1055@XXX.XXX.XXX.XXX

   docker login ghcr.io/ansys-internal
   docker-compose up -d

On the other hand, SpeosRPC server can be started locally.
For Windows:

.. code::

    %AWP_ROOT251%\Optical Products\SPEOS_RPC\SpeosRPC_Server.exe

For Linux:

.. code::

    $AWP_ROOT251\OpticalProducts\SPEOS_RPC\SpeosRPC_Server.x

And test configuration file `<tests/local_config.json>`_ must be updated to use local server:

.. code-block:: json

   {
      "SpeosServerOnDocker": false,
      "SpeosContainerName" : "speos-rpc",
      "SpeosServerPort": 50098
   }

Launch unit tests
~~~~~~~~~~~~~~~~~

.. code::

   pip install .[tests]
   pytest -vx

Use jupyter notebook
~~~~~~~~~~~~~~~~~~~~

.. code::

   pip install .[jupyter]
   jupyter notebook

jupyter notebook can be downloaded from the documentations example section

License
-------
`PySpeos`_ is licensed under the MIT license.
The full license can be found in the root directory of the repository, see `<LICENSE>`_.

.. LINKS AND REFERENCES
.. _PySpeos: https://github.com/ansys-internal/pyspeos
.. _PyAnsys: https://docs.pyansys.com
.. _Sphinx: https://www.sphinx-doc.org/en/master/
