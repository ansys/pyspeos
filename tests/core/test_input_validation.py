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

from types import SimpleNamespace

from ansys.api.speos.spectrum.v1 import spectrum_pb2
import pytest

from ansys.speos.core import Intensity, Spectrum
from ansys.speos.core.ground_plane import GroundPlane
from ansys.speos.core.kernel.intensity_template import ProtoIntensityTemplate
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.opt_prop import BaseSop, BaseVop, TextureLayer
from ansys.speos.core.simulation import BaseSimulation


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
    ground = GroundPlane.__new__(GroundPlane)
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
        weight=SimpleNamespace(minimum_energy_percentage=0.0),
        stable_ctr=True,
    )
    with pytest.raises(ValueError, match="minimum_energy_percentage must be between 0 and 1."):
        weight.minimum_energy_percentage = 1.5


def test_opt_prop_setters_validate_inputs() -> None:
    """Optical property helpers should reject invalid input values."""
    sop_parent = SimpleNamespace(_sop_template=ProtoSOPTemplate(name="SOP.Validation"))
    sop_library = BaseSop.SopLibrary(parent=sop_parent, stable_ctr=True)
    with pytest.raises(TypeError, match="file_uri must be a string or Path."):
        sop_library.file_uri = 42

    vop_parent = SimpleNamespace(_vop_template=ProtoVOPTemplate(name="VOP.Validation"))
    vop_optic = BaseVop.VopOptic(parent=vop_parent, stable_ctr=True)
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
