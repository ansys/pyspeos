# # How to create a anisotropic bsdf file

# This tutorial demonstrates how to create bsdf file using pyspeos

# ## What is a BSDF

# BSDF stands for Bidirectional Scattering Distribution Function, which is
# a mathematical function that characterizes how light is scattered from a
# surface.
# In Speos we have two models to represent BSDF data: Spectral BSDF(*.brdf)
# and Anisotropic BSDF (*.anisotropicbsdf).
# The first allows for each wavelength to store a full bsdf description with
# this it allows for great color representation.
# the second uses spectral modulation to represent the color but allows for
# anisotropic behaviour by taking a BSDF for each anisotropic angle.
# Both formats need an interpolation between incident/anisotropic angles and wavelength
# In many cases the data comes from measurements and need coordinate transformations
# to be used

# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

import numpy as np

from ansys.speos.core import Speos
from ansys.speos.core.bsdf import AnisotropicBSDF, BxdfDatapoint
from ansys.speos.core.kernel.client import (
    SpeosClient,
    default_docker_channel,
)
from ansys.speos.core.launcher import launch_local_speos_rpc_server

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ### Define helper functions


def clean_all_dbs(speos_client: SpeosClient):
    """Clean all database entries of a current SpeosRPC client.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        SpeosRPC server client

    Returns
    -------
    None
    """
    for item in (
        speos_client.jobs().list()
        + speos_client.scenes().list()
        + speos_client.simulation_templates().list()
        + speos_client.sensor_templates().list()
        + speos_client.source_templates().list()
        + speos_client.intensity_templates().list()
        + speos_client.spectrums().list()
        + speos_client.vop_templates().list()
        + speos_client.sop_templates().list()
        + speos_client.parts().list()
        + speos_client.bodies().list()
        + speos_client.faces().list()
    ):
        item.delete()


def create_lambertian_bsdf(is_brdf, nb_theta=5, nb_phi=5):
    """
    Create a lambertian distribution as np.array.

    Parameters
    ----------
    is_brdf: bool
        True if generating brdf data, False btdf data
    nb_theta: int
        number of theta samplings
    nb_phi: int
        number of phi samplings

    Returns
    -------
    thetas: np.array,
        shape (nb_theta)
    phis: np.array,
        shape (nb_phi)
    bxdf: np.array,
        shape (nb_theta, nb_phi)

    """
    thetas = np.zeros(nb_theta)
    phis = np.zeros(nb_phi)
    bxdf = np.zeros((nb_theta, nb_phi))
    if is_brdf:
        for t in range(nb_theta):
            thetas[t] = t * np.pi * 0.5 / (nb_theta - 1)
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                bxdf[t, p] = np.cos(thetas[t]) / np.pi
    else:
        for t in range(nb_theta):
            thetas[t] = np.pi * 0.5 * (1 + t / (nb_theta - 1))
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                bxdf[t, p] = (
                    -np.cos(thetas[t]) / np.pi if -np.cos(thetas[t]) / np.pi > 0.0000000001 else 0
                )
    return thetas, phis, bxdf


def create_gaussian_bsdf(is_brdf, inc, nb_theta=91, nb_phi=361, fwhm=np.radians(40)):
    """
    Create a gaussian distribution as np.array.

    Parameters
    ----------
    is_brdf: bool
        True if generating brdf data, False btdf data
    inc: float
        incident angle in radians
    nb_theta: int
        number of theta samplings
    nb_phi: int
        number of phi samplings
    fwhm: float
        Gaussian width in radians

    Returns
    -------
    thetas: np.array,
        shape (nb_theta)
    phis: np.array,
        shape (nb_phi)
    bxdf: np.array,
        shape (nb_theta, nb_phi)

    """
    thetas = np.zeros(nb_theta)
    phis = np.zeros(nb_phi)
    bxdf = np.zeros((nb_theta, nb_phi))
    if is_brdf:
        vector_specular_direction = [np.sin(inc), 0.0, np.cos(inc)]
        for t in range(nb_theta):
            thetas[t] = t * np.pi * 0.5 / (nb_theta - 1)
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                vector_direction = [
                    np.sin(thetas[t]) * np.cos(phis[p]),
                    np.sin(thetas[t]) * np.sin(phis[p]),
                    np.cos(thetas[t]),
                ]
                alpha = np.arccos(np.dot(vector_specular_direction, vector_direction))
                sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
                bxdf[t, p] = np.exp(-0.5 * (alpha / sigma) ** 2)
    else:
        # Here, the angle of specular transmission is identical
        # to the angle of incidence (the refraction is not considered)
        vector_specular_direction = [np.sin(inc), 0.0, -np.cos(inc)]
        for t in range(nb_theta):
            thetas[t] = np.pi * 0.5 * (1 + t / (nb_theta - 1))
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                vector_direction = [
                    np.sin(thetas[t]) * np.cos(phis[p]),
                    np.sin(thetas[t]) * np.sin(phis[p]),
                    np.cos(thetas[t]),
                ]
                alpha = np.arccos(np.dot(vector_specular_direction, vector_direction))
                sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
                bxdf[t, p] = np.exp(-0.5 * (alpha / sigma) ** 2)
    return thetas, phis, bxdf


