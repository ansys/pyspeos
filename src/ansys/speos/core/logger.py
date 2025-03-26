# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Logging module.

This module supplies a general framework for logging in PySpeos.  This module is
built upon `logging <https://docs.python.org/3/library/logging.html>`_ library
and it does not intend to replace it but rather provide a way to interact between
``logging`` and pyspeos.

The loggers used in the module include the name of the instance, which
is intended to be unique. This name is printed in all active
outputs and is used to track the different PySpeos instances.

Usage
-----

Global logger
~~~~~~~~~~~~~
There is a global logger named ``pyspeos_global`` that is created at
``ansys.speos.core.__init__``.  If you want to use this global logger,
you must call it at the top of your module:

.. code:: python

   from ansys.speos.core import LOG

You can also rename it to avoid conflicts with other loggers (if any):

.. code:: python

   from ansys.speos.core import LOG as logger

It should be noticed that the default logging level of ``LOG`` is ``ERROR``.
You can change this and output lower-level messages with:

.. code:: python

   LOG.logger.setLevel("DEBUG")
   LOG.file_handler.setLevel("DEBUG")  # If present.
   LOG.stdout_handler.setLevel("DEBUG")  # If present.

Alternatively, you can ensure all the handlers are set to the input log
level with:

.. code:: python

   LOG.setLevel("DEBUG")

By default, this logger does not log to a file. If you want to do so,
you can add a file handler with:

.. code:: python

   import os

   file_path = os.path.join(os.getcwd(), "pyspeos.log")
   LOG.log_to_file(file_path)

This sets the logger to be redirected also to this file. If you want
to change the characteristics of this global logger from the beginning
of the execution, you must edit the ``__init__`` file in the directory
``ansys.speos.core``.

To log using this logger, call the desired method as a normal logger with:

.. code:: pycon

    >>> import logging
    >>> from ansys.speos.core.logger import Logger
    >>> LOG = Logger(level=logging.DEBUG, to_file=False, to_stdout=True)
    >>> LOG.debug("This is LOG debug message.")
    DEBUG -  -  <ipython-input-24-80df150fe31f> - <module> - This is LOG debug message.

Instance Logger
~~~~~~~~~~~~~~~
Every time an instance of :class:`ansys.speos.core.speos.Speos`
is created, a logger is created and stored in ``LOG._instances``. This field is a
dictionary where the key is the name of the created logger.
These instance loggers inherit the ``pyspeos_global`` output handlers and
logging level unless otherwise specified. The way this logger works is very
similar to the global logger. If you want to add a file handler, you can use
the :func:`log_to_file() <PySpeosCustomAdapter.log_to_file>` method. If you want
to change the log level, you can use the :func:`logger.Logging.setLevel` method.
You can use this logger like this:

.. code:: pycon

    >>> from ansys.speos.core import SpeosClient
    >>> speos = SpeosClient()
    >>> speos._log.info("This is a useful message")
    INFO - GRPC_127.0.0.1:50056 -  <...> - <module> - This is a useful message

Other loggers
~~~~~~~~~~~~~
You can create your own loggers using a Python ``logging`` library as
you would do in any other script. There would be no conflicts between
these loggers.

