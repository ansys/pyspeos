# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""Provides a way to interact with Speos BSDF file."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Union

from google.protobuf.empty_pb2 import Empty
import numpy as np

import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2 as anisotropic_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2_grpc as anisotropic_bsdf__v1__pb2_grpc
from ansys.speos.core.speos import Speos


class BaseBSDF:
    """Super class for all BSDF datamodels.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
    stub :
        grpc stub to connect to BSDF service

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**

    """

    def __init__(self, speos: Speos, stub):
        self.client = speos.client
        self._stub = stub

    def _export_file(self, filepath):
        pass

    @property
    def has_transmission(self) -> bool:
        """Contains the BSDF Transmission data."""
        return self._has_transmission

    @has_transmission.setter
    def has_transmission(self, value: bool):
        if value:
            self._has_transmission = value
        else:
            self._has_transmission = value
            self._btdf = None

    @property
    def has_reflection(self) -> bool:
        """Contains the BSDF Reflection data."""
        return self._has_reflection

    @has_reflection.setter
    def has_reflection(self, value: bool):
        if value:
            self._has_reflection = value
        else:
            self._has_reflection = value
            self._brdf = None

    @property
    def brdf(self) -> Collection[BxdfDatapoint]:
        """List of BRDFDatapoints."""
        return self._brdf

    @brdf.setter
    def brdf(self, value: Collection[BxdfDatapoint]):
        check = any([bxdf.is_brdf for bxdf in value])
        if check is True or value is None:
            self._brdf = value
            self.has_reflection = True
        else:
            msg = "One or multiple datapoints are transmission datapoints"
            raise ValueError(msg)

    @property
    def btdf(self) -> Collection[BxdfDatapoint]:
        """List of BTDFDatapoints."""
        return self._btdf

    @btdf.setter
    def btdf(self, value: Collection[BxdfDatapoint]):
        check = any([not bxdf.is_brdf for bxdf in value])
        if check is True or value is None:
            self._btdf = value
            self.has_transmission = True
        else:
            msg = "One or multiple datapoints are reflection datapoints"
            raise ValueError(msg)

    @property
    def nb_incidents(self) -> list[int]:
        """Number of incidence angle for reflection and transmission.

        Returns
        -------
        list[int]:
            first value of the list is nb of reflective data, second value is nb of transmittive
            data
        """
        return [len(self.brdf), len(self.btdf)]

    @property
    def incident_angles(self) -> list[Union[list[float], None], Union[list[float], None]]:
        """List of incident angles for reflection and transmission.

        Returns
        -------
        list[Union[list[float], None],Union[list[float], None]]
            Returns a nested list of incidence angels for reflective and transmittive
            data if not available the value will be None
        """
        r_angle = [bxdf.incident_angle for bxdf in self.brdf]
        t_angle = [bxdf.incident_angle for bxdf in self.btdf]
        return [r_angle, t_angle]