def create_spectrum(value, w_start=380.0, w_end=780.0, w_step=10):
    """
    Create a spectrum for a bsdf.

    Parameters
    ----------
    value: float
        spectrum value
    w_start: float
        wavelength start
    w_end: float
        wavelength end
    w_step: int
        wavelength sampling number

    Returns
    -------
    spectrum: np.array,

    """
    spectrum = np.zeros((2, w_step))
    for w in range(w_step):
        spectrum[0, w] = w_start + w * (w_end - w_start) / (w_step - 1)
        spectrum[1, w] = value
    return spectrum


# ## Model Setup
#
# ### Load assets
# The assets used to run this example are available in the
# [PySpeos repository](https://github.com/ansys/pyspeos/) on GitHub.
#
# > **Note:** Make sure you have downloaded simulation assets and
# > set ``assets_data_path`` to point to the assets folder.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

# ### Create Anisotropic BSDF from datapoints
# To create and save a bsdf we need to first create a connection to the SpeosRPC server
# ### Connect to the RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launch_local_speos_rpc_server()

# ### Create a BXDFDatapoint - Example of a lambertian BRDF
# to create a bsdf we need the bsdf for multiple incident angles.
# In this example we assume the color doesn't change over the incident
# angles so we can use anisotropic bsdf and we assume the data has no
# anisotropy

clean_all_dbs(speos.client)  # clean all the database entries

incident_angles = [np.radians(5), np.radians(25), np.radians(40), np.radians(65), np.radians(85)]
all_bxdfs = []
for inc in incident_angles:
    thetas, phis, brdf = create_lambertian_bsdf(True)
    all_bxdfs.append(BxdfDatapoint(True, inc, thetas, phis, brdf))
print("all brdf", all_bxdfs[0])

# ### Create Anisotropic BSDF class instance
new_bsdf = AnisotropicBSDF(speos)
new_bsdf.description = "PySpeos BSDF Example"
new_bsdf.anisotropy_vector = [1, 0, 0]

# Create Spectrum with 80% reflectivity
spectrum = create_spectrum(0.8)

# Assign reflection spectrum to bsdf
new_bsdf.spectrum_incidence = np.radians(5)
new_bsdf.spectrum_anisotropy = np.radians(0)
new_bsdf.has_reflection = True
new_bsdf.reflection_spectrum = spectrum
new_bsdf.brdf = all_bxdfs

save_path = assets_data_path / "example_bsdf_lambertian.anisotropicbsdf"
new_bsdf.save(save_path)
print(new_bsdf)

# ### Create a BXDFDatapoint - Example of a gaussian BRDF and BTDF
# to create a bsdf we need the bsdf for multiple incident angles.
# In this example we assume the color doesn't change over the incident
# angles so we can use anisotropic bsdf and we assume the data has no
# anisotropy

clean_all_dbs(speos.client)  # clean all the database entries

incident_angles = [np.radians(5), np.radians(25), np.radians(40), np.radians(65), np.radians(85)]
all_bxdfs_reflexion = []
all_bxdfs_transmission = []

