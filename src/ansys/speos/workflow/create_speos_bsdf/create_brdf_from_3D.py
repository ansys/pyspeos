import math

import numpy as np

from src.ansys.speos.workflow.create_speos_bsdf.create_spectral_bsdf import BrdfStructure


def create_brdf(
    wavelengths: np.array,
    incident_angles: np.array,
    theta_list: np.array,
    phi_list: np.array,
    reflectances: np.array,
    transmittances: np.array,
    brdf: np.array,
    btdf: np.array,
) -> None:
    """
    create speos brdf file.

    Parameters
    ----------
    wavelengths:np.array
    incident_angles:np.array
    theta_list:np.array
    phi_list:np.array
    reflectances: np.array
    transmittances: np.array
    brdf: np.array
    btdf: np.array
    """
    brdf_data = BrdfStructure(wavelengths)
    brdf_data.file_name = "example_2"
    brdf_data.incident_angles = incident_angles
    brdf_data.theta_1d_ressampled = theta_list
    brdf_data.phi_1d_ressampled = phi_list
    brdf_data.reflectance = reflectances
    brdf_data.brdf = brdf
    brdf_data.transmittance = transmittances
    brdf_data.btdf = btdf
    brdf_data.export_to_speos(r"D:\\", debug=True)


def main():
    """
    main function to create speos brdf file.
    """
    wavelength_nb = 10
    incident_angle_nb = 7
    theta_nb = 10
    phi_nb = 37

    wavelength_list = np.linspace(360.0, 780.0, wavelength_nb)
    incident_angles = np.linspace(0, 90, incident_angle_nb)
    theta_list = np.linspace(0, 90, theta_nb)
    phi_list = np.linspace(0, 360, phi_nb)
    reflectance = np.zeros((len(incident_angles), len(wavelength_list)))
    transmittance = np.zeros((len(incident_angles), len(wavelength_list)))
    brdf = np.zeros((len(incident_angles), len(wavelength_list), len(theta_list), len(phi_list)))
    btdf = np.zeros((len(incident_angles), len(wavelength_list), len(theta_list), len(phi_list)))

    for incident_angle_idx, incident_angle in enumerate(incident_angles):
        for wavelength_idx, wavelength in enumerate(wavelength_list):
            reflectance[incident_angle_idx, wavelength_idx] = 0.5
            for theta_idx, theta in enumerate(theta_list):
                for phi_idx, phi in enumerate(phi_list):
                    brdf[incident_angle_idx, wavelength_idx, theta_idx, phi_idx] = 0.5 * math.cos(theta * math.pi / 180.0) / math.pi

            transmittance[incident_angle_idx, wavelength_idx] = 0.5
            for theta_idx, theta in enumerate(theta_list):
                for phi_idx, phi in enumerate(phi_list):
                    btdf[incident_angle_idx, wavelength_idx, theta_idx, phi_idx] = (
                        0.5 * abs(math.cos(math.pi * 0.5 + theta * math.pi / 180.0)) / math.pi
                    )
    create_brdf(wavelength_list, incident_angles, theta_list, phi_list, reflectance, transmittance, brdf, btdf)


main()
