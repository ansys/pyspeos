Contribute
##########

Overall guidance on contributing to a PyAnsys library appears in the
`Contributing <https://dev.docs.pyansys.com/how-to/contributing.html>`_ topic
in the *PyAnsys Developer's Guide*. Ensure that you are thoroughly familiar
with this guide before attempting to contribute to PySpeos.

The following contribution information is specific to PySpeos.

Clone the repository
--------------------

To clone and install the latest PySpeos release in development mode, run
these commands:

.. code::

    git clone https://github.com/ansys-internal/pyspeos
    cd pyspeos
    python -m pip install --upgrade pip
    pip install -e .


Post issues
-----------

Use the `PySpeos Issues <https://github.com/ansys-internal/pyspeos/issues>`_
page to submit questions, report bugs, and request new features. When possible, you
should use these issue templates:

* Bug, problem, error: For filing a bug report
* Documentation error: For requesting modifications to the documentation
* Adding an example: For proposing a new example
* New feature: For requesting enhancements to the code

If your issue does not fit into one of these template categories, you can click
the link for opening a blank issue.

To reach the project support team, email `pyansys.core@ansys.com <pyansys.core@ansys.com>`_.

View documentation
------------------

Documentation for the latest stable release of PySpeos is hosted at
`PySpeos Documentation <https://speos.docs.pyansys.com>`_.

In the upper right corner of the documentation's title bar, there is an option
for switching from viewing the documentation for the latest stable release
to viewing the documentation for the development version or previously
released versions.

Adhere to code style
--------------------

PySpeos follows the PEP8 standard as outlined in
`PEP 8 <https://dev.docs.pyansys.com/coding-style/pep8.html>`_ in
the *PyAnsys Developer's Guide* and implements style checking using
`pre-commit <https://pre-commit.com/>`_.

To ensure your code meets minimum code styling standards, run these commands::

  pip install pre-commit
  pre-commit run --all-files

You can also install this as a pre-commit hook by running this command::

  pre-commit install

This way, it's not possible for you to push code that fails the style checks::

  $ pre-commit install
  $ git commit -am "added my cool feature"
  ruff.....................................................................Passed
  ruff-format..............................................................Passed
  codespell................................................................Passed
  check for merge conflicts................................................Passed
  debug statements (python)................................................Passed
  check yaml...............................................................Passed
  trim trailing whitespace.................................................Passed
  Validate GitHub Workflows................................................Passed
  Add License Headers......................................................Passed

Build the documentation
-----------------------

.. note::

  To build the full documentation, you must have a running SpeosRPC server
  because it is used to generate the examples in the documentation. It is also
  recommended that the service is running as a Docker container.

  If you do not have the SpeosRPC server installed, you can still build the
  documentation, but the examples are not generated. To build the
  documentation without the examples, define the following environment variable::

      # On Linux or macOS
      export BUILD_EXAMPLES=false

      # On Windows CMD
      set BUILD_EXAMPLES=false

      # On Windows PowerShell
      $env:BUILD_EXAMPLES="false"

To build the documentation locally, you must run this command to install the
documentation dependencies::

  pip install -e .[doc]

Then, navigate to the ``docs`` directory and run this command::

  # On Linux or macOS
  make html

  # On Windows
  ./make.bat html

The documentation is built in the ``docs/_build/html`` directory.

You can clean the documentation build by running this command::

  # On Linux or macOS
  make clean

  # On Windows
  ./make.bat clean

Run tests
---------

PySpeos uses `pytest <https://docs.pytest.org/en/stable/>`_ for testing.

Prerequisites
^^^^^^^^^^^^^

Prior to running the tests, you must run this command to install the test dependencies::

  pip install -e .[tests]


Running the tests
^^^^^^^^^^^^^^^^^

To run the tests, you need to first start navigate to the root directory of the repository and run this command::

  pytest

.. note::

  The tests require the SpeosRPC server to be installed and running on your machine.
  The tests fail if the service is not running. It is recommended for the SpeosRPC server
  to be running as a Docker container.
