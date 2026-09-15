# # How to create Speos input files

# This tutorial demonstrates how to create the files that Speos takes as inputs:
# materials, surface optical properties, spectra, ray files and 3D texture mappings.

# ## What are Speos input files

# Speos reads a handful of documented file formats to describe optical properties,
# spectral distributions, measured light sources and textured surfaces. They are usually
# authored in the Speos editors, but they can also be generated from raw measurement data
# or from another simulation tool.
#
# PySpeos models each of these formats with a dataclass exposing the same three methods:
#
# * `save(path)` writes the model to a file,
# * `load(path)` reads a file back into a model,
# * `validate()` checks the model against the constraints of the format.
#
# Unlike the rest of PySpeos, these classes work entirely offline: no connection to a
# Speos RPC server is needed. Once the files are written, they are handed over to the
# features that consume them, through their file URI.

# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path
import tempfile

from ansys.speos.core import (
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    MaterialConstringence,
    MaterialFile,
    Ray,
    RayFile,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringSurfaceFile,
    SpectrumFile,
    Texture3DMappingFile,
    TexturePattern,
    VolumeScatteringHenyeyGreenstein,
)

# -

# ### Define constants
# Every file created by this example is written into a temporary directory.
OUTPUT_DIR = Path(tempfile.mkdtemp(prefix="pyspeos_file_formats_"))

# ## Create a spectrum file

# A `*.spectrum` file is a sampled spectral distribution, used by most source types and by
# the camera sensors. The wavelengths are given in nm and the values in percent.

spectrum = SpectrumFile(
    description="Amber LED",
    wavelengths=[560.0, 580.0, 600.0, 620.0, 640.0],
    values=[5.0, 45.0, 100.0, 55.0, 10.0],
)
spectrum_path = spectrum.save(OUTPUT_DIR / "amber_led.spectrum")
print(spectrum_path.read_text())

# Reading the file back gives an equivalent model, which makes it easy to adjust a file
# that already exists.

reloaded = SpectrumFile.load(spectrum_path)
print(reloaded.wavelengths, reloaded.values)

# ## Create a volume optical property file

# A `*.material` file describes how light travels inside a body. It always holds a
# dispersion model and an absorption curve. Here the dispersion is given by the refractive
# index at 587.6 nm and the Abbe number, which is how most data sheets report it.

pmma = MaterialFile(
    description="PMMA",
    dispersion=MaterialConstringence(constringence=57.2, index=1.49),
    absorption_wavelengths=[486.0, 532.0, 643.0],
    absorption_values=[0.0001, 0.00015, 0.0005],
)
pmma_path = pmma.save(OUTPUT_DIR / "pmma.material")
print(pmma_path.read_text())

# Adding a scattering phase function turns the same file into a diffusing material. The
# diffusion coefficient is given in mm-1 for each wavelength, and the Henyey-Greenstein
# anisotropy factor drives how forward the scattering is.

diffuser = MaterialFile(
    description="Diffusing PMMA",
    dispersion=MaterialConstringence(constringence=57.2, index=1.49),
    absorption_wavelengths=[486.0, 643.0],
    absorption_values=[0.0001, 0.0005],
    scattering_wavelengths=[480.0, 555.0, 650.0],
    scattering_values=[0.016, 0.0165, 0.025],
    scattering=VolumeScatteringHenyeyGreenstein(
        wavelengths=[480.0, 555.0, 650.0], anisotropies=[0.8, 0.9, 0.9]
    ),
)
diffuser_path = diffuser.save(OUTPUT_DIR / "diffusing_pmma.material")
print(diffuser_path.read_text())

# ## Create surface optical property files

# The `*.simplescattering` format is the quickest way to describe a scattering surface: it
# does not depend on the wavelength nor on the angle of incidence. This one is a perfect
# white Lambertian reflector.

white = SimpleScatteringSurfaceFile(mode="Reflection", absorption=0.0, lambertian=100.0)
white_path = white.save(OUTPUT_DIR / "white_diffuser.simplescattering")
print(white_path.read_text())

