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

import numpy as np

import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2_grpc as anisotropic_bsdf__v1__pb2_grpc
from ansys.speos.core.speos import Speos


class BSDF:
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
        self.client = speos.client
        self._stub = anisotropic_bsdf__v1__pb2_grpc.AnisotropicBsdfServiceStub(speos.client.channel)
        if not file_path:
            self.file_path = Path(file_path)
            self._grpcbsdf = self._importfile(str(self.file_path))
            self._brdf, self._btdf = self._extract_bsdf()
            self._has_transmission = bool(self._btdf)
            self._has_reflection = bool(self._brdf)
            self._transmission_spectrum, self._reflection_spectrum = self._extract_spectrum()
        else:
            self.file_path = None
            self._grpcbsdf = None
            self.has_transmission = False
            self.has_reflection = False
            self._spectrum = None

    def _importfile(self, filepath):
        pass

    def _extract_bsdf(self) -> tuple[Collection[BxdfDatapoint], Collection[BxdfDatapoint]]:
        pass

    def _extract_spectrum(self) -> Collection[Collection[float], Collection[float]]:
        pass

    def _export_file(self, filepath):
        pass

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

    def reset(self):
        """Reset BSDF data to what was stored in file."""
        pass


class BxdfDatapoint:
    """Class to store a BxDF data point.

    Parameters
    ----------
    bxdf_type : bool
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
        bxdf_type: bool,
        incident_angle: float,
        theta_values: Collection[float],
        phi_values: Collection[float],
        bxdf: Collection[float],
        anisotropy: float = 0,
    ):
        self.is_brdf = bxdf_type
        self.incident_angle = incident_angle
        self.anisotropy = anisotropy
        self.theta_values = theta_values
        self.phi_values = phi_values
        self.bxdf = bxdf

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
        if value:
            bxdf = np.array(value, ndmin=2)
            if np.shape(bxdf) == (len(self.theta_values), len(self.phi_values)):
                self._bxdf = bxdf
            elif np.shape(bxdf) == (len(self.phi_values), len(self.theta_values)):
                self._bxdf = bxdf.transpose()
            else:
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
