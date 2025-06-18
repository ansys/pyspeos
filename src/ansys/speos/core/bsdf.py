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

from collections import Counter, UserDict
from collections.abc import Collection
from pathlib import Path
from typing import Union
import warnings

from google.protobuf.empty_pb2 import Empty
import grpc
import numpy as np

import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2 as anisotropic_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2_grpc as anisotropic_bsdf__v1__pb2_grpc
import ansys.api.speos.bsdf.v1.bsdf_creation_pb2 as bsdf_creation__v1__pb2
import ansys.api.speos.bsdf.v1.bsdf_creation_pb2_grpc as bsdf_creation__v1__pb2_grpc
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2 as spectral_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2_grpc as spectral_bsdf__v1__pb2_grpc
import ansys.speos.core
from ansys.speos.core.speos import Speos


class BaseBSDF:
    """Super class for all BSDF datamodels.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
    stub :
        grpc stub to connect to BSDF service
    namespace :
        grpc namespace for the bsdf

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**

    """

    def __init__(self, speos: Speos, stub, namespace):
        self.client = speos.client
        self._stub = stub
        self._grpcbsdf = None
        self.has_transmission = False
        self.has_reflection = False
        self.anisotropy_vector = [1, 0, 0]
        self.description = ""
        self.__namespace = namespace
        self.__interpolation_settings = None

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
    def brdf(self, value: list[BxdfDatapoint]):
        if value is None:
            self._brdf = value
        else:
            check = any([bxdf.is_brdf for bxdf in value])
            if check is True:
                value.sort(key=lambda x: (x.anisotropy, x.wavelength, x.incident_angle))
                self._brdf = value
                self.has_reflection = True
            else:
                raise ValueError("One or multiple datapoints are transmission datapoints")

    @property
    def btdf(self) -> Collection[BxdfDatapoint]:
        """List of BTDFDatapoints."""
        return self._btdf

    @btdf.setter
    def btdf(self, value: list[BxdfDatapoint]):
        if value is None:
            self._btdf = value
        else:
            check = any([not bxdf.is_brdf for bxdf in value])
            if check is True:
                value.sort(key=lambda x: (x.anisotropy, x.wavelength, x.incident_angle))
                self._btdf = value
                self.has_transmission = True
            else:
                raise ValueError("One or multiple datapoints are reflection datapoints")

    @property
    def nb_incidents(self) -> list[int]:
        """Number of incidence angle for reflection and transmission.

        Returns
        -------
        list[int]:
            first value of the list is nb of reflective data, second value is nb of transmittive
            data
        """
        if self.has_transmission:
            t = len(self.btdf)
        else:
            t = 0
        if self.has_reflection:
            r = len(self.brdf)
        else:
            r = 0
        return [r, t]

    @property
    def incident_angles(self) -> list[Union[list[float], None], Union[list[float], None]]:
        """List of incident angles for reflection and transmission.

        Returns
        -------
        list[Union[list[float], None],Union[list[float], None]]
            Returns a nested list of incidence angels for reflective and transmittive
            data if not available the value will be None
        """
        if self.has_transmission:
            t_angle = [bxdf.incident_angle for bxdf in self.btdf]
        else:
            t_angle = []
        if self.has_reflection:
            r_angle = [bxdf.incident_angle for bxdf in self.brdf]
        else:
            r_angle = []
        return [r_angle, t_angle]

    @property
    def interpolation_settings(self) -> Union[None, InterpolationEnhancement]:
        """Interpolation enhancement settings of the bsdf file.

        If bsdf file does not have interpolation enhancement settings, return None.
        if bsdf file has interpolation enhancement settings, return InterpolationEnhancement.
        """
        return self.__interpolation_settings

    def create_interpolation_enhancement(
        self, index_1: float = 1.0, index_2: float = 1.0
    ) -> InterpolationEnhancement:
        """Apply automatic interpolation enhancement.

        Return interpolation settings to user if settings need change.

        Parameters
        ----------
        index_1 : float
            outside refractive index
        index_2 : float
            inside refractive index

        Returns
        -------
        ansys.speos.core.bsdf._InterpolationEnhancement
            automatic interpolation settings with index_1 = 1 and index_2 = 1 by default.
        """
        self._stub.Import(self._grpcbsdf)
        self.__interpolation_settings = InterpolationEnhancement(
            bsdf=self, bsdf_namespace=self.__namespace, index_1=index_1, index_2=index_2
        )
        return self.__interpolation_settings


