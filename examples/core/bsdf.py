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
# anisotropic behaviour by taking a BSDF for each anistropic angle.
# Both formats need an interpolation between incident/anistropic angles and wavelength
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
from ansys.speos.core.launcher import launch_local_speos_rpc_server

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ### Define helper functions


def create_lambertian_bsdf(is_brdf, nb_theta=5, nb_phi=5):
    """Create a lambertian Distribution as np.array."""
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
    return thetas, phis, bxdf


def create_spectrum(value, w_start=380.0, w_end=780.0, w_step=10):
    """Create a spectrum for a bsdf."""
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
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launch_local_speos_rpc_server(port=GRPC_PORT)

# ### Create a BXDFDatapoint
# to create a bsdf we need the bsdf for multiple incident angles.
# In this example we assume the color doesn't change over the icnident
# angles so we can use anisotropic bsdf and we assume the data has no
# anisotropy

incident_angles = [np.radians(5), np.radians(25), np.radians(45), np.radians(65), np.radians(85)]
all_brdfs = []
for inc in incident_angles:
    thetas, phis, brdf = create_lambertian_bsdf(True)
    all_brdfs.append(BxdfDatapoint(True, inc, thetas, phis, brdf))
print(all_brdfs[0])

# ### Create Anistropic BSDF class instance

new_bsdf = AnisotropicBSDF(speos)
new_bsdf.description = "PySpeos BSDF Example"
new_bsdf.anisotropy_vector = [1, 0, 0]

# Create Spectrum with 80% reflectivity
spectrum = create_spectrum(0.8)

# Assign reflection spectrum to bsdf
new_bsdf.has_reflection = True
new_bsdf.spectrum_incidence = np.radians(0)
new_bsdf.spectrum_anisotropy = np.radians(0)
new_bsdf.reflection_spectrum = spectrum

# Assign brdf data
new_bsdf.brdf = all_brdfs
save_path = assets_data_path / "example_bsdf.anisotropicbsdf"
new_bsdf.save(save_path)
print(new_bsdf)
