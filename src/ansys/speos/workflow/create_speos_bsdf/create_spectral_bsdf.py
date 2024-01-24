import math
import os

import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2 as spectral_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2_grpc as spectral_bsdf__v1__pb2_grpc
from google.protobuf.empty_pb2 import Empty
import numpy as np
from scipy import interpolate
from scipy.integrate import nquad

import ansys.speos.core as core

EPSILON = 1e-6


class BsdfMeasurementPoint:
    """
    class of a single bsdf point measure: bsdf = f(wavelength, incidence, theta)
    no phi dependency for measured bsdf
    """

    def __init__(self, input_incidence, input_wavelength, input_theta, input_bsdf):
        self.incidence = input_incidence
        self.wavelength = input_wavelength
        self.theta = input_theta
        self.bsdf = input_bsdf


class BrdfStructure:
    """
    class of BRDF contains method to host and convert 2d bsdf values into 3d bsdf file.
    """

    def __init__(self, wavelength_list):
        self.speos = core.Speos(host="localhost", port=50051)
        self.stub = spectral_bsdf__v1__pb2_grpc.SpectralBsdfServiceStub(self.speos.client.channel)
        wavelength_list = sorted(set(wavelength_list))
        self.rt = [1, 0]
        self.wavelengths = wavelength_list
        self.incident_angles = []
        self.theta_1d_ressampled = None
        self.phi_1d_ressampled = None
        self.measurement_2d_bsdf = []
        self.brdf = []
        self.btdf = []
        self.reflectance = []
        self.transmittance = []
        self.file_name = "gRPC_export_brdf"

    def bsdf_1d_function(self, wavelength, incident):
        """
        to provide a 1d linear fitting function for 2d measurement bsdf points.

        Parameters
        ----------
        wavelength : float
            wavelength used to find the target bsdf values.
        incident : float
            incident used to find the target bsdf values.

        Returns
        -------


        """
        theta_bsdf = [
            [MeasurePoint.theta, MeasurePoint.bsdf]
            for MeasurePoint in self.measurement_2d_bsdf
            if (MeasurePoint.incidence == incident and MeasurePoint.wavelength == wavelength)
        ]
        theta_brdf = [item for item in theta_bsdf if abs(item[0]) < 90]
        theta_brdf = np.array(theta_brdf).T
        if any(abs(item[0]) >= 90 for item in theta_bsdf):
            self.rt = [1, 1]
            theta_btdf_1 = [[abs(item[0]) - 180, item[1]] for item in theta_bsdf if item[0] <= -90]  # theta -180 -> - 90
            theta_btdf_2 = [[abs(item[0] - 180), item[1]] for item in theta_bsdf if item[0] >= 90]  # theta 90 -> 180
            theta_btdf = theta_btdf_1[::-1] + theta_btdf_2[::-1]
            theta_btdf = np.array(theta_btdf).T
            return (
                interpolate.interp1d(theta_brdf[0], theta_brdf[1], fill_value="extrapolate"),
                interpolate.interp1d(theta_btdf[0], theta_btdf[1], fill_value="extrapolate"),
                np.max(theta_brdf[0]),
            )
        return (
            interpolate.interp1d(theta_brdf[0], theta_brdf[1], fill_value="extrapolate"),
            None,
            np.max(theta_brdf[0]),
        )

    def __bsdf_integral(self, theta, phi, bsdf):
        """
        function to calculate the reflectance of the bsdf at one incident and wavelength

        Parameters
        ----------
        theta : np.array
        phi : np.array
        bsdf : 2d bsdf function

        Returns
        -------
        float
            bsdf half-done integration value.

        """
        theta_rad, phi_rad = np.radians(theta), np.radians(phi)  # samples on which integrande is known
        integrande = (1 / math.pi) * bsdf * np.sin(theta_rad)  # *theta for polar integration
        # calculation of integrande as from samples
        f = interpolate.RectBivariateSpline(phi_rad, theta_rad, integrande, kx=1, ky=1)
        r = nquad(f, [[0, 2 * math.pi], [0, math.pi / 2]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
        # reflectance calculaiton thanks to nquad lib
        return min(r[0], 1)  # return reflectance as percentage

    def convert_2D_3D(self, sampling=1):
        """
        convert the provided 2d measurement bsdf data.

        Parameters
        ----------
        sampling : int
            sampling used for exported 4d bsdf structure.

        Returns
        -------
        None

        """

        def bsdf_2d_function(theta, phi, bsdf_1d_func):
            """
            an internal method to calculate the 2d bsdf based on location theta and phi.

            Parameters
            ----------
            bsdf_1d_func:
                bsdf linear function
            theta : float
                target point with theta value
            phi : float
                target point with phi value

            Returns
            -------
            float
                value of bsdf value

            """
            # function that calculated 2d bsdf from 1d using revolution assumption.
            angular_distance = np.sqrt((incidence - theta * np.cos(np.radians(phi))) ** 2 + (theta * np.sin(np.radians(phi))) ** 2)
            # +4l for interpolation between measurement value on both side from specular direction
            angular_distance = np.where(angular_distance < EPSILON, 1, angular_distance)
            # special case for specular point (no interpolation due to null distance)
            weight = (incidence + angular_distance - theta * np.cos(np.radians(phi))) / (2 * angular_distance)
            weight = np.where(incidence + angular_distance > theta_max, 1, weight)
            # theta max : maximal reflected angle that is measured. for angle > theta_max we do not have values
            return weight * (bsdf_1d_func(incidence - angular_distance)) + (1 - weight) * bsdf_1d_func(incidence + angular_distance)

        if len(self.incident_angles) == 0:
            for measurement in self.measurement_2d_bsdf:
                if measurement.incidence not in self.incident_angles:
                    self.incident_angles.append(measurement.incidence)
        # mesh grid for direct 2d matrix calculation
        for incidence in self.incident_angles:
            for wavelength in self.wavelengths:
                brdf_1d, btdf_1d, theta_max = self.bsdf_1d_function(wavelength, incidence)
                self.theta_1d_ressampled = np.linspace(0, 90, int(90 / sampling + 1))
                self.phi_1d_ressampled = np.linspace(0, 360, int(360 / sampling + 1))
                theta_2d_ressampled, phi_2d_ressampled = np.meshgrid(self.theta_1d_ressampled, self.phi_1d_ressampled)
                self.brdf.append(bsdf_2d_function(theta_2d_ressampled, phi_2d_ressampled, brdf_1d))
                self.reflectance.append(self.__bsdf_integral(self.theta_1d_ressampled, self.phi_1d_ressampled, self.brdf[-1]))
                if self.rt[1] == 1 and btdf_1d is not None:
                    self.btdf.append(bsdf_2d_function(theta_2d_ressampled, phi_2d_ressampled, btdf_1d))
                    self.transmittance.append(self.__bsdf_integral(self.theta_1d_ressampled, self.phi_1d_ressampled, self.btdf[-1]))
        self.brdf = np.reshape(
            self.brdf,
            (
                len(self.incident_angles),
                len(self.wavelengths),
                2 * int(180 / sampling + 1) - 1,
                int(90 / sampling + 1),
            ),
        )
        if np.all(self.brdf == 0):
            msg = "All NULL values at brdf structure, please provide valid inputs"
            raise ValueError(msg)
        self.brdf = np.moveaxis(self.brdf, 2, 3)
        self.reflectance = np.reshape(self.reflectance, (len(self.incident_angles), len(self.wavelengths)))
        if self.rt[1] == 1 and len(self.btdf) != 0:
            self.btdf = np.reshape(
                self.btdf,
                (
                    len(self.incident_angles),
                    len(self.wavelengths),
                    2 * int(180 / sampling + 1) - 1,
                    int(90 / sampling + 1),
                ),
            )
            if np.all(self.btdf == 0):
                msg = "All NULL values at btdf structure"
                print(msg)
            self.btdf = np.moveaxis(self.btdf, 2, 3)
            self.btdf = np.flip(self.btdf, axis=0)
            self.transmittance = np.reshape(self.transmittance, (len(self.incident_angles), len(self.wavelengths)))

    def export_to_speos(self, export_dir, debug=False):
        msg = ""
        if self.reflectance.shape != (len(self.incident_angles), len(self.wavelengths)):
            msg += "incorrect format: reflectance dimension does not match with incident angle and wavelength\n"
        if self.brdf.shape != (
            len(self.incident_angles),
            len(self.wavelengths),
            len(self.theta_1d_ressampled),
            len(self.phi_1d_ressampled),
        ):
            msg += "incorrect data format: brdf dimension does not match\n"
        if len(self.btdf) != 0:
            self.rt[1] = 1
            if self.btdf.shape != (
                len(self.incident_angles),
                len(self.wavelengths),
                len(self.theta_1d_ressampled),
                len(self.phi_1d_ressampled),
            ):
                msg += "incorrect data format: btdf dimension does not match\n"
            if self.transmittance.shape != (len(self.incident_angles), len(self.wavelengths)):
                msg += "incorrect format: transmittance dimension does not match with incident angle and wavelength\n"
        if msg != "":
            print(msg)
            return

        bsdf = spectral_bsdf__v1__pb2.SpectralBsdfData(description="gRPC Spectral BSDF Description")
        for incident_angle in self.incident_angles:
            bsdf.incidence_samples.append(incident_angle * math.pi / 180.0)
        for wavelength_idx, wavelength in enumerate(self.wavelengths):
            bsdf.wavelength_samples.append(wavelength)
            for incident_angle_idx, incident_angle in enumerate(self.incident_angles):
                iw = bsdf.wavelength_incidence_samples.add()
                iw.reflection.integral = self.reflectance[incident_angle_idx, wavelength_idx]
                for phi in self.phi_1d_ressampled:
                    iw.reflection.phi_samples.append(phi * math.pi / 180.0)
                for theta_idx, theta in enumerate(self.theta_1d_ressampled):
                    iw.reflection.theta_samples.append(theta * math.pi / 180.0)
                    for phi_idx, _ in enumerate(self.phi_1d_ressampled):
                        iw.reflection.bsdf_cos_theta.append(self.brdf[incident_angle_idx, wavelength_idx, theta_idx, phi_idx])

                if self.rt[1] == 1:
                    iw.transmission.integral = self.transmittance[incident_angle_idx, wavelength_idx]
                    for phi in self.phi_1d_ressampled:
                        iw.transmission.phi_samples.append(phi * math.pi / 180.0)
                    for theta_idx, theta in enumerate(self.theta_1d_ressampled):
                        iw.transmission.theta_samples.append((theta + 90) * math.pi / 180.0)
                        for phi_idx, _ in enumerate(self.phi_1d_ressampled):
                            iw.transmission.bsdf_cos_theta.append(self.btdf[incident_angle_idx, wavelength_idx, theta_idx, phi_idx])

        file_name = spectral_bsdf__v1__pb2.FileName()
        if debug:
            file_name.file_name = os.path.join(export_dir, self.file_name + "_unencrypted.brdf")
            self.stub.Import(bsdf)
            self.stub.Save(file_name)

        indices = spectral_bsdf__v1__pb2.RefractiveIndices(refractive_index_1=1.0, refractive_index_2=1.5)
        self.stub.GenerateSpecularInterpolationEnhancementData(indices)
        cones = self.stub.GetSpecularInterpolationEnhancementData(Empty())
        self.stub.SetSpecularInterpolationEnhancementData(cones)
        file_name.file_name = os.path.join(export_dir, self.file_name + ".brdf")
        self.stub.Save(file_name)
