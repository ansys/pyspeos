# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""
Test source template.
"""
import json
import os

from ansys.api.speos.common.v1 import data_pb2
import grpc
import pytest

from ansys.speos.core.intensity_template import IntensityTemplate
from ansys.speos.core.source_template import SourceTemplate
from ansys.speos.core.spectrum import Spectrum
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_source_template(speos: Speos):
    """Test the source template creation."""
    assert speos.client.healthy is True

    # Get DB
    source_t_db = speos.client.source_templates()  # Create source_templates stub from client channel
    spec_db = speos.client.spectrums()  # Create spectrums stub from client channel
    intens_t_db = speos.client.intensity_templates()  # Create intensity_templates stub from client channel

    # This spectrum will be used by both src_t_luminaire and src_t_surface
    spec_bb_2500 = spec_db.create(
        Spectrum(name="blackbody_2500", description="blackbody spectrum - T 2500K", blackbody=Spectrum.BlackBody(temperature=2500.0))
    )

    # This intensity template will be used in several luminaire source template
    intens_t_lamb = intens_t_db.create(
        message=IntensityTemplate(
            name="lambertian_180", description="lambertian intensity template 180", cos=IntensityTemplate.Cos(N=1.0, total_angle=180.0)
        )
    )

    # Luminaire source template with flux from intensity file
    src_t_luminaire = source_t_db.create(
        message=SourceTemplate(
            name="luminaire_0",
            description="Luminaire source template",
            luminaire=SourceTemplate.Luminaire(
                flux_from_intensity_file=SourceTemplate.FromIntensityFile(),
                intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
                spectrum_guid=spec_bb_2500.key,
            ),
        )
    )
    assert src_t_luminaire.key != ""

    # Surface with luminous flux, exitance constant
    src_t_surface = source_t_db.create(
        message=SourceTemplate(
            name="surface_0",
            description="Surface source template",
            surface=SourceTemplate.Surface(
                luminous_flux=SourceTemplate.Luminous(luminous_value=683.0),
                intensity_guid=intens_t_lamb.key,
                exitance_constant=SourceTemplate.Surface.ExitanceConstant(),
                spectrum_guid=spec_bb_2500.key,
            ),
        )
    )
    assert src_t_surface.key != ""

    # Some parameters are not compatible
    # For example a Surface source template with flux from intensity file AND
    # no intensity file provided (instead lambertian intensity template)
    with pytest.raises(grpc.RpcError) as exc_info:
        source_t_db.create(
            message=SourceTemplate(
                name="surface_err0",
                description="Surface source template in error",
                surface=SourceTemplate.Surface(
                    flux_from_intensity_file=SourceTemplate.FromIntensityFile(),
                    intensity_guid=intens_t_lamb.key,
                    exitance_constant=SourceTemplate.Surface.ExitanceConstant(),
                    spectrum_guid=spec_bb_2500.key,
                ),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "FluxFromIntensityWithoutFile"

    # Another incompatibility
    # Surface source template with spectrum from xmp file AND no xmp file provided
    with pytest.raises(grpc.RpcError) as exc_info:
        source_t_db.create(
            message=SourceTemplate(
                name="surface_err1",
                description="Surface source template in error",
                surface=SourceTemplate.Surface(
                    luminous_flux=SourceTemplate.Luminous(luminous_value=683.0),
                    intensity_guid=intens_t_lamb.key,
                    exitance_constant=SourceTemplate.Surface.ExitanceConstant(),
                    spectrum_from_xmp_file=SourceTemplate.Surface.SpectrumFromXMPFile(),
                ),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTNullSpectrum"

    src_t_luminaire.delete()
    src_t_surface.delete()
    spec_bb_2500.delete()
    intens_t_lamb.delete()


# Tests not yet available on linux
if os.name == "nt":

    def test_action_get_ray_file_info(speos: Speos):
        """Test the source template action : get_ray_file_info."""
        assert speos.client.healthy is True

        # Create source_templates stub from client channel
        source_t_db = speos.client.source_templates()

        # Create a source template link - a Ray-File source
        src_t_rayfile = source_t_db.create(
            message=SourceTemplate(
                name="Ray-File",
                rayfile=SourceTemplate.RayFile(
                    ray_file_uri=os.path.join(test_path, "Rays.ray"),
                    flux_from_ray_file=SourceTemplate.FromRayFile(),
                    spectrum_from_ray_file=SourceTemplate.RayFile.SpectrumFromRayFile(),
                ),
            )
        )

        # Get flux
        flux = src_t_rayfile.get_ray_file_info().flux
        assert flux.magnitude == data_pb2.Magnitude.radiant_flux
        assert flux.unit == data_pb2.Unit.watts
        assert flux.values[0] == 4.01765775680542