# The `*.scattering` format describes the same physics, but every contribution can vary
# with the angle of incidence and the wavelength. Speos needs at least two wavelengths and
# expects the angles of incidence to span 0 to 90 degrees.
#
# What is left once the reflection and transmission contributions are summed is absorbed,
# which the `absorption` property reports.

# +
half_diffusing = ScatteringSurfaceSample(
    specular_reflection=30.0,
    lambertian_reflection=20.0,
    specular_transmission=20.0,
    lambertian_transmission=10.0,
)
glazing = ScatteringSurfaceFile(
    description="Half diffusing glazing",
    wavelengths=[400.0, 700.0],
    incident_angles=[0.0, 90.0],
    samples=[[half_diffusing, half_diffusing], [half_diffusing, half_diffusing]],
)
glazing_path = glazing.save(OUTPUT_DIR / "glazing.scattering")

print("Absorption at 0 degrees and 400 nm:", glazing.samples[0][0].absorption, "%")
print(glazing_path.read_text())
# -

# The `*.coated` format describes a non-scattering coating, with the reflection and the
# transmission given separately for the S and P polarizations. A Speos coating is only
# valid for the rays crossing the interface in one direction.

# +
coating_rows = {
    0.0: [(31.9, 68.1), (1.5, 98.5), (25.7, 74.3)],
    50.0: [(11.3, 88.7), (11.4, 88.6), (23.3, 76.7)],
    90.0: [(100.0, 0.0), (100.0, 0.0), (100.0, 0.0)],
}
coating = CoatedSurfaceFile(
    description="Antireflective coating",
    wavelengths=[480.0, 580.0, 780.0],
    incident_angles=list(coating_rows),
    samples=[
        [
            CoatedSurfaceSample(reflection, transmission, reflection, transmission)
            for reflection, transmission in row
        ]
        for row in coating_rows.values()
    ],
)
coating_path = coating.save(OUTPUT_DIR / "antireflective.coated")
print(coating_path.read_text())
# -

# ## Create a ray file

# A ray file holds the rays emitted by a measured or simulated source. Each ray carries a
# start position in mm, a direction given as cosines, a wavelength in nm and a relative
# energy. The direction must be a unit vector, which `validate()` enforces.

# +
rays = RayFile(
    rays=[
        Ray(position=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
        Ray(position=(0.1, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
        Ray(position=(0.0, 0.1, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
    ],
    radiant_flux=1.0,
    luminous_flux=112.0,
)
rays_path = rays.save(OUTPUT_DIR / "collimated.ray")
print(rays_path, rays_path.stat().st_size, "bytes")
# -

# The same rays can be exported to the text flavor that the Speos ray file editor reads.
# Beware that this flavor does not carry the flux of the file.

text_path = rays.save_text(OUTPUT_DIR / "collimated.txt")
print(text_path.read_text())

# ## Create a 3D texture mapping file

# A Speos 3D Texture is made of a mesh and of a `*.OPT3DMapping` file, which lays out
# where each pattern sits on the support. That mapping file is the recipe handed over to
# manufacture the physical part, so it is often generated or post-processed outside of
# Speos.
#
# Below, a rectangular grid of patterns is laid out, with a scale growing along the grid
# so that the light extraction increases away from the source.

# +
patterns = []
for row in range(5):
    for column in range(10):
        scale = round(0.5 + 0.1 * column, 2)
        patterns.append(
            TexturePattern(
                position=(column * 2.0, row * 2.0, 0.0),
                scale=(scale, scale, scale),
            )
        )

mapping_path = Texture3DMappingFile(patterns=patterns).save(OUTPUT_DIR / "light_guide.OPT3DMapping")
print("\n".join(mapping_path.read_text().splitlines()[:4]))
# -

# Reading the mapping back gives every pattern placement, ready to be inspected or
# converted to the format expected by a tooling supplier.

mapping = Texture3DMappingFile.load(mapping_path)
print(len(mapping.patterns), "patterns")
print(mapping.patterns[-1])
