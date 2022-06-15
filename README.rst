PyOptics Library
########################
|pyansys| |GH-CI|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |GH-CI| image:: https://github.com/pyansys/pyoptics/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/pyansys/pyoptics/actions/workflows/ci_cd.yml

Project Overview
----------------
``PyOptics`` is a Python library that gathers functionalities and tools based on remote API of Ansys software `Speos <https://www.ansys.com/fr-fr/products/optics-vr>`_, `Zemax <https://www.zemax.com/>`_ and `Lumerical <https://www.lumerical.com/>`_.

Installation
------------
Installation can be done using the published `package`_ or the repository `sources`_. 

Package
~~~~~~~
.. warning:: Not currently available, work in progress... Please use `Sources`_ 

This repository is deployed as the Python packages `ansys-pyoptics <...>`_.
As usual, installation is done by running 

.. code:: 

   pip install ansys-pyoptics

Sources
~~~~~~~
**Prerequisite**: User needs to have a GitHub account and a valid Personnal Access Token 
(see GitHub Settings/Developer settings/Personnal access tokens/Generate new token).

Clone and install
^^^^^^^^^^^^^^^^^

.. code::

   git clone https://<PAT>@github.com/pyansys/pyoptics.git
   cd pyoptics
   pip install -r requirements/requirements_style.txt
   pre-commit install
   pip install -e .


Functionalities
^^^^^^^^^^^^^^^
All sources are located in `<./ansys>`_ folder. 

.. code:: python

   from ansys.pyoptics import speos
   stub = speos.get_stub_insecure_channel()
   stub...

Documentation
-------------
Documentation is stored in `<./doc>`_ folder and generated using `Sphinx <https://www.sphinx-doc.org/en/master/>`_.
To build it manually, just run

.. code::

   pip install -r requirements/requirements_docs.txt
   doc\make.bat singlehtml
   

.. note:: 
   
      Include a link to the full sphinx documentation.  For example `PyAnsys <https://docs.pyansys.com/>`_

Testing
-------
Tests and assets are in `<./tests>`_ and `<./tests/assets>`_ folder. 
Running PyOptics tests requires a running SpeosRPC server.
A configuration file allows to choose between a local server and a Docker server (by default).

Test configuration file
~~~~~~~~~~~~~~~~~~~~~~~
The configuration file `<tests/local_config.json>`_ located in tests folder contains several parameters that can be changed according to your needs, for example:

 - **SpeosServerOnDocker** (boolean): Speos server launched in a docker container
 - **SpeosServerPort** (integer): Port used by Speos server for HTTP transfert 

Start server
~~~~~~~~~~~~
First options is to use the Docker container of `SpeosRPC_Server <https://github.com/orgs/pyansys/packages/container/package/pyoptics%2Fspeos-rpc>`_.
It can be started using `<docker-compose.yml>`_ (if needed, please provide GitHub username and PAT as password) :

.. code::

   docker login ghcr.io/pyansys/pyoptics
   docker-compose up -d

On the other hand, SpeosRPC server can be started locally.
The pipeline artifact can be found in La Farlède shared folders.

.. code::

   \\win.ansys.com\eu\LaFarlede\Product Artifacts\SpeosRPC\refs\heads\main

And test configuration file `<tests/local_config.json>`_ must be updated to use local server:

.. code-block:: json
   
   {
      "SpeosServerOnDocker": false,
      "SpeosContainerName" : "pyoptics_speos-rpc",
      "SpeosServerPort": 50051
   }

Launch unit tests
~~~~~~~~~~~~~~~~~

.. code::

   pip install -r requirements/requirements_test.txt
   pytest -vx


License
-------
`PyOptics <https://github.com/pyansys/pyoptics>`_ is licensed under the MIT license.
The full license can be found in the root directory of the repository, see `<LICENSE>`_.
