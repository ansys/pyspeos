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

"""Check that a running Speos server accepts the input files PySpeos writes locally.

:mod:`ansys.speos.core.generic.file_format` always writes ``*.material``, ``*.coated``,
``*.scattering``, ``*.simplescattering`` and ``*.spectrum`` files with Windows line endings
(``\\r\\n``), because most Speos applications only run on Windows. This module builds a full
simulation whose optical property and sources reference files generated that way (plus a
binary ``*.ray`` file, unaffected by line endings but generated locally too), and commits it
to the Speos server used by the test suite, to confirm the server reads them correctly
regardless of the platform it runs on. The volume and surface optical property files are
parametrized over every dispersion, scattering and surface model PySpeos can write.

3D Texture mapping files (``*.OPT3DMapping``) are not covered here: PySpeos has no feature
yet to attach one to a project.
"""

import itertools
from pathlib import Path

import pytest

from ansys.speos.core import (
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    GeoRef,
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialKettlerHelmholtz,
    MaterialSellmeier,
    Project,
    Ray,
    RayFile,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringSurfaceFile,
    Spectrum,
    SpectrumFile,
    Speos,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.source import SourceLuminaire, SourceRayFile
from tests.conftest import test_path

_ABSORPTION_WAVELENGTHS = [400.0, 550.0, 700.0]
_ABSORPTION_VALUES = [0.1, 0.2, 0.01]
"""Absorption curve shared by every generated volume material."""

_DIFFUSION_WAVELENGTHS = [486.0, 532.0, 643.0]
_DIFFUSION_VALUES = [0.016813, 7.3952e-17, 0.017344]
"""Diffusion curve shared by every generated scattering volume material."""

_DISPERSION_CURVE = MaterialDispersionCurve(
    wavelengths=[486.0, 532.0, 643.0], indices=[2.0, 1.5, 1.2]
)
"""Index curve used whenever a scattering phase function needs a dispersion model."""


def _material(dispersion, scattering=None) -> MaterialFile:
    """Build a material sharing the absorption curve, and the diffusion curve if scattering."""
    material = MaterialFile(
        dispersion=dispersion,
        absorption_wavelengths=_ABSORPTION_WAVELENGTHS,
        absorption_values=_ABSORPTION_VALUES,
    )
    if scattering is not None:
        material.scattering_wavelengths = _DIFFUSION_WAVELENGTHS
        material.scattering_values = _DIFFUSION_VALUES
        material.scattering = scattering
    return material


VOLUME_MATERIALS = {
    # One material per dispersion model, with no scattering.
    "constringence": _material(MaterialConstringence(constringence=57.2, index=1.49)),
    "dispersion_curve": _material(_DISPERSION_CURVE),
    "sellmeier": _material(
        MaterialSellmeier(b1=1.03, c1=0.0060, b2=0.23, c2=0.02, b3=1.01, c3=103.56)
    ),
    "kettler_helmholtz": _material(MaterialKettlerHelmholtz(a0=2.4, a1=-0.01, a2=0.001)),
    # One material per scattering phase function, all sharing the same dispersion model.
    "henyey_greenstein": _material(
        _DISPERSION_CURVE, VolumeScatteringHenyeyGreenstein(wavelengths=[], anisotropies=[0.9])
    ),
    "double_henyey_greenstein": _material(
        _DISPERSION_CURVE,
        VolumeScatteringDoubleHenyeyGreenstein(
            wavelengths=[], anisotropies_1=[0.9], anisotropies_2=[0.9], ratios=[0.5]
        ),
    ),
    "gegenbauer": _material(
        _DISPERSION_CURVE,
        VolumeScatteringGegenbauer(wavelengths=[], anisotropies=[0.9], alphas=[0.5]),
    ),
    "user_defined": _material(
        _DISPERSION_CURVE,
        VolumeScatteringUserDefined(
            wavelengths=[], angles=[0.0, 90.0, 180.0], values=[[100.0], [50.0], [0.0]]
        ),
    ),
}
"""One :class:`MaterialFile` per dispersion model and per scattering phase function."""

SURFACE_MATERIALS = {
    "coated": CoatedSurfaceFile(
        wavelengths=[480.0, 580.0, 780.0],
        incident_angles=[0.0, 50.0, 70.0, 90.0],
        samples=[[CoatedSurfaceSample(35.0, 65.0, 31.9, 68.1)] * 3 for _ in range(4)],
    ),
    "scattering": ScatteringSurfaceFile(
        wavelengths=[400.0, 700.0],
        incident_angles=[0.0, 90.0],
        samples=[[ScatteringSurfaceSample(lambertian_reflection=50.0)] * 2 for _ in range(2)],
    ),
    "simple_scattering": SimpleScatteringSurfaceFile(mode="Reflection", lambertian=100.0),
}
"""One surface property file per Speos surface property format."""

# Pair each volume material with a surface material, cycling the shorter list, so every
# format is exercised once instead of testing the full cross-product of combinations.
_TEST_CASES = list(zip(VOLUME_MATERIALS, itertools.cycle(SURFACE_MATERIALS)))


@pytest.mark.parametrize(
    ("volume_name", "surface_name"), _TEST_CASES, ids=[f"{v}-{s}" for v, s in _TEST_CASES]
)
def test_generated_files_are_usable_in_a_full_simulation(
    speos: Speos, tmp_path: Path, surface_name: str, volume_name: str
):
    """A whole simulation combining every generated file type must commit successfully."""
    material_path = VOLUME_MATERIALS[volume_name].save(tmp_path / "integration.material")
    surface_path = SURFACE_MATERIALS[surface_name].save(
        tmp_path / ("integration" + SURFACE_MATERIALS[surface_name].EXTENSION)
    )

    spectrum_path = SpectrumFile(
        description="Integration test spectrum",
        wavelengths=[400.0, 550.0, 700.0],
        values=[10.0, 100.0, 50.0],
    ).save(tmp_path / "integration.spectrum")

    ray_path = RayFile(
        rays=[
            Ray(position=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
            Ray(position=(1.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
        ],
        radiant_flux=1.0,
        luminous_flux=112.0,
    ).save(tmp_path / "integration.ray")

    p = Project(speos=speos)
    root_part = p.create_root_part()
    face = root_part.create_body(name="Body.1").create_face(name="Face.1")
    face.vertices = [0, 1, 0, 0, 2, 0, 1, 2, 0]
    face.facets = [0, 1, 2]
    face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    root_part.commit()

    # Volume optical property, from a generated *.material file.
    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_library()
    opt_prop.vop_library.material_file_uri = material_path
    # Surface optical property, from a generated surface property file.
    opt_prop.set_surface_library()
    opt_prop.sop_library.file_uri = surface_path
    opt_prop.geometries = [GeoRef.from_native_link(geopath="Body.1")]
    opt_prop.commit()

    sensor = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    sensor.axis_system = [0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sensor.commit()

    # Luminaire source, spectrum from a generated *.spectrum file.
    luminaire = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    luminaire.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
    luminaire.spectrum.set_library().file_uri = spectrum_path
    luminaire.commit()

    # Ray file source, from a generated *.ray file.
    ray_source = p.create_source(name="RayFile.1", feature_type=SourceRayFile)
    ray_source.ray_file_uri = ray_path
    ray_source.commit()

    simulation = p.create_simulation(name="Direct.1", feature_type=SimulationDirect)
    simulation.sensor_paths = [sensor]
    simulation.source_paths = [luminaire, ray_source]
    simulation.commit()

    assert simulation.simulation_template_link is not None
    assert simulation.simulation_template_link.get().HasField("direct_mc_simulation_template")

    assert opt_prop.vop_template_link.get().HasField("library")
    assert opt_prop.vop_template_link.get().library.material_file_uri.endswith(
        "integration.material"
    )
    assert opt_prop.sop_template_link.get().HasField("library")
    assert opt_prop.sop_template_link.get().library.sop_file_uri.endswith(surface_path.name)

    spectrum_guid = luminaire.source_template_link.get().luminaire.spectrum_guid
    assert spectrum_guid
    created_spectrum = Spectrum(speos_client=speos.client, name="", key=spectrum_guid)
    assert created_spectrum._to_dict()["library"]["file_uri"].endswith("integration.spectrum")

    assert ray_source.source_template_link.get().rayfile.ray_file_uri.endswith("integration.ray")
