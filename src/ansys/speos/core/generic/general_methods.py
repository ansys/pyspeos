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

from collections.abc import Collection
from functools import lru_cache, wraps
import os
from pathlib import Path
from typing import List, Optional, Union, cast
import warnings

import numpy as np

from ansys.speos.core.generic.constants import DEFAULT_VERSION
from ansys.tools.path import get_available_ansys_installations

_GRAPHICS_AVAILABLE = None

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


@lru_cache
def run_if_graphics_required(warning=False):
    """Check if graphics are available."""
    global _GRAPHICS_AVAILABLE
    if _GRAPHICS_AVAILABLE is None:
        try:
            import pyvista as pv  # noqa: F401

            from ansys.tools.visualization_interface import Plotter  # noqa: F401

            _GRAPHICS_AVAILABLE = True
        except ImportError:  # pragma: no cover
            _GRAPHICS_AVAILABLE = False

    if _GRAPHICS_AVAILABLE is False and warning is False:  # pragma: no cover
        raise ImportError(GRAPHICS_ERROR)
    elif _GRAPHICS_AVAILABLE is False:  # pragma: no cover
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


def magnitude_vector(vector: Collection[float]) -> float:
    """Compute the magnitude (length) of a 2D or 3D vector using NumPy.

    Parameters
    ----------
    vector: List[float]
        A 2D or 3D vector as a list [x, y] or [x, y, z].

    Returns
    -------
    float
        The magnitude (length) of the vector.
    """
    vector_np = np.array(vector, dtype=float)
    if vector_np.size not in (2, 3):
        raise ValueError("Input vector must be either 2D or 3D")
    return float(np.linalg.norm(vector_np))


def normalize_vector(vector: Collection[float]) -> List[float]:
    """
    Normalize a 2D or 3D vector to have a length of 1 using NumPy.

    Parameters
    ----------
    vector: List[float]
        A vector as a list [x, y] for 2D or [x, y, z] for 3D.

    Returns
    -------
    List[float]
        The normalized vector.
    """
    vector_np = np.array(vector, dtype=float)
    if vector_np.size not in (2, 3):
        raise ValueError("Input vector must be either 2D or 3D")

    magnitude = magnitude_vector(vector_np)
    if magnitude == 0:
        raise ValueError("Cannot normalize the zero vector")

    return cast(List[float], (vector_np / magnitude).tolist())


def error_no_install(install_path: Union[Path, str], version: Union[int, str]):
    """Raise error that installation was not found at a location.

    Parameters
    ----------
    install_path : Union[Path, str]
        Installation Path
    version : Union[int, str]
        Version
    """
    install_loc_msg = ""
    if install_path:
        install_loc_msg = f"at {Path(install_path).parent}"
    raise FileNotFoundError(
        f"Ansys Speos RPC server installation not found{install_loc_msg}. "
        f"Please define AWP_ROOT{version} environment variable"
    )


def retrieve_speos_install_dir(
    speos_rpc_path: Optional[Union[Path, str]] = None, version: str = DEFAULT_VERSION
) -> Path:
    """Retrieve Speos install location based on Path or Environment.

    Parameters
    ----------
    speos_rpc_path : Optional[str, Path]
        location of Speos rpc executable
    version : Union[str, int]
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as
        ``ansys.speos.core.kernel.client.LATEST_VERSION``.

    """
    if not speos_rpc_path:
        speos_rpc_path = ""

    if not speos_rpc_path or not Path(speos_rpc_path).exists():
        if not Path(speos_rpc_path).exists():
            warnings.warn(
                "Provided executable location not found, looking for local installation",
                UserWarning,
            )
        versions = get_available_ansys_installations()
        ansys_loc = versions.get(int(version), "")
        if not ansys_loc:
            ansys_loc = os.environ.get("AWP_ROOT{}".format(version), "")
            if not ansys_loc:
                error_no_install(speos_rpc_path, int(version))

        speos_rpc_path = Path(ansys_loc) / "Optical Products" / "SPEOS_RPC"
    elif Path(speos_rpc_path).is_file():
        if "SpeosRPC_Server" not in Path(speos_rpc_path).name:
            error_no_install(speos_rpc_path, int(version))
        else:
            speos_rpc_path = Path(speos_rpc_path).parent

    speos_rpc_path = Path(speos_rpc_path)
    if os.name == "nt":
        speos_exec = speos_rpc_path / "SpeosRPC_Server.exe"
    else:
        speos_exec = speos_rpc_path / "SpeosRPC_Server.x"
    if not speos_exec.is_file():
        error_no_install(speos_rpc_path, int(version))
    return speos_rpc_path
