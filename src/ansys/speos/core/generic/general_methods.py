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

"""General methods and helpers collection.

this includes decorator and methods
"""

from functools import wraps
import warnings

__GRAPHICS_AVAILABLE = None
GRAPHICS_ERROR = (
    "Preview unsupported without 'ansys-tools-visualization_interface' installed. "
    "You can install this using `pip install ansys-speos-core[graphics]`."
)


def deprecate_kwargs(old_arguments: dict, removed_version="0.3.0"):
    """Issues deprecation warnings for arguments.

    Parameters
    ----------
    old_arguments : dict
        key old argument value new argument name
    removed_version : str
        Release version with which argument support will be removed
        By Default, next major release

    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            func_name = function.__name__
            for alias, new in old_arguments.items():
                if alias in kwargs:
                    if new in kwargs:
                        msg = f"{func_name} received both {alias} and {new} as arguments!\n"
                        msg += f"{alias} is deprecated, use {new} instead."
                        raise TypeError(msg)
                    msg = f"Argument `{alias}` is deprecated for method `{func_name}`; it will be "
                    msg += f"removed with Release v{removed_version}. Please use `{new}` instead."
                    kwargs[new] = kwargs.pop(alias)
                    warnings.warn(msg, DeprecationWarning, stacklevel=2)
            retval = function(*args, **kwargs)
            return retval

        return wrapper

    return decorator


def run_if_graphics_required(warning=False):
    """Check if graphics are available."""
    global __GRAPHICS_AVAILABLE
    if __GRAPHICS_AVAILABLE is None:
        try:
            import pyvista as pv  # noqa: F401

            from ansys.tools.visualization_interface import Plotter  # noqa: F401

            __GRAPHICS_AVAILABLE = True
        except ImportError:  # pragma: no cover
            __GRAPHICS_AVAILABLE = False

    if __GRAPHICS_AVAILABLE is False and warning is False:  # pragma: no cover
        raise ImportError(GRAPHICS_ERROR)
    elif __GRAPHICS_AVAILABLE is False:  # pragma: no cover
        warnings.warn(GRAPHICS_ERROR)


def graphics_required(method):
    """Decorate a method as requiring graphics.

    Parameters
    ----------
    method : callable
        Method to decorate.

    Returns
    -------
    callable
        Decorated method.
    """

    def wrapper(*args, **kwargs):
        run_if_graphics_required()
        return method(*args, **kwargs)

    return wrapper