class AnisotropicBSDF(BaseBSDF):
    """BSDF - Bidirectional scattering distribution function.

    This class contains the methods and functions to load and edit existing Speos bsdf datasets.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos Object to connect to speos rpc server
    file_path : Union[Path, str]
        File path to bsdf file
    """

    def __init__(self, speos: Speos, file_path: Union[Path, str] = None):
        super().__init__(
            speos, anisotropic_bsdf__v1__pb2_grpc.AnisotropicBsdfServiceStub(speos.client.channel)
        )
        self._spectrum_incidence = [0, 0]
        self._spectrum_anisotropy = [0, 0]
        if file_path:
            self.file_path = Path(file_path)
            self._grpcbsdf = self._import_file(str(self.file_path))
            self._brdf, self._btdf = self._extract_bsdf()
            self._has_transmission = bool(self._btdf)
            self._has_reflection = bool(self._brdf)
            self._transmission_spectrum, self._reflection_spectrum = self._extract_spectrum()
        else:
            self.file_path = None
            self._grpcbsdf = None
            self.has_transmission = False
            self.has_reflection = False
            self._transmission_spectrum, self._reflection_spectrum = None, None

            # anisotropic file
            self.ansistropy_vector = [1, 0, 0]
            self._spectrum = None
            self.description = ""

    def _import_file(self, filepath):
        file_name = anisotropic_bsdf__v1__pb2.FileName()
        file_name.file_name = str(filepath)
        self._stub.Load(file_name)
        return self._stub.Export(Empty())

    def _extract_bsdf(self) -> tuple[Collection[BxdfDatapoint], Collection[BxdfDatapoint]]:
        self.description = self._grpcbsdf.description
        self.ansistropy_vector = [
            self._grpcbsdf.anisotropy_vector.x,
            self._grpcbsdf.anisotropy_vector.y,
            self._grpcbsdf.anisotropy_vector.z,
        ]
        brdf = []
        btdf = []
        for i in range(len(self._grpcbsdf.reflection.anisotropic_samples)):
            ani_bsdf_data = self._grpcbsdf.reflection.anisotropic_samples[i]
            anisotropic_angle = ani_bsdf_data.anisotropic_sample
            for j in range(len(ani_bsdf_data.incidence_samples)):
                bsdf_data = ani_bsdf_data.incidence_samples[j]
                incident_angle = bsdf_data.incidence_sample
                thetas = np.array(bsdf_data.theta_samples)
                phis = np.array(bsdf_data.phi_samples)
                bsdf = np.array(bsdf_data.bsdf_cos_theta)
                tis = bsdf_data.integral
                brdf.append(
                    BxdfDatapoint(True, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle)
                )
        for i in range(len(self._grpcbsdf.transmission.anisotropic_samples)):
            ani_bsdf_data = self._grpcbsdf.transmission.anisotropic_samples[i]
            anisotropic_angle = ani_bsdf_data.anisotropic_sample
            for j in range(len(ani_bsdf_data.incidence_samples)):
                bsdf_data = ani_bsdf_data.incidence_samples[j]
                incident_angle = bsdf_data.incidence_sample
                thetas = np.array(bsdf_data.theta_samples)
                phis = np.array(bsdf_data.phi_samples)
                bsdf = np.array(bsdf_data.bsdf_cos_theta)
                tis = bsdf_data.integral
                btdf.append(
                    BxdfDatapoint(True, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle)
                )
        return brdf, btdf

    def _extract_spectrum(self) -> list[np.ndarray, np.ndarray]:
        if self.has_reflection:
            self.spectrum_incidence[0] = self._grpcbsdf.reflection.spectrum_incidence
            self.spectrum_anisotropy[0] = self._grpcbsdf.reflection.spectrum_anisotropy
        if self.has_transmission:
            self.spectrum_incidence[1] = self._grpcbsdf.transmission.spectrum_incidence
            self.spectrum_anisotropy[1] = self._grpcbsdf.transmission.spectrum_anisotropy
        refl_s = np.array([[], []])
        trans_s = np.array([[], []])
        for value in self._grpcbsdf.reflection.spectrum:
            refl_s = np.append(refl_s, [[value.wavelength], [value.coefficient]], axis=1)
        for value in self._grpcbsdf.transmission.spectrum:
            trans_s = np.append(trans_s, [[value.wavelength], [value.coefficient]], axis=1)
        return [refl_s, trans_s]

    def _export_file(self, filepath):
        pass

    @property
    def spectrum_incidence(self) -> list[float]:
        """Incident angle (theta) of spectrum measurement.

        First value is for reflection second for transmission
        """
        return self._spectrum_incidence

    @spectrum_incidence.setter
    def spectrum_incidence(self, value) -> list[float]:
        if isinstance(value, float) and self.has_reflection and self.has_transmission:
            raise ValueError("You need to define the value for both reflection and transmission")
        elif isinstance(value, float) and 0 <= value <= np.pi / 2:
            if self.has_reflection:
                self._spectrum_incidence[0] = value
            else:
                self._spectrum_incidence[1] = value
        elif isinstance(value, list):
            if len(value) == 2 and any([0 <= theta <= np.pi / 2 for theta in value]):
                self._spectrum_incidence = value
        else:
            raise ValueError(
                "You need to define the value in radian for both reflection and transmission"
            )

    @property
    def spectrum_anisotropy(self) -> list[float]:
        """Incident angle (phi) of spectrum measurement.

        First value is for reflection second for transmission
        """
        return self._spectrum_anisotropy

    @spectrum_anisotropy.setter
    def spectrum_anisotropy(self, value):
        if isinstance(value, float) and self.has_reflection and self.has_transmission:
            raise ValueError("You need to define the value for both reflection and transmission")
        elif isinstance(value, float) and 0 <= value <= 2 * np.pi:
            if self.has_reflection:
                self._spectrum_anisotropy[0] = value
            else:
                self._spectrum_anisotropy[1] = value
        elif isinstance(value, list):
            if len(value) == 2 and any([0 <= theta <= 2 * np.pi for theta in value]):
                self._spectrum_anisotropy = value
        else:
            raise ValueError(
                "You need to define the value in radian for both reflection and transmission"
            )

    @property
    def reflection_spectrum(self):
        """Reflection Spectrum of the bsdf.

        The spectrum is used to modulate the bsdf.
        """
        return self._reflection_spectrum

    @reflection_spectrum.setter
    def reflection_spectrum(self, value: list[Collection[float], Collection[float]]):
        if len(value[0]) == len(value[1]):
            self._reflection_spectrum = value
        else:
            raise ValueError("You need the same number of wavelength and energy values")

    @property
    def transmission_spectrum(self):
        """Transmission  Spectrum of the bsdf.

        The spectrum is used to modulate the bsdf.
        """
        return self._transmission_spectrum

    @transmission_spectrum.setter
    def transmission_spectrum(self, value: list[Collection[float], Collection[float]]):
        if len(value[0]) == len(value[1]):
            self._transmission_spectrum = value
        else:
            raise ValueError("You need the same number of wavelength and energy values")

    def reset(self):
        """Reset BSDF data to what was stored in file."""
        pass

    def commit(self):
        """Sent Data to gRPC interface."""
        pass

    def save(self, file_path: Union[Path, str], commit: bool = True) -> Path:
        """Save a Speos anistropic bsdf.

        Parameters
        ----------
        file_path : Union[Path, str]
            Filepath to save bsdf
        commit : bool
            commit data before saving

        Returns
        -------
        Path
            File location
        """
        file_path = Path(file_path)
        file_name = anisotropic_bsdf__v1__pb2.FileName()
        if not file_path.parent.exists():
            file_path.parent.mkdir()
        elif file_path.suffix == ".anisotropicbsdf":
            file_name.file_name = str(file_path)
        else:
            file_name.file_name = str(file_path.parent / (file_path.name + ".anisotropicbsdf"))
        self.file_path = Path(file_name.file_name)
        self._stub.Save(file_name)
        return self.file_path


