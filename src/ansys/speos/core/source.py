# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Provides a way to interact with Speos feature: Source."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Mapping, Optional, Union
import uuid

from ansys.api.speos.scene.v2 import scene_pb2
from ansys.api.speos.source.v1 import source_pb2
import numpy as np

from ansys.speos.core import (
    project as project,
    proto_message_utils as proto_message_utils,
)
import ansys.speos.core.body as body
import ansys.speos.core.face as face
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.parameters import (
    AmbientEnvironmentParameters,
    AmbientNaturalLightParameters,
    AutomaticSunParameters,
    ColorSpaceType,
    ConstantExitanceParameters,
    FluxFromFileParameters,
    IntensityFluxParameters,
    IntensityOrientationType,
    LuminaireSourceParameters,
    LuminousFluxParameters,
    ManualSunParameters,
    RadiantFluxParameters,
    RayFileSourceParameters,
    SpectrumType,
    SurfaceSourceParameters,
    UserDefinedColorSpaceParameters,
    UserDefinedWhitePointParameters,
    VariableExitanceParameters,
    WhitePointType,
)
from ansys.speos.core.generic.visualization_methods import _VisualArrow, _VisualData
from ansys.speos.core.geo_ref import GeoRef
import ansys.speos.core.intensity as intensity
from ansys.speos.core.intensity import Intensity
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.source_template import ProtoSourceTemplate
from ansys.speos.core.spectrum import Spectrum