for inc in incident_angles:
    thetas, phis, brdf = create_gaussian_bsdf(
        True, inc, nb_theta=91, nb_phi=361, fwhm=np.radians(20)
    )
    all_bxdfs_reflexion.append(BxdfDatapoint(True, inc, thetas, phis, brdf))

for inc in incident_angles:
    thetas, phis, brdf = create_gaussian_bsdf(
        False, inc, nb_theta=91, nb_phi=361, fwhm=np.radians(40)
    )
    all_bxdfs_transmission.append(BxdfDatapoint(False, inc, thetas, phis, brdf))

# ### Create Anisotropic BSDF class instance
new_bsdf_gaussian = AnisotropicBSDF(speos)
new_bsdf_gaussian.description = "PySpeos BSDF Example"
new_bsdf_gaussian.anisotropy_vector = [1, 0, 0]

# Assign reflection spectrum to bsdf
new_bsdf_gaussian.spectrum_incidence = np.radians(5)
new_bsdf_gaussian.spectrum_anisotropy = np.radians(0)

new_bsdf_gaussian.has_reflection = True
new_bsdf_gaussian.has_transmission = True
new_bsdf_gaussian.reflection_spectrum = create_spectrum(0.5)
new_bsdf_gaussian.transmission_spectrum = create_spectrum(0.4)
new_bsdf_gaussian.brdf = all_bxdfs_reflexion
new_bsdf_gaussian.btdf = all_bxdfs_transmission

save_path = assets_data_path / "example_bsdf_gaussian.anisotropicbsdf"
new_bsdf_gaussian.save(save_path)
print(new_bsdf_gaussian)


# ### BSDF Interpolation Enhancement
# This section shows:
# - How to apply automatic interpolation settings and save a post-processed bsdf file.
# - How to change interpolation settings, apply the new settings to bsdf,
# and save the post-processed file
# - How to re-load a bsdf file has interpolation enhanced and retrieve the interpolation settings.

print(
    new_bsdf_gaussian.interpolation_settings
)  # user can check if there was interpolation settings, here is None
new_bsdf_gaussian.create_interpolation_enhancement(index_1=1.0, index_2=1.4)
print(new_bsdf_gaussian.interpolation_settings)  # Now interpolation settings is not None
new_bsdf_gaussian.save(
    file_path=assets_data_path / "example_bsdf_gaussian_automatic_interpolation.anisotropicbsdf"
)

# Apply user defined interpolation enhancement

interpolation_settings = new_bsdf_gaussian.create_interpolation_enhancement(
    index_1=1.0, index_2=1.4
)
interpolation_settings_reflection = (
    interpolation_settings.get_reflection_interpolation_settings
)  # return as fixed dictionary, user cannot add/remove item
print(interpolation_settings_reflection)

# Change interpolation settings

interpolation_settings_reflection["0"][str(np.radians(5))]["half_angle"] = 0.523
interpolation_settings_reflection["0"][str(np.radians(5))]["height"] = 0.5

# Set the changed interpolation settings back to bsdf file and save

interpolation_settings.set_interpolation_settings(
    is_brdf=True, settings=interpolation_settings_reflection
)
new_bsdf_gaussian.save(
    file_path=assets_data_path / "example_bsdf_gaussian_user_interpolation.anisotropicbsdf"
)

# Load a bsdf file with interpolation enhanced

clean_all_dbs(speos.client)
saved_bsdf = AnisotropicBSDF(
    speos=speos,
    file_path=assets_data_path / "example_bsdf_gaussian_user_interpolation.anisotropicbsdf",
)
print(
    saved_bsdf.interpolation_settings
)  # here an InterpolationEnhancement Class object is returned
previous_settings = saved_bsdf.interpolation_settings
print(
    previous_settings.get_reflection_interpolation_settings
)  # user can review the previous settings
previous_settings = saved_bsdf.create_interpolation_enhancement(index_1=1.0, index_2=1.4)
print(
    previous_settings.get_reflection_interpolation_settings
)  # with same index values, user use create_interpolation_enhancement to create a new settings

# Defined new interpolation settings for an already enhanced bsdf file

previous_settings_diff_index = saved_bsdf.create_interpolation_enhancement(index_1=1.0, index_2=1.5)
print(
    previous_settings.get_reflection_interpolation_settings
)  # with different index values, a new automatic settings is returned

speos.close()