class BxdfDatapoint:
    """Class to store a BxDF data point.

    Parameters
    ----------
    is_brdf : bool
        true for transmittive date, False for reflective
    incident_angle : float
        incident angle in radian
    theta_values : Collection[float]
        list of theta values for the bxdf data matrix, in radian
    phi_values : Collection[float]
        list of phi values for the bxdf data matrix, in radian
    bxdf : Collection[float]
        nested list of bxdf values in 1/sr
    anisotropy : float
        Anisotropy angle in radian
    """

    def __init__(
        self,
        is_brdf: bool,
        incident_angle: float,
        theta_values: Collection[float],
        phi_values: Collection[float],
        bxdf: Collection[float],
        tis: float,
        anisotropy: float = 0,
    ):
        # data_reset
        self._theta_values = []
        self._phi_values = []
        self._bxdf = None
        # define data
        self.is_brdf = is_brdf
        self.incident_angle = incident_angle
        self.anisotropy = anisotropy
        self.theta_values = theta_values
        self.phi_values = phi_values
        self.bxdf = bxdf
        self.tis = tis

    @property
    def anisotropy(self):
        """Anisotropy angels of Datapoint."""
        return self._anisotropy

    @anisotropy.setter
    def anisotropy(self, value):
        if 0 <= value <= 2 * np.pi:
            self._anisotropy = value
        else:
            msg = "Anisotropy angle needs to be between [0, 2*pi]"
            raise ValueError(msg)

    @property
    def bxdf(self) -> np.array:
        """BxDF data as np matrix in 1/sr.

        Returns
        -------
        np.array:
            bxdf data in shape theta_values, phi_values

        """
        return self._bxdf

    @bxdf.setter
    def bxdf(self, value: Collection[float]):
        if value is not None:
            bxdf = np.array(value)
            if np.shape(bxdf) == (len(self.theta_values), len(self.phi_values)):
                self._bxdf = bxdf
            elif np.shape(bxdf) == (len(self.phi_values), len(self.theta_values)):
                self._bxdf = bxdf.transpose()
            else:
                try:
                    self._bxdf = bxdf.reshape((len(self.theta_values), len(self.phi_values)))
                except ValueError:
                    raise ValueError("bxdf data has incorrect dimensions")
        elif value is None:
            self._bxdf = None
        else:
            raise ValueError("bxdf data has to be a 2d Array of bsdfdata")

    @property
    def is_brdf(self):
        """Type of bxdf data point eitehr reflective or transmittive.

        Returns
        -------
        bool:
            true if reflective false if transmittive
        """
        return self._is_brdf

    @is_brdf.setter
    def is_brdf(self, value):
        self._is_brdf = bool(value)

    @property
    def incident_angle(self):
        """Incident angle of the Datapoint in radian.

        Returns
        -------
        float:
            Incidence angle in radian

        """
        return self._incident_angle

    @incident_angle.setter
    def incident_angle(self, value):
        if 0 <= value <= np.pi / 2:
            self._incident_angle = value
        else:
            msg = "Incident angle needs to be between [0, pi/2]"
            raise ValueError(msg)

    def set_incident_angle(self, value, is_deg=True):
        """Allow to set an incident value in degree.

        Parameters
        ----------
        value : float
            value to be set
        is_deg : bool
            Allows to define if value is radian or degree
        """
        if is_deg:
            self.incident_angle = np.deg2rad(value)
        else:
            self.incident_angle = value

    @property
    def theta_values(self):
        """List of theta values for which values are stored in bxdf data."""
        return self._theta_values

    @theta_values.setter
    def theta_values(self, value):
        if not self.is_brdf:
            if any([np.pi / 2 <= theta <= np.pi for theta in value]):
                self._theta_values = value
                if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                    self.bxdf = None
            else:
                msg = "Theta values for Transmission need to be between [pi/2, pi]"
                raise ValueError(msg)
        else:
            if any([0 <= theta <= np.pi / 2 for theta in value]):
                self._theta_values = value
                if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                    self.bxdf = None
            else:
                msg = "Theta values for Transmission need to be between [0, pi/2]"
                raise ValueError(msg)

    @property
    def phi_values(self):
        """List of phi values  for which values are stored in bxdf data."""
        return self._phi_values

    @phi_values.setter
    def phi_values(self, value):
        if any([0 <= phi <= 2 * np.pi for phi in value]):
            self._phi_values = value
            if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                self.bxdf = None
        else:
            msg = "Theta values for Transmission need to be between [pi/2, pi]"
            raise ValueError(msg)