class BaseSource:
    """
    Super Class for all sources.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which source shall be created.
    name : str
        Name of the source.
    description : str
        Description of the source.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance, optional
        Source instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    class UserDefinedColorSpace:
        """Type of color space is user defined.

        Parameters
        ----------
        userdefined_color_space : source_pb2.SourceTemplate.UserDefinedRGBSpace
            source_pb2.SourceTemplate.UserDefinedRGBSpace
        default_parameters: Optional[UserDefinedColorSpaceParameters] = None,
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_userdefined_color_space() method.
        """

        class UserDefinedWhitePoint:
            """Type of white point is user defined.

            Parameters
            ----------
            userdefined_white_point : source_pb2.SourceTemplate.UserDefinedWhitePoint
                source_pb2.SourceTemplate.UserDefinedWhitePoint
            default_parameters: Optional[UserDefinedWhitePointParameters] = None,
                Uses default values when True.
            stable_ctr : bool
                Variable to indicate if usage is inside class scope

            Notes
            -----
            **Do not instantiate this class yourself**,
            use set_white_point_type_user_defined() method.
            """

            def __init__(
                self,
                userdefined_white_point: source_pb2.SourceTemplate.UserDefinedWhitePoint,
                default_parameters: Optional[UserDefinedWhitePointParameters] = None,
                stable_ctr: bool = True,
            ):
                if not stable_ctr:
                    msg = "UserDefinedWhitePoint class instantiated outside of class scope"
                    raise RuntimeError(msg)
                self._userdefined_white_point = userdefined_white_point

                if default_parameters is not None:
                    self.white_point = [default_parameters.x, default_parameters.y]

            @property
            def white_point(self):
                """White point coordinate.

                This property gets or sets the white point coordinate [x, y]

                Parameters
                ----------
                value: List[float]
                    The white point coordinate, [0.31271, 0.32902] by default.

                Returns
                -------
                List[float]
                    User defined white point coordinate

                """
                return self._userdefined_white_point.white_point

            @white_point.setter
            def white_point(self, value: List[float]):
                self._userdefined_white_point.white_point[:] = value

        def __init__(
            self,
            project: project.Project,
            userdefined_color_space: source_pb2.SourceTemplate.UserDefinedRGBSpace,
            default_parameters: Optional[UserDefinedColorSpaceParameters] = None,
            stable_ctr: bool = True,
        ):
            self._project = project
            if not stable_ctr:
                msg = "UserDefinedColorSpace class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._userdefined_color_space = userdefined_color_space
            self._white_point_type = None

            self._red_spectrum = BaseSource._Spectrum(
                speos_client=self._project.client,
                name="",
                message_to_complete=self._userdefined_color_space,
                field_name_to_complete="red_spectrum_guid",
                spectrum_guid=self._userdefined_color_space.red_spectrum_guid,
            )

            self._green_spectrum = BaseSource._Spectrum(
                speos_client=self._project.client,
                name="",
                message_to_complete=self._userdefined_color_space,
                field_name_to_complete="green_spectrum_guid",
                spectrum_guid=self._userdefined_color_space.green_spectrum_guid,
            )

            self._blue_spectrum = BaseSource._Spectrum(
                speos_client=self._project.client,
                name="",
                message_to_complete=self._userdefined_color_space,
                field_name_to_complete="blue_spectrum_guid",
                spectrum_guid=self._userdefined_color_space.blue_spectrum_guid,
            )

            if default_parameters is not None:
                # Default values
                self.red_spectrum = str(default_parameters.red_spectrum_uri)
                self.green_spectrum = str(default_parameters.green_spectrum_uri)
                self.blue_spectrum = str(default_parameters.blue_spectrum_uri)
                match default_parameters.white_point_type:
                    case WhitePointType.d65:
                        self.set_white_point_type_d65()
                    case WhitePointType.d50:
                        self.set_white_point_type_d50()
                    case WhitePointType.c:
                        self.set_white_point_type_c()
                    case WhitePointType.e:
                        self.set_white_point_type_e()
                    case _:
                        match type(default_parameters.white_point_type).__name__:
                            case "UserDefinedWhitePointParameters":
                                self.set_white_point_type_user_defined().white_point = [
                                    default_parameters.white_point_type.x,
                                    default_parameters.white_point_type.y,
                                ]
                            case _:
                                raise ValueError(
                                    "Unsupported white point_type type: {}".format(
                                        type(default_parameters.white_point_type).__name__
                                    )
                                )

        @property
        def red_spectrum(self) -> dict:
            """Property of red spectrum.

            Parameters
            ----------
            red_spectrum_file_uri: str
                Red spectrum file uri.


            Returns
            -------
            dict
                Red spectrum dictionary

            """
            return self._red_spectrum._spectrum._to_dict()

        @red_spectrum.setter
        def red_spectrum(self, red_spectrum_file_uri: str) -> None:
            if self._red_spectrum._message_to_complete is not self._userdefined_color_space:
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._red_spectrum._message_to_complete = self._userdefined_color_space

            # name for the spectrum chosen: <file_uri>.Spectrum
            self._red_spectrum._spectrum._spectrum.name = Path(red_spectrum_file_uri).name
            self._red_spectrum._spectrum.set_library().file_uri = red_spectrum_file_uri

        @property
        def green_spectrum(self) -> dict:
            """Property of the green spectrum.

            Parameters
            ----------
            green_spectrum_file_uri: str
                Green spectrum file uri.

            Returns
            -------
            dict
                Green spectrum dictionary

            """
            return self._green_spectrum._spectrum._to_dict()

        @green_spectrum.setter
        def green_spectrum(self, green_spectrum_file_uri: str) -> None:
            if self._green_spectrum._message_to_complete is not self._userdefined_color_space:
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._green_spectrum._message_to_complete = self._userdefined_color_space

            # name for the spectrum chosen: <file_uri>.Spectrum
            self._green_spectrum._spectrum._spectrum.name = Path(green_spectrum_file_uri).name
            self._green_spectrum._spectrum.set_library().file_uri = green_spectrum_file_uri

        @property
        def blue_spectrum(self) -> dict:
            """Property of blue spectrum.

            Parameters
            ----------
            blue_spectrum_file_uri: str
                Blue spectrum file uri.

            Returns
            -------
            dict
                Blue spectrum dictionary

            """
            return self._blue_spectrum._spectrum._to_dict()

        @blue_spectrum.setter
        def blue_spectrum(self, blue_spectrum_file_uri: str) -> None:
            if self._blue_spectrum._message_to_complete is not self._userdefined_color_space:
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._blue_spectrum._message_to_complete = self._userdefined_color_space

            # name for the spectrum chosen: <file_uri>.Spectrum
            self._blue_spectrum._spectrum._spectrum.name = Path(blue_spectrum_file_uri).name
            self._blue_spectrum._spectrum.set_library().file_uri = blue_spectrum_file_uri

        @property
        def white_point_type(
            self,
        ) -> Union[
            None,
            source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D65,
            source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D50,
            source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.C,
            source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.E,
            UserDefinedWhitePoint,
        ]:
            """Get the white point type.

            Returns
            -------
            Union
            [
                None,
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D65,
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D50,
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.C,
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.E,
                UserDefinedWhitePoint,
            ]
            Predefined White Point Type or User Defined White Point Type.

            """
            return self._white_point_type

        def set_white_point_type_d65(self) -> None:
            """Set white point type to D65.

            Returns
            -------
            None

            """
            self._userdefined_color_space.pre_defined_white_point.white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D65
            )
            self._white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D65
            )

        def set_white_point_type_c(self) -> None:
            """Set white point type to C.

            Returns
            -------
            None

            """
            self._userdefined_color_space.pre_defined_white_point.white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.C
            )
            self._white_point_type = source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.C

        def set_white_point_type_d50(self) -> None:
            """Set white point type to D50.

            Returns
            -------
            None

            """
            self._userdefined_color_space.pre_defined_white_point.white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D50
            )
            self._white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.D50
            )

        def set_white_point_type_e(self) -> None:
            """Set white point type to E.

            Returns
            -------
            None

            """
            self._userdefined_color_space.pre_defined_white_point.white_point_type = (
                source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.E
            )
            self._white_point_type = source_pb2.SourceTemplate.PredefinedWhitePoint.WhitePointType.E

        def set_white_point_type_user_defined(self) -> UserDefinedWhitePoint:
            """Set white point type to user_defined.

            Returns
            -------
            UserDefinedWhitePoint
                User defined white point settings.

            """
            if self._white_point_type is None and self._userdefined_color_space.HasField(
                "user_defined_white_point"
            ):
                self._white_point_type = BaseSource.UserDefinedColorSpace.UserDefinedWhitePoint(
                    userdefined_white_point=self._userdefined_color_space.user_defined_white_point,
                    default_parameters=None,
                    stable_ctr=True,
                )
            if not isinstance(
                self._white_point_type, BaseSource.UserDefinedColorSpace.UserDefinedWhitePoint
            ):
                # if the _type is not UserDefinedWhitePoint then we create a new type.
                self._white_point_type = BaseSource.UserDefinedColorSpace.UserDefinedWhitePoint(
                    userdefined_white_point=self._userdefined_color_space.user_defined_white_point,
                    default_parameters=UserDefinedWhitePointParameters(),
                    stable_ctr=True,
                )
            elif (
                self._white_point_type._userdefined_white_point
                is not self._userdefined_color_space.user_defined_white_point
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._white_point_type._userdefined_white_point = (
                    self._userdefined_color_space.user_defined_white_point
                )
            return self._white_point_type

    class PredefinedColorSpace:
        """Type of color space is predefined value.

        Parameters
        ----------
        predefined_color_space :
            ansys.api.speos.source.v1.source_pb2.SourceTemplate.PredefinedColorSpace
        default_parameters: Optional[ColorSpaceType] = None,
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_predefined_color_space() method.
        """

        def __init__(
            self,
            predefined_color_space: source_pb2.SourceTemplate.PredefinedColorSpace,
            default_parameters: Optional[ColorSpaceType] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "PredefinedColorSpace class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._predefined_color_space = predefined_color_space

            if default_parameters is not None:
                # Default values
                match default_parameters:
                    case ColorSpaceType.srgb:
                        self.set_color_space_srgb()
                    case ColorSpaceType.adobe_rgb:
                        self.set_color_space_adobergb()

        def set_color_space_srgb(self) -> SourceAmbientEnvironment.PredefinedColorSpace:
            """Set the color space to the srgb preset.

            Returns
            -------
            ansys.speos.core.source.SourceAmbientEnvironment.PredefinedColorSpace
            """
            self._predefined_color_space.color_space_type = (
                source_pb2.SourceTemplate.PredefinedColorSpace.sRGB
            )
            return self

        def set_color_space_adobergb(self) -> SourceAmbientEnvironment.PredefinedColorSpace:
            """Set the color space to the Adobe RGB preset.

            Returns
            -------
            ansys.speos.core.source.SourceAmbientEnvironment.PredefinedColorSpace
            """
            self._predefined_color_space.color_space_type = (
                source_pb2.SourceTemplate.PredefinedColorSpace.AdobeRGB
            )
            return self

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
    ) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self._visual_data = _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
        self.source_template_link = None
        """Link object for the source template in database."""

        if metadata is None:
            metadata = {}

        if source_instance is None:
            # Create local SourceTemplate
            self._source_template = ProtoSourceTemplate(
                name=name, description=description, metadata=metadata
            )

            # Create local SourceInstance
            self._source_instance = ProtoScene.SourceInstance(
                name=name, description=description, metadata=metadata
            )
        else:
            self._unique_id = source_instance.metadata["UniqueId"]
            self.source_template_link = self._project.client[source_instance.source_guid]
            self._reset()

    class Flux:
        """Type of flux.

        By default, Luminous flux value is set with value 683 lm.

        Parameters
        ----------
        flux : ansys.api.speos.source.v1.source_pb2
            flux protobuf object to modify.
        default_parameters: Optional[
                LuminousFluxParameters,
                RadiantFluxParameters,
                FluxFromFileParameters,
                IntensityFluxParameters,
            ] = None,
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_flux method available in source classes.
        """

        def __init__(
            self,
            flux: source_pb2,
            default_parameters: Optional[
                LuminousFluxParameters,
                RadiantFluxParameters,
                FluxFromFileParameters,
                IntensityFluxParameters,
            ] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Flux class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._flux = flux
            self._flux_type = None

            if default_parameters is not None:
                if isinstance(default_parameters, LuminousFluxParameters):
                    self.set_luminous()
                    self.value = default_parameters.value
                elif isinstance(default_parameters, RadiantFluxParameters):
                    self.set_radiant()
                    self.value = default_parameters.value
                elif isinstance(
                    default_parameters, (FluxFromFileParameters, IntensityFluxParameters)
                ):
                    pass
                else:
                    raise ValueError(f"Unsupported flux type: {type(default_parameters).__name__}")

        def set_luminous(self) -> BaseSource.Flux:
            """Set flux type luminous.

            Returns
            -------
            ansys.speos.core.source.BaseSource.Flux
                Flux object

            """
            if self._flux_type is None or not isinstance(
                self._flux_type, source_pb2.SourceTemplate.Luminous
            ):
                self._flux_type = self._flux.luminous_flux
            return self

        def set_radiant(self) -> BaseSource.Flux:
            """Set flux type radiant.

            Returns
            -------
            ansys.speos.core.source.BaseSource.Flux
                Flux object

            """
            if self._flux_type is None or not isinstance(
                self._flux_type, source_pb2.SourceTemplate.Radiant
            ):
                self._flux_type = self._flux.radiant_flux
            return self

        @property
        def value(self) -> float:
            """Property of flux type's value.

            Parameters
            ----------
            value: float
                Value of the flux.

            Returns
            -------
            float
                Flux type value.

            """
            match self._flux_type.__name__:
                case "Luminous":
                    return self._flux.luminous_flux.luminous_value
                case "Radiant":
                    return self._flux.radiant_flux.radiant_value
                case "LuminousIntensity":
                    return self._flux.luminous_intensity_flux.luminous_intensity_value
                case _:
                    raise ValueError(f"Unsupported flux type: {self._flux_type.__name__}")

        @value.setter
        def value(self, value: float) -> None:
            match self._flux_type.__name__:
                case "Luminous":
                    self._flux.luminous_flux.luminous_value = value
                case "Radiant":
                    self._flux.radiant_flux.radiant_value = value
                case "LuminousIntensity":
                    self._flux.luminous_intensity_flux.luminous_intensity_value = value
                case _:
                    raise ValueError(f"Unsupported flux type: {self._flux_type.__name__}")

    class _Spectrum:
        def __init__(
            self,
            speos_client: SpeosClient,
            name: str,
            message_to_complete: Union[
                ProtoSourceTemplate.RayFile,
                ProtoSourceTemplate.Surface,
                ProtoSourceTemplate.Luminaire,
            ],
            field_name_to_complete="",
            spectrum_guid: str = "",
        ) -> None:
            self._message_to_complete = message_to_complete
            self._field_name_to_complete = field_name_to_complete
            if spectrum_guid != "":
                self._spectrum = Spectrum(
                    speos_client=speos_client,
                    name=name + ".Spectrum",
                    key=spectrum_guid,
                )
            else:
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum")

            self._no_spectrum = None  # None means never committed, or deleted
            self._no_spectrum_local = False

        def __str__(self) -> str:
            if self._no_spectrum is None:
                if self._no_spectrum_local is False:
                    return str(self._spectrum)
            else:
                if self._no_spectrum is False:
                    return str(self._spectrum)
            return ""

        def _commit(self) -> BaseSource._Spectrum:
            if not self._no_spectrum_local:
                self._spectrum.commit()
                if self._field_name_to_complete == "":
                    self._message_to_complete.spectrum_guid = self._spectrum.spectrum_link.key
                elif self._field_name_to_complete == "red_spectrum_guid":
                    self._message_to_complete.red_spectrum_guid = self._spectrum.spectrum_link.key
                elif self._field_name_to_complete == "green_spectrum_guid":
                    self._message_to_complete.green_spectrum_guid = self._spectrum.spectrum_link.key
                elif self._field_name_to_complete == "blue_spectrum_guid":
                    self._message_to_complete.blue_spectrum_guid = self._spectrum.spectrum_link.key
                self._no_spectrum = self._no_spectrum_local
            return self

        def _reset(self) -> BaseSource._Spectrum:
            self._spectrum.reset()
            if self._no_spectrum is not None:
                self._no_spectrum_local = self._no_spectrum
            return self

        def _delete(self) -> BaseSource._Spectrum:
            self._no_spectrum = None
            return self

    def _to_dict(self) -> dict:
        out_dict = {}

        # SourceInstance (= source guid + source properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=src_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._source_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._source_instance
            )

        if "source" not in out_dict.keys():
            # SourceTemplate
            if self.source_template_link is None:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._source_template,
                )
            else:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.source_template_link.get(),
                )

        # # handle spectrum & intensity
        # if self._type is not None:
        #     self._type._to_dict(dict_to_complete=out_dict)

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> list[tuple[str, dict]]:
        """Get dictionary corresponding to the project - read only.

        Parameters
        ----------
        key: str

        Returns
        -------
        str | dict
        """
        if key == "":
            return self._to_dict()
        info = proto_message_utils._value_finder_key_startswith(dict_var=self._to_dict(), key=key)
        content = list(info)
        if len(content) != 0:
            content.sort(
                key=lambda x: SequenceMatcher(None, x[0], key).ratio(),
                reverse=True,
            )
            return content[0][1]
        info = proto_message_utils._flatten_dict(dict_var=self._to_dict())
        print("Used key: {} not found in key list: {}.".format(key, info.keys()))

    def __str__(self) -> str:
        """Return the string representation of the source."""
        out_str = ""
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def _commit(self) -> BaseSource:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # The _unique_id will help to find correct item in the scene.sources:
        # the list of SourceInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._source_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the source template (depending on if it was already saved before)
        if self.source_template_link is None:
            self.source_template_link = self._project.client.source_templates().create(
                message=self._source_template
            )
            self._source_instance.source_guid = self.source_template_link.key
        elif self.source_template_link.get() != self._source_template:
            self.source_template_link.set(
                data=self._source_template
            )  # Only update if template has changed

        # Update the scene with the source instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                if src_inst != self._source_instance:
                    src_inst.CopyFrom(self._source_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.sources.append(
                    self._source_instance
                )  # if no, just add it to the list of sources

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def _reset(self) -> BaseSource:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # Reset source template
        if self.source_template_link is not None:
            self._source_template = self.source_template_link.get()

        # Reset source instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                self._source_instance = src_inst
        return self

    def _delete(self) -> BaseSource:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # This allows to clean-managed object contained in _luminaire, _rayfile, etc..
        # Like Spectrum, IntensityTemplate

        # Delete the source template
        if self.source_template_link is not None:
            self.source_template_link.delete()
            self.source_template_link = None

        # Reset then the source_guid (as the source template was deleted just above)
        self._source_instance.source_guid = ""

        # Remove the source from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        src_inst = next(
            (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if src_inst is not None:
            scene_data.sources.remove(src_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._source_instance.metadata.pop("UniqueId")
        return self

    def _fill(self, src_inst):
        self._unique_id = src_inst.metadata["UniqueId"]
        self._source_instance = src_inst
        self.source_template_link = self._project.client[src_inst.source_guid]
        self._reset()

    def commit(self) -> BaseSource:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._commit()
        self._commit()
        if general_methods._GRAPHICS_AVAILABLE:
            self._visual_data.updated = False
        return self

    def reset(self) -> BaseSource:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._reset()
        self._reset()
        return self

    def delete(self) -> BaseSource:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._delete()
        self._delete()
        return self


class SourceLuminaire(BaseSource):
    """LuminaireSource.

    By default, a flux from intensity file is chosen, with an incandescent spectrum.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    default_parameters : Optional[LuminaireSourceParameters] = None
        Uses default parameters.
    """

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_parameters: Optional[LuminaireSourceParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )

        # Attribute gathering more complex flux type
        self._type = None

        self._spectrum = self._Spectrum(
            speos_client=self._project.client,
            name=name,
            message_to_complete=self._source_template.luminaire,
            spectrum_guid=self._source_template.luminaire.spectrum_guid,
        )

        if default_parameters is not None:
            # New Default values
            self.intensity_file_uri = default_parameters.intensity_file_uri
            match type(default_parameters.flux_type).__name__:
                case "FluxFromFileParameters":
                    self.set_flux_from_intensity_file()
                case "LuminousFluxParameters":
                    self.flux.set_luminous()
                    self.flux.value = default_parameters.flux_type.value
                case "RadiantFluxParameters":
                    self.flux.set_radiant()
                    self.flux.value = default_parameters.flux_type.value
                case _:
                    raise ValueError(
                        f"Unsupported flux type: {type(default_parameters.flux_type).__name__}"
                    )

            match default_parameters.spectrum_type:
                case SpectrumType.incandescent:
                    self.spectrum.set_incandescent()
                case SpectrumType.warm_white_fluorescent:
                    self.spectrum.set_warmwhitefluorescent()
                case SpectrumType.daylight_fluorescent:
                    self.spectrum.set_daylightfluorescent()
                case SpectrumType.white_led:
                    self.spectrum.set_white_led()
                case SpectrumType.halogen:
                    self.spectrum.set_halogen()
                case SpectrumType.metal_halide:
                    self.spectrum.set_metalhalide()
                case SpectrumType.high_pressure_sodium:
                    self.spectrum.set_highpressuresodium()
                case _:
                    match type(default_parameters.spectrum_type).__name__:
                        case "SpectrumLibraryParameters":
                            self.spectrum.set_library().file_uri = (
                                default_parameters.spectrum_type.file_uri
                            )
                        case "SpectrumBlackBodyParameters":
                            self.spectrum.set_blackbody().temperature = (
                                default_parameters.spectrum_type.temperature
                            )
                        case _:
                            raise ValueError(
                                "Unsupported spectrum type: {}".format(
                                    type(default_parameters.spectrum_type).__name__
                                )
                            )
            self.axis_system = default_parameters.axis_system

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Luminaire source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            feature_pos_info = self.get(key="axis_system")
            feature_luminaire_pos = np.array(feature_pos_info[:3])
            feature_luminaire_x_dir = np.array(feature_pos_info[3:6])
            feature_luminaire_y_dir = np.array(feature_pos_info[6:9])
            feature_luminaire_z_dir = np.array(feature_pos_info[9:12])
            self._visual_data.coordinates.origin = feature_luminaire_pos
            self._visual_data.coordinates.x_axis = feature_luminaire_x_dir
            self._visual_data.coordinates.y_axis = feature_luminaire_y_dir
            self._visual_data.coordinates.z_axis = feature_luminaire_z_dir
            self._visual_data.updated = True
            return self._visual_data

    def set_flux_from_intensity_file(self) -> SourceLuminaire:
        """Take flux from intensity file provided.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        self._source_template.luminaire.flux_from_intensity_file.SetInParent()
        return self

    @property
    def flux(self) -> SourceLuminaire.Flux:
        """Flux definition of the luminaire source.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire.Flux
            flux object of the source

        """
        if self._type is None and self._source_template.HasField("luminaire"):
            self._type = self.Flux(
                flux=self._source_template.luminaire,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSource.Flux):
            self._type = self.Flux(
                flux=self._source_template.luminaire,
                default_parameters=LuminaireSourceParameters().flux_type,
                stable_ctr=True,
            )
        elif self._type._flux is not self._source_template.luminaire:
            self._type._flux = self._source_template.luminaire
        return self._type

    @property
    def intensity_file_uri(self) -> str:
        """Property of intensity file.

        Parameters
        ----------
        uri : Union[str, Path]
            IES or EULUMDAT format file uri.

        Returns
        -------
        str
            Intensity file uri.
        """
        return self._source_template.luminaire.intensity_file_uri

    @intensity_file_uri.setter
    def intensity_file_uri(self, uri: Union[str, Path]) -> None:
        self._source_template.luminaire.intensity_file_uri = str(uri)

    @property
    def spectrum(self) -> Spectrum:
        """Spectrum property.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._spectrum._message_to_complete is not self._source_template.luminaire:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.luminaire
        return self._spectrum._spectrum

    @property
    def axis_system(self) -> list[float]:
        """Property of the position of the source.

        Parameters
        ----------
        axis_system : List[float]
            Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        List[float]
            Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
        """
        return self._source_instance.luminaire_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: list[float]) -> None:
        self._source_instance.luminaire_properties.axis_system[:] = axis_system


class SourceRayFile(BaseSource):
    """RayFile Source.

    By default, flux and spectrum from ray file are selected.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    default_parameters : Optional[RayFileSourceParameters] = None,
        Uses default values when True.
    """

    class ExitGeometries:
        """ExitGeometries of rayfile source.

        By default, ExitGeometries list is set to be empty.

        Parameters
        ----------
        rayfile_props : ansys.api.speos.scene.v2.scene_pb2.RayFileProperties
            protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_exit_geometries
        method available in Source classes.
        """

        def __init__(
            self,
            rayfile_props: scene_pb2.RayFileProperties,
            default_parameters: Optional[RayFileSourceParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "ExitGeometries class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._rayfile_props = rayfile_props

            if default_parameters is not None:
                self.geometries = default_parameters.exit_geometry

        @property
        def geometries(self) -> List[GeoRef]:
            """Exit geometries.

            Parameters
            ----------
            exit_geometries: Optional[List[Union[GeoRef, body.Body, face.Face]]]
                Exit Geometries that will use this rayfile source.
                By default, ``[]``.


            Returns
            -------
            List[GeoRef]
                Exit Geometries that will use this rayfile source.
                By default, ``[]``.

            """
            return self._rayfile_props.exit_geometries.geo_paths

        @geometries.setter
        def geometries(
            self,
            exit_geometries: Optional[List[Union[GeoRef, body.Body, face.Face]]] = None,
        ) -> None:
            geo_paths = []
            if not exit_geometries or len(exit_geometries) == 0:
                self._rayfile_props.ClearField("exit_geometries")
            else:
                for geometry in exit_geometries:
                    if isinstance(geometry, GeoRef):
                        geo_paths.append(geometry.to_native_link())
                    elif isinstance(geometry, (body.Body, face.Face)):
                        geo_paths.append(geometry.geo_path.to_native_link())
                    else:
                        raise ValueError("provided geometry is not of type supported")
                self._rayfile_props.exit_geometries.geo_paths[:] = geo_paths

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_parameters: Optional[RayFileSourceParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._client = self._project.client

        spectrum_guid = ""
        if self._source_template.rayfile.HasField("spectrum_guid"):
            spectrum_guid = self._source_template.rayfile.spectrum_guid
        self._spectrum = self._Spectrum(
            speos_client=self._client,
            name=name,
            message_to_complete=self._source_template.rayfile,
            spectrum_guid=spectrum_guid,
        )
        if spectrum_guid == "":
            self.set_spectrum_from_ray_file()

        self._name = name
        # Attribute gathering more complex flux type
        self._type = None
        # Attribute gathering more complex exit geometries settings
        self._exit_geometry_type = None

        if default_parameters is not None:
            self.ray_file_uri = default_parameters.ray_file_uri
            match type(default_parameters.flux_type).__name__:
                case "FluxFromFileParameters":
                    self.set_flux_from_ray_file()
                case "LuminousFluxParameters":
                    self.flux.set_luminous()
                    self.flux.value = default_parameters.flux_type.value
                case "RadiantFluxParameters":
                    self.flux.set_radiant()
                    self.flux.value = default_parameters.flux_type.value
                case _:
                    raise ValueError(
                        f"Unsupported flux type: {type(default_parameters.flux_type).__name__}"
                    )

            self.axis_system = default_parameters.axis_system

            if default_parameters.spectrum_type is not None:
                match type(default_parameters.spectrum_type).__name__:
                    case "SpectrumBlackBodyParameters":
                        self.spectrum.set_blackbody().temperature = (
                            default_parameters.spectrum_type.temperature
                        )
                    case "SpectrumLibraryParameters":
                        self.spectrum.set_library().file_uri = (
                            default_parameters.spectrum_type.file_uri
                        )
                    case "SpectrumMonochromaticParameters":
                        self.spectrum.set_monochromatic().wavelength = (
                            default_parameters.spectrum_type.wavelength
                        )
                    case _:
                        raise ValueError(
                            "Unsupported spectrum type: {}".format(
                                type(default_parameters.spectrum_type).__name__
                            )
                        )

            if default_parameters.exit_geometry is not None:
                self.set_exit_geometries().geometries = default_parameters.exit_geometry

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Rayfile source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            feature_pos_info = self.get(key="axis_system")
            feature_rayfile_pos = np.array(feature_pos_info[:3])
            feature_rayfile_x_dir = np.array(feature_pos_info[3:6])
            feature_rayfile_y_dir = np.array(feature_pos_info[6:9])
            feature_rayfile_z_dir = np.array(feature_pos_info[9:12])
            self._visual_data.coordinates.origin = feature_rayfile_pos
            self._visual_data.coordinates.x_axis = feature_rayfile_x_dir
            self._visual_data.coordinates.y_axis = feature_rayfile_y_dir
            self._visual_data.coordinates.z_axis = feature_rayfile_z_dir
            self._visual_data.updated = True
            return self._visual_data

    @property
    def ray_file_uri(self) -> str:
        """Ray file URI.

        This property retrieve and defines the file uri of ray file used.

        Parameters
        ----------
        uri: Union[Path, str]
            Ray file URI.

        Returns
        -------
        str
            Ray file URI.

        """
        return self._source_template.rayfile.ray_file_uri

    @ray_file_uri.setter
    def ray_file_uri(self, uri: Union[Path, str]) -> None:
        self._source_template.rayfile.ray_file_uri = str(uri)

    def set_flux_from_ray_file(self) -> SourceRayFile:
        """Take flux from ray file provided.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.flux_from_ray_file.SetInParent()
        return self

    @property
    def flux(self) -> SourceRayFile.Flux:
        """Flux definition of the Rayfile source.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile.Flux
            flux object of the source

        """
        if self._type is None and self._source_template.HasField("rayfile"):
            self._type = BaseSource.Flux(
                flux=self._source_template.rayfile,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSource.Flux):
            self._type = BaseSource.Flux(
                flux=self._source_template.rayfile,
                default_parameters=RayFileSourceParameters().flux_type,
                stable_ctr=True,
            )
        elif self._type._flux is not self._source_template.rayfile:
            self._type._flux = self._source_template.rayfile
        return self._type

    def set_spectrum_from_ray_file(self) -> SourceRayFile:
        """Take spectrum from ray file provided.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.spectrum_from_ray_file.SetInParent()
        self._spectrum._no_spectrum_local = True
        return self

    @property
    def spectrum(self) -> Spectrum:
        """Spectrum property of the Source.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._source_template.rayfile.HasField("spectrum_from_ray_file"):
            guid = ""
            if self._spectrum._spectrum.spectrum_link is not None:
                guid = self._spectrum._spectrum.spectrum_link.key
            self._source_template.rayfile.spectrum_guid = guid

        if self._spectrum._message_to_complete is not self._source_template.rayfile:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.rayfile

        self._spectrum._no_spectrum_local = False
        return self._spectrum._spectrum

    @property
    def axis_system(self) -> list[float]:
        """Axis system of the Source.

        This property retrieve and defines the axis system of the source.

        Parameters
        ----------
        axis_system: list[float]
            Position of the rayfile source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        list[float]
            Position of the rayfile source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        """
        return self._source_instance.rayfile_properties.axis_system[:]

    @axis_system.setter
    def axis_system(self, axis_system: list[float]) -> None:
        self._source_instance.rayfile_properties.axis_system[:] = axis_system

    def set_exit_geometries(self) -> SourceRayFile.ExitGeometries:
        """Set exit geometries.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile.ExitGeometries
            ExitGeometries settings of rayfile source.
        """
        if self._exit_geometry_type is None and self._source_instance.rayfile_properties.HasField(
            "exit_geometries"
        ):
            self._exit_geometry_type = SourceRayFile.ExitGeometries(
                rayfile_props=self._source_instance.rayfile_properties,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._exit_geometry_type, SourceRayFile.ExitGeometries):
            self._exit_geometry_type = SourceRayFile.ExitGeometries(
                rayfile_props=self._source_instance.rayfile_properties,
                default_parameters=RayFileSourceParameters(),
                stable_ctr=True,
            )
        elif (
            self._exit_geometry_type._rayfile_props is not self._source_instance.rayfile_properties
        ):
            self._exit_geometry_type._rayfile_props = self._source_instance.rayfile_properties
        return self._exit_geometry_type