class InterpolationEnhancement:
    """Class to facilitate Specular interpolation enhancement.

    Notes
    -----
    **Do not instantiate this class yourself**
    """

    class _InterpolationSettings(UserDict):
        """Class to facilitate interpolation settings as fixed dictionary."""

        def __init__(self, initial_data) -> None:
            self._fixed_keys = list(initial_data.keys())
            super().__init__(initial_data)

        def __setitem__(self, key, value) -> None:
            """Dis-able setting values under two conditions.

            1) methods to set value if dictionary value is a fixed dictionary.
            2) key is not inside fixed dictionary.
            """
            if key in self._fixed_keys:
                if not isinstance(self.get(key), self.__class__):
                    super().__setitem__(key, value)
                else:
                    raise ValueError(
                        "Cannot update key {key} with a FixedKeyDict as value.".format(key=key)
                    )
            else:
                raise KeyError("Cannot add new key: {key} is not allowed.".format(key=key))

        def __delitem__(self, key) -> None:
            """Dis-able delete key from a fixed dictionary."""
            raise KeyError("Deletion of key: {key}  is not allowed.".format(key=key))

        def __iter__(self):
            """Iterate keys in fixed key order."""
            return iter(self._fixed_keys)

        def keys(self) -> list[str]:
            """Return keys from fixed dictionary."""
            return self._fixed_keys

        def items(self):
            """Return items from fixed dictionary."""
            return [(key, self[key]) for key in self._fixed_keys]

        def update(self, *args, **kwargs) -> None:
            """
            Update the fixed dictionary with multiple values.

            Example:
                my_dict.update({'a': 10, 'b': 20})
                my_dict.update({'x': 100})
                my_dict.update(x=200, y=300)

            Parameters
            ----------
            args: tuple
                Dictionary or iterable of key-value pairs.
            kwargs: dict
                Key-value pairs to update the dictionary.
            """
            updates = dict(*args, **kwargs)
            for key in updates:
                if key not in self._fixed_keys:
                    raise KeyError("Cannot add new key: {key} is not allowed.".format(key=key))
                if isinstance(self.get(key), self.__class__):
                    raise ValueError(
                        "Cannot update key {key} with FixedKeyDict as value.".format(key=key)
                    )
            super().update(updates)

    def __init__(
        self,
        bsdf: Union[AnisotropicBSDF, SpectralBRDF],
        bsdf_namespace: Union[spectral_bsdf__v1__pb2, anisotropic_bsdf__v1__pb2],
        index_1: Union[float, None] = 1.0,
        index_2: Union[float, None] = 1.0,
    ) -> None:
        self._bsdf = bsdf

        self.__cones_data = None
        try:
            self.__cones_data = self._bsdf._stub.GetSpecularInterpolationEnhancementData(Empty())
            if index_1 is not None and index_2 is not None:
                self.__indices = bsdf_namespace.RefractiveIndices(
                    refractive_index_1=index_1,
                    refractive_index_2=index_2,
                )
                self._bsdf._stub.GenerateSpecularInterpolationEnhancementData(self.__indices)
                self.__cones_data = self._bsdf._stub.GetSpecularInterpolationEnhancementData(
                    Empty()
                )
        except grpc.RpcError:
            self.__indices = bsdf_namespace.RefractiveIndices(
                refractive_index_1=index_1,
                refractive_index_2=index_2,
            )
            self._bsdf._stub.GenerateSpecularInterpolationEnhancementData(self.__indices)
            self.__cones_data = self._bsdf._stub.GetSpecularInterpolationEnhancementData(Empty())

    @property
    def index1(self) -> float:
        """Refractive index on reflection side."""
        return self.__cones_data.refractive_index_1

    @index1.setter
    def index1(self, value: Union[float, int]) -> None:
        """Set refractive index on reflection side."""
        self.__cones_data.refractive_index_1 = value
        self._bsdf._stub.Import(self._bsdf._grpcbsdf)
        self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)

    @property
    def index2(self) -> float:
        """Refractive index on transmission side."""
        return self.__cones_data.refractive_index_2

    @index2.setter
    def index2(self, value: Union[float, int]) -> None:
        """Set refractive index on transmission side."""
        self.__cones_data.refractive_index_2 = value
        self._bsdf._stub.Import(self._bsdf._grpcbsdf)
        self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)

    @property
    def get_reflection_interpolation_settings(self) -> Union[None, _InterpolationSettings]:
        """Return a fixed dictionary for reflection interpolation settings to be set by user."""
        if not self._bsdf.has_reflection:
            return None
        if isinstance(self._bsdf, AnisotropicBSDF):
            reflection_interpolation_settings = self._InterpolationSettings(
                {str(key): 0 for key in self._bsdf.anisotropic_angles[0]}
            )
            for aniso_sample_index, ani_sample in enumerate(
                self.__cones_data.reflection.anisotropic_samples
            ):
                reflection_incident_interpolation_settings = self._InterpolationSettings(
                    {str(key): 0 for key in self._bsdf.incident_angles[0]}
                )
                tmp_reflection_key = str(self._bsdf.anisotropic_angles[0][aniso_sample_index])
                reflection_interpolation_settings.update(
                    {tmp_reflection_key: reflection_incident_interpolation_settings}
                )
                for incident_sample_index, incident in enumerate(ani_sample.incidence_samples):
                    tmp_reflection_incident_key = str(
                        self._bsdf.incident_angles[0][
                            aniso_sample_index * len(ani_sample.incidence_samples)
                            + incident_sample_index
                        ]
                    )
                    reflection_interpolation_settings[
                        str(self._bsdf.anisotropic_angles[0][aniso_sample_index])
                    ].update(
                        {
                            tmp_reflection_incident_key: {
                                "half_angle": incident.cone_half_angle,
                                "height": incident.cone_height,
                            }
                        }
                    )
            return reflection_interpolation_settings
        if isinstance(self._bsdf, SpectralBRDF):
            reflection_interpolation_settings = self._InterpolationSettings(
                {str(key): 0 for key in self._bsdf.wavelength}
            )
            r_angles = list(set(self._bsdf.incident_angles[0]))
            for wl_index, wl in enumerate(self._bsdf.wavelength):
                tmp_reflection_key = str(wl)
                reflection_incident_interpolation_settings = self._InterpolationSettings(
                    {str(key): 0 for key in r_angles}
                )
                reflection_interpolation_settings.update(
                    {tmp_reflection_key: reflection_incident_interpolation_settings}
                )
                for inc_index, inc in enumerate(r_angles):
                    ani_sample = self.__cones_data.wavelength_incidence_samples[
                        (wl_index + 1) * inc_index
                    ]
                    tmp_reflection_incident_key = str(inc)
                    reflection_interpolation_settings[str(wl)].update(
                        {
                            tmp_reflection_incident_key: {
                                "half_angle": ani_sample.reflection.cone_half_angle,
                                "height": ani_sample.reflection.cone_height,
                            }
                        }
                    )
            return reflection_interpolation_settings
        else:
            raise ValueError("only anisotropic and spectral bsdf supported")

    def set_interpolation_settings(
        self, is_brdf: bool, settings: InterpolationEnhancement._InterpolationSettings
    ) -> None:
        """Set interpolation obtained from bsdf Class or that modified by user.

        Parameters
        ----------
        is_brdf: bool
            true if settings is for brdf, else for btdf
        settings: InterpolationEnhancement._InterpolationSettings
            interpolation settings.
        """
        if not isinstance(
            settings, ansys.speos.core.bsdf.InterpolationEnhancement._InterpolationSettings
        ):
            raise ImportError("only interpolation settings are supported")
        if is_brdf and not self._bsdf.has_reflection:
            raise ValueError("BSDF has no reflection data")
        if not is_brdf and not self._bsdf.has_transmission:
            raise ValueError("BSDF has no transmission data")
        if isinstance(self._bsdf, AnisotropicBSDF):
            self._bsdf._stub.Import(self._bsdf._grpcbsdf)
            if is_brdf:
                for iso_sample_key_index, iso_sample_key in enumerate(settings.keys()):
                    for incident_key_index, incident_key in enumerate(
                        settings[iso_sample_key].keys()
                    ):
                        self.__cones_data.reflection.anisotropic_samples[
                            iso_sample_key_index
                        ].incidence_samples[incident_key_index].cone_half_angle = settings[
                            iso_sample_key
                        ][incident_key]["half_angle"]
                        self.__cones_data.reflection.anisotropic_samples[
                            iso_sample_key_index
                        ].incidence_samples[incident_key_index].cone_height = settings[
                            iso_sample_key
                        ][incident_key]["height"]
                self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)
            else:
                for iso_sample_key_index, iso_sample_key in enumerate(settings.keys()):
                    for incident_key_index, incident_key in enumerate(
                        settings[iso_sample_key].keys()
                    ):
                        self.__cones_data.transmission.anisotropic_samples[
                            iso_sample_key_index
                        ].incidence_samples[incident_key_index].cone_half_angle = settings[
                            iso_sample_key
                        ][incident_key]["half_angle"]
                        self.__cones_data.transmission.anisotropic_samples[
                            iso_sample_key_index
                        ].incidence_samples[incident_key_index].cone_height = settings[
                            iso_sample_key
                        ][incident_key]["height"]
                self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)
        elif isinstance(self._bsdf, SpectralBRDF):
            self._bsdf._stub.Import(self._bsdf._grpcbsdf)
            if is_brdf:
                for wl_sample_key_index, wl_sample_key in enumerate(settings.keys()):
                    for incident_key_index, incident_key in enumerate(
                        settings[wl_sample_key].keys()
                    ):
                        self.__cones_data.wavelength_incidence_samples[
                            (wl_sample_key_index + 1) * incident_key_index
                        ].reflection.cone_half_angle = settings[wl_sample_key][incident_key][
                            "half_angle"
                        ]
                        self.__cones_data.wavelength_incidence_samples[
                            (wl_sample_key_index + 1) * incident_key_index
                        ].reflection.cone_height = settings[wl_sample_key][incident_key]["height"]
                self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)
            else:
                for wl_sample_key_index, wl_sample_key in enumerate(settings.keys()):
                    for incident_key_index, incident_key in enumerate(
                        settings[wl_sample_key].keys()
                    ):
                        self.__cones_data.wavelength_incidence_samples[
                            (wl_sample_key_index + 1) * incident_key_index
                        ].transmission.cone_half_angle = settings[wl_sample_key][incident_key][
                            "half_angle"
                        ]
                        self.__cones_data.wavelength_incidence_samples[
                            (wl_sample_key_index + 1) * incident_key_index
                        ].transmission.cone_height = settings[wl_sample_key][incident_key]["height"]
                self._bsdf._stub.SetSpecularInterpolationEnhancementData(self.__cones_data)
        else:
            raise ValueError("only anisotropic bsdf and spectral brdf are supported")

    @property
    def get_transmission_interpolation_settings(self) -> Union[None, _InterpolationSettings]:
        """Return a fixed dictionary for reflection interpolation settings to be set by user."""
        if not self._bsdf.has_transmission:
            return None
        if isinstance(self._bsdf, AnisotropicBSDF):
            transmission_interpolation_settings = self._InterpolationSettings(
                {str(key): 0 for key in self._bsdf.anisotropic_angles[1]}
            )
            for aniso_sample_index, ani_sample in enumerate(
                self.__cones_data.transmission.anisotropic_samples
            ):
                transmission_incident_interpolation_settings = self._InterpolationSettings(
                    {str(key): 0 for key in self._bsdf.incident_angles[1]}
                )
                tmp_transmission_key = str(self._bsdf.anisotropic_angles[1][aniso_sample_index])
                transmission_interpolation_settings.update(
                    {tmp_transmission_key: transmission_incident_interpolation_settings}
                )
                for incident_sample_index, incident in enumerate(ani_sample.incidence_samples):
                    tmp_transmission_incident_key = str(
                        self._bsdf.incident_angles[1][
                            aniso_sample_index * len(ani_sample.incidence_samples)
                            + incident_sample_index
                        ]
                    )
                    transmission_interpolation_settings[
                        str(self._bsdf.anisotropic_angles[1][aniso_sample_index])
                    ].update(
                        {
                            tmp_transmission_incident_key: {
                                "half_angle": incident.cone_half_angle,
                                "height": incident.cone_height,
                            }
                        }
                    )
            return transmission_interpolation_settings
        if isinstance(self._bsdf, SpectralBRDF):
            transmission_interpolation_settings = self._InterpolationSettings(
                {str(key): 0 for key in self._bsdf.wavelength}
            )
            r_angles = list(set(self._bsdf.incident_angles[0]))
            for wl_index, wl in enumerate(self._bsdf.wavelength):
                tmp_reflection_key = str(wl)
                transmission_incident_interpolation_settings = self._InterpolationSettings(
                    {str(key): 0 for key in r_angles}
                )
                transmission_interpolation_settings.update(
                    {tmp_reflection_key: transmission_incident_interpolation_settings}
                )
                for inc_index, inc in enumerate(r_angles):
                    sample = self.__cones_data.wavelength_incidence_samples[
                        (wl_index + 1) * inc_index
                    ]
                    tmp_reflection_incident_key = str(inc)
                    transmission_interpolation_settings[str(wl)].update(
                        {
                            tmp_reflection_incident_key: {
                                "half_angle": sample.transmission.cone_half_angle,
                                "height": sample.transmission.cone_height,
                            }
                        }
                    )
            return transmission_interpolation_settings
        else:
            raise ValueError("only anisotropic and spectral bsdf supported")


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
            speos,
            anisotropic_bsdf__v1__pb2_grpc.AnisotropicBsdfServiceStub(speos.client.channel),
            anisotropic_bsdf__v1__pb2,
        )
        self._spectrum_incidence = [0, 0]
        self._spectrum_anisotropy = [0, 0]
        if file_path:
            file_path = Path(file_path)
            self._grpcbsdf = self._import_file(file_path)
            self._brdf, self._btdf = self._extract_bsdf()
            self._has_transmission = bool(self._btdf)
            self._has_reflection = bool(self._brdf)
            self._reflection_spectrum, self._transmission_spectrum = self._extract_spectrum()
            try:
                self._stub.GetSpecularInterpolationEnhancementData(Empty())
                self._BaseBSDF__interpolation_settings = InterpolationEnhancement(
                    bsdf=self,
                    bsdf_namespace=anisotropic_bsdf__v1__pb2,
                    index_1=None,
                    index_2=None,
                )
            except grpc.RpcError:
                self.__interpolation_settings = None
        else:
            self._transmission_spectrum, self._reflection_spectrum = None, None

    def get(self, key=""):
        """Retrieve any information from the BSDF object.

        Parameters
        ----------
        key : str
            Name of the property.

        Returns
        -------
        property
            Values/content of the associated property.
        """
        data = {k: v.fget(self) for k, v in BaseBSDF.__dict__.items() if isinstance(v, property)}
        data.update(
            {
                k: v.fget(self)
                for k, v in AnisotropicBSDF.__dict__.items()
                if isinstance(v, property)
            }
        )
        if key == "":
            return data
        elif data.get(key):
            return data.get(key)
        else:
            print("Used key: {} not found in key list: {}.".format(key, data.keys()))

    def __str__(self):
        """Create string representation of a BSDF."""
        return str(self.get())

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
        for ani_bsdf_data in self._grpcbsdf.reflection.anisotropic_samples:
            anisotropic_angle = ani_bsdf_data.anisotropic_sample
            for bsdf_data in ani_bsdf_data.incidence_samples:
                incident_angle = bsdf_data.incidence_sample
                thetas = np.array(bsdf_data.theta_samples)
                phis = np.array(bsdf_data.phi_samples)
                bsdf = np.array(bsdf_data.bsdf_cos_theta).reshape((len(thetas), len(phis)))
                tis = bsdf_data.integral
                brdf.append(
                    BxdfDatapoint(True, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle)
                )
        for ani_bsdf_data in self._grpcbsdf.transmission.anisotropic_samples:
            anisotropic_angle = ani_bsdf_data.anisotropic_sample
            for bsdf_data in ani_bsdf_data.incidence_samples:
                incident_angle = bsdf_data.incidence_sample
                thetas = np.array(bsdf_data.theta_samples)
                phis = np.array(bsdf_data.phi_samples)
                bsdf = np.array(bsdf_data.bsdf_cos_theta).reshape((len(thetas), len(phis)))
                tis = bsdf_data.integral
                btdf.append(
                    BxdfDatapoint(False, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle)
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

    @property
    def anisotropic_angles(self):
        """Anisotropic angles available in bsdf data."""
        if self.has_transmission:
            t_angles = [btdf.anisotropy for btdf in self.btdf]
        else:
            t_angles = []
        if self.has_reflection:
            r_angles = [brdf.anisotropy for brdf in self.brdf]
        else:
            r_angles = []
        return [list(Counter(r_angles).keys()), list(Counter(t_angles).keys())]

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
        self._brdf, self._btdf = self._extract_bsdf()
        self._has_transmission = bool(self._btdf)
        self._has_reflection = bool(self._brdf)
        self._transmission_spectrum, self._reflection_spectrum = self._extract_spectrum()

    def commit(self):
        """Sent Data to gRPC interface."""
        # set basic values
        bsdf = anisotropic_bsdf__v1__pb2.AnisotropicBsdfData()
        bsdf.description = self.description
        bsdf.anisotropy_vector.x = self.anisotropy_vector[0]
        bsdf.anisotropy_vector.y = self.anisotropy_vector[1]
        bsdf.anisotropy_vector.z = self.anisotropy_vector[2]
        if self.has_reflection:
            bsdf.reflection.spectrum_incidence = self.spectrum_incidence[0]
            bsdf.reflection.spectrum_anisotropy = self.spectrum_anisotropy[0]
            for w in range(len(self.reflection_spectrum[0])):
                pair = bsdf.reflection.spectrum.add()
                pair.wavelength = self.reflection_spectrum[0][w]
                pair.coefficient = self.reflection_spectrum[1][w]
            for ani in self.anisotropic_angles[0]:
                slice = bsdf.reflection.anisotropic_samples.add()
                slice.anisotropic_sample = ani
                for brdf in self.brdf:
                    if brdf.anisotropy == ani:
                        incidence_diag = slice.incidence_samples.add()
                        incidence_diag.incidence_sample = brdf.incident_angle
                        # intensity diagrams
                        incidence_diag.phi_samples[:] = list(brdf.phi_values)
                        incidence_diag.theta_samples[:] = list(brdf.theta_values)
                        incidence_diag.bsdf_cos_theta[:] = brdf.bxdf.flatten().tolist()
        if self.has_transmission:
            bsdf.transmission.spectrum_incidence = self.spectrum_incidence[1]
            bsdf.transmission.spectrum_anisotropy = self.spectrum_anisotropy[1]
            for w in range(len(self.transmission_spectrum[0])):
                pair = bsdf.transmission.spectrum.add()
                pair.wavelength = self.transmission_spectrum[0][w]
                pair.coefficient = self.transmission_spectrum[1][w]
            for ani in self.anisotropic_angles[1]:
                slice = bsdf.transmission.anisotropic_samples.add()
                slice.anisotropic_sample = ani
                for btdf in self.btdf:
                    if btdf.anisotropy == ani:
                        incidence_diag = slice.incidence_samples.add()
                        incidence_diag.incidence_sample = btdf.incident_angle
                        # intensity diagrams
                        incidence_diag.phi_samples[:] = list(btdf.phi_values)
                        incidence_diag.theta_samples[:] = list(btdf.theta_values)
                        incidence_diag.bsdf_cos_theta[:] = btdf.bxdf.flatten().tolist()
        self._stub.Import(bsdf)
        self._grpcbsdf = bsdf
        if self._BaseBSDF__interpolation_settings is not None:
            self._stub.SetSpecularInterpolationEnhancementData(
                self._BaseBSDF__interpolation_settings._InterpolationEnhancement__cones_data
            )

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
        if commit:
            self.commit()
        else:
            self._stub.Import(self._grpcbsdf)
        if file_path.suffix == ".anisotropicbsdf":
            file_name.file_name = str(file_path)
        else:
            file_name.file_name = str(file_path.parent / (file_path.name + ".anisotropicbsdf"))
        self._stub.Save(file_name)
        return Path(file_name.file_name)


class SpectralBRDF(BaseBSDF):
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
            speos,
            spectral_bsdf__v1__pb2_grpc.SpectralBsdfServiceStub(speos.client.channel),
            spectral_bsdf__v1__pb2,
        )
        self._spectrum_incidence = [0, 0]
        self._spectrum_anisotropy = [0, 0]
        if file_path:
            file_path = Path(file_path)
            self._grpcbsdf = self._import_file(file_path)
            self.brdf, self.btdf = self._extract_bsdf()
            self._has_transmission = bool(self._btdf)
            self._has_reflection = bool(self._brdf)
            try:
                self._stub.GetSpecularInterpolationEnhancementData(Empty())
                self._BaseBSDF__interpolation_settings = InterpolationEnhancement(
                    bsdf=self,
                    bsdf_namespace=spectral_bsdf__v1__pb2,
                    index_1=None,
                    index_2=None,
                )
            except grpc.RpcError:
                self.__interpolation_settings = None
        else:
            self._transmission_spectrum, self._reflection_spectrum = None, None

    @property
    def wavelength(self):
        """List of all Wavelength in BRDF."""
        r_wl = []
        t_wl = []
        if self.has_reflection:
            for brdf in self.brdf:
                r_wl.append(brdf.wavelength)
            return list(set(r_wl))
        if self.has_transmission:
            for btdf in self.btdf:
                t_wl.append(btdf.wavelength)
            return list(set(t_wl))
        else:
            return []

    def get(self, key=""):
        """Retrieve any information from the BSDF object.

        Parameters
        ----------
        key : str
            Name of the property.

        Returns
        -------
        property
            Values/content of the associated property.
        """
        data = {k: v.fget(self) for k, v in BaseBSDF.__dict__.items() if isinstance(v, property)}
        data.update(
            {k: v.fget(self) for k, v in SpectralBRDF.__dict__.items() if isinstance(v, property)}
        )
        if key == "":
            return data
        elif data.get(key):
            return data.get(key)
        else:
            print("Used key: {} not found in key list: {}.".format(key, data.keys()))

    def __str__(self):
        """Create string representation of a BSDF."""
        return str(self.get())

    def _import_file(self, filepath):
        file_name = spectral_bsdf__v1__pb2.FileName()
        file_name.file_name = str(filepath)
        self._stub.Load(file_name)
        return self._stub.Export(Empty())

    def _extract_bsdf(self) -> tuple[list[BxdfDatapoint], list[BxdfDatapoint]]:
        self.description = self._grpcbsdf.description
        brdf = []
        btdf = []
        for i, spectral_bsdf_data in enumerate(self._grpcbsdf.wavelength_incidence_samples):
            anisotropic_angle = 0
            incident_angle = self._grpcbsdf.incidence_samples[
                i % len(self._grpcbsdf.incidence_samples)
            ]
            wl = self._grpcbsdf.wavelength_samples[int(i / len(self._grpcbsdf.incidence_samples))]
            if spectral_bsdf_data.HasField("reflection"):
                thetas = np.array(spectral_bsdf_data.reflection.theta_samples)
                phis = np.array(spectral_bsdf_data.reflection.phi_samples)
                bsdf = np.array(spectral_bsdf_data.reflection.bsdf_cos_theta).reshape(
                    (len(thetas), len(phis))
                )
                tis = spectral_bsdf_data.reflection.integral
                brdf.append(
                    BxdfDatapoint(
                        True, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle, wl
                    )
                )
            if spectral_bsdf_data.HasField("transmission"):
                thetas = np.array(spectral_bsdf_data.transmission.theta_samples)
                phis = np.array(spectral_bsdf_data.transmission.phi_samples)
                bsdf = np.array(spectral_bsdf_data.transmission.bsdf_cos_theta).reshape(
                    (len(thetas), len(phis))
                )
                tis = spectral_bsdf_data.transmission.integral
                btdf.append(
                    BxdfDatapoint(
                        False, incident_angle, thetas, phis, bsdf, tis, anisotropic_angle, wl
                    )
                )
        if not brdf:
            brdf = None
        if not btdf:
            btdf = None
        return brdf, btdf

    def reset(self):
        """Reset BSDF data to what was stored in file."""
        self._brdf, self._btdf = self._extract_bsdf()
        self._has_transmission = bool(self._btdf)
        self._has_reflection = bool(self._brdf)

    def sanity_check(self, silent: bool = True) -> str:
        """Verify BSDF data is correctly defined.

        Parameters
        ----------
        silent : bool
            If False Warnings will be raised else not, by Default True

        Returns
        -------
        WarningInformation : str
            Description of what data is missing or incorrect
        """
        return self._sanity_check(raise_error=False, silent=silent)

    def _sanity_check(self, raise_error=False, silent=True):
        """Validate data.

        Allow to raise an error
        """
        r_wl = []
        r_inc = []
        t_wl = []
        t_inc = []
        error_msg = ""
        match self.has_reflection, self.has_transmission:
            case True, True:
                for brdf, btdf in zip(self.brdf, self.btdf):
                    r_inc.append(brdf.incident_angle)
                    r_wl.append(brdf.wavelength)
                    t_inc.append(btdf.incident_angle)
                    t_wl.append(btdf.wavelength)
                if r_inc != t_inc or r_wl != t_wl:
                    error_msg += (
                        "Incidence and/or Wavelength information between reflection and"
                        " transmission is not identical. "
                    )
                test_inc = r_inc
                test_wl = r_wl
            case True, False:
                for brdf in self.brdf:
                    r_inc.append(brdf.incident_angle)
                    r_wl.append(brdf.wavelength)
                test_inc = r_inc
                test_wl = r_wl
            case False, True:
                for btdf in self.btdf:
                    t_inc.append(btdf.incident_angle)
                    t_wl.append(btdf.wavelength)
                test_inc = t_inc
                test_wl = t_wl
            case _:
                test_inc = []
                test_wl = []
        inc_f = dict(Counter(test_inc))
        wl_f = dict(Counter(test_wl))
        inc_error_l = []
        wl_error_l = []
        for key in inc_f:
            if len(wl_f.keys()) != inc_f[key]:
                inc_error_l.append(key)
        for key in wl_f:
            if len(inc_f.keys()) != wl_f[key]:
                wl_error_l.append(key)
        if inc_error_l:
            error_msg += (
                "The bsdf is missing information's for the for the following incidence"
                " angles one or more wavelengths are missing: {}. ".format(inc_error_l)
            )
        if inc_error_l:
            error_msg += (
                "The bsdf is missing information's for the for the following wavelength"
                " one or more incidence angles are missing: {}. ".format(wl_error_l)
            )
        if raise_error:
            if error_msg:
                raise ValueError(error_msg)
        elif silent:
            return error_msg
        else:
            if error_msg:
                warnings.warn(error_msg, stacklevel=2)
            return error_msg

    def commit(self):
        """Sent Data to gRPC interface."""
        # set basic values
        self._sanity_check(raise_error=True)
        spectral_bsdf = spectral_bsdf__v1__pb2.SpectralBsdfData()
        spectral_bsdf.description = self.description
        wl = []
        inc = []
        match self.has_reflection, self.has_transmission:
            case True, True:
                for brdf, btdf in zip(self.brdf, self.btdf):
                    inc.append(brdf.incident_angle)
                    wl.append(brdf.wavelength)
                    iw = spectral_bsdf.wavelength_incidence_samples.add()
                    iw.reflection.integral = brdf.tis
                    iw.reflection.phi_samples[:] = list(brdf.phi_values)
                    iw.reflection.theta_samples[:] = list(brdf.theta_values)
                    iw.reflection.bsdf_cos_theta[:] = brdf.bxdf.flatten().tolist()
                    iw.transmission.integral = btdf.tis
                    iw.transmission.phi_samples[:] = list(btdf.phi_values)
                    iw.transmission.theta_samples[:] = list(btdf.theta_values)
                    iw.transmission.bsdf_cos_theta[:] = btdf.bxdf.flatten().tolist()
            case True, False:
                for brdf in self.brdf:
                    inc.append(brdf.incident_angle)
                    wl.append(brdf.wavelength)
                    iw = spectral_bsdf.wavelength_incidence_samples.add()
                    iw.reflection.integral = brdf.tis
                    iw.reflection.phi_samples[:] = list(brdf.phi_values)
                    iw.reflection.theta_samples[:] = list(brdf.theta_values)
                    iw.reflection.bsdf_cos_theta[:] = brdf.bxdf.flatten().tolist()
            case False, True:
                for btdf in self.btdf:
                    inc.append(btdf.incident_angle)
                    wl.append(btdf.wavelength)
                    iw = spectral_bsdf.wavelength_incidence_samples.add()
                    iw.transmission.integral = btdf.tis
                    iw.transmission.phi_samples[:] = list(btdf.phi_values)
                    iw.transmission.theta_samples[:] = list(btdf.theta_values)
                    iw.transmission.bsdf_cos_theta[:] = btdf.bxdf.flatten().tolist()
        inc = list(set(inc))
        wl = list(set(wl))
        inc.sort()
        wl.sort()
        spectral_bsdf.incidence_samples[:] = inc
        spectral_bsdf.wavelength_samples[:] = wl
        self._stub.Import(spectral_bsdf)
        self._grpcbsdf = spectral_bsdf
        if self._BaseBSDF__interpolation_settings is not None:
            self._stub.SetSpecularInterpolationEnhancementData(
                self._BaseBSDF__interpolation_settings._InterpolationEnhancement__cones_data
            )

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
        file_name = spectral_bsdf__v1__pb2.FileName()
        if commit:
            self.commit()
        else:
            self._stub.Import(self._grpcbsdf)
        if file_path.suffix == ".brdf":
            file_name.file_name = str(file_path)
        else:
            file_name.file_name = str(file_path.parent / (file_path.name + ".brdf"))
        self._stub.Save(file_name)
        return Path(file_name.file_name)


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
    wavelength : float
        Wavelength in nm
    """

    def __init__(
        self,
        is_brdf: bool,
        incident_angle: float,
        theta_values: Collection[float],
        phi_values: Collection[float],
        bxdf: Collection[float],
        tis: float = 1,
        anisotropy: float = 0,
        wavelength: float = 555,
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
        self.wavelength = wavelength

    def get(self, key=""):
        """Retrieve any information from the BxdfDatapoint object.

        Parameters
        ----------
        key : str
            Name of the property.

        Returns
        -------
        property
            Values/content of the associated property.
        """
        data = {
            k: v.fget(self) for k, v in BxdfDatapoint.__dict__.items() if isinstance(v, property)
        }
        if key == "":
            return data
        elif data.get(key):
            return data.get(key)
        else:
            print("Used key: {} not found in key list: {}.".format(key, data.keys()))

    def __str__(self):
        """Create string representation of a RayPath."""
        return str(self.get())

    @property
    def anisotropy(self):
        """Anisotropy angels of Datapoint."""
        return self._anisotropy

    @anisotropy.setter
    def anisotropy(self, value):
        if 0 <= value <= 2 * np.pi:
            self._anisotropy = value
        else:
            raise ValueError("Anisotropy angle needs to be between [0, 2*pi]")

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
            if any((bxdf < 0).flatten()):
                raise ValueError("bxdf data has to be positive")
            if np.shape(bxdf) == (len(self.theta_values), len(self.phi_values)):
                self._bxdf = bxdf
            elif np.shape(bxdf) == (len(self.phi_values), len(self.theta_values)):
                self._bxdf = bxdf.transpose()
            else:
                raise ValueError("bxdf data has incorrect dimensions")
        else:
            self._bxdf = None

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
            raise ValueError("Incident angle needs to be between [0, pi/2]")

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
            if all([np.pi / 2 <= theta <= np.pi for theta in value]):
                self._theta_values = value
                if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                    self.bxdf = None
            else:
                raise ValueError("Theta values for Transmission need to be between [pi/2, pi]")
        else:
            if all([0 <= theta <= np.pi / 2 for theta in value]):
                self._theta_values = value
                if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                    self.bxdf = None
            else:
                raise ValueError("Theta values for Reflection need to be between [0, pi/2]")

    @property
    def phi_values(self):
        """List of phi values  for which values are stored in bxdf data."""
        return self._phi_values

    @phi_values.setter
    def phi_values(self, value):
        if all([0 <= phi <= 2 * np.pi for phi in value]):
            self._phi_values = value
            if np.shape(self.bxdf) != (len(self.theta_values), len(self.phi_values)):
                self.bxdf = None
        else:
            raise ValueError("Phi values need to be between [0, 2pi]")


def create_bsdf180(
    speos: ansys.speos.core.Speos,
    bsdf180_file_path: Union[str, Path],
    path_normal_bsdf: Union[str, Path],
    path_opposite_bsdf: Union[str, Path],
) -> Path:
    """Create a bsdf180 from 2 bsdf.

    This function allows to create BSDF180 from 2 bsdf files
    allowed files: *.coated *.brdf *.anisotropicbsdf *.scattering

    Parameters
    ----------
    speos : ansys.speos.core.Speos
        Speos Object to connect to RPC server
    bsdf180_file_path : Union[str, Path]
        File location of created bsdf180
    path_normal_bsdf : Union[str, Path]
        File location of first file, which represent normal direction
        Allowed files: *.coated, *.brdf, *.anisotropicbsdf, *.scattering
    path_opposite_bsdf : Union[str, Path]
        File location of first file, which represent anti-normal direction
        Allowed files: *.coated, *.brdf, *.anisotropicbsdf, *.scattering
    fix_disparity : bool
        This allows to create a bsdf when the two files are not normalized to each other.
        By default, ``False``

    Returns
    -------
    Path
        Returns where the file location of the bsdf180
    """
    supported = [".coated", ".brdf", ".anisotropicbsdf", ".scattering"]
    stub = bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub(speos.client.channel)
    bsdf180_file_path = Path(bsdf180_file_path)
    path_normal_bsdf = Path(path_normal_bsdf)
    path_opposite_bsdf = Path(path_opposite_bsdf)
    if path_normal_bsdf.suffix not in supported or path_opposite_bsdf.suffix not in supported:
        raise TypeError(
            f"Filetype not support please use one of the supported filetype, {supported}."
        )
    if bsdf180_file_path.suffix != ".bsdf180":
        bsdf180_file_path = bsdf180_file_path.parent / (bsdf180_file_path.name + ".bsdf180")
    bsdf180_request = bsdf_creation__v1__pb2.Bsdf180InputData()
    bsdf180_request.input_front_bsdf_file_name = str(path_normal_bsdf)
    bsdf180_request.input_opposite_bsdf_file_name = str(path_opposite_bsdf)
    bsdf180_request.output_file_name = str(bsdf180_file_path)
    stub.BuildBsdf180(bsdf180_request)
    return bsdf180_file_path


def create_spectral_brdf(
    speos: ansys.speos.core.Speos,
    spectral_bsdf_file_path: Union[str, Path],
    wavelength_list: list[float],
    anisotropic_bsdf_file_list: list[Union[Path, str]],
) -> Path:
    """Create a brdf from multiple bsdf.

    This function allows to create BRDF from multiple bsdf files
    allowed files: *.anisotropicbsdf

    Parameters
    ----------
    speos : ansys.speos.core.Speos
        Speos Object to connect to RPC server
    spectral_bsdf_file_path : Union[str, Path]
        File location of created BRDF file
    wavelength_list : list[float]
        List of wavelength
    anisotropic_bsdf_file_list :  list[Union[Path, str]]
        list of bsdf file locations

    Returns
    -------
    Path
        Location of created BRDF
    """
    stub = bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub(speos.client.channel)
    spectral_request = bsdf_creation__v1__pb2.SpectralBsdfInputData()
    spectral_bsdf_file_path = Path(spectral_bsdf_file_path)
    if spectral_bsdf_file_path.suffix != ".brdf":
        spectral_bsdf_file_path = spectral_bsdf_file_path.parent / (
            spectral_bsdf_file_path.name + ".brdf"
        )
    spectral_request.output_file_name = str(spectral_bsdf_file_path)
    if len(wavelength_list) == len(anisotropic_bsdf_file_list):
        anisotropic_bsdf_file_list = [Path(bsdf_loc) for bsdf_loc in anisotropic_bsdf_file_list]
        for bsdf_loc in anisotropic_bsdf_file_list:
            if bsdf_loc.suffix != ".anisotropicbsdf":
                raise TypeError("Filetype not support please use only anisotropicbsdf files.")
    else:
        raise RuntimeError("The Number BSDF file and wavelength needs to be identical")
    for wl, file in zip(wavelength_list, anisotropic_bsdf_file_list):
        tmp = spectral_request.input_anisotropic_samples.add()
        tmp.wavelength = float(wl)
        tmp.file_name = str(file)
    stub.BuildSpectralBsdf(spectral_request)
    return spectral_bsdf_file_path


def create_anisotropic_bsdf(
    speos: ansys.speos.core.Speos,
    anisotropic_bsdf_file_path: Union[str, Path],
    anisotropy_list: list[float],
    anisotropic_bsdf_file_list: list[Union[Path, str]],
    fix_disparity: bool = False,
) -> Path:
    """Create an anisotropic bsdf from anisotropic bsdf files.

    Parameters
    ----------
    speos : ansys.speos.core.Speos
        Speos Object to connect to RPC server
    anisotropic_bsdf_file_path : Union[str, Path]
        File location of created Anisotropic BSDF file
    anisotropy_list : list[float]
        ordered List of anisotropy value, in radian
    anisotropic_bsdf_file_list : list[Union[Path, str]]
        list of bsdf file locations
    fix_disparity : bool
        Fixes normalization disparity between BSDF,
        By default: ``False``

    Notes
    -----
    Please note that the bsdf files from the bsdf list need to be isotropic.

    Returns
    -------
    Path
        Location of created Anisotropic BSDF files
    """
    stub = bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub(speos.client.channel)
    ani_request = bsdf_creation__v1__pb2.AnisotropicBsdfInputData()
    anisotropic_bsdf_file_path = Path(anisotropic_bsdf_file_path)
    if anisotropic_bsdf_file_path.suffix != ".anisotropicbsdf":
        anisotropic_bsdf_file_path = anisotropic_bsdf_file_path.parent / (
            anisotropic_bsdf_file_path.name + ".anisotropicbsdf"
        )
    ani_request.output_file_name = str(anisotropic_bsdf_file_path)
    if len(anisotropy_list) == len(anisotropic_bsdf_file_list):
        anisotropic_bsdf_file_list = [Path(bsdf_loc) for bsdf_loc in anisotropic_bsdf_file_list]
        for bsdf_loc in anisotropic_bsdf_file_list:
            if bsdf_loc.suffix != ".anisotropicbsdf":
                raise TypeError("Filetype not support please use only anisotropicbsdf files.")
    else:
        raise RuntimeError("The Number BSDF file and wavelength needs to be identical")
    for ani, file in zip(anisotropy_list, anisotropic_bsdf_file_list):
        temp = ani_request.input_anisotropic_bsdf_samples.add()
        temp.anisotropic_angle = ani
        temp.file_name = str(file)
    ani_request.fix_disparity = fix_disparity
    ani_request.output_file_name = str(anisotropic_bsdf_file_path)
    stub.BuildAnisotropicBsdf(ani_request)
    return anisotropic_bsdf_file_path
