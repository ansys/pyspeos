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

"""Validation tests for public helpers across core modules."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from ansys.api.speos.source.v1 import source_pb2
from ansys.api.speos.spectrum.v1 import spectrum_pb2
import numpy as np
import pytest

from ansys.speos.core import Intensity, Spectrum
from ansys.speos.core.generic import general_methods
from ansys.speos.core.ground_plane import GroundPlane
from ansys.speos.core.kernel.intensity_template import ProtoIntensityTemplate
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.opt_prop import BaseSop, BaseVop, TextureLayer
from ansys.speos.core.simulation import BaseSimulation
from ansys.speos.core.source import BaseSource


@pytest.mark.parametrize(
    ("value", "error_type", "message"),
    [
        pytest.param(
            "bad", TypeError, "A white point must be a list or tuple of two finite numbers."
        ),
        pytest.param([0.31271], ValueError, "A white point must contain exactly two values."),
        pytest.param([True, 0.32902], TypeError, "White point values must be numeric."),
        pytest.param([0.31271, float("inf")], ValueError, "White point values must be finite."),
        pytest.param([0.31271, float("nan")], ValueError, "White point values must be finite."),
        pytest.param([0.31271, 10**1000], ValueError, "White point values must be finite."),
    ],
)
def test_validate_numeric_sequence_rejects_invalid_inputs(value, error_type, message) -> None:
    """Numeric sequence validators should raise precise errors for invalid inputs."""
    with pytest.raises(error_type, match=message):
        general_methods._validate_numeric_sequence(cast(Any, value), 2, "white point")


@pytest.mark.parametrize(
    ("value", "error_type", "message"),
    [
        pytest.param(True, TypeError, "A scalar must be a finite number."),
        pytest.param("bad", TypeError, "A scalar must be a finite number."),
        pytest.param(float("inf"), ValueError, "A scalar must be finite."),
        pytest.param(float("nan"), ValueError, "A scalar must be finite."),
        pytest.param(10**1000, ValueError, "A scalar must be finite."),
    ],
)
def test_validate_scalar_rejects_invalid_inputs(value, error_type, message) -> None:
    """Scalar validator should reject unsupported and non-finite values."""
    with pytest.raises(error_type, match=message):
        general_methods._validate_scalar(cast(Any, value))


def test_axis_frame_validates_coordinate_frames() -> None:
    """Axis frame helper should accept rigid frames and reject invalid ones."""
    axis_system = np.array(
        [1.0, 2.0, 3.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        dtype=float,
    )

    origin, rotation = general_methods._axis_frame(axis_system)

    assert np.allclose(origin, [1.0, 2.0, 3.0])
    assert np.allclose(rotation, np.eye(3))

    with pytest.raises(
        ValueError,
        match="An axis system must contain an orthonormal, right-handed coordinate frame.",
    ):
        general_methods._axis_frame(
            np.array(
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                dtype=float,
            )
        )


def test_white_point_and_pathlike_helpers_validate_inputs() -> None:
    """White point and path-like helpers should validate values and preserve valid paths."""
    white_point = BaseSource.UserDefinedColorSpace.UserDefinedWhitePoint(
        userdefined_white_point=source_pb2.SourceTemplate.UserDefinedWhitePoint(),
        stable_ctr=True,
    )

    with pytest.raises(TypeError, match="White point values must be numeric."):
        white_point.white_point = [0.31271, True]

    with pytest.raises(ValueError, match="White point values must be finite."):
        white_point.white_point = [0.31271, float("nan")]

    assert general_methods._validate_pathlike(Path("test.spectrum"), "file_uri") == str(
        Path("test.spectrum")
    )


def test_intensity_setters_validate_inputs() -> None:
    """Intensity helper setters should reject invalid inputs."""
    library = ProtoScene.SourceInstance.IntensityProperties.LibraryProperties()
    helper = Intensity.Library(
        library=ProtoIntensityTemplate.Library(),
        library_props=library,
    )

    with pytest.raises(TypeError, match="intensity_file_uri must be a string or Path."):
        helper.intensity_file_uri = 123

    with pytest.raises(ValueError, match="An axis system must contain exactly twelve values."):
        helper.orientation_axis_system = [0.0] * 11

    gaussian = Intensity.Gaussian(
        gaussian=ProtoIntensityTemplate.Gaussian(),
        gaussian_props=ProtoScene.SourceInstance.IntensityProperties.GaussianProperties(),
    )
    with pytest.raises(ValueError, match="fwhm_angle_x must be greater than or equal to 0."):
        gaussian.fwhm_angle_x = -1
    with pytest.raises(ValueError, match="total_angle must be in the interval ]0, 360]."):
        gaussian.total_angle = 0

    cos = Intensity.Cos(cos=ProtoIntensityTemplate.Cos())
    with pytest.raises(ValueError, match="n must be greater than 0."):
        cos.n = 0
    with pytest.raises(ValueError, match="total_angle must be in the interval ]0, 360]."):
        cos.total_angle = 361


def test_spectrum_setters_validate_inputs() -> None:
    """Spectrum helper setters should reject invalid inputs."""
    monochromatic = Spectrum.Monochromatic(
        monochromatic=spectrum_pb2.Spectrum.Monochromatic(),
        stable_ctr=True,
    )
    with pytest.raises(ValueError, match="wavelength must be greater than 0."):
        monochromatic.wavelength = 0

    blackbody = Spectrum.Blackbody(blackbody=spectrum_pb2.Spectrum.BlackBody(), stable_ctr=True)
    with pytest.raises(ValueError, match="temperature must be greater than 0."):
        blackbody.temperature = -1

    sampled = Spectrum.Sampled(sampled=spectrum_pb2.Spectrum.Sampled(), stable_ctr=True)
    with pytest.raises(TypeError, match="wavelengths must be a list or tuple of finite numbers."):
        sampled.wavelengths = "bad"
    with pytest.raises(ValueError, match="wavelengths must contain only values greater than 0."):
        sampled.wavelengths = [400.0, -1.0]
    with pytest.raises(ValueError, match=r"values must be within \[0, 100\]."):
        sampled.values = [10.0, 150.0]

    library = Spectrum.Library(library=spectrum_pb2.Spectrum.Library(), stable_ctr=True)
    with pytest.raises(TypeError, match="file_uri must be a string or Path."):
        library.file_uri = 123


def test_ground_plane_setters_validate_inputs() -> None:
    """Ground plane setters should validate vector and scalar inputs."""
    ground = cast(GroundPlane, object.__new__(GroundPlane))
    ground._ground = ProtoScene.GroundPlane()

    with pytest.raises(ValueError, match="A vector must contain exactly three values."):
        ground.ground_origin = [0.0, 0.0]

    with pytest.raises(
        TypeError, match="A vector must be a list or tuple of three finite numbers."
    ):
        ground.ground_zenith = "invalid"

    with pytest.raises(ValueError, match="ground_height must be greater than 0."):
        ground.ground_height = 0


def test_simulation_setters_validate_inputs() -> None:
    """Simulation helper setters should validate input values."""
    adaptive = BaseSimulation.SourceSampling.Adaptive(
        adaptive=SimpleNamespace(file_uri=""),
        stable_ctr=True,
    )
    with pytest.raises(TypeError, match="adaptive_uri must be a string or Path."):
        adaptive.adaptive_uri = 12

    uniform = BaseSimulation.SourceSampling.Uniform(
        uniform=SimpleNamespace(theta_sampling=0),
        stable_ctr=True,
    )
    with pytest.raises(ValueError, match="theta_sampling must be greater than 0."):
        uniform.theta_sampling = 0

    weight = BaseSimulation.Weight(
        weight=cast(Any, SimpleNamespace(minimum_energy_percentage=0.0)),
        stable_ctr=True,
    )
    with pytest.raises(ValueError, match="minimum_energy_percentage must be between 0 and 1."):
        weight.minimum_energy_percentage = 1.5


def test_opt_prop_setters_validate_inputs() -> None:
    """Optical property helpers should reject invalid input values."""
    sop_parent = SimpleNamespace(_sop_template=ProtoSOPTemplate(name="SOP.Validation"))
    sop_library = BaseSop.SopLibrary(parent=cast(Any, sop_parent), stable_ctr=True)
    with pytest.raises(TypeError, match="file_uri must be a string or Path."):
        sop_library.file_uri = 42

    vop_parent = SimpleNamespace(_vop_template=ProtoVOPTemplate(name="VOP.Validation"))
    vop_optic = BaseVop.VopOptic(parent=cast(Any, vop_parent), stable_ctr=True)
    with pytest.raises(ValueError, match="index must be greater than 0."):
        vop_optic.index = 0
    with pytest.raises(ValueError, match="absorption must be greater than or equal to 0."):
        vop_optic.absorption = -0.1
    with pytest.raises(ValueError, match="constringence must be greater than 0."):
        vop_optic.constringence = 0

    texture_layer = ProtoScene.MaterialInstance.Texture.Layer()
    texture_layer.image_properties.mapping_operator.SetInParent()
    mapping = TextureLayer.TextureUVMappingOperator(texture_layer.image_properties)
    with pytest.raises(
        ValueError,
        match="An axis system must contain exactly twelve values.",
    ):
        mapping.axis_system = [1.0, 0.0, 0.0]