class SourceSurface(BaseSource):
    """Type of Source : Surface.

    By default, a luminous flux and existence constant are chosen. With a monochromatic spectrum,
    and lambertian intensity (cos with N = 1).

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    name : str
        Name of the source feature.
    surface : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface
        Surface source to complete.
    surface_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.SurfaceProperties
        Surface source properties to complete.
    default_parameters : Optional[SurfaceSourceParameters] = None
        Uses default values when True.
    """

    class Flux(BaseSource.Flux):
        """Different types of flux including luminous flux of intensity."""

        def __init__(
            self,
            flux: source_pb2,
            default_parameters: Optional[
                Union[
                    LuminousFluxParameters,
                    RadiantFluxParameters,
                    IntensityFluxParameters,
                    FluxFromFileParameters,
                ]
            ] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Flux class instantiated outside of class scope"
                raise RuntimeError(msg)
            super().__init__(flux, default_parameters, stable_ctr)

            if default_parameters is not None:
                if isinstance(default_parameters, IntensityFluxParameters):
                    self.set_luminous_intensity()
                    self.value = default_parameters.value

        def set_luminous_intensity(self):
            """Set flux type luminous intensity.

            Returns
            -------
            None

            """
            self._flux_type = self._flux.luminous_intensity_flux

    class ExitanceConstant:
        """Type of surface source existence : existence constant.

        Parameters
        ----------
        exitance_constant : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface.
        ExitanceConstant
            Existence constant to complete.
        exitance_constant_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.
        SurfaceProperties.ExitanceConstantProperties
            Existence constant properties to complete.
        default_parameters: Optional[ConstantExitanceParameters] = None,
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_exitance_constant method
        available in Source classes.
        """

        def __init__(
            self,
            exitance_constant,
            exitance_constant_props,
            default_parameters: Optional[ConstantExitanceParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "ExitanceConstant class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._exitance_constant = exitance_constant
            self._exitance_constant_props = exitance_constant_props
            if default_parameters is not None:
                self.geometries = default_parameters.emissive_faces

        @property
        def geometries(self) -> List[tuple[GeoRef, bool]]:
            """Geometries linked to surface source.

            Parameters
            ----------
            geometries: List[tuple[GeoRef, bool]]
                list of tuple which contains geometry ref and bool for normal direction.

            Returns
            -------
            List[tuple[GeoRef, bool]]
                list of tuple which contains geometry ref and bool for normal direction.

            """
            return self._exitance_constant_props.geo_paths

        @geometries.setter
        def geometries(self, geometries: List[tuple[Union[GeoRef, face.Face, body.Body], bool]]):
            geo_paths = []
            for gr, reverse_normal in geometries:
                if isinstance(gr, GeoRef):
                    geo_paths.append(
                        ProtoScene.GeoPath(
                            geo_path=gr.to_native_link(), reverse_normal=reverse_normal
                        )
                    )
                elif isinstance(gr, (face.Face, body.Body)):
                    geo_paths.append(
                        ProtoScene.GeoPath(
                            geo_path=gr.geo_path.to_native_link(), reverse_normal=reverse_normal
                        )
                    )
                else:
                    msg = f"Type {type(gr)} is not supported as Surface Source geometry input."
                    raise TypeError(msg)
            self._exitance_constant_props.ClearField("geo_paths")
            self._exitance_constant_props.geo_paths.extend(geo_paths)

    class ExitanceVariable:
        """Type of surface source existence : existence variable.

        Parameters
        ----------
        exitance_variable : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface.
        ExitanceVariable
            Existence variable to complete.
        exitance_variable_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.
        SurfaceProperties.ExitanceVariableProperties
            Existence variable properties to complete.
        default_parameters: Optional[VariableExitanceParameters] = None
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_exitance_variable method available in
        Source classes.
        """

        def __init__(
            self,
            exitance_variable,
            exitance_variable_props,
            default_parameters: Optional[VariableExitanceParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "ExitanceVariable class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._exitance_variable = exitance_variable
            self._exitance_variable_props = exitance_variable_props

            if default_parameters is not None:
                # Default values
                self._exitance_variable.SetInParent()
                self.axis_plane = default_parameters.axis_system
                self.xmp_file_uri = default_parameters.xmp_file_uri

        @property
        def xmp_file_uri(self) -> str:
            """Xmp file uri.

            Parameters
            ----------
            xmp_file_uri: Union[str, Path]
                xmp file uri.

            Returns
            -------
            str
                xmp file uri.

            """
            return self._exitance_variable.exitance_xmp_file_uri

        @xmp_file_uri.setter
        def xmp_file_uri(self, xmp_file_uri: Union[str, Path]) -> None:
            self._exitance_variable.exitance_xmp_file_uri = str(xmp_file_uri)

        @property
        def axis_plane(self) -> List[float]:
            """Axis plane of the variable exitance surface source.

            Parameters
            ----------
            axis_plane: List[float]
                Position of the existence map [Ox Oy Oz Xx Xy Xz Yx Yy Yz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.

            Returns
            -------
            List[float]
                Position of the existence map [Ox Oy Oz Xx Xy Xz Yx Yy Yz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.

            """
            return self._exitance_variable_props.axis_plane

        @axis_plane.setter
        def axis_plane(self, axis_plane: List[float]) -> None:
            self._exitance_variable_props.axis_plane[:] = axis_plane

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_parameters: Optional[SurfaceSourceParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._speos_client = self._project.client
        self._name = name

        spectrum_guid = ""
        if self._source_template.surface.HasField("spectrum_guid"):
            spectrum_guid = self._source_template.surface.spectrum_guid
        self._spectrum = self._Spectrum(
            speos_client=self._speos_client,
            name=name,
            message_to_complete=self._source_template.surface,
            spectrum_guid=spectrum_guid,
        )

        self._intensity = Intensity(
            speos_client=self._speos_client,
            name=name + ".Intensity",
            intensity_props_to_complete=self._source_instance.surface_properties.intensity_properties,
            key=self._source_template.surface.intensity_guid,
        )

        # Attribute gathering more complex existence type
        self._exitance_type = None
        # Attribute gathering more complex flux type
        self._flux_type = None

        if default_parameters is not None:
            # Flux
            match type(default_parameters.flux_type).__name__:
                case "FluxFromFileParameters":
                    self.set_flux_from_intensity_file()
                case "LuminousFluxParameters":
                    self.flux.set_luminous()
                    self.flux.value = default_parameters.flux_type.value
                case "RadiantFluxParameters":
                    self.flux.set_radiant()
                    self.flux.value = default_parameters.flux_type.value
                case "IntensityFluxParameters":
                    self.flux.set_luminous_intensity()
                    self.flux.value = default_parameters.flux_type.value
                case _:
                    raise ValueError(
                        f"Unsupported flux type: {type(default_parameters.flux_type).__name__}"
                    )

            # Exitance
            match type(default_parameters.exitance_type).__name__:
                case "VariableExitanceParameters":
                    self.set_exitance_variable().xmp_file_uri = (
                        default_parameters.exitance_type.xmp_file_uri
                    )
                    self.set_exitance_variable().axis_plane = (
                        default_parameters.exitance_type.axis_system
                    )
                case "ConstantExitanceParameters":
                    self.set_exitance_constant().geometries = (
                        default_parameters.exitance_type.emissive_faces
                    )
                case _:
                    raise ValueError(
                        "Unsupported exitance type: {}".format(
                            type(default_parameters.exitance_type).__name__
                        )
                    )

            # Spectrum
            if default_parameters.spectrum_type is not None:
                match type(default_parameters.spectrum_type).__name__:
                    case "SpectrumBlackBodyParameters":
                        self.spectrum.set_blackbody().temperature = (
                            default_parameters.spectrum_type.temperature
                        )
                    case "SpectrumLibraryParameters":
                        self.spectrum.set_library().file_uri = (
                            default_parameters.spectrum_type.file_uri
                        )
                    case "SpectrumMonochromaticParameters":
                        self.spectrum.set_monochromatic().wavelength = (
                            default_parameters.spectrum_type.wavelength
                        )
                    case _:
                        raise ValueError(
                            "Unsupported spectrum type: {}".format(
                                type(default_parameters.spectrum_type).__name__
                            )
                        )

            # Intensity
            match type(default_parameters.intensity_type).__name__:
                case "IntensityLambertianParameters":
                    self.intensity.set_cos().n = 1
                    self.intensity.set_cos().total_angle = (
                        default_parameters.intensity_type.total_angle
                    )
                case "IntensityCosParameters":
                    self.intensity.set_cos().n = default_parameters.intensity_type.n
                    self.intensity.set_cos().total_angle = (
                        default_parameters.intensity_type.total_angle
                    )
                case "IntensitySymmetricGaussianParameters":
                    self.intensity.set_gaussian().fwhm_angle_x = (
                        default_parameters.intensity_type.fwhm
                    )
                    self.intensity.set_gaussian().fwhm_angle_y = (
                        default_parameters.intensity_type.fwhm
                    )
                    self.intensity.set_gaussian().total_angle = (
                        default_parameters.intensity_type.total_angle
                    )
                case "IntensitAsymmetricGaussianParameters":
                    self.intensity.set_gaussian().fwhm_angle_x = (
                        default_parameters.intensity_type.fwhm_x
                    )
                    self.intensity.set_gaussian().fwhm_angle_y = (
                        default_parameters.intensity_type.fwhm_y
                    )
                    self.intensity.set_gaussian().total_angle = (
                        default_parameters.intensity_type.total_angle
                    )
                    self.intensity.set_gaussian().axis_system = (
                        default_parameters.intensity_type.axis_system
                    )
                case "IntensityLibraryParameters":
                    self.intensity.set_library().intensity_file_uri = (
                        default_parameters.intensity_type.intensity_file_uri
                    )
                    if default_parameters.intensity_type.exit_geometries is not None:
                        self.intensity.set_library().exit_geometries = (
                            default_parameters.intensity_type.exit_geometries
                        )
                    match default_parameters.intensity_type.orientation_type:
                        case IntensityOrientationType.normal_to_uv:
                            self.intensity.set_library().set_orientation_normal_to_uv_map()
                        case IntensityOrientationType.normal_to_surface:
                            self.intensity.set_library().set_orientation_normal_to_surface()
                        case _:
                            match type(default_parameters.intensity_type.orientation_type).__name__:
                                case "IntensityOrientationAxisSystemParameters":
                                    orientation_axis = (
                                        default_parameters.intensity_type.orientation_type
                                    )
                                    axis_parameters = orientation_axis.axis_system
                                    self.intensity.set_library().orientation_axis_system = (
                                        axis_parameters
                                    )
                                case _:
                                    raise ValueError(
                                        "Unsupported orientation type: {}".format(
                                            type(
                                                default_parameters.intensity_type.orientation_type
                                            ).__name__
                                        )
                                    )
                case _:
                    raise ValueError(
                        "Unsupported intensity type: {}".format(
                            type(default_parameters.intensity_type).__name__
                        )
                    )

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Surface source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(
                    ray=True,
                    coordinate_system=True
                    if isinstance(self._exitance_type, SourceSurface.ExitanceVariable)
                    else False,
                )
                if general_methods._GRAPHICS_AVAILABLE
                else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            if self._visual_data.coordinates is not None:
                feature_pos_info = self.get(key="axis_plane")
                feature_surface_pos = np.array(feature_pos_info[:3])
                feature_surface_x_dir = np.array(feature_pos_info[3:6])
                feature_surface_y_dir = np.array(feature_pos_info[6:9])
                self._visual_data.coordinates.origin = feature_surface_pos
                self._visual_data.coordinates.x_axis = feature_surface_x_dir
                self._visual_data.coordinates.y_axis = feature_surface_y_dir
            self._visual_data.updated = True
            return self._visual_data

    def set_flux_from_intensity_file(self) -> SourceSurface:
        """Take flux from intensity file provided.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.flux_from_intensity_file.SetInParent()
        return self

    @property
    def flux(self) -> SourceSurface.Flux:
        """Flux property of the Surface source.

        Returns
        -------
        ansys.speos.core.source.SourceSurface.Flux
            flux object of the source

        """
        if self._flux_type is None and self._source_template.HasField("surface"):
            self._flux_type = SourceSurface.Flux(
                flux=self._source_template.surface,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._flux_type, SourceSurface.Flux):
            self._flux_type = SourceSurface.Flux(
                flux=self._source_template.surface,
                default_parameters=SurfaceSourceParameters().flux_type,
                stable_ctr=True,
            )
        elif self._flux_type._flux is not self._source_template.surface:
            self._flux_type._flux = self._source_template.surface
        return self._flux_type

    @property
    def intensity(self) -> intensity.Intensity:
        """Intensity property.

        Returns
        -------
        ansys.speos.core.intensity.Intensity
            Intensity.
        """
        if (
            self._intensity._intensity_properties
            is not self._source_instance.surface_properties.intensity_properties
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._intensity._intensity_properties = (
                self._source_instance.surface_properties.intensity_properties
            )

        return self._intensity

    def set_exitance_constant(self) -> SourceSurface.ExitanceConstant:
        """Set existence constant.

        Returns
        -------
        ansys.speos.core.source.SourceSurface.ExitanceConstant
            ExitanceConstant of surface source.
        """
        if self._exitance_type is None and self._source_template.surface.HasField(
            "exitance_constant"
        ):
            # Happens in case of project created via load of speos file
            self._exitance_type = SourceSurface.ExitanceConstant(
                exitance_constant=self._source_template.surface.exitance_constant,
                exitance_constant_props=self._source_instance.surface_properties.exitance_constant_properties,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._exitance_type, SourceSurface.ExitanceConstant):
            # if the _exitance_type is not ExitanceConstant then we create a new type.
            self._source_template.surface.exitance_constant.SetInParent()
            self._exitance_type = SourceSurface.ExitanceConstant(
                exitance_constant=self._source_template.surface.exitance_constant,
                exitance_constant_props=self._source_instance.surface_properties.exitance_constant_properties,
                default_parameters=ConstantExitanceParameters(),
                stable_ctr=True,
            )
        elif (
            self._exitance_type._exitance_constant
            is not self._source_template.surface.exitance_constant
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._exitance_type._exitance_constant = self._source_template.surface.exitance_constant
            self._exitance_type.__exitance_constant_props = (
                self._source_instance.surface_properties.exitance_constant_properties
            )
        return self._exitance_type

    def set_exitance_variable(self) -> SourceSurface.ExitanceVariable:
        """Set existence variable, taken from XMP map.

        Returns
        -------
        ansys.speos.core.source.SourceSurface.ExitanceVariable
            ExitanceVariable of surface source.
        """
        if self._exitance_type is None and self._source_template.surface.HasField(
            "exitance_variable"
        ):
            # Happens in case of project created via load of speos file
            self._exitance_type = SourceSurface.ExitanceVariable(
                exitance_variable=self._source_template.surface.exitance_variable,
                exitance_variable_props=self._source_instance.surface_properties.exitance_variable_properties,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._exitance_type, SourceSurface.ExitanceVariable):
            # if the _exitance_type is not ExitanceVariable then we create a new type.
            self._exitance_type = SourceSurface.ExitanceVariable(
                exitance_variable=self._source_template.surface.exitance_variable,
                exitance_variable_props=self._source_instance.surface_properties.exitance_variable_properties,
                default_parameters=VariableExitanceParameters(),
                stable_ctr=True,
            )
        elif (
            self._exitance_type._exitance_variable
            is not self._source_template.surface.exitance_variable
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._exitance_type._exitance_variable = self._source_template.surface.exitance_variable
            self._exitance_type._exitance_variable_props = (
                self._source_instance.surface_properties.exitance_variable_properties
            )
        return self._exitance_type

    def set_spectrum_from_xmp_file(self) -> SourceSurface:
        """Take spectrum from xmp file provided.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.spectrum_from_xmp_file.SetInParent()
        self._spectrum._no_spectrum_local = True
        return self

    @property
    def spectrum(self) -> Spectrum:
        """Spectrum property of the Source.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._source_template.surface.HasField("spectrum_from_xmp_file"):
            guid = ""
            if self._spectrum._spectrum.spectrum_link is not None:
                guid = self._spectrum._spectrum.spectrum_link.key
            self._source_template.surface.spectrum_guid = guid

        if self._spectrum._message_to_complete is not self._source_template.surface:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.surface

        self._spectrum._no_spectrum_local = False
        return self._spectrum._spectrum

    def commit(self) -> SourceSurface:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        # intensity
        self._intensity.commit()
        self._source_template.surface.intensity_guid = self._intensity.intensity_template_link.key

        # spectrum & source
        super().commit()
        return self

    def reset(self) -> SourceSurface:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        self._intensity.reset()
        # spectrum & source
        super().reset()
        return self

    def delete(self) -> SourceSurface:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        # Currently we don't perform delete in cascade,
        # so deleting a surface source does not delete the intensity template used
        # self._intensity.delete()

        # spectrum & source
        super().delete()
        return self


class BaseSourceAmbient(BaseSource):
    """
    Super Class for ambient sources.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which source shall be created.
    name : str
        Name of the source.
    description : str
        Description of the source.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance, optional
        Source instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
    ) -> None:
        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )

    class AutomaticSun:
        """Sun type Automatic.

        By default, user's current time and Ansys France is used a time zone.

        Parameters
        ----------
        sun: ansys.api.speos.scene.v2.scene_pb2.AutomaticSun
            Wavelengths range protobuf object to modify.
        default_parameters: Optional[AutomaticSunParameters] = None,
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_sun_automatic method available in
        source classes.
        """

        def __init__(
            self,
            sun: scene_pb2.AutomaticSun,
            default_parameters: Optional[AutomaticSunParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError(
                    "BaseSourceAmbient.AutomaticSun class instantiated outside of class scope"
                )
            self._sun = sun

            if default_parameters is not None:
                self.year = default_parameters.year
                self.month = default_parameters.month
                self.day = default_parameters.day
                self.hour = default_parameters.hour
                self.minute = default_parameters.minute
                self.time_zone = default_parameters.time_zone
                self.longitude = default_parameters.longitude
                self.latitude = default_parameters.latitude

        @property
        def year(self) -> int:
            """Property of year info of the automatic sun.

            Parameters
            ----------
            year: int
                year information.

            Returns
            -------
            int
                year info.
            """
            return self._sun.year

        @year.setter
        def year(self, year: int) -> None:
            self._sun.year = year

        @property
        def month(self) -> int:
            """Property of month info of the automatic sun.

            Parameters
            ----------
            month: int
                month information.

            Returns
            -------
            int
                month information.

            """
            return self._sun.month

        @month.setter
        def month(self, month: int) -> None:
            self._sun.month = month

        @property
        def day(self) -> int:
            """Property of day info of the automatic sun.

            Parameters
            ----------
            day: int
                day information.

            Returns
            -------
            int
                day information.
            """
            return self._sun.day

        @day.setter
        def day(self, day: int) -> None:
            self._sun.day = day

        @property
        def hour(self) -> int:
            """Get hour info of the automatic sun.

            Parameters
            ----------
            hour: int
                hour information.

            Returns
            -------
            int
                hour information.

            """
            return self._sun.hour

        @hour.setter
        def hour(self, hour: int) -> None:
            self._sun.hour = hour

        @property
        def minute(self) -> int:
            """Property of minute info of the automatic sun.

            Parameters
            ----------
            minute: int
                minute information.

            Returns
            -------
            int
                minute information.

            """
            return self._sun.minute

        @minute.setter
        def minute(self, minute: int) -> None:
            self._sun.minute = minute

        @property
        def longitude(self) -> float:
            """Property of longitude info of the automatic sun.

            Parameters
            ----------
            longitude: float
                longitude information.

            Returns
            -------
            float
                longitude information.
            """
            return self._sun.longitude

        @longitude.setter
        def longitude(self, longitude: float) -> None:
            self._sun.longitude = longitude

        @property
        def latitude(self) -> float:
            """Property of latitude info of the automatic sun.

            Parameters
            ----------
            latitude: float
                latitude information.

            Returns
            -------
            float
                latitude information.
            """
            return self._sun.latitude

        @latitude.setter
        def latitude(self, latitude: float) -> None:
            self._sun.latitude = latitude

        @property
        def time_zone(self) -> str:
            """Property of time zone info of the automatic sun.

                default value to be "CET".

            Parameters
            ----------
            timezone: str
                timezone abbreviation.

            Returns
            -------
            str
                time zone abbreviation.
            """
            return self._sun.time_zone_uri

        @time_zone.setter
        def time_zone(self, time_zone: str) -> None:
            self._sun.time_zone_uri = time_zone

    class Manual:
        """Sun type Manual>.

        By default, z-axis [0, 0, 1] is used as sun direction.

        Parameters
        ----------
        sun: ansys.api.speos.scene.v2.scene_pb2.ManualSun
            Wavelengths range protobuf object to modify.
        default_parameters: Optional[ManualSunParameters] = None
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_sun_manual method available in
        source classes.
        """

        def __init__(
            self,
            sun: scene_pb2.ManualSun,
            default_parameters: Optional[ManualSunParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError(
                    "BaseSourceAmbient.Manual class instantiated outside of class scope"
                )
            self._sun = sun

            if default_parameters is not None:
                self.direction = default_parameters.direction

        @property
        def direction(self) -> List[float]:
            """Property of direction of the manual sun.

                default value to be [0, 0, 1].

            Parameters
            ----------
            direction: List[float]
                direction of the sun.

            Returns
            -------
            list of float
                list describing the direction of the manual sun.

            """
            return self._sun.sun_direction

        @direction.setter
        def direction(self, direction: List[float]) -> None:
            self._sun.sun_direction[:] = direction

        @property
        def reverse_sun(self) -> bool:
            """Property of whether reverse direction of the manual sun.

                default value to be False.

            Parameters
            ----------
            value: bool
                True to reverse direction, False to not reverse direction

            Returns
            -------
            bool
                True to reverse direction, False to not reverse direction

            """
            return self._sun.reverse_sun

        @reverse_sun.setter
        def reverse_sun(self, value: bool) -> None:
            self._sun.reverse_sun = value


class SourceAmbientNaturalLight(BaseSourceAmbient):
    """Natural light ambient source.

    By default, turbidity is set to be 3 with Sky.
    [0, 0, 1] is used as zenith direction, [0, 1, 0] as north direction.
    Sun type is set to be automatic type.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    default_parameters : Optional[AmbientNaturalLightParameters] = None
        Uses default values when True.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_parameters: Optional[AmbientNaturalLightParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._speos_client = self._project.client
        self._name = name
        self._type = None

        if default_parameters is not None:
            self.with_sky = default_parameters.with_sky
            self.turbidity = default_parameters.turbidity
            self.zenith_direction = default_parameters.zenith_direction
            self.north_direction = default_parameters.north_direction
            if isinstance(default_parameters.sun_type, AutomaticSunParameters):
                self.set_sun_automatic().longitude = default_parameters.sun_type.longitude
                self.set_sun_automatic().latitude = default_parameters.sun_type.latitude
                self.set_sun_automatic().year = default_parameters.sun_type.year
                self.set_sun_automatic().month = default_parameters.sun_type.month
                self.set_sun_automatic().day = default_parameters.sun_type.day
                self.set_sun_automatic().hour = default_parameters.sun_type.hour
                self.set_sun_automatic().minute = default_parameters.sun_type.minute
            elif isinstance(default_parameters.sun_type, ManualSunParameters):
                self.set_sun_manual().direction = default_parameters.sun_type.direction
            else:
                raise ValueError(
                    f"Unsupported sun type: {type(default_parameters.sun_type).__name__}"
                )

    @property
    def turbidity(self) -> float:
        """Property turbidity of the natural light source.

            default value to be 3.

        Parameters
        ----------
        value: float
            set value of Turbidity the measure of the fraction of scattering.


        Returns
        -------
        float
            value of Turbidity the measure of the fraction of scattering.

        """
        return self._source_template.ambient.natural_light.turbidity

    @turbidity.setter
    def turbidity(self, value: float) -> None:
        if not 1.9 <= value <= 9.9:
            raise ValueError("Varies needs to be between 1.9 and 9.9")
        self._source_template.ambient.natural_light.turbidity = value

    @property
    def with_sky(self) -> bool:
        """Bool Property of whether activated using sky in the natural light source.

            default value to be True.

        Parameters
        ----------
        value: bool
            True as using sky, while False as using natural light without the sky.


        Returns
        -------
        bool
            True as using sky, while False as using natural light without the sky.

        """
        return self._source_template.ambient.natural_light.with_sky

    @with_sky.setter
    def with_sky(self, value: bool) -> None:
        self._source_template.ambient.natural_light.with_sky = value

    @property
    def zenith_direction(self) -> List[float]:
        """Property zenith direction of the natural light source.

            default value to be [0, 0, 1]

        Parameters
        ----------
        direction: Optional[List[float]]
            direction defines the zenith direction of the natural light.

        Returns
        -------
        List[float]
            direction defines the zenith direction of the natural light.

        """
        return self._source_instance.ambient_properties.zenith_direction

    @zenith_direction.setter
    def zenith_direction(self, direction: Optional[List[float]] = None) -> None:
        self._source_instance.ambient_properties.zenith_direction[:] = direction

    @property
    def reverse_zenith_direction(self) -> bool:
        """
        Property whether reverse zenith direction of the natural light source.

            default value to be False.

        Parameters
        ----------
        value: bool
            True to reverse zenith direction, False otherwise.

        Returns
        -------
        bool
            True to reverse zenith direction, False otherwise.

        """
        return self._source_instance.ambient_properties.reverse_zenith

    @reverse_zenith_direction.setter
    def reverse_zenith_direction(self, value: bool) -> None:
        self._source_instance.ambient_properties.reverse_zenith = value

    @property
    def north_direction(self) -> List[float]:
        """Property north direction of the natural light source.

            default value to be [0, 1, 0].

        Parameters
        ----------
        direction: List[float]
            direction defines the north direction of the natural light.

        Returns
        -------
        List[float]
            direction defines the north direction of the natural light.

        """
        return self._source_instance.ambient_properties.natural_light_properties.north_direction

    @north_direction.setter
    def north_direction(self, direction: List[float]) -> None:
        self._source_instance.ambient_properties.natural_light_properties.north_direction[:] = (
            direction
        )

    @property
    def reverse_north_direction(self) -> bool:
        """Property whether reverse north direction of the natural light source.

            default value to be False.

        Parameters
        ----------
        value: bool
            True to reverse north direction, False otherwise.

        Returns
        -------
        bool
            True as reverse north direction, False otherwise.

        """
        return self._source_instance.ambient_properties.natural_light_properties.reverse_north

    @reverse_north_direction.setter
    def reverse_north_direction(self, value: bool) -> None:
        self._source_instance.ambient_properties.natural_light_properties.reverse_north = value

    def set_sun_automatic(self) -> BaseSourceAmbient.AutomaticSun:
        """Set natural light sun type as automatic.

        Returns
        -------
        BaseSourceAmbient.AutomaticSun

        """
        natural_light_properties = self._source_instance.ambient_properties.natural_light_properties
        if self._type is None and natural_light_properties.sun_axis_system.HasField(
            "automatic_sun"
        ):
            self._type = BaseSourceAmbient.AutomaticSun(
                natural_light_properties.sun_axis_system.automatic_sun,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSourceAmbient.AutomaticSun):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSourceAmbient.AutomaticSun(
                natural_light_properties.sun_axis_system.automatic_sun,
                default_parameters=AutomaticSunParameters(),
                stable_ctr=True,
            )
        elif self._type._sun is not natural_light_properties.sun_axis_system.automatic_sun:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sun = natural_light_properties.sun_axis_system.automatic_sun
        return self._type

    def set_sun_manual(self) -> BaseSourceAmbient.Manual:
        """Set natural light sun type as manual.

        Returns
        -------
        BaseSourceAmbient.Manual
        """
        natural_light_properties = self._source_instance.ambient_properties.natural_light_properties
        if self._type is None and natural_light_properties.sun_axis_system.HasField("manual_sun"):
            self._type = BaseSourceAmbient.Manual(
                natural_light_properties.sun_axis_system.manual_sun,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSourceAmbient.Manual):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSourceAmbient.Manual(
                natural_light_properties.sun_axis_system.manual_sun,
                default_parameters=ManualSunParameters(),
                stable_ctr=True,
            )
        elif self._type._sun is not natural_light_properties.sun_axis_system.manual_sun:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sun = natural_light_properties.sun_axis_system.manual_sun
        return self._type


class SourceAmbientEnvironment(BaseSourceAmbient):
    """Environment ambient source.

    By default [0, 0, 1] is used as zenith direction, [0, 1, 0] as north direction.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    default_parameters : Optional[AmbientEnvironmentParameters] = None
        Uses default values when True.
    """

    # source_type = "SourceAmbientEnvironment"
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_parameters: Optional[AmbientEnvironmentParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._speos_client = self._project.client
        self._name = name
        self._type = None

        if default_parameters is not None:
            self.zenith_direction = default_parameters.zenith_direction
            self.north_direction = default_parameters.north_direction
            self.luminance = default_parameters.luminance
            match default_parameters.color_space_type:
                case ColorSpaceType.srgb:
                    self.set_predefined_color_space().set_color_space_srgb()
                case ColorSpaceType.adobe_rgb:
                    self.set_predefined_color_space().set_color_space_adobergb()
                case _:
                    if isinstance(
                        default_parameters.color_space_type, UserDefinedColorSpaceParameters
                    ):
                        self.set_userdefined_color_space().red_spectrum = (
                            default_parameters.color_space_type.red_spectrum_uri
                        )
                        self.set_userdefined_color_space().green_spectrum = (
                            default_parameters.color_space_type.green_spectrum_uri
                        )
                        self.set_userdefined_color_space().blue_spectrum = (
                            default_parameters.color_space_type.blue_spectrum_uri
                        )
                        match default_parameters.color_space_type.white_point_type:
                            case WhitePointType.d65:
                                self.set_userdefined_color_space().set_white_point_type_d65()
                            case WhitePointType.d50:
                                self.set_userdefined_color_space().set_white_point_type_d50()
                            case WhitePointType.c:
                                self.set_userdefined_color_space().set_white_point_type_c()
                            case WhitePointType.e:
                                self.set_userdefined_color_space().set_white_point_type_e()
                            case _:
                                if isinstance(
                                    default_parameters.color_space_type.white_point_type,
                                    UserDefinedWhitePointParameters,
                                ):
                                    color_space_prop = self.set_userdefined_color_space()
                                    white_point_prop = (
                                        color_space_prop.set_white_point_type_user_defined()
                                    )
                                    white_point_prop.white_point = [
                                        default_parameters.color_space_type.white_point_type.x,
                                        default_parameters.color_space_type.white_point_type.y,
                                    ]
                                else:
                                    raise ValueError(
                                        "Unsupported white point type: {}".format(
                                            type(
                                                default_parameters.color_space_type.white_point_type
                                            ).__name__
                                        )
                                    )
                    else:
                        raise ValueError(
                            "Unsupported color space type: {}".format(
                                type(default_parameters.color_space_type).__name__
                            )
                        )

    @property
    def zenith_direction(self) -> List[float]:
        """Zenith direction of the environment light source.

        This property get and set the zenith direction of the environment source.

        Parameters
        ----------
        direction: Optional[List[float]]
            direction defines the zenith direction of the environment light source.

        Returns
        -------
        List[float]
            direction defines the zenith direction of the environment light source.

        """
        return self._source_instance.ambient_properties.zenith_direction

    @zenith_direction.setter
    def zenith_direction(self, direction: Optional[List[float]]) -> None:
        self._source_instance.ambient_properties.zenith_direction[:] = direction

    @property
    def reverse_zenith_direction(self) -> bool:
        """Reverse zenith direction of the environment light source.

        This property get and set if reverse zenith direction is True.


        Parameters
        ----------
        value: bool
            True to reverse zenith direction, False otherwise.

        Returns
        -------
        bool
            True to reverse zenith direction, False otherwise.

        """
        return self._source_instance.ambient_properties.reverse_zenith

    @reverse_zenith_direction.setter
    def reverse_zenith_direction(self, value: bool) -> None:
        self._source_instance.ambient_properties.reverse_zenith = value

    @property
    def north_direction(self) -> List[float]:
        """North direction of the environment light source.

        This property get and set the north direction of the environment source.

        Parameters
        ----------
        direction: List[float]
            direction defines the north direction, default value to be [0, 1, 0].

        Returns
        -------
        List[float]
            direction defines the north direction of the environment source.

        """
        return self._source_instance.ambient_properties.environment_map_properties.north_direction

    @north_direction.setter
    def north_direction(self, direction: List[float]) -> None:
        self._source_instance.ambient_properties.environment_map_properties.north_direction[:] = (
            direction
        )

    @property
    def reverse_north_direction(self) -> bool:
        """Reverse north direction of the environment light source.

        This property get and set if reverse north direction is True.

        Parameters
        ----------
        value: bool
            True to reverse north direction, False otherwise.

        Returns
        -------
        bool
            True as reverse north direction, False otherwise.

        """
        return self._source_instance.ambient_properties.environment_map_properties.reverse_north

    @reverse_north_direction.setter
    def reverse_north_direction(self, value: bool) -> None:
        self._source_instance.ambient_properties.environment_map_properties.reverse_north = value

    @property
    def luminance(self) -> float:
        """Luminance of the environment light source.

        This property get and set the Luminance value of the source.

        Parameters
        ----------
        value: float
            set value of Luminance (cd/m^2).

        Returns
        -------
        float
            value of Luminance setting (cd/m^2).

        """
        return self._source_template.ambient.environment_map.luminance

    @luminance.setter
    def luminance(self, value: float) -> None:
        self._source_template.ambient.environment_map.luminance = value

    @property
    def image_file_uri(self) -> str:
        """Location of the environment image file.

        This property gets or sets the environment image file used by the
        ambient environment source.

        Parameters
        ----------
         uri : Union[str, Path]
            format file uri (hdr, exr, png, bmp, jpg, tiff, rgb).

        Returns
        -------
        uri : str
            format file uri (hdr, exr, png, bmp, jpg, tiff, rgb).
        """
        return self._source_template.ambient.environment_map.image_uri

    @image_file_uri.setter
    def image_file_uri(self, uri: Union[str, Path]) -> None:
        self._source_template.ambient.environment_map.image_uri = str(uri)

    @property
    def color_space(
        self,
    ) -> Union[
        None,
        SourceAmbientEnvironment.PredefinedColorSpace,
        SourceAmbientEnvironment.UserDefinedColorSpace,
    ]:
        """Property containing all options in regard to the color space properties.

        Returns
        -------
        Union[
            None,
            ansys.speos.core.source.SourceAmbientEnvironment.PredefinedColorSpace,
            ansys.speos.core.source.SourceAmbientEnvironment.UserDefinedColorSpace
            ]
            Instance of Predefined Color Space class
        """
        return self._type

    def set_userdefined_color_space(self) -> SourceAmbientEnvironment.UserDefinedColorSpace:
        """Set the color space to user-defined.

        Returns
        -------
        SourceAmbientEnvironment.UserDefinedColorSpace
            Settings for user defined color space.

        """
        if self._type is None and self._source_template.ambient.environment_map.HasField(
            "user_defined_rgb_space"
        ):
            self._type = SourceAmbientEnvironment.UserDefinedColorSpace(
                project=self._project,
                userdefined_color_space=self._source_template.ambient.environment_map.user_defined_rgb_space,
                default_parameters=None,
                stable_ctr=True,
            )
        if not isinstance(self._type, SourceAmbientEnvironment.UserDefinedColorSpace):
            # if the _type is not UserDefinedColorSpace then we create a new type.
            self._type = SourceAmbientEnvironment.UserDefinedColorSpace(
                project=self._project,
                userdefined_color_space=self._source_template.ambient.environment_map.user_defined_rgb_space,
                default_parameters=UserDefinedColorSpaceParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._userdefined_color_space
            is not self._source_template.ambient.environment_map.user_defined_rgb_space
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._userdefined_color_space = (
                self._source_template.ambient.environment_map.user_defined_rgb_space
            )
        return self._type

    def set_predefined_color_space(self) -> SourceAmbientEnvironment.PredefinedColorSpace:
        """Set the color space to use one of the presets.

        Returns
        -------
        ansys.speos.core.source.SourceAmbientEnvironment.PredefinedColorSpace
            Environment source color space for sRGB or AdobeRGB
        """
        if self._type is None and self._source_template.ambient.environment_map.HasField(
            "predefined_color_space"
        ):
            self._type = SourceAmbientEnvironment.PredefinedColorSpace(
                predefined_color_space=self._source_template.ambient.environment_map.predefined_color_space,
                default_parameters=None,
                stable_ctr=True,
            )
        if not isinstance(self._type, SourceAmbientEnvironment.PredefinedColorSpace):
            # if the _type is not PredefinedColorSpace then we create a new type.
            self._type = SourceAmbientEnvironment.PredefinedColorSpace(
                predefined_color_space=self._source_template.ambient.environment_map.predefined_color_space,
                default_parameters=ColorSpaceType.srgb,
                stable_ctr=True,
            )
        elif (
            self._type._predefined_color_space
            is not self._source_template.ambient.environment_map.predefined_color_space
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._predefined_color_space = (
                self._source_template.ambient.environment_map.predefined_color_space
            )
        return self._type

    def commit(self) -> SourceAmbientEnvironment:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceAmbientEnvironment
            Ambient environment Source feature.
        """
        if isinstance(self._type, BaseSource.UserDefinedColorSpace):
            self._type._red_spectrum._commit()
            self._type._green_spectrum._commit()
            self._type._blue_spectrum._commit()
        super().commit()

    def reset(self) -> SourceAmbientEnvironment:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceAmbientEnvironment
            Ambient environment Source feature.
        """
        if isinstance(self._type, BaseSource.UserDefinedColorSpace):
            self._type._red_spectrum._reset()
            self._type._green_spectrum._reset()
            self._type._blue_spectrum._reset()
        super().reset()

    def delete(self) -> SourceAmbientEnvironment:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.SourceAmbientEnvironment
            Ambient environment Source feature.
        """
        if isinstance(self._type, BaseSource.UserDefinedColorSpace):
            self._type._red_spectrum._delete()
            self._type._green_spectrum._delete()
            self._type._blue_spectrum._delete()
        super().delete()
