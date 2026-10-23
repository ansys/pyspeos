# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

from __future__ import annotations

from collections.abc import Collection, Sequence
from functools import lru_cache, wraps
import math
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union, cast
import warnings

from ansys.tools.common.path import get_available_ansys_installations
import numpy as np

from ansys.speos.core.generic.constants import DEFAULT_VERSION
from ansys.speos.core.generic.version_checker import server_version_checker

_GRAPHICS_AVAILABLE = None

GRAPHICS_ERROR = (
    "Preview unsupported without 'ansys-tools-visualization_interface' installed. "
    "You can install this using `pip install ansys-speos-core[graphics]`."
)

VERSION_ERROR = "The pySpeos feature : {feature_name} needs a Speos Version of {version} or higher."


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
            from ansys.tools.visualization_interface import Plotter  # noqa: F401
            import pyvista as pv  # noqa: F401

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
    magnitude = magnitude_vector(cast(List[float], vector_np.tolist()))
    if magnitude == 0:
        raise ValueError("Cannot normalize a zero vector")
    return cast(List[float], (vector_np / magnitude).tolist())


def _validate_numeric_sequence(
    value: Collection[float], expected_length: int, noun: str, article: str = "A"
) -> np.ndarray:
    """Validate and convert a finite numeric sequence."""
    length_words = {2: "two", 3: "three", 9: "nine", 12: "twelve"}
    expected_text = length_words.get(expected_length, str(expected_length))
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(
            f"{article} {noun} must be a list or tuple of {expected_text} finite numbers."
        )
    if len(value) != expected_length:
        raise ValueError(f"{article} {noun} must contain exactly {expected_text} values.")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TypeError(f"{noun.capitalize()} values must be numeric.")
    try:
        array = np.asarray(value, dtype=float)
    except OverflowError as error:
        raise ValueError(f"{noun.capitalize()} values must be finite.") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{noun.capitalize()} values must be finite.")
    return array


def _validate_vector3(value: Collection[float]) -> np.ndarray:
    """Validate and convert a three-dimensional vector."""
    return _validate_numeric_sequence(value, 3, "vector")


def _validate_axis_system12(value: Collection[float]) -> np.ndarray:
    """Validate and convert a twelve-value axis system."""
    return _validate_numeric_sequence(value, 12, "axis system", article="An")


def _validate_scalar(value: float) -> float:
    """Validate and convert a finite scalar."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("A scalar must be a finite number.")
    try:
        scalar = float(value)
    except OverflowError as error:
        raise ValueError("A scalar must be finite.") from error
    if not math.isfinite(scalar):
        raise ValueError("A scalar must be finite.")
    return scalar


def _validate_positive_int(value: int) -> int:
    """Validate a positive integer value."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Value must be an integer.")
    if value <= 0:
        raise ValueError("Value must be greater than 0.")
    return value


def _validate_pathlike(value: Union[str, Path], name: str) -> str:
    """Validate and convert a string or path-like value to a string."""
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{name} must be a string or Path.")
    return str(value)


def _rotation_matrix(axis: np.ndarray, angle_deg: float) -> np.ndarray:
    """Return the rotation matrix for a right-handed rotation in degrees."""
    x, y, z = normalize_vector(axis)
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return np.array(
        [
            [
                cosine + x * x * (1 - cosine),
                x * y * (1 - cosine) - z * sine,
                x * z * (1 - cosine) + y * sine,
            ],
            [
                y * x * (1 - cosine) + z * sine,
                cosine + y * y * (1 - cosine),
                y * z * (1 - cosine) - x * sine,
            ],
            [
                z * x * (1 - cosine) - y * sine,
                z * y * (1 - cosine) + x * sine,
                cosine + z * z * (1 - cosine),
            ],
        ]
    )