"""

from copy import copy
from datetime import datetime
import logging
import sys
from typing import TYPE_CHECKING, Optional
import weakref

if TYPE_CHECKING:
    from ansys.speos.core.kernel.client import SpeosClient  # pragma: no cover

## Default configuration
LOG_LEVEL = logging.DEBUG
FILE_NAME = "pyspeos.log"

# For convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

## Formatting

STDOUT_MSG_FORMAT = "%(levelname)s - %(instance_name)s -  %(module)s - %(funcName)s - %(message)s"

FILE_MSG_FORMAT = STDOUT_MSG_FORMAT

DEFAULT_STDOUT_HEADER = """
LEVEL - INSTANCE NAME - MODULE - FUNCTION - MESSAGE
"""
DEFAULT_FILE_HEADER = DEFAULT_STDOUT_HEADER

NEW_SESSION_HEADER = f"""
===============================================================================
       NEW SESSION - {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
==============================================================================="""

string_to_loglevel = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARN": WARN,
    "WARNING": WARN,
    "ERROR": ERROR,
    "CRITICAL": CRITICAL,
}


class PySpeosCustomAdapter(logging.LoggerAdapter):
    """Keeps the reference to the speos instance name dynamic.

    If we use the standard approach, which is supplying **extra** input
    to the logger, we would need to keep inputing speos instances
    every time we do a log.
    Using adapters, we only need to specify the speos instance that
    we are referring to once.

    """

    level = (
        None  # This is maintained for compatibility with ``supress_logging``, but it does nothing.
    )
    file_handler = None
    stdout_handler = None

    def __init__(self, logger, extra=None):
        """Initialize the logger adapter."""
        self.logger = logger
        if extra is not None:
            self.extra = weakref.proxy(extra)
        else:
            self.extra = None  # pragma: no cover
        self.file_handler = logger.file_handler
        self.std_out_handler = logger.std_out_handler

    def process(self, msg, kwargs) -> tuple[str, dict]:
        """Process extra Arguments.

        Parameters
        ----------
        msg : str
            Log message
        kwargs : dict
            extra Arguments dictionary

        Returns
        -------
        tuple[str, dict]
            Message and processed extra arguments
        """
        kwargs["extra"] = {}
        # This are the extra parameters sent to log
        kwargs["extra"]["instance_name"] = (
            self.extra.get_name()
        )  # here self.extra is the argument pass to the log records.
        return msg, kwargs

    def log_to_file(self, filename: str = FILE_NAME, level: int = LOG_LEVEL):
        """Add a file handler to the logger.

        Parameters
        ----------
        filename : str, optional
            Name of the file to write log messages to. The default is
            ``"pyspeos.log"``.
        level : str, optional
            Level of logging. The default is ``10``, in which case the
            ``logging.DEBUG`` level is used.
        """
        self.logger = addfile_handler(
            self.logger, filename=filename, level=level, write_headers=True
        )
        self.file_handler = self.logger.file_handler

    def log_to_stdout(self, level=LOG_LEVEL):
        """Add a standard output handler to the logger.

        Parameters
        ----------
        level : int, optional
            Level of logging. The default is ``10``, in which case the
            ``logging.DEBUG`` level is used.
        """
        if self.std_out_handler:
            raise Exception("Stdout logger is already defined.")

        self.logger = add_stdout_handler(self.logger, level=level)
        self.std_out_handler = self.logger.std_out_handler

    def setLevel(self, level="DEBUG"):
        """Change the log level of the object and the attached handlers.

        Parameters
        ----------
        level : int, optional
            Level of logging. The default is ``10``, in which case the
            ``logging.DEBUG`` level is used.
        """
        self.logger.setLevel(level)
        for each_handler in self.logger.handlers:
            each_handler.setLevel(level)
        self.level = level


class PySpeosPercentStyle(logging.PercentStyle):
    """Customized ``PercentStyle`` class for overwriting default format styles."""

    def __init__(self, fmt, *, defaults=None):
        """Initialize the class."""
        self._fmt = fmt or self.default_format
        self._defaults = defaults

    def _format(self, record):
        """Format the record.

        Parameters
        ----------
        record : logging.LogRecord
            Record to format.

        Returns
        -------
        str
            Formatted record.
        """
        defaults = self._defaults
        if defaults:
            values = defaults | record.__dict__
        else:
            values = record.__dict__

        # We can make any changes that we want in the record here. For example,
        # adding a key.

        # We could create an ``if`` here if we want conditional formatting, and even
        # change the record.__dict__.
        # Because we don't want to create conditional fields now, it is fine to keep
        # the same MSG_FORMAT for all of them.

        # For the case of logging exceptions to the logger.
        values.setdefault("instance_name", "")

        return STDOUT_MSG_FORMAT % values


class PySpeosFormatter(logging.Formatter):
    """Provides the customized ``Formatter`` class for overwriting default format styles."""

    def __init__(
        self,
        fmt=STDOUT_MSG_FORMAT,
        datefmt=None,
        style="%",
        validate=True,
        defaults=None,
    ):
        """Initialize the class."""
        if sys.version_info[1] < 8:
            super().__init__(fmt, datefmt, style)
        else:
            # 3.8: The validate parameter was added
            super().__init__(fmt, datefmt, style, validate)
        self._style = PySpeosPercentStyle(fmt, defaults=defaults)  # overwriting


class InstanceFilter(logging.Filter):
    """Ensures that the ``instance_name`` record always exists."""

    def filter(self, record):
        """Filter the record.

        Parameters
        ----------
        record : logging.LogRecord
            Record to filter.

        Returns
        -------
        bool
            Whether the record is valid.
        """
        if not hasattr(record, "instance_name"):
            record.instance_name = ""
        return True


class Logger:
    """Provides the logger used for each PySpeos session.

    This class allows you to add handlers to the logger to output messages
    to a file or to the standard output.

    Parameters
    ----------
    level : int, default: 10
        Logging level to filter the message severity allowed in the logger.
        By default, the ``logging.DEBUG`` level is used.
    to_file : bool, default: False
        Whether to write log messages to a file.
    to_stdout : bool, default: True
        Whether to write log messages to the standard output (stdout).
    filename : str, default: "pyspeos.log"
        Name of the file to write log log messages to.

    Examples
    --------
    Demonstrate logger usage from the ``Speos`` instance, which is automatically
    created when a speos instance is created.

    >>> from ansys.speos.core import speos
    >>> speos = Speos(loglevel="DEBUG")
    >>> speos._log.info("This is a useful message")
    INFO -  -  <ipython-input-24-80df150fe31f> - <module> - This is LOG debug message.

    Import the global pyspeos logger and add a file output handler.

    >>> import os
    >>> from ansys.speos.core import LOG
    >>> file_path = os.path.join(os.getcwd(), "pyspeos.log")
    >>> LOG.log_to_file(file_path)
    """

    file_handler = None
    std_out_handler = None
    _level = logging.DEBUG
    _instances = {}

    def __init__(
        self,
        level=logging.DEBUG,
        to_file=False,
        to_stdout=True,
        filename=FILE_NAME,
    ):
        """Customize the logger class for PySpeos.

        Parameters
        ----------
        level : int, optional
            Level of logging as defined in the ``logging`` package. The default
            is ``10``, in which case the ``logging.DEBUG`` level is used.
        to_file : bool, optional
            Whether to write log messages to a file. The default is ``False``.
        to_stdout : bool, optional
            Whether to write log messages to the standard output (stdout). The
            default is ``True``.
        filename : str, optional
           Name of the file to write log messages to. The default is ``"pyspeos.log"``.
        """
        # create default main logger
        self.logger = logging.getLogger("pyspeos_global")
        self.logger.addFilter(InstanceFilter())
        self.logger.setLevel(level)
        self.logger.propagate = True

        # Writing logging methods.
        self.debug = self.logger.debug
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.log = self.logger.log

        if to_file or filename != FILE_NAME:
            # We record to file
            self.log_to_file(filename=filename, level=level)

        if to_stdout:
            self.log_to_stdout(level=level)

        # Using logger to record unhandled exceptions
        self.add_handling_uncaught_expections(self.logger)

    def log_to_file(self, filename=FILE_NAME, level=LOG_LEVEL):
        """Add file handler to logger.

        Parameters
        ----------
        filename : str, optional
            Name of the file to write log messages to. The default
            is ``"pyspeos.log"``.
        level : int, optional
            Level of logging. The default is ``10``, in which case the
            ``logging.DEBUG`` level is used.

        Examples
        --------
        Write to the ``"pyspeos.log"`` file in the current working directory.

        >>> from ansys.speos.core import LOG
        >>> import os
        >>> file_path = os.path.join(os.getcwd(), "pyspeos.log")
        >>> LOG.log_to_file(file_path)
        """
        self = addfile_handler(self, filename=filename, level=level, write_headers=True)

    def log_to_stdout(self, level=LOG_LEVEL):
        """Add the standard output handler to the logger.

        Parameters
        ----------
        level : int, optional
            Level of logging. The default is ``10``, in which case the
            ``logging.DEBUG`` level is used.
        """
        self = add_stdout_handler(self, level=level)

    def setLevel(self, level="DEBUG"):
        """Change the log level of the object and the attached handlers."""
        self.logger.setLevel(level)
        for each_handler in self.logger.handlers:
            each_handler.setLevel(level)
        self._level = level

    def _make_child_logger(self, suffix, level):
        """Create a child logger.

        This method uses the ``getChild`` method or copies attributes between the
        ``pyspeos_global`` logger and the new one.
        """
        logger = logging.getLogger(suffix)
        logger.std_out_handler = None
        logger.file_handler = None

        if self.logger.hasHandlers:
            for each_handler in self.logger.handlers:
                new_handler = copy(each_handler)

                if each_handler == self.file_handler:
                    logger.file_handler = new_handler
                elif each_handler == self.std_out_handler:
                    logger.std_out_handler = new_handler

                if level and isinstance(level, str):
                    # The logger handlers are copied and changed the loglevel is
                    # the specified log level is lower than the one of the
                    # global.
                    if isinstance(level, int) and each_handler.level > level:
                        new_handler.setLevel(level)
                    elif (
                        isinstance(level, str)
                        and each_handler.level > string_to_loglevel[level.upper()]
                    ):
                        new_handler.setLevel(level)

                logger.addHandler(new_handler)

        if level:
            if isinstance(level, str):
                level = string_to_loglevel[level.upper()]
            logger.setLevel(level)

        else:
            logger.setLevel(self.logger.level)

        logger.propagate = True
        return logger

    def add_child_logger(self, suffix: str, level: Optional[str] = None):
        """Add a child logger to the main logger.

        This logger is more general than an instance logger, which is designed to
        track the state of speos instances.
        If the logging level is in the arguments, a new logger with a reference
        to the ``_global`` logger handlers is created instead of a child logger.

        Parameters
        ----------
        suffix : str
            Name of the child logger.
        level : str, optional
            Level of logging. The default is ``None``.

        Returns
        -------
        logging.logger
            Logger class.
        """
        name = self.logger.name + "." + suffix
        self._instances[name] = self._make_child_logger(self, name, level)
        return self._instances[name]

    def add_instance_logger(
        self,
        name: str,
        client_instance: "SpeosClient",
        level: Optional[int] = None,
    ) -> PySpeosCustomAdapter:
        """Add a logger for a speos instance.

        The speos instance logger is a logger with an adapter that adds
        contextual information such as the speos instance name. This logger is
        returned, and you can use it to log events as a normal logger. It is
        stored in the ``_instances`` field.

        Parameters
        ----------
        name : str
            Name for the new instance logger.
        client_instance : ansys.speos.core.kernel.client.SpeosClient
            speos SpeosClient object, which should contain the ``get_name`` method.
        level : int, optional
            Level of logging. The default is ``None``.

        Returns
        -------
        PySpeosCustomAdapter
            Logger adapter customized to add speos information to the
            logs. You can use this class to log events in the same
            way you would with the ``Logger`` class.
        """
        count_ = 0
        new_name = name
        while new_name in logging.root.manager.__dict__.keys():
            count_ += 1
            new_name = f"{name}_{count_}"

        self._instances[new_name] = PySpeosCustomAdapter(
            self._make_child_logger(name, level), client_instance
        )

        return self._instances[new_name]

    def __getitem__(self, key):
        """Magic method to allow retrieval of instances."""
        if key in self._instances.keys():
            return self._instances[key]
        else:
            raise KeyError(f"There is no instances with name {key}.")

    def add_handling_uncaught_expections(self, logger):
        """Redirect the output of an exception to a logger.

        Parameters
        ----------
        logger : str
            Name of the logger.
        """

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

        sys.excepthook = handle_exception


def addfile_handler(logger, filename=FILE_NAME, level=LOG_LEVEL, write_headers=False):
    """Add a file handler to the input.

    Parameters
    ----------
    logger : logging.Logger or logging.Logger, optional
        Logger to add the file handler to.
    filename : str, optional
        Name of the output file. The default is ``"pyspeos.log"``.
    level : int, optional
        Level of logging. The default is ``LOG_LEVEL``.
    write_headers : bool, optional
        Whether to write the headers to the file. The default is ``False``.

    Returns
    -------
    logger
        Logger or Logger object.
    """
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(FILE_MSG_FORMAT))

    if isinstance(logger, Logger):
        logger.file_handler = file_handler
        logger.logger.addHandler(file_handler)

    elif isinstance(logger, logging.Logger):
        logger.file_handler = file_handler
        logger.addHandler(file_handler)

    if write_headers:
        file_handler.stream.write(NEW_SESSION_HEADER)
        file_handler.stream.write(DEFAULT_FILE_HEADER)

    return logger


def add_stdout_handler(logger, level=LOG_LEVEL, write_headers=False):
    """Add a standout handler to the logger.

    Parameters
    ----------
    logger : logging.Logger or logging.Logger
        Logger to add the file handler to.
    level : in, optional
        Level of logging. The default is ``10``, in which case the
           ``logging.DEBUG`` level is used.
    write_headers : bool, optional
        Whether to write headers to the file. The default is ``False``.

    Returns
    -------
    logger
        Logger or Logger object.
    """
    std_out_handler = logging.StreamHandler()
    std_out_handler.setLevel(level)
    std_out_handler.setFormatter(PySpeosFormatter(STDOUT_MSG_FORMAT))

    if isinstance(logger, Logger):
        logger.std_out_handler = std_out_handler
        logger.logger.addHandler(std_out_handler)

    elif isinstance(logger, logging.Logger):
        logger.addHandler(std_out_handler)

    if write_headers:
        std_out_handler.stream.write(DEFAULT_STDOUT_HEADER)

    return logger


# Logger
# ------------------------------------------------------------------------------
LOG = Logger(level=logging.ERROR, to_file=False, to_stdout=True)
LOG.debug("Loaded logging module as LOG")
