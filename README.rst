PySpeos library
================
|pyansys| |python| |pypi| |codecov| |GH-CI| |MIT| |ruff|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/ansys-speos-core?logo=pypi
   :target: https://pypi.org/project/ansys-speos-core/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-speos-core.svg?logo=python&logoColor=white&label=PyPI
   :target: https://pypi.org/project/ansys-speos-core
   :alt: PyPI

.. |codecov| image:: https://codecov.io/github/ansys/pyspeos/graph/badge.svg?token=34FKDS6ZKJ
   :target: https://codecov.io/github/ansys/pyspeos
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys/pyspeos/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/pyspeos/actions/workflows/ci_cd.yml

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: Ruff


Project overview
----------------
``PySpeos`` is a Python library that gathers functionalities and tools based on remote API provided by gRPC server of Ansys software `Speos <https://www.ansys.com/products/optics>`_ .

Installation
------------
Installation can be done using the published `package`_ or the repository `sources`_.

Package
~~~~~~~

This repository is deployed as the Python packages `ansys-speos-core <https://pypi.org/project/ansys-speos-core>`_.
As usual, installation is done by running:

.. code:: bash

   pip install ansys-speos-core

Sources
~~~~~~~
**Prerequisite**: user needs to have a GitHub account and a valid Personal Access Token
(see GitHub Settings/Developer settings/Personal access tokens/Generate new token).

Clone and install
^^^^^^^^^^^^^^^^^

.. code:: bash

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

Documentation and issues
------------------------

Documentation for the latest stable release of PySpeos is hosted at
`PySpeos Documentation <https://speos.docs.pyansys.com>`_.

In the upper right corner of the documentation's title bar, there is an option for switching from
viewing the documentation for the latest stable release to viewing the documentation for the
development version or previously released versions.

On the `PySpeos Issues <https://github.com/ansys/pyspeos/issues>`_ page,
you can create issues to report bugs and request new features. On the `PySpeos Discussions
<https://github.com/ansys/pyspeos/discussions>`_ page or the `Discussions <https://discuss.ansys.com/>`_
page on the Ansys Developer portal, you can post questions, share ideas, and get community feedback.

To reach the project support team, email `pyansys.core@ansys.com <mailto:pyansys.core@ansys.com>`_.

The documentation sources are stored in `<doc>`_ folder and generated using `Sphinx`_.
To build it manually :

.. code:: bash

   pip install -U pip tox
   pip install .[doc]
   tox -e doc && your_browser_name .tox/doc_out/index.html


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

The first option is to use the Docker image from the `PySpeos repository <https://github.com/orgs/ansys/pyspeos>`_ on Github.

.. note::

   This option is only available for users with write access to the repository or
   who are members of the Ansys organization.

Use a GitHub personal access token with permission for reading packages to authorize Docker to access this repository.
For more information, see `Managing your personal access tokens <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`_ in the GitHub documentation.
Save the token to a file with this command:

.. code-block:: bash

      echo XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX > GH_TOKEN.txt

Since the Docker image contains no license server, you will need to enter your license server IP address in the `LICENSE_SERVER` environment variable.
Then, to launch SpeosRPC server with product version 2025.1, you can run:

.. code:: bash

   export GH_USERNAME=<my-github-username>
   export LICENSE_SERVER=1055@XXX.XXX.XXX.XXX

   cat GH_TOKEN.txt | docker login ghcr.io -u "$GH_USERNAME" --password-stdin
   docker pull ghcr.io/ansys/speos-rpc:252
   docker run --detach --name speos-rpc -p 50098:50098 -e ANSYSLMD_LICENSE_FILE=$LICENSE_SERVER --entrypoint /app/SpeosRPC_Server.x ghcr.io/ansys/speos-rpc:252

.. note::

   To use the latest image in development, you can use `ghcr.io/ansys/speos-rpc:252`.

On the other hand, the SpeosRPC server can be started locally.

For Windows:

.. code:: bash

    %AWP_ROOT251%\Optical Products\SPEOS_RPC\SpeosRPC_Server.exe

For Linux:

.. code:: bash

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

.. code:: bash

   pip install .[tests]
   pytest -vx

Use jupyter notebook
~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   pip install .[jupyter]
   jupyter notebook

jupyter notebook can be downloaded from the documentations example section.

Features
--------

Information of the latest stable release features:

PySpeos core features
~~~~~~~~~~~~~~~~~~~~~

Features supported in the latest release can be found at:

* `Optical Materials <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/opt_prop/OptProp.html>`_
* `Light Sources <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/source/index.html>`_
* `Sensors <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/sensor/index.html>`_
* `Simulations <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/simulation/index.html>`_
* `BSDF Viewer <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/bsdf/index.html>`_
* `Light Path Finder <https://speos.docs.pyansys.com/version/stable/api/ansys/speos/core/lxp/LightPathFinder.html>`_

Speos RPC features
~~~~~~~~~~~~~~~~~~

Speos RPC is based on a gRPC server and provides APIs to interact with Speos solver.

Features supported in the latest Speos RPC can be found at:
`Ansys Speos for developers Speos RPC <https://developer.ansys.com/docs/speos>`_.



License
-------
`PySpeos`_ is licensed under the MIT license.
The full license can be found in the root directory of the repository, see `<LICENSE>`_.

.. LINKS AND REFERENCES
.. _PySpeos: https://github.com/ansys/pyspeos
.. _PyAnsys: https://docs.pyansys.com
.. _Sphinx: https://www.sphinx-doc.org/en/master/