def _axis_frame(axis_system: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return origin and rotation matrix from a rigid axis system."""
    origin = axis_system[:3]
    rotation = axis_system[3:].reshape(3, 3).T
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6) or not np.isclose(
        np.linalg.det(rotation), 1.0, atol=1e-6
    ):
        raise ValueError(
            "An axis system must contain an orthonormal, right-handed coordinate frame."
        )
    return origin, rotation


def error_no_install(install_path: Union[Path, str], version: Union[int, str]) -> None:
    """Raise error that installation was not found at a location.

    Parameters
    ----------
    install_path : Union[Path, str]
        Installation path where the executable was expected.
    version : Union[int, str]
        Ansys version number (e.g. 242).

    Raises
    ------
    FileNotFoundError
        Always raised to signal a missing Speos RPC installation.
    """
    raise FileNotFoundError(
        f"Ansys Speos RPC server installation not found at {str(install_path)}. "
        f"Please define AWP_ROOT{version} environment variable. "
    )


def retrieve_speos_install_dir(
    speos_rpc_path: Optional[Union[Path, str]] = None,
    version: Union[str, int] = DEFAULT_VERSION,
) -> Path:
    """Retrieve the Speos RPC installation directory.

    Resolution order:
    1. Validate / normalise a caller-supplied path.
    2. Discover the installation via :func:`get_available_ansys_installations`.
    3. Fall back to the ``AWP_ROOT<version>`` environment variable.

    Parameters
    ----------
    speos_rpc_path : Optional[Union[str, Path]]
        Explicit path to the Speos RPC executable or its parent directory.
        When *None* or empty the function performs automatic discovery.
    version : Union[str, int]
        Three-digit Ansys version string or integer (e.g. ``"242"`` or ``242``).
        Defaults to :data:`DEFAULT_VERSION`.

    Returns
    -------
    Path
        Directory that contains the ``SpeosRPC_Server`` executable.

    Raises
    ------
    FileNotFoundError
        When no valid installation can be located.
    """
    path = Path(speos_rpc_path) if speos_rpc_path else None

    # --- caller supplied a path -------------------------------------------
    if path is not None:
        if path.is_file():
            if "SpeosRPC_Server" not in path.name:
                error_no_install(path, int(version))
            path = path.parent
        elif path.exists():
            pass  # directory supplied directly — validated below
        else:
            warnings.warn(
                f"Provided executable location '{path}' not found; "
                "falling back to local installation discovery.",
                UserWarning,
                stacklevel=3,
            )
            path = None  # trigger auto-discovery

    # --- auto-discovery ---------------------------------------------------
    if path is None:
        installations = get_available_ansys_installations()  # {261: 'C:\\...\\v261', ...}
        ansys_loc = (
            installations.get(int(version))  # dict keys are int
            or os.environ.get(f"AWP_ROOT{version}", "")  # fallback: env var
        )
        path = Path(ansys_loc) / "Optical Products" / "SPEOS_RPC"
        if not ansys_loc:
            error_no_install(speos_rpc_path or "<unset>", int(version))

    # --- verify executable exists -----------------------------------------
    speos_exec = path / ("SpeosRPC_Server.exe" if os.name == "nt" else "SpeosRPC_Server.x")
    if not speos_exec.is_file():
        error_no_install(path, int(version))

    return path


def wavelength_to_rgb(wavelength: float, gamma: float = 0.8) -> Tuple[int, int, int, int]:
    """Convert a given wavelength of light to an approximate RGB color value.

    The wavelength must be given in nanometers in the range from 380 nm to 750 nm.
    Based on the code from http://www.physics.sfasu.edu/astro/color/spectra.html

    Parameters
    ----------
    wavelength : float
        Wavelength in nanometer between 380-750 nm
    gamma : float
        Gamma value.
        By default : ``0.8``

    Returns
    -------
    Tuple[int, int, int, int]
        A tuple representing the RGBA color value, where each component is an integer in the range
        0-255.
    """
    wavelength = float(wavelength)
    if 380 <= wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        r = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        g = 0.0
        b = (1.0 * attenuation) ** gamma
    elif 440 <= wavelength <= 490:
        r = 0.0
        g = ((wavelength - 440) / (490 - 440)) ** gamma
        b = 1.0
    elif 490 <= wavelength <= 510:
        r = 0.0
        g = 1.0
        b = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif 510 <= wavelength <= 580:
        r = ((wavelength - 510) / (580 - 510)) ** gamma
        g = 1.0
        b = 0.0
    elif 580 <= wavelength <= 645:
        r = 1.0
        g = (-(wavelength - 645) / (645 - 580)) ** gamma
        b = 0.0
    elif 645 <= wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        r = (1.0 * attenuation) ** gamma
        g = 0.0
        b = 0.0
    else:
        r = 0.0
        g = 0.0
        b = 0.0
    r *= 255
    g *= 255
    b *= 255
    return (int(r), int(g), int(b), 255)


def min_speos_version(major: int, minor: int, service_pack: int):
    """Raise version warning.

    Parameters
    ----------
    major : int
        Major release version, e.g. 25
    minor : int
        Minor release version e.g. 1
    service_pack : int
        Service Pack version e.g. 3
    """
    version = f"20{major} R{minor} SP{service_pack}"

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if function.__qualname__.endswith("__init__"):
                name = function.__qualname__[:-9]
            else:
                name = function.__qualname__
            is_error = not server_version_checker.is_version_supported(
                2000 + major, minor, service_pack
            )
            if is_error:
                if server_version_checker._version is None:
                    warnings.warn(
                        VERSION_ERROR.format(version=version, feature_name=name), stacklevel=2
                    )
                else:
                    raise NotImplementedError(
                        VERSION_ERROR.format(version=version, feature_name=name)
                    )
            return function(*args, **kwargs)

        return wrapper

    return decorator
