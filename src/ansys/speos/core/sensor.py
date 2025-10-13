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

"""Provides a way to interact with Speos feature: Sensor."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Mapping, Optional, Union
import uuid
import warnings

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2, sensor_pb2
import grpc
import numpy as np

import ansys.speos.core as core
import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.generic.constants import (
    BalanceModeDisplayPrimariesParameters,
    BalanceModeUserWhiteParameters,
    CameraSensorParameters,
    ColorimetricParameters,
    ColorParameters,
    DimensionsParameters,
    Irradiance3DSensorParameters,
    IrradianceSensorParameters,
    LayerByFaceParameters,
    LayerByIncidenceAngleParameters,
    LayerBySequenceParameters,
    MeasuresParameters,
    MonoChromaticParameters,
    PhotometricCameraParameters,
    RadianceSensorParameters,
    SpectralParameters,
    WavelengthsRangeParameters,
)
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.visualization_methods import _VisualData, local2absolute
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sensor_template import ProtoSensorTemplate
import ansys.speos.core.part as part
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils


class BaseSensor:
    """Base class for Sensor.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Attributes
    ----------
    sensor_template_link : ansys.speos.core.kernel.sensor_template.SensorTemplateLink
        Link object for the sensor template in database.

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
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
    ) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self._visual_data = _VisualData() if general_methods._GRAPHICS_AVAILABLE else None
        self.sensor_template_link = None
        """Link object for the sensor template in database."""
        if metadata is None:
            metadata = {}

        if sensor_instance is None:
            # Create local SensorTemplate
            self._sensor_template = ProtoSensorTemplate(
                name=name, description=description, metadata=metadata
            )
            # Create local SensorInstance
            self._sensor_instance = ProtoScene.SensorInstance(
                name=name, description=description, metadata=metadata
            )
            self.lxp_path_number = None
        else:
            self._unique_id = sensor_instance.metadata["UniqueId"]
            self.sensor_template_link = self._project.client[sensor_instance.sensor_guid]
            # reset will fill _sensor_instance and _sensor_template from respectively project
            # (using _unique_id) and sensor_template_link
            self.reset()

    @property
    def lxp_path_number(self) -> Union[None, int]:
        """Number of LXP rays simulated for the Sensor.

        Returns
        -------
        int
            Number of Rays stored in the lpf file for this Sensor
        """
        if self._sensor_instance.HasField("lxp_properties"):
            return self._sensor_instance.lxp_properties.nb_max_paths
        return None

    @lxp_path_number.setter
    def lxp_path_number(self, value: int):
        """Setter for lxp_path_number property.

        Parameters
        ----------
        value : int
            Integer value to define number of rays stored
        """
        if value:
            self._sensor_instance.lxp_properties.nb_max_paths = int(value)
        else:
            self._sensor_instance.ClearField("lxp_properties")

    class WavelengthsRange:
        """Range of wavelengths.

        By default, a range from 400nm to 700nm is chosen, with a sampling of 13.

        Parameters
        ----------
        wavelengths_range : ansys.api.speos.sensor.v1.common_pb2.WavelengthsRange
            Wavelengths range protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_wavelengths_range method available in
        sensor classes.
        """

        def __init__(
            self,
            wavelengths_range: Union[common_pb2.WavelengthsRange, sensor_pb2.TypeColorimetric],
            default_parameters: Union[None, WavelengthsRangeParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "WavelengthsRange class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._wavelengths_range = wavelengths_range

            if default_parameters:
                # Default values
                self.start = default_parameters.start
                self.end = default_parameters.end
                self.sampling = default_parameters.sampling

        @property
        def start(self) -> float:
            """Minimum wavelength of the range.

            By default, ``400``.

            Returns
            -------
            float
                Lower Bound of the wavelength range.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_start
            else:
                return self._wavelengths_range.wavelength_start

        @start.setter
        def start(self, value: float):
            """Minimum wavelength of the range.

            Parameters
            ----------
            value : float
                Minimum wavelength (nm).
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_start = value
            else:
                self._wavelengths_range.wavelength_start = value

        @property
        def end(self) -> float:
            """Maximum wavelength of the range.

            By default, ``700``.

            Returns
            -------
            float
                Upper Bound of the wavelength range.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_end
            else:
                return self._wavelengths_range.wavelength_end

        @end.setter
        def end(self, value: float):
            """Maximum wavelength of the range.

            Parameters
            ----------
            value : float
                Maximum wavelength (nm).
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_end = value
            else:
                self._wavelengths_range.wavelength_end = value

        @property
        def sampling(self) -> int:
            """Wavelength sampling of between start and end value.

            By default, ``13``.

            Returns
            -------
            int
                Number of Samples used to split the wavelength range.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_sampling

        @sampling.setter
        def sampling(self, value):
            """Wavelength sampling of between start and end value.

            Parameters
            ----------
            value : int
                Number of wavelengths to be taken into account between the minimum and maximum
                wavelengths range.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_sampling = value

    class Dimensions:
        """Dimensions of the sensor.

        By default, for both x and y axis: from -50mm to 50mm is chosen, with a sampling of 100.

        Parameters
        ----------
        sensor_dimensions : ansys.api.speos.sensor.v1.common_pb2.SensorDimensions
            SensorDimensions protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_dimensions method available in sensor
        classes.
        """

        def __init__(
            self,
            sensor_dimensions: common_pb2.SensorDimensions,
            default_parameters: Union[None, DimensionsParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Dimension class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_dimensions = sensor_dimensions

            if default_parameters:
                # Default values
                self.x_start = default_parameters.x_start
                self.y_start = default_parameters.y_start
                self.x_end = default_parameters.x_end
                self.y_end = default_parameters.y_end
                self.x_sampling = default_parameters.x_sampling
                self.y_sampling = default_parameters.y_sampling

        @property
        def x_start(self) -> float:
            """Minimum value on x axis.

            By default, ``-50``.

            Returns
            -------
            float
                minimum value in x axis
            """
            return self._sensor_dimensions.x_start

        @x_start.setter
        def x_start(self, value: float):
            """Minimum value on x axis.

            Parameters
            ----------
            value : float
                Minimum value on x axis (mm).
            """
            self._sensor_dimensions.x_start = value

        @property
        def x_end(self) -> float:
            """Maximum value on x axis.

            By default, ``50``.

            Returns
            -------
            float
                maximum value on x axis.
            """
            return self._sensor_dimensions.x_end

        @x_end.setter
        def x_end(self, value: float):
            """Maximum value on x axis.

            Parameters
            ----------
            value : float
                Maximum value on x axis (mm).
            """
            self._sensor_dimensions.x_end = value

        @property
        def x_sampling(self) -> int:
            """Value of the sampling on x axis.

            By default, ``100``.

            Returns
            -------
            float
                 sampling value on x axis.
            """
            return self._sensor_dimensions.x_sampling

        @x_sampling.setter
        def x_sampling(self, value: int):
            """Value of the sampling on x axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on x axis.
            """
            self._sensor_dimensions.x_sampling = value

        @property
        def y_start(self) -> float:
            """Minimum value on y axis.

            By default, ``-50``.

            Returns
            -------
            float
                minimum value in y axis
            """
            return self._sensor_dimensions.y_start

        @y_start.setter
        def y_start(self, value: float):
            """Minimum value on y axis.

            Parameters
            ----------
            value : float
                Minimum value on y axis (mm).
            """
            self._sensor_dimensions.y_start = value

        @property
        def y_end(self) -> float:
            """Maximum value on y axis.

            By default, ``50``.

            Returns
            -------
            float
                maximum value on y axis.
            """
            return self._sensor_dimensions.y_end

        @y_end.setter
        def y_end(self, value: float):
            """Maximum value on y axis.

            Parameters
            ----------
            value : float
                Maximum value on y axis (mm).
            """
            self._sensor_dimensions.y_end = value

        @property
        def y_sampling(self) -> int:
            """Value of the sampling on y axis.

            By default, ``100``.

            Returns
            -------
            float
                 sampling value on y axis.
            """
            return self._sensor_dimensions.y_sampling

        @y_sampling.setter
        def y_sampling(self, value: int):
            """Value of the sampling on y axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on y axis.
            """
            self._sensor_dimensions.y_sampling = value

    class Colorimetric:
        """Type of sensor : Colorimetric.

        This kind of sensor will generate color results without any spectral data or layer
        separation in lx or W//m2.
        By default, it uses a default wavelengths range.

        Parameters
        ----------
        sensor_type_colorimetric : ansys.api.speos.sensor.v1.common_pb2.SensorTypeColorimetric
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_colorimetric: common_pb2.SensorTypeColorimetric,
            default_parameters: Union[None, ColorimetricParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Colorimetric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_colorimetric = sensor_type_colorimetric

            if default_parameters:
                # Default values
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_colorimetric.wavelengths_range,
                    default_parameters=default_parameters.wavelength_range,
                    stable_ctr=stable_ctr,
                )
            else:
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_colorimetric.wavelengths_range,
                    default_parameters=None,
                    stable_ctr=stable_ctr,
                )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range.
            """
            if (
                self._wavelengths_range._wavelengths_range
                is not self._sensor_type_colorimetric.wavelengths_range
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._wavelengths_range._wavelengths_range = (
                    self._sensor_type_colorimetric.wavelengths_range
                )
            return self._wavelengths_range

    class Spectral:
        """Type of sensor : Spectral.

        This kind of sensor will generate color results and spectral data separated by wavelength
        in lx or W/m2.
        By default, it uses a default wavelengths range.

        Parameters
        ----------
        sensor_type_spectral : ansys.api.speos.sensor.v1.common_pb2.SensorTypeSpectral
            SensorTypeSpectral protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_spectral method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_spectral: common_pb2.SensorTypeSpectral,
            default_parameters: Union[None, SpectralParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Spectral class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_spectral = sensor_type_spectral

            if default_parameters:
                # Default values
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_spectral.wavelengths_range,
                    default_parameters=default_parameters.wavelength_range,
                    stable_ctr=stable_ctr,
                )
            else:
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_spectral.wavelengths_range,
                    default_parameters=None,
                    stable_ctr=stable_ctr,
                )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range.
            """
            if (
                self._wavelengths_range._wavelengths_range
                is not self._sensor_type_spectral.wavelengths_range
            ):
                self._wavelengths_range._wavelengths_range = (
                    self._sensor_type_spectral.wavelengths_range
                )
            return self._wavelengths_range

    class FaceLayer:
        """Layer composed of name and geometries.

        Parameters
        ----------
        name : str
            Name of the layer.
        geometries : list[ansys.speos.core.geo_ref.GeoRef]
            List of geometries included in this layer.

        """

        def __init__(self, name: str, geometries: list[GeoRef]) -> None:
            self.name = name
            """Name of the layer"""
            self.geometry = geometries

        @property
        def geometry(self):
            """List of geometries included in this layer.

            Returns
            -------
            list[GeoRef]
                List of the Geometries contained in the FaceLayer group
            """
            return self._geometry

        @geometry.setter
        def geometry(
            self, value: Optional[list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]]
        ):
            """Set the geometry for this Face Layer group.

            Parameters
            ----------
            value : Optional[list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]]
                Geometry within the Face Layer group
            """
            geo_paths = []
            for gr in value:
                if isinstance(gr, GeoRef):
                    geo_paths.append(gr)
                elif isinstance(gr, (face.Face, body.Body, part.Part.SubPart)):
                    geo_paths.append(gr.geo_path)
            self._geometry = geo_paths

    class LayerTypeFace:
        """Type of layer : Face.

        Includes in the result one layer per surface selected.
        By default, a filtering mode by last impact is chosen.

        Parameters
        ----------
        layer_type_face : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeFace
            LayerTypeFace protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_face method available in
        sensor classes.
        """

        def __init__(
            self,
            layer_type_face: ProtoScene.SensorInstance.LayerTypeFace,
            default_parameters: Union[None, LayerByFaceParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeFace class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_face = layer_type_face

            if default_parameters:
                # Default values
                match default_parameters.sca_filtering_types:
                    case "last_impact":
                        self.set_sca_filtering_mode_last_impact()
                    case "intersected_one_time":
                        self.set_sca_filtering_mode_intersected_one_time()
                if default_parameters.geometries:
                    for item in default_parameters.geometries:
                        self.layers.append(BaseSensor.FaceLayer(item.name, item.geometry))

        def set_sca_filtering_mode_intersected_one_time(
            self,
        ) -> BaseSensor.LayerTypeFace:
            """Set the filtering mode as intersected one time.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace
                LayerTypeFace.
            """
            self._layer_type_face.sca_filtering_mode = (
                self._layer_type_face.EnumSCAFilteringType.IntersectedOneTime
            )
            return self

        def set_sca_filtering_mode_last_impact(
            self,
        ) -> BaseSensor.LayerTypeFace:
            """Set the filtering mode as last impact.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace
                LayerTypeFace.
            """
            self._layer_type_face.sca_filtering_mode = (
                self._layer_type_face.EnumSCAFilteringType.LastImpact
            )
            return self

        @property
        def layers(self) -> list[BaseSensor.FaceLayer]:
            """List of Face layer Groups of this sensor.

            Returns
            -------
            list[ansys.speos.core.sensor.BaseSensor.FaceLayer]
                list of FaceLayer Classes
            """
            layer_data = []
            for layer in self._layer_type_face.layers:
                layer_data.append(BaseSensor.FaceLayer(layer.name, layer.geometries))
            return layer_data

        @layers.setter
        def layers(self, values: list[BaseSensor.FaceLayer]):
            """Set the layers.

            Parameters
            ----------
            values : list[ansys.speos.core.sensor.BaseSensor.FaceLayer]
                List of layers
            """
            my_list = [
                ProtoScene.SensorInstance.LayerTypeFace.Layer(
                    name=layer.name,
                    geometries=ProtoScene.GeoPaths(
                        geo_paths=[gr.to_native_link() for gr in layer.geometry]
                    ),
                )
                for layer in values
            ]
            self._layer_type_face.ClearField("layers")
            self._layer_type_face.layers.extend(my_list)

    class LayerTypeSequence:
        """Type of layer : Sequence.

        Includes in the result one layer per sequence.
        By default, the sequence is defined per geometries, with a maximum number of 10 sequences.

        Parameters
        ----------
        layer_type_sequence : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeSequence
            LayerTypeSequence protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_sequence method available in
        sensor classes.
        """

        def __init__(
            self,
            layer_type_sequence: ProtoScene.SensorInstance.LayerTypeSequence,
            default_parameters: Union[None, LayerBySequenceParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeSequence class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_sequence = layer_type_sequence

            if default_parameters:
                # Default values
                self.maximum_nb_of_sequence = default_parameters.maximum_nb_of_sequence
                match default_parameters.sequence_type:
                    case "by_face":
                        self.set_define_sequence_per_faces()
                    case "by_geometry":
                        self.set_define_sequence_per_geometries()

        @property
        def maximum_nb_of_sequence(self) -> int:
            """Value of the maximum number of sequences.

            By default, ``10``.

            Returns
            -------
            int
                maximum number of sequences.
            """
            return self._layer_type_sequence.maximum_nb_of_sequence

        @maximum_nb_of_sequence.setter
        def maximum_nb_of_sequence(self, value: int):
            """Value of the maximum number of sequences.

            Parameters
            ----------
            value : int
                Maximum number of sequences.
            """
            self._layer_type_sequence.maximum_nb_of_sequence = value

        def set_define_sequence_per_geometries(
            self,
        ) -> BaseSensor.LayerTypeSequence:
            """Define sequence per geometries.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.define_sequence_per = (
                self._layer_type_sequence.EnumSequenceType.Geometries
            )
            return self

        def set_define_sequence_per_faces(self) -> BaseSensor.LayerTypeSequence:
            """Define sequence per faces.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.define_sequence_per = (
                self._layer_type_sequence.EnumSequenceType.Faces
            )
            return self

    class LayerTypeIncidenceAngle:
        """Type of layer : IncidenceAngle.

        Includes in the result one layer per range of incident angles.
        By default, a sampling of 9 is chosen.

        Parameters
        ----------
        layer_type_incidence_angle : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeIncidenceAngle
            LayerTypeIncidenceAngle protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_incidence_angle method
        available in sensor classes.
        """

        def __init__(
            self,
            layer_type_incidence_angle: ProtoScene.SensorInstance.LayerTypeIncidenceAngle,
            default_parameters: Union[None, LayerByIncidenceAngleParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeIncidenceAngle class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_incidence_angle = layer_type_incidence_angle

            if default_parameters:
                # Default values
                self.sampling = default_parameters.incidence_sampling

        @property
        def sampling(self) -> BaseSensor.LayerTypeIncidenceAngle:
            """Value of the sampling for incidence angles.

            By default, ``9``.

            Returns
            -------
            int
                Sampling for incidence angles.
            """
            return self._layer_type_incidence_angle.sampling

        @sampling.setter
        def sampling(self, value: int) -> BaseSensor.LayerTypeIncidenceAngle:
            """Value of the sampling for incidence angles.

            Parameters
            ----------
            value : int
                Sampling for incidence angles.
                By default, ``9``.
            """
            self._layer_type_incidence_angle.sampling = value

    def _to_dict(self) -> dict:
        out_dict = {}

        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next(
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if ssr_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=ssr_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._sensor_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._sensor_instance
            )

        if "sensor" not in out_dict.keys():
            # SensorTemplate
            if self.sensor_template_link is None:
                out_dict["sensor"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._sensor_template,
                )
            else:
                out_dict["sensor"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.sensor_template_link.get(),
                )

        proto_message_utils._replace_properties(json_dict=out_dict)
        return out_dict

    def get(self, key: str = "") -> str | dict:
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
        """Return the string representation of the sensor."""
        out_str = ""
        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next(
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if ssr_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())

        return out_str

    def commit(self) -> BaseSensor:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            Sensor feature.
        """
        if general_methods._GRAPHICS_AVAILABLE:
            self._visual_data.updated = False

        # The _unique_id will help to find the correct item in the scene.sensors:
        # the list of SensorInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._sensor_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the sensor template (depending on if it was already saved before)
        if self.sensor_template_link is None:
            self.sensor_template_link = self._project.client.sensor_templates().create(
                message=self._sensor_template
            )
            self._sensor_instance.sensor_guid = self.sensor_template_link.key
        elif self.sensor_template_link.get() != self._sensor_template:
            self.sensor_template_link.set(
                data=self._sensor_template
            )  # Only update if the template has changed

        # Update the scene with the sensor instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            ssr_inst = next(
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if ssr_inst is not None:
                if ssr_inst != self._sensor_instance:
                    ssr_inst.CopyFrom(self._sensor_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.sensors.append(
                    self._sensor_instance
                )  # if no, just add it to the list of sensor instances

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> BaseSensor:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            Sensor feature.
        """
        # Reset sensor template
        if self.sensor_template_link is not None:
            self._sensor_template = self.sensor_template_link.get()

        # Reset sensor instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            ssr_inst = next(
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if ssr_inst is not None:
                self._sensor_instance = ssr_inst
        return self

    def delete(self) -> BaseSensor:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            Sensor feature.
        """
        # Delete the sensor template
        if self.sensor_template_link is not None:
            self.sensor_template_link.delete()
            self.sensor_template_link = None

        # Reset then the sensor_guid (as the sensor template was deleted just above)
        self._sensor_instance.sensor_guid = ""

        # Remove the sensor from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        ssr_inst = next(
            (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if ssr_inst is not None:
            scene_data.sensors.remove(ssr_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._sensor_instance.metadata.pop("UniqueId")
        return self


class SensorCamera(BaseSensor):
    """Sensor feature: Camera.

    By default, regarding inherent characteristics, a camera with mode photometric is chosen.
    By default, regarding properties, an axis system is selected to position the sensor,
    and no layer separation is chosen.

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
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_values : bool
        Uses default values when True.
        By default, ``True``.
    """

    class Photometric:
        """Mode of camera sensor : Photometric.

        This allows to set every Camera Sensor parameters, including the photometric definition
        parameters.
        By default, a camera with mode color is chosen (vs monochromatic mode).

        Parameters
        ----------
        mode_photometric : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraModePhotometric
            SensorCameraModePhotometric protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_photometric method available in
        sensor classes.

        """

        class Color:
            """Mode of camera sensor : Color.

            Results will be available in color according to the White Balance mode.
            By default, a balance mode none is chosen (referred as the basic conversion).

            Parameters
            ----------
            mode_color : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraColorModeColor
                SensorCameraColorModeColor protobuf object to modify.
            default_values : bool
                Uses default values when True.
            stable_ctr : bool
                Variable to indicate if usage is inside class scope

            Notes
            -----
            **Do not instantiate this class yourself**, use set_mode_color method available in
            photometric class.

            """

            class BalanceModeUserWhite:
                """BalanceMode : UserWhite.

                In addition to the basic treatment, it allows to apply specific coefficients to the
                red, green, blue images.
                By default, coefficients of 1 are chosen for red, green and blue images.

                Parameters
                ----------
                balance_mode_user_white : ansys.api.speos.sensor.v1.camera_sensor_pb2.
                SensorCameraBalanceModeUserwhite
                    SensorCameraBalanceModeUserwhite protobuf object to modify.
                default_values : bool
                    Uses default values when True.
                stable_ctr : bool
                    Variable to indicate if usage is inside class scope

                Notes
                -----
                **Do not instantiate this class yourself**, use set_balance_mode_user_white method
                available in color class.

                """

                def __init__(
                    self,
                    balance_mode_user_white: camera_sensor_pb2.SensorCameraBalanceModeUserwhite,
                    default_parameters: Union[None, BalanceModeUserWhiteParameters] = None,
                    stable_ctr: bool = False,
                ) -> None:
                    if not stable_ctr:
                        msg = "BalanceModeUserWhite class instantiated outside of class scope"
                        raise RuntimeError(msg)
                    self._balance_mode_user_white = balance_mode_user_white

                    if default_parameters:
                        # Default values
                        self._balance_mode_user_white.SetInParent()
                        self.red_gain = default_parameters.red_gain
                        self.green_gain = default_parameters.green_gain
                        self.blue_gain = default_parameters.blue_gain

                @property
                def red_gain(self) -> float:
                    """Value of the red gain of the Camera Sensor.

                    By default, ``1``.

                    Returns
                    -------
                    float
                        Red gain.
                    """
                    return self._balance_mode_user_white.red_gain

                @red_gain.setter
                def red_gain(self, value: float):
                    """Set red gain.

                    Parameters
                    ----------
                    value : float
                        Red gain.
                    """
                    self._balance_mode_user_white.red_gain = value

                @property
                def green_gain(self) -> float:
                    """Value of the green gain of the Camera Sensor.

                    By default, ``1``.

                    Returns
                    -------
                    float
                        green gain.
                    """
                    return self._balance_mode_user_white.green_gain

                @green_gain.setter
                def green_gain(self, value: float):
                    """Set green gain.

                    Parameters
                    ----------
                    value : float
                        green gain.
                    """
                    self._balance_mode_user_white.green_gain = value

                @property
                def blue_gain(self) -> float:
                    """Value of the Blue gain of the Camera Sensor.

                    By default, ``1``.

                    Returns
                    -------
                    float
                        blue gain.
                    """
                    return self._balance_mode_user_white.blue_gain

                @blue_gain.setter
                def blue_gain(self, value: float):
                    """Set blue gain value.

                    Parameters
                    ----------
                    value : float
                        blue gain.
                    """
                    self._balance_mode_user_white.blue_gain = value

            class BalanceModeDisplayPrimaries:
                """BalanceMode : DisplayPrimaries.

                Spectral results are converted in a three-channel result.
                Then a post-treatment is realized to take the distortion induced by the display
                devices into account.
                With this method, displayed results are similar to what the camera really gets.

                Parameters
                ----------
                balance_mode_display : ansys.api.speos.sensor.v1.camera_sensor_pb2.
                SensorCameraBalanceModeDisplay
                    SensorCameraBalanceModeDisplay protobuf object to modify.
                default_values : bool
                    Uses default values when True.

                Notes
                -----
                **Do not instantiate this class yourself**, use set_balance_mode_display_primaries
                method available in color class.

                """

                def __init__(
                    self,
                    balance_mode_display: camera_sensor_pb2.SensorCameraBalanceModeDisplay,
                    default_parameters: Union[None, BalanceModeDisplayPrimariesParameters] = None,
                    stable_ctr: bool = False,
                ) -> None:
                    if not stable_ctr:
                        msg = (
                            "BalanceModeDisplayPrimaries class instantiated outside of class scope"
                        )
                        raise RuntimeError(msg)

                    self._balance_mode_display = balance_mode_display

                    if default_parameters:
                        # Default values
                        self._balance_mode_display.SetInParent()
                        if default_parameters.red_display_file_uri:
                            self.red_display_file_uri = default_parameters.red_display_file_uri
                        if default_parameters.green_display_file_uri:
                            self.green_display_file_uri = default_parameters.green_display_file_uri
                        if default_parameters.green_display_file_uri:
                            self.blue_display_file_uri = default_parameters.blue_display_file_uri

                @property
                def red_display_file_uri(self) -> str:
                    """Location of the red display file.

                    Returns
                    -------
                    str
                        Red display file.
                    """
                    return self._balance_mode_display.red_display_file_uri

                @red_display_file_uri.setter
                def red_display_file_uri(self, uri: Union[str, Path]):
                    """Location of the red display file.

                    Parameters
                    ----------
                    uri : Union[str, Path]
                        Red display file.
                    """
                    self._balance_mode_display.red_display_file_uri = str(Path(uri))

                @property
                def green_display_file_uri(self) -> str:
                    """Location of the green display file.

                    Returns
                    -------
                    str
                        green display file.
                    """
                    return self._balance_mode_display.green_display_file_uri

                @green_display_file_uri.setter
                def green_display_file_uri(self, uri: Union[str, Path]):
                    """Location of the green display file.

                    Parameters
                    ----------
                    uri : Union[str, Path]
                        green display file.
                    """
                    self._balance_mode_display.green_display_file_uri = str(Path(uri))

                @property
                def blue_display_file_uri(self) -> str:
                    """Location of the blue display file.

                    Returns
                    -------
                    str
                        blue display file.
                    """
                    return self._balance_mode_display.blue_display_file_uri

                @blue_display_file_uri.setter
                def blue_display_file_uri(self, uri: Union[str, Path]):
                    """Location of the blue display file.

                    Parameters
                    ----------
                    uri : Union[str, Path]
                        blue display file.
                    """
                    self._balance_mode_display.blue_display_file_uri = str(Path(uri))

            def __init__(
                self,
                mode_color: camera_sensor_pb2.SensorCameraColorModeColor,
                default_parameters: Union[None, ColorParameters] = None,
                stable_ctr: bool = False,
            ) -> None:
                if not stable_ctr:
                    msg = "Color class instantiated outside of class scope"
                    raise RuntimeError(msg)
                self._mode_color = mode_color

                # Attribute gathering more complex camera balance mode
                self._mode = None

                if default_parameters:
                    # Default values
                    if isinstance(default_parameters.balance_mode, BalanceModeUserWhiteParameters):
                        self._mode = SensorCamera.Photometric.Color.BalanceModeUserWhite(
                            balance_mode_user_white=self._mode_color.balance_mode_userwhite,
                            default_parameters=default_parameters.balance_mode,
                            stable_ctr=True,
                        )
                    elif isinstance(
                        default_parameters.balance_mode, BalanceModeDisplayPrimariesParameters
                    ):
                        self._mode = SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries(
                            balance_mode_display=self._mode_color.balance_mode_display,
                            default_parameters=default_parameters.balance_mode,
                            stable_ctr=True,
                        )
                    elif default_parameters.balance_mode == "grey_world":
                        self.set_balance_mode_grey_world()
                    elif default_parameters.balance_mode == "none":
                        self.set_balance_mode_none()
                    if default_parameters.red_spectrum_file_uri:
                        self.red_spectrum_file_uri = default_parameters.red_spectrum_file_uri
                    if default_parameters.green_spectrum_file_uri:
                        self.green_spectrum_file_uri = default_parameters.green_spectrum_file_uri
                    if default_parameters.blue_spectrum_file_uri:
                        self.blue_spectrum_file_uri = default_parameters.blue_spectrum_file_uri

            @property
            def red_spectrum_file_uri(self) -> str:
                """Location of the red spectrum.

                Returns
                -------
                str
                    Red spectrum file. It is expressed in a .spectrum file.
                """
                return self._mode_color.red_spectrum_file_uri

            @red_spectrum_file_uri.setter
            def red_spectrum_file_uri(self, uri: Union[str, Path]):
                """Location of the red spectrum.

                Parameters
                ----------
                uri : Union[str, Path]
                    Red spectrum file. It is expressed in a .spectrum file.
                """
                self._mode_color.red_spectrum_file_uri = str(Path(uri))

            @property
            def blue_spectrum_file_uri(self) -> str:
                """Location of the blue spectrum.

                Returns
                -------
                str
                    blue spectrum file. It is expressed in a .spectrum file.
                """
                return self._mode_color.blue_spectrum_file_uri

            @blue_spectrum_file_uri.setter
            def blue_spectrum_file_uri(self, uri: Union[str, Path]):
                """Location of the blue spectrum.

                Parameters
                ----------
                uri : Union[str, Path]
                    blue spectrum file. It is expressed in a .spectrum file.
                """
                self._mode_color.blue_spectrum_file_uri = str(Path(uri))

            @property
            def green_spectrum_file_uri(self) -> str:
                """Location of the green spectrum.

                Returns
                -------
                str
                    green spectrum file. It is expressed in a .spectrum file.
                """
                return self._mode_color.green_spectrum_file_uri

            @green_spectrum_file_uri.setter
            def green_spectrum_file_uri(self, uri: Union[str, Path]):
                """Location of the green spectrum.

                Parameters
                ----------
                uri : Union[str, Path]
                    green spectrum file. It is expressed in a .spectrum file.
                """
                self._mode_color.green_spectrum_file_uri = str(Path(uri))

            def set_balance_mode_none(self) -> SensorCamera.Photometric.Color:
                """Set the balance mode as none.

                The spectral transmittance of the optical system and the spectral sensitivity for
                each channel are applied to the detected spectral image before the conversion in
                a three-channel result. This method is referred to as the basic conversion.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color
                    Color mode.
                """
                self._mode = None
                self._mode_color.balance_mode_none.SetInParent()
                return self

            def set_balance_mode_grey_world(
                self,
            ) -> SensorCamera.Photometric.Color:
                """Set the balance mode as grey world.

                The grey world assumption states that the content of the image is grey on average.
                This method converts spectral results in a three-channel result with the basic
                conversion. Then it computes and applies coefficients to the red, green and blue
                images to make sure their averages are equal.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color
                    Color mode.
                """
                self._mode = None
                self._mode_color.balance_mode_greyworld.SetInParent()
                return self

            def set_balance_mode_user_white(
                self,
            ) -> SensorCamera.Photometric.Color.BalanceModeUserWhite:
                """Set the balance mode as user white.

                In addition to the basic treatment, it allows to apply specific coefficients to the
                red, green, blue images.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color.BalanceModeUserWhite
                    Balance UserWhite mode.
                """
                if self._mode is None and self._mode_color.HasField("balance_mode_userwhite"):
                    # Happens in case of project created via load of speos file
                    self._mode = SensorCamera.Photometric.Color.BalanceModeUserWhite(
                        balance_mode_user_white=self._mode_color.balance_mode_userwhite,
                        default_parameters=None,
                        stable_ctr=True,
                    )
                elif not isinstance(
                    self._mode, SensorCamera.Photometric.Color.BalanceModeUserWhite
                ):
                    # if the _mode is not BalanceModeUserWhite then we create a new type.
                    self._mode = SensorCamera.Photometric.Color.BalanceModeUserWhite(
                        balance_mode_user_white=self._mode_color.balance_mode_userwhite,
                        default_parameters=BalanceModeUserWhiteParameters(),
                        stable_ctr=True,
                    )
                elif (
                    self._mode._balance_mode_user_white
                    is not self._mode_color.balance_mode_userwhite
                ):
                    # Happens in case of feature reset (to be sure to always modify correct data)
                    self._mode._balance_mode_user_white = self._mode_color.balance_mode_userwhite
                return self._mode

            def set_balance_mode_display_primaries(
                self,
            ) -> SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries:
                """Set the balance mode as display primaries.

                Spectral results are converted in a three-channel result.
                Then a post-treatment is realized to take the distortion induced by the display
                devices into account. With this method, displayed results are similar to what the
                camera really gets.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries
                    Balance DisplayPrimaries mode.
                """
                if self._mode is None and self._mode_color.HasField("balance_mode_display"):
                    # Happens in case of project created via load of speos file
                    self._mode = SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries(
                        balance_mode_display=self._mode_color.balance_mode_display,
                        default_parameters=None,
                        stable_ctr=True,
                    )
                elif not isinstance(
                    self._mode, SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries
                ):
                    # if the _mode is not BalanceModeDisplayPrimaries then we create a new type.
                    self._mode = SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries(
                        balance_mode_display=self._mode_color.balance_mode_display,
                        default_parameters=BalanceModeDisplayPrimariesParameters(),
                        stable_ctr=True,
                    )
                elif self._mode._balance_mode_display is not self._mode_color.balance_mode_display:
                    # Happens in case of feature reset (to be sure to always modify correct data)
                    self._mode._balance_mode_display = self._mode_color.balance_mode_display
                return self._mode

        def __init__(
            self,
            mode_photometric: camera_sensor_pb2.SensorCameraModePhotometric,
            camera_props: ProtoScene.SensorInstance.CameraProperties,
            default_parameters: Union[None, PhotometricCameraParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Photometric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._mode_photometric = mode_photometric
            self._camera_props = camera_props

            # Attribute gathering more complex camera color mode
            self._mode = None

            # Attribute to keep track of wavelength range object

            if default_parameters:
                # Default values
                self.acquisition_integration = default_parameters.acquisition_integration_time
                self.acquisition_lag_time = default_parameters.acquisition_lag_time
                self.gamma_correction = default_parameters.gamma_correction
                if default_parameters.transmittance_file_uri:
                    self.transmittance_file_uri = default_parameters.transmittance_file_uri
                match default_parameters.png_bits:
                    case "png_08":
                        self.set_png_bits_08()
                    case "png_10":
                        self.set_png_bits_10()
                    case "png_12":
                        self.set_png_bits_12()
                    case "png_16":
                        self.set_png_bits_16()
                match default_parameters.layer_type:
                    case "none":
                        self.set_layer_type_none()
                    case "by_source":
                        self.set_layer_type_source()
                self._wavelengths_range = SensorCamera.WavelengthsRange(
                    wavelengths_range=self._mode_photometric.wavelengths_range,
                    default_parameters=default_parameters.wavelength_range,
                    stable_ctr=stable_ctr,
                )
                if isinstance(default_parameters.color_mode, MonoChromaticParameters):
                    self.set_mode_monochromatic(default_parameters.color_mode.sensitivity)
                elif isinstance(default_parameters.color_mode, ColorParameters):
                    self._mode = SensorCamera.Photometric.Color(
                        mode_color=self._mode_photometric.color_mode_color,
                        default_parameters=default_parameters.color_mode,
                        stable_ctr=True,
                    )
            elif default_parameters is None:
                self._wavelengths_range = SensorCamera.WavelengthsRange(
                    wavelengths_range=self._mode_photometric.wavelengths_range,
                    default_parameters=None,
                    stable_ctr=stable_ctr,
                )

        @property
        def acquisition_integration(self) -> float:
            """Value of the acquisition integration.

            By default, ``0.01``.

            Returns
            -------
            float
                Acquisition integration value (s).
            """
            return self._mode_photometric.acquisition_integration

        @acquisition_integration.setter
        def acquisition_integration(self, value: float):
            """Value of the acquisition integration.

            Parameters
            ----------
            value : float
                Acquisition integration value (s).
                By default, ``0.01``.
            """
            self._mode_photometric.acquisition_integration = value

        @property
        def acquisition_lag_time(self) -> float:
            """Value of the acquisition lag time.

            By default, ``0.0``.

            Returns
            -------
            float
                Acquisition lag time value (s).
            """
            return self._mode_photometric.acquisition_lag_time

        @acquisition_lag_time.setter
        def acquisition_lag_time(self, value: float):
            """Value of the acquisition lag time.

            Parameters
            ----------
            value : float
                Acquisition lag time value (s).
                By default, ``0.0``.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode_photometric.acquisition_lag_time = value

        @property
        def transmittance_file_uri(self) -> str:
            """Location of the transmittance file.

            Returns
            -------
            str
                Amount of light of the source that passes through the lens and reaches the sensor.
            """
            return self._mode_photometric.transmittance_file_uri

        @transmittance_file_uri.setter
        def transmittance_file_uri(self, uri: Union[str, Path]):
            """Location of the transmittance file.

            Parameters
            ----------
            uri : Union[str, Path]
                Amount of light of the source that passes through the lens and reaches the sensor.
                The transmittance is expressed in a .spectrum file.
            """
            self._mode_photometric.transmittance_file_uri = str(Path(uri))

        @property
        def gamma_correction(self) -> float:
            """Value used to apply the gamma correction.

            By default, ``2.2``.

            Returns
            -------
            float
                Gamma Correction value
            """
            return self._mode_photometric.gamma_correction

        @gamma_correction.setter
        def gamma_correction(self, value: float):
            """Value used to apply the gamma correction.

            By default, ``2.2``.

            Parameters
            ----------
            value : float
                Gamma Correction value
            """
            self._mode_photometric.gamma_correction = value

        def set_png_bits_08(self) -> SensorCamera.Photometric:
            """Choose 08-bits for png.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
            return self

        def set_png_bits_10(self) -> SensorCamera.Photometric:
            """Choose 10-bits for png.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
            return self

        def set_png_bits_12(self) -> SensorCamera.Photometric:
            """Choose 12-bits for png.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
            return self

        def set_png_bits_16(self) -> SensorCamera.Photometric:
            """Choose 16-bits for png.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
            return self

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range.
            """
            if (
                self._wavelengths_range._wavelengths_range
                is not self._mode_photometric.wavelengths_range
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._wavelengths_range._wavelengths_range = (
                    self._mode_photometric.wavelengths_range
                )
            return self._wavelengths_range

        def set_mode_monochromatic(
            self, spectrum_file_uri: Union[str, Path]
        ) -> SensorCamera.Photometric:
            """Set the monochromatic mode.

            Results will be available in grey scale.

            Parameters
            ----------
            spectrum_file_uri : Union[str, Path]
                Spectrum file uri.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._mode = None
            self._mode_photometric.color_mode_monochromatic.spectrum_file_uri = str(
                Path(spectrum_file_uri)
            )
            return self

        def set_mode_color(self) -> SensorCamera.Photometric.Color:
            """Set the color mode.

            Results will be available in color.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric.Color
                Color mode.
            """
            if self._mode is None and self._mode_photometric.HasField("color_mode_color"):
                # Happens in case of project created via load of speos file
                self._mode = SensorCamera.Photometric.Color(
                    mode_color=self._mode_photometric.color_mode_color,
                    default_parameters=None,
                    stable_ctr=True,
                )
            elif not isinstance(self._mode, SensorCamera.Photometric.Color):
                # if the _mode is not Color then we create a new type.
                self._mode = SensorCamera.Photometric.Color(
                    mode_color=self._mode_photometric.color_mode_color,
                    default_parameters=None,
                    stable_ctr=True,
                )
            elif self._mode._mode_color is not self._mode_photometric.color_mode_color:
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._mode._mode_color = self._mode_photometric.color_mode_color
            return self._mode

        @property
        def trajectory_file_uri(self) -> str:
            """Location of the trajectory file.

            Returns
            -------
            str
                Trajectory file, used to define the position and orientations of the Camera sensor
                in time.
            """
            return self._camera_props.trajectory_file_uri

        @trajectory_file_uri.setter
        def trajectory_file_uri(self, uri: Union[str, Path]):
            """Location of the trajectory file.

            Parameters
            ----------
            uri : Union[str, Path]
                Trajectory file, used to define the position and orientations of the Camera sensor
                in time.
            """
            self._camera_props.trajectory_file_uri = str(Path(uri))

        def set_layer_type_none(self) -> SensorCamera.Photometric:
            """Set no layer separation: includes the simulation's results in one layer.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._camera_props.layer_type_none.SetInParent()
            return self

        def set_layer_type_source(self) -> SensorCamera.Photometric:
            """Set layer separation by source: includes one layer per active source in the result.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode.
            """
            self._camera_props.layer_type_source.SetInParent()
            return self

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Union[None, CameraSensorParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            sensor_instance=sensor_instance,
        )

        # Attribute gathering more complex camera mode
        self._type = None
        if sensor_instance is None:
            if not default_parameters:
                default_parameters = CameraSensorParameters()
            if isinstance(default_parameters.sensor_type_parameters, PhotometricCameraParameters):
                self._type = SensorCamera.Photometric(
                    mode_photometric=self._sensor_template.camera_sensor_template.sensor_mode_photometric,
                    camera_props=self._sensor_instance.camera_properties,
                    default_parameters=default_parameters.sensor_type_parameters,
                    stable_ctr=True,
                )
            else:
                self.set_mode_geometric()
            self.imager_distance = default_parameters.imager_distance
            self.focal_length = default_parameters.focal_length
            self.f_number = default_parameters.f_number
            self.horz_pixel = default_parameters.horz_pixel
            self.vert_pixel = default_parameters.vert_pixel
            self.width = default_parameters.width
            self.height = default_parameters.height
            self.axis_system = default_parameters.axis_system
            self.lxp_path_number = default_parameters.lxp_path_number

    @property
    def visual_data(self) -> _VisualData:
        """Property containing camera sensor visualization data.

        Returns
        -------
        BaseSensor.VisualData
            Instance of VisualData Class for pyvista.PolyData of feature faces, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            feature_pos_info = self.get(key="axis_system")
            feature_camera_pos = np.array(feature_pos_info[:3])
            feature_camera_x_dir = np.array(feature_pos_info[3:6])
            feature_camera_y_dir = np.array(feature_pos_info[6:9])
            feature_camera_z_dir = np.array(feature_pos_info[9:12])
            feature_width = float(self.get(key="width"))
            feature_height = float(self.get(key="height"))
            feature_camera_focal = float(self.get(key="focal_length"))
            feature_camera_image_dis = float(self.get(key="imager_distance"))

            # camera radiance sensor
            p1 = (
                feature_camera_pos
                + feature_camera_x_dir * feature_width / 2.0
                + feature_camera_y_dir * feature_height / 2.0
                + feature_camera_z_dir * feature_camera_image_dis
            )
            p2 = (
                feature_camera_pos
                + feature_camera_x_dir * feature_width / 2.0
                - feature_camera_y_dir * feature_height / 2.0
                + feature_camera_z_dir * feature_camera_image_dis
            )
            p3 = (
                feature_camera_pos
                - feature_camera_x_dir * feature_width / 2.0
                + feature_camera_y_dir * feature_height / 2.0
                + feature_camera_z_dir * feature_camera_image_dis
            )
            p4 = (
                feature_camera_pos
                - feature_camera_x_dir * feature_width / 2.0
                - feature_camera_y_dir * feature_height / 2.0
                + feature_camera_z_dir * feature_camera_image_dis
            )
            self._visual_data.add_data_rectangle([p1, p2, p3])

            p5 = feature_camera_pos + feature_camera_z_dir * (
                feature_camera_image_dis - feature_camera_focal
            )
            self._visual_data.add_data_triangle([p1, p2, p5])
            self._visual_data.add_data_triangle([p3, p4, p5])
            self._visual_data.add_data_triangle([p1, p3, p5])
            self._visual_data.add_data_triangle([p2, p4, p5])

            # NOTE: camera object field to be added
            # current gRPC service not available to get object field open angle
            # camera_object_field_radius = 500
            # camera_object_field_data = pv.Sphere(
            #     radius=camera_object_field_radius,
            #     center=feature_camera_pos,
            #     direction=feature_camera_y_dir,
            #     theta_resolution=30,
            #     phi_resolution=30,
            #     start_theta=0.0,
            #     end_theta=60.0,
            #     start_phi=90,
            #     end_phi=135,
            # )
            # camera_object_field_data = camera_object_field_data.rotate_vector(
            #     vector=feature_camera_y_dir, angle=-30, point=feature_camera_pos
            # )
            # self._visual_data.data = self._visual_data.data.append_polydata(
            #     camera_object_field_data
            # )

            # camera axis system
            self._visual_data.coordinates.origin = feature_camera_pos
            self._visual_data.coordinates.x_axis = feature_camera_x_dir
            self._visual_data.coordinates.y_axis = feature_camera_y_dir
            self._visual_data.coordinates.z_axis = feature_camera_z_dir

            self._visual_data.updated = True
            return self._visual_data

    @property
    def photometric(self) -> Union[SensorCamera.Photometric, None]:
        """Property containing the instance of SensorCamera.Photometric used to build the sensor.

        Returns
        -------
        Union[ansys.speos.core.sensor.SensorCamera.Photometric, None]
            Photometric class instance if it exists

        """
        return self._type

    @property
    def focal_length(self) -> float:
        """Focal length of the optical system.

        By default, ``5.0``.

        Returns
        -------
        float
            Distance between the center of the optical system and the focus. (mm)
        """
        return self._sensor_template.camera_sensor_template.focal_length

    @focal_length.setter
    def focal_length(self, value: float) -> SensorCamera:
        """Focal length of the optical system.

        Parameters
        ----------
        value : float
            Distance between the center of the optical system and the focus. (mm)
            By default, ``5.0``.
        """
        self._sensor_template.camera_sensor_template.focal_length = value

    @property
    def imager_distance(self) -> SensorCamera:
        """Imager distance.

        By default, ``10``.

        Returns
        -------
        float
            Imager distance (mm). The imager is located at the focal point.
            The Imager distance has no impact on the result.
        """
        return self._sensor_template.camera_sensor_template.imager_distance

    @imager_distance.setter
    def imager_distance(self, value: float):
        """Imager distance.

        Parameters
        ----------
        value : float
            Imager distance (mm). The imager is located at the focal point.
            The Imager distance has no impact on the result.
            By default, ``10``.
        """
        self._sensor_template.camera_sensor_template.imager_distance = value

    @property
    def f_number(self) -> float:
        """F number of the optical system.

        By default, ``20``.

        Returns
        -------
        float
            F-number represents the aperture of the front lens.
            F number has no impact on the result.
        """
        return self._sensor_template.camera_sensor_template.f_number

    @f_number.setter
    def f_number(self, value: float = 20):
        """F number of the optical system.

        Parameters
        ----------
        value : float
            F-number represents the aperture of the front lens.
            F number has no impact on the result.
            By default, ``20``.
        """
        self._sensor_template.camera_sensor_template.f_number = value

    @property
    def distortion_file_uri(self) -> str:
        """Location of the distortion file.

        Returns
        -------
        str
            Optical aberration that deforms and bends straight lines. The distortion is expressed in
            a .OPTDistortion file.
        """
        return self._sensor_template.camera_sensor_template.distortion_file_uri

    @distortion_file_uri.setter
    def distortion_file_uri(self, uri: Union[str, Path]):
        """Location of the distortion file.

        Parameters
        ----------
        uri : Union[str, Path]
            Optical aberration that deforms and bends straight lines. The distortion is expressed in
            a .OPTDistortion file.
        """
        self._sensor_template.camera_sensor_template.distortion_file_uri = str(Path(uri))

    @property
    def horz_pixel(self) -> int:
        """Horizontal pixels number corresponding to the camera resolution.

        Returns
        -------
        int
            The horizontal pixels number corresponding to the camera resolution.
        """
        return self._sensor_template.camera_sensor_template.horz_pixel

    @horz_pixel.setter
    def horz_pixel(self, value: int):
        """Horizontal pixels number corresponding to the camera resolution.

        Parameters
        ----------
        value : int
            The horizontal pixels number corresponding to the camera resolution.
            By default, ``640``.
        """
        self._sensor_template.camera_sensor_template.horz_pixel = value

    @property
    def vert_pixel(self) -> int:
        """Vertical pixels number corresponding to the camera resolution.

        By default, ``480``.

        Returns
        -------
        int
            The vertical pixels number corresponding to the camera resolution.
        """
        return self._sensor_template.camera_sensor_template.vert_pixel

    @vert_pixel.setter
    def vert_pixel(self, value: int):
        """Vertical pixels number corresponding to the camera resolution.

        Parameters
        ----------
        value : int
            The vertical pixels number corresponding to the camera resolution.
            By default, ``480``.
        """
        self._sensor_template.camera_sensor_template.vert_pixel = value

    @property
    def width(self) -> float:
        """Width of the imager.

        By default, ``5.0``.

        Returns
        -------
        float
            Sensor's width (mm).
        """
        return self._sensor_template.camera_sensor_template.width

    @width.setter
    def width(self, value: float):
        """Width of the imager.

        Parameters
        ----------
        value : float
            Sensor's width (mm).
            By default, ``5.0``.
        """
        self._sensor_template.camera_sensor_template.width = value

    @property
    def height(self) -> float:
        """Height of the imager.

        By default, ``5.0``

        Returns
        -------
        float
            Sensor's height (mm).
            `.
        """
        return self._sensor_template.camera_sensor_template.height

    @height.setter
    def height(self, value: float):
        """Height of the imager.

        Parameters
        ----------
        value : float
            Sensor's height (mm).
            By default, ``5.0``.
        """
        self._sensor_template.camera_sensor_template.height = value

    @property
    def axis_system(self) -> list[float]:
        """The position of the sensor.

        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._sensor_instance.camera_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: list[float]):
        """Position of the sensor.

        Parameters
        ----------
        axis_system : list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
        """
        self._sensor_instance.camera_properties.axis_system[:] = axis_system

    def set_mode_geometric(self) -> SensorCamera:
        """Set mode geometric for the camera sensor.

        This is a simplified version of the Camera Sensor.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera
            Geometric Camera feature
        """
        self._type = None
        self._sensor_template.camera_sensor_template.sensor_mode_geometric.SetInParent()
        return self

    def set_mode_photometric(self) -> SensorCamera.Photometric:
        """Set mode photometric for the camera sensor.

        This allows setting every Camera Sensor parameter, including the photometric definition
        parameters.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera.Photometric
            Photometric Camera Sensor feature
        """
        if self._type is None and self._sensor_template.camera_sensor_template.HasField(
            "sensor_mode_photometric"
        ):
            # Happens in case of project created via load of speos file
            self._type = SensorCamera.Photometric(
                mode_photometric=self._sensor_template.camera_sensor_template.sensor_mode_photometric,
                camera_props=self._sensor_instance.camera_properties,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, SensorCamera.Photometric):
            # if the _type is not Photometric then we create a new type.
            self._type = SensorCamera.Photometric(
                mode_photometric=self._sensor_template.camera_sensor_template.sensor_mode_photometric,
                camera_props=self._sensor_instance.camera_properties,
                default_parameters=PhotometricCameraParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._mode_photometric
            is not self._sensor_template.camera_sensor_template.sensor_mode_photometric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._mode_photometric = (
                self._sensor_template.camera_sensor_template.sensor_mode_photometric
            )
        return self._type

    def commit(self) -> SensorCamera:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera
            Sensor feature.
        """
        msg = (
            "Please note that the following values {} were over written by the values"
            " stored in the distortion file"
        )
        values_v2 = ["focal_length", "imager_distance", "f_number"]
        values_v4 = ["focal_length", "imager_distance", "f_number", "Transmittance Spectrum"]
        try:
            super().commit()
        except grpc.RpcError:
            for value in values_v2:
                self._sensor_template.camera_sensor_template.ClearField(value)
            try:
                super().commit()
                warnings.warn(msg.format(str(values_v2)), stacklevel=2)
            except grpc.RpcError:
                self._sensor_template.camera_sensor_template.sensor_mode_photometric.ClearField(
                    "transmittance_file_uri"
                )
                try:
                    super().commit()
                    warnings.warn(msg.format(str(values_v4)), stacklevel=2)
                except grpc.RpcError as e:
                    raise e
        return self


class SensorIrradiance(BaseSensor):
    """Sensor feature: Irradiance.

    By default, regarding inherent characteristics, an irradiance sensor of type photometric and
    illuminance type planar is chosen. By default, regarding properties, an axis system is
    selected to position the sensor, no layer separation and no ray file generation are chosen.

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
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_parameters : bool
        Uses default values when True.
        By default, ``True``.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Union[None, IrradianceSensorParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            sensor_instance=sensor_instance,
        )

        # Attribute gathering more complex irradiance type
        self._type = None

        # Attribute gathering more complex layer type
        self._layer_type = None

        if sensor_instance is None:
            if default_parameters is None:
                default_parameters = IrradianceSensorParameters()
            # Default values template
            self._sensor_dimensions = self.Dimensions(
                sensor_dimensions=self._sensor_template.irradiance_sensor_template.dimensions,
                default_parameters=default_parameters.dimensions,
                stable_ctr=True,
            )

            if isinstance(default_parameters.sensor_type, ColorimetricParameters):
                self._type = BaseSensor.Colorimetric(
                    sensor_type_colorimetric=self._sensor_template.irradiance_sensor_template.sensor_type_colorimetric,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.sensor_type, SpectralParameters):
                self._type = BaseSensor.Spectral(
                    sensor_type_spectral=self._sensor_template.irradiance_sensor_template.sensor_type_spectral,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == "radiometric":
                self.set_type_radiometric()
            elif default_parameters.sensor_type == "photometric":
                self.set_type_photometric()

            match default_parameters.integration_type:
                case "planar":
                    self.set_illuminance_type_planar()
                    self.integration_direction = default_parameters.integration_direction
                case "radial":
                    self.set_illuminance_type_radial()
                case "hemispherical":
                    self.set_illuminance_type_hemispherical()
                case "cylindrical":
                    self.set_illuminance_type_cylindrical()
                case "semi_cylindrical":
                    self.set_illuminance_type_semi_cylindrical()
                    self.integration_direction = default_parameters.integration_direction

            match default_parameters.rayfile_type:
                case "none":
                    self.set_ray_file_type_none()
                case "classic":
                    self.set_ray_file_type_classic()
                case "polarization":
                    self.set_ray_file_type_polarization()
                case "tm25":
                    self.set_ray_file_type_tm25()
                case "tm25_no_polarization":
                    self.set_ray_file_type_tm25_no_polarization()

            if default_parameters.layer_type == "none":
                self.set_layer_type_none()
            elif default_parameters.layer_type == "by_source":
                self.set_layer_type_source()
            elif default_parameters.layer_type == "by_polarization":
                self.set_layer_type_polarization()
            elif isinstance(default_parameters.layer_type, LayerByFaceParameters):
                self._layer_type = BaseSensor.LayerTypeFace(
                    layer_type_face=self._sensor_instance.irradiance_properties.layer_type_face,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.layer_type, LayerBySequenceParameters):
                self._layer_type = BaseSensor.LayerTypeSequence(
                    layer_type_sequence=self._sensor_instance.irradiance_properties.layer_type_sequence,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.layer_type, LayerByIncidenceAngleParameters):
                self._layer_type = BaseSensor.LayerTypeIncidenceAngle(
                    layer_type_incidence_angle=self._sensor_instance.irradiance_properties.layer_type_incidence_angle,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            # Default values properties
            self.axis_system = default_parameters.axis_system
            self.output_face_geometries = default_parameters.outpath_face_geometry
        else:
            self._sensor_dimensions = self.Dimensions(
                sensor_dimensions=self._sensor_template.irradiance_sensor_template.dimensions,
                default_parameters=None,
                stable_ctr=True,
            )

    @property
    def visual_data(self) -> _VisualData:
        """Property containing irradiance sensor visualization data.

        Returns
        -------
        BaseSensor.VisualData
            Instance of VisualData Class for pyvista.PolyData of feature faces, coordinate_systems.

        """
        if self._visual_data.updated is True:
            return self._visual_data
        else:
            feature_pos_info = self.get(key="axis_system")
            feature_irradiance_pos = np.array(feature_pos_info[:3])
            feature_irradiance_x_dir = np.array(feature_pos_info[3:6])
            feature_irradiance_y_dir = np.array(feature_pos_info[6:9])
            if self._sensor_instance.irradiance_properties.integration_direction:
                feature_irradiance_z_dir = np.array(
                    self._sensor_instance.irradiance_properties.integration_direction
                )
            else:
                feature_irradiance_z_dir = np.array(feature_pos_info[9:12])
            feature_x_start = float(self.get(key="x_start"))
            feature_x_end = float(self.get(key="x_end"))
            feature_y_start = float(self.get(key="y_start"))
            feature_y_end = float(self.get(key="y_end"))

            # irradiance sensor
            p1 = (
                feature_irradiance_pos
                + feature_irradiance_x_dir * feature_x_end
                + feature_irradiance_y_dir * feature_y_end
            )
            p2 = (
                feature_irradiance_pos
                + feature_irradiance_x_dir * feature_x_start
                + feature_irradiance_y_dir * feature_y_start
            )
            p3 = (
                feature_irradiance_pos
                + feature_irradiance_x_dir * feature_x_end
                + feature_irradiance_y_dir * feature_y_start
            )
            self._visual_data.add_data_rectangle([p1, p2, p3])

            # irradiance direction
            self._visual_data.coordinates.origin = feature_irradiance_pos
            self._visual_data.coordinates.x_axis = feature_irradiance_x_dir
            self._visual_data.coordinates.y_axis = feature_irradiance_y_dir
            self._visual_data.coordinates.z_axis = feature_irradiance_z_dir

            self._visual_data.updated = True
            return self._visual_data

    @property
    def dimensions(self) -> BaseSensor.Dimensions:
        """Property containing all options in regard to the Dimensions sensor properties.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Instance of Dimensions Class for this sensor feature
        """
        return self._sensor_dimensions

    @property
    def type(self) -> str:
        """Type of sensor.

        Returns
        -------
        str
            Sensor type as string
        """
        if type(self._type) is str:
            return self._type
        elif isinstance(self._type, BaseSensor.Colorimetric):
            return "Colorimetric"
        elif isinstance(self._type, BaseSensor.Spectral):
            return "Spectral"
        else:
            return self._type

    @property
    def colorimetric(self) -> Union[None, BaseSensor.Colorimetric]:
        """Property containing all options in regard to the Colorimetric sensor properties.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Colorimetric]
            Instance of Colorimetric Class for this sensor feature
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return self._type
        else:
            return None

    @property
    def spectral(self) -> Union[None, BaseSensor.Spectral]:
        """Property containing all options in regard to the Spectral sensor properties.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Spectral]
            Instance of Spectral Class for this sensor feature
        """
        if isinstance(self._type, BaseSensor.Spectral):
            return self._type
        else:
            return None

    @property
    def layer(
        self,
    ) -> Union[
        None,
        SensorIrradiance,
        BaseSensor.LayerTypeFace,
        BaseSensor.LayerTypeSequence,
        BaseSensor.LayerTypeIncidenceAngle,
    ]:
        """Property containing all options in regard to the layer separation properties.

        Returns
        -------
        Union[\
            None,\
            ansys.speos.core.sensor.SensorIrradiance,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeIncidenceAngle\
        ]
            Instance of Layertype Class for this sensor feature
        """
        return self._layer_type

    def set_dimensions(self) -> BaseSensor.Dimensions:
        """Set the dimensions of the sensor.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimension class
        """
        if (
            self._sensor_dimensions._sensor_dimensions
            is not self._sensor_template.irradiance_sensor_template.dimensions
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._sensor_dimensions._sensor_dimensions = (
                self._sensor_template.irradiance_sensor_template.dimensions
            )
        return self._sensor_dimensions

    def set_type_photometric(self) -> SensorIrradiance:
        """Set type photometric.

        The sensor considers the visible spectrum and gets the results in lm/m2 or lx.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor
        """
        self._sensor_template.irradiance_sensor_template.sensor_type_photometric.SetInParent()
        self._type = "Photometric"
        return self

    def set_type_colorimetric(self) -> BaseSensor.Colorimetric:
        """Set type colorimetric.

        The sensor will generate color results without any spectral data or layer separation
        in lx or W//m2.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Colorimetric
            Colorimetric type.
        """
        if self._type is None and self._sensor_template.irradiance_sensor_template.HasField(
            "sensor_type_colorimetric"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_sensor_template.sensor_type_colorimetric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_sensor_template.sensor_type_colorimetric,
                default_parameters=ColorimetricParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.irradiance_sensor_template.sensor_type_colorimetric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_colorimetric = (
                self._sensor_template.irradiance_sensor_template.sensor_type_colorimetric
            )
        return self._type

    def set_type_radiometric(self) -> SensorIrradiance:
        """Set type radiometric.

        The sensor considers the entire spectrum and gets the results in W/m2.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_template.irradiance_sensor_template.sensor_type_radiometric.SetInParent()
        self._type = "Radiometric"
        return self

    def set_type_spectral(self) -> BaseSensor.Spectral:
        """Set type spectral.

        The sensor will generate color results and spectral data separated by wavelength
        in lx or W/m2.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Spectral
            Spectral type.
        """
        if self._type is None and self._sensor_template.irradiance_sensor_template.HasField(
            "sensor_type_spectral"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.irradiance_sensor_template.sensor_type_spectral,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Spectral):
            # if the _type is not Spectral then we create a new type.
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.irradiance_sensor_template.sensor_type_spectral,
                default_parameters=SpectralParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_spectral
            is not self._sensor_template.irradiance_sensor_template.sensor_type_spectral
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_spectral = (
                self._sensor_template.irradiance_sensor_template.sensor_type_spectral
            )
        return self._type

    @property
    def integration_direction(self):
        """Integration direction of irradiance Sensor.

        Sensor global integration direction [x,y,z], optional (default direction is Z axis of
        axis_system).

        Note: Contrary to any visualization of integration directions within Speos Software or its
        documentation the integration direction must be set in the anti-rays direction to integrate
        their signal.
        Integration direction is only settable for sensor template with IlluminanceTypePlanar or
        IlluminanceTypeSemiCylindrical as illuminance_type

        Returns
        -------
        list[float]
            Sensor global integration direction [x,y,z]
        """
        return self._sensor_instance.irradiance_properties.integration_direction

    @integration_direction.setter
    def integration_direction(self, value: list[float]):
        """Set integration direction.

        Parameters
        ----------
        value : list[float]
            Sensor global integration direction [x,y,z]
        """
        if not value:
            self._sensor_instance.irradiance_properties.ClearField("integration_direction")
        else:
            if self._sensor_template.irradiance_sensor_template.HasField(
                "illuminance_type_semi_cylindrical"
            ) or self._sensor_template.irradiance_sensor_template.HasField(
                "illuminance_type_planar"
            ):
                self._sensor_instance.irradiance_properties.integration_direction[:] = value
            else:
                msg = (
                    "Integration direction is only settable for sensor template with"
                    "IlluminanceTypePlanar or IlluminanceTypeSemiCylindrical as illuminance_type."
                )
                raise TypeError(msg)

    def set_illuminance_type_planar(self) -> SensorIrradiance:
        """Set illuminance type planar.

        Parameters
        ----------
        integration_direction : list[float], optional
            Sensor global integration direction [x,y,z].
            The integration direction must be set in the anti-rays direction to integrate their
            signal.
            By default, ``None``. None means that the Z axis of axis_system is taken.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.

        Notes
        -----
        Contrary to any visualization of integration directions within Speos Software or its
        documentation, the integration direction must be set in the anti-rays direction to integrate
        their signal.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_planar.SetInParent()
        self._sensor_instance.irradiance_properties.ClearField("integration_direction")
        return self

    def set_illuminance_type_radial(self) -> SensorIrradiance:
        """Set illuminance type radial.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_radial.SetInParent()
        return self

    def set_illuminance_type_hemispherical(self) -> SensorIrradiance:
        """Set illuminance type hemispherical.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_hemispherical.SetInParent()
        return self

    def set_illuminance_type_cylindrical(self) -> SensorIrradiance:
        """Set illuminance type cylindrical.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_cylindrical.SetInParent()
        return self

    def set_illuminance_type_semi_cylindrical(self) -> SensorIrradiance:
        """Set illuminance type semi cylindrical.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_semi_cylindrical.SetInParent()
        self._sensor_instance.irradiance_properties.ClearField("integration_direction")
        return self

    @property
    def axis_system(self) -> list[float]:
        """Position of the sensor.

        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._sensor_instance.irradiance_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: list[float]):
        """Position of the sensor.

        Parameters
        ----------
        axis_system : list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
        """
        self._sensor_instance.irradiance_properties.axis_system[:] = axis_system

    def set_ray_file_type_none(self) -> SensorIrradiance:
        """Set no ray file generation.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileNone
        )
        return self

    def set_ray_file_type_classic(self) -> SensorIrradiance:
        """Set ray file generation without polarization data.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileClassic
        )
        return self

    def set_ray_file_type_polarization(self) -> SensorIrradiance:
        """Set ray file generation with the polarization data for each ray.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFilePolarization
        )
        return self

    def set_ray_file_type_tm25(self) -> SensorIrradiance:
        """Set ray file generation: a .tm25ray file with polarization data for each ray.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25
        )
        return self

    def set_ray_file_type_tm25_no_polarization(self) -> SensorIrradiance:
        """Set ray file generation: a .tm25ray file without polarization data.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization
        )
        return self

    def set_layer_type_none(self) -> SensorIrradiance:
        """
        Define layer separation type as None.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            irradiance class instance

        """
        self._sensor_instance.irradiance_properties.layer_type_none.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_source(self) -> SensorIrradiance:
        """Define layer separation as by source.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
           irradiance class instance

        """
        self._sensor_instance.irradiance_properties.layer_type_source.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_face(self) -> BaseSensor.LayerTypeFace:
        """Define layer separation as by face.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeFace
            LayerTypeFace property instance
        """
        if self._layer_type is None and self._sensor_instance.irradiance_properties.HasField(
            "layer_type_face"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.irradiance_properties.layer_type_face,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeFace):
            # if the _layer_type is not LayerTypeFace then we create a new type.
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.irradiance_properties.layer_type_face,
                default_parameters=LayerByFaceParameters(),
                stable_ctr=True,
            )
        elif (
            self._layer_type._layer_type_face
            is not self._sensor_instance.irradiance_properties.layer_type_face
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_face = (
                self._sensor_instance.irradiance_properties.layer_type_face
            )
        return self._layer_type

    def set_layer_type_sequence(self) -> BaseSensor.LayerTypeSequence:
        """Define layer separation as by sequence.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
            LayerTypeSequence property instance
        """
        if self._layer_type is None and self._sensor_instance.irradiance_properties.HasField(
            "layer_type_sequence"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.irradiance_properties.layer_type_sequence,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeSequence):
            # if the _type is not LayerTypeSequence then we create a new type.
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.irradiance_properties.layer_type_sequence,
                default_parameters=LayerBySequenceParameters(),
                stable_ctr=True,
            )
        elif (
            self._layer_type._layer_type_sequence
            is not self._sensor_instance.irradiance_properties.layer_type_sequence
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_sequence = (
                self._sensor_instance.irradiance_properties.layer_type_sequence
            )
        return self._layer_type

    def set_layer_type_polarization(self) -> SensorIrradiance:
        """Define layer separation as by polarization.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance class instance
        """
        self._sensor_instance.irradiance_properties.layer_type_polarization.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_incidence_angle(
        self,
    ) -> BaseSensor.LayerTypeIncidenceAngle:
        """Define layer separation as by incidence angle.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeIncidenceAngle
            LayerTypeIncidenceAngle property instance
        """
        if self._layer_type is None and self._sensor_instance.irradiance_properties.HasField(
            "layer_type_incidence_angle"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeIncidenceAngle(
                layer_type_incidence_angle=self._sensor_instance.irradiance_properties.layer_type_incidence_angle,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeIncidenceAngle):
            # if the _layer_type is not LayerTypeIncidenceAngle then we create a new type.
            self._layer_type = BaseSensor.LayerTypeIncidenceAngle(
                layer_type_incidence_angle=self._sensor_instance.irradiance_properties.layer_type_incidence_angle,
                default_parameters=LayerByIncidenceAngleParameters(),
                stable_ctr=True,
            )
        elif (
            self._layer_type._layer_type_incidence_angle
            is not self._sensor_instance.irradiance_properties.layer_type_incidence_angle
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_incidence_angle = (
                self._sensor_instance.irradiance_properties.layer_type_incidence_angle
            )
        return self._layer_type

    @property
    def output_face_geometries(self) -> SensorIrradiance:
        """Select output faces for inverse simulation optimization.

        Parameters
        ----------
        geometries : list[ansys.speos.core.geo_ref.GeoRef]
            list of geometries that will be considered as output faces.
            By default, ``[]``, ie no output faces.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        if self._sensor_instance.irradiance_properties.HasField("output_face_geometries"):
            return self._sensor_instance.irradiance_properties.output_face_geometries.geo_paths

    @output_face_geometries.setter
    def output_face_geometries(
        self,
        geometries: Optional[list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]] = None,
    ) -> SensorIrradiance:
        """Select output faces for inverse simulation optimization.

        Parameters
        ----------
        geometries : list[ansys.speos.core.geo_ref.GeoRef]
            List of geometries that will be considered as output faces.
            By default, ``[]``, ie no output faces.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Irradiance sensor.
        """
        if not geometries:
            self._sensor_instance.irradiance_properties.ClearField("output_face_geometries")
        else:
            geo_paths = []
            for gr in geometries:
                if isinstance(gr, GeoRef):
                    geo_paths.append(gr)
                elif isinstance(gr, (face.Face, body.Body, part.Part.SubPart)):
                    geo_paths.append(gr.geo_path)
                else:
                    msg = f"Type {type(gr)} is not supported as output faces geometry input."
                    raise TypeError(msg)
            self._sensor_instance.irradiance_properties.output_face_geometries.geo_paths[:] = [
                gp.to_native_link() for gp in geo_paths
            ]


class SensorRadiance(BaseSensor):
    """Sensor feature: Radiance.

    By default, regarding inherent characteristics, a radiance sensor of type photometric is chosen.
    By default, regarding properties, an axis system is selected to position the sensor and no layer
    separation is chosen.

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
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_parameters : bool
        Uses default values when True.
        By default, ``True``.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Union[None, RadianceSensorParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            sensor_instance=sensor_instance,
        )

        # Attribute gathering more complex radiance type
        self._type = None

        # Attribute gathering more complex layer type
        self._layer_type = None

        # Attribute to keep track of sensor dimensions object
        self._sensor_dimensions = self.Dimensions(
            sensor_dimensions=self._sensor_template.radiance_sensor_template.dimensions,
            default_parameters=None,
            stable_ctr=True,
        )
        if sensor_instance is None:
            if default_parameters is None:
                default_parameters = RadianceSensorParameters()
            # Default values template
            self.focal = default_parameters.focal_length
            self.integration_angle = default_parameters.integration_angle
            self.axis_system = default_parameters.axis_system
            self.observer_point = default_parameters.observer
            self._sensor_dimensions = self.Dimensions(
                sensor_dimensions=self._sensor_template.radiance_sensor_template.dimensions,
                default_parameters=default_parameters.dimensions,
                stable_ctr=True,
            )
            if isinstance(default_parameters.sensor_type, ColorimetricParameters):
                self._type = BaseSensor.Colorimetric(
                    sensor_type_colorimetric=self._sensor_template.radiance_sensor_template.sensor_type_colorimetric,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.sensor_type, SpectralParameters):
                self._type = BaseSensor.Spectral(
                    sensor_type_spectral=self._sensor_template.radiance_sensor_template.sensor_type_spectral,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == "radiometric":
                self.set_type_radiometric()
            elif default_parameters.sensor_type == "photometric":
                self.set_type_photometric()

            if default_parameters.layer_type == "none":
                self.set_layer_type_none()
            elif default_parameters.layer_type == "by_source":
                self.set_layer_type_source()
            elif isinstance(default_parameters.layer_type, LayerByFaceParameters):
                self._layer_type = BaseSensor.LayerTypeFace(
                    layer_type_face=self._sensor_instance.radiance_properties.layer_type_face,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.layer_type, LayerBySequenceParameters):
                self._layer_type = BaseSensor.LayerTypeSequence(
                    layer_type_sequence=self._sensor_instance.radiance_properties.layer_type_sequence,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
        else:
            self._sensor_dimensions = self.Dimensions(
                sensor_dimensions=self._sensor_template.radiance_sensor_template.dimensions,
                default_parameters=None,
                stable_ctr=True,
            )

    @property
    def visual_data(self) -> _VisualData:
        """Property containing radiance sensor visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature faces, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            feature_pos_info = self.get(key="axis_system")
            feature_radiance_pos = np.array(feature_pos_info[:3])
            feature_radiance_x_dir = np.array(feature_pos_info[3:6])
            feature_radiance_y_dir = np.array(feature_pos_info[6:9])
            feature_radiance_z_dir = np.array(feature_pos_info[9:12])
            feature_x_start = float(self.get(key="x_start"))
            feature_x_end = float(self.get(key="x_end"))
            feature_y_start = float(self.get(key="y_start"))
            feature_y_end = float(self.get(key="y_end"))
            feature_radiance_focal = float(self.get(key="focal"))

            # radiance sensor
            p1 = (
                feature_radiance_pos
                + feature_radiance_x_dir * feature_x_end
                + feature_radiance_y_dir * feature_y_end
            )
            p2 = (
                feature_radiance_pos
                + feature_radiance_x_dir * feature_x_end
                + feature_radiance_y_dir * feature_y_start
            )
            p3 = (
                feature_radiance_pos
                + feature_radiance_x_dir * feature_x_start
                + feature_radiance_y_dir * feature_y_start
            )
            p4 = (
                feature_radiance_pos
                + feature_radiance_x_dir * feature_x_start
                + feature_radiance_y_dir * feature_y_end
            )
            self._visual_data.add_data_rectangle([p1, p2, p3])

            p5 = feature_radiance_pos + feature_radiance_z_dir * feature_radiance_focal
            self._visual_data.add_data_triangle([p1, p2, p5])
            self._visual_data.add_data_triangle([p3, p4, p5])
            self._visual_data.add_data_triangle([p1, p4, p5])
            self._visual_data.add_data_triangle([p2, p3, p5])

            # radiance direction
            self._visual_data.coordinates.origin = feature_radiance_pos
            self._visual_data.coordinates.x_axis = feature_radiance_x_dir
            self._visual_data.coordinates.y_axis = feature_radiance_y_dir

            self._visual_data.updated = True
            return self._visual_data

    @property
    def dimensions(self) -> BaseSensor.Dimensions:
        """Property containing all options in regard to the Dimensions sensor properties.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Instance of Dimensions Class for this sensor feature
        """
        return self._sensor_dimensions

    @property
    def type(self) -> str:
        """Type of sensor.

        Returns
        -------
        str
            Sensor type as string
        """
        if type(self._type) is str:
            return self._type
        elif isinstance(self._type, BaseSensor.Colorimetric):
            return "Colorimetric"
        elif isinstance(self._type, BaseSensor.Spectral):
            return "Spectral"
        else:
            return self._type

    @property
    def colorimetric(self) -> Union[None, BaseSensor.Colorimetric]:
        """Property containing all options in regard to the Colorimetric sensor properties.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Colorimetric
            Instance of Colorimetric Class for this sensor feature
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return self._type
        else:
            return None

    @property
    def spectral(self) -> Union[None, BaseSensor.Spectral]:
        """Property containing all options in regard to the Spectral sensor properties.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Spectral
            Instance of Spectral Class for this sensor feature
        """
        if isinstance(self._type, BaseSensor.Spectral):
            return self._type
        else:
            return None

    @property
    def layer(
        self,
    ) -> Union[None, BaseSensor.LayerTypeFace, BaseSensor.LayerTypeSequence]:
        """Property containing all options in regard to the layer separation property.

        Returns
        -------
        Union[\
            None,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence\
        ]
            Instance of Layer type Class for this sensor feature
        """
        return self._layer_type

    def set_dimensions(self) -> BaseSensor.Dimensions:
        """Set the dimensions of the sensor.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimension class
        """
        if (
            self._sensor_dimensions._sensor_dimensions
            is not self._sensor_template.radiance_sensor_template.dimensions
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._sensor_dimensions._sensor_dimensions = (
                self._sensor_template.radiance_sensor_template.dimensions
            )
        return self._sensor_dimensions

    def set_type_photometric(self) -> SensorRadiance:
        """Set type photometric.

        The sensor considers the visible spectrum and gets the results in lm/m2 or lx.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Radiance sensor.
        """
        self._sensor_template.radiance_sensor_template.sensor_type_photometric.SetInParent()
        self._type = None
        return self

    def set_type_colorimetric(self) -> BaseSensor.Colorimetric:
        """Set type colorimetric.

        The sensor will generate color results without any spectral data or layer separation
        in lx or W//m2.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Colorimetric
            Colorimetric type.
        """
        if self._type is None and self._sensor_template.radiance_sensor_template.HasField(
            "sensor_type_colorimetric"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.radiance_sensor_template.sensor_type_colorimetric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.radiance_sensor_template.sensor_type_colorimetric,
                default_parameters=ColorimetricParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.radiance_sensor_template.sensor_type_colorimetric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_colorimetric = (
                self._sensor_template.radiance_sensor_template.sensor_type_colorimetric
            )
        return self._type

    def set_type_radiometric(self) -> SensorRadiance:
        """Set type radiometric.

        The sensor considers the entire spectrum and gets the results in W/m2.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Radiance sensor.
        """
        self._sensor_template.radiance_sensor_template.sensor_type_radiometric.SetInParent()
        self._type = None
        return self

    def set_type_spectral(self) -> BaseSensor.Spectral:
        """Set type spectral.

        The sensor will generate color results and spectral data separated by wavelength
        in lx or W/m2.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Spectral
            Spectral type.
        """
        if self._type is None and self._sensor_template.radiance_sensor_template.HasField(
            "sensor_type_spectral"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.radiance_sensor_template.sensor_type_spectral,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Spectral):
            # if the _type is not Spectral then we create a new type.
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.radiance_sensor_template.sensor_type_spectral,
                default_parameters=SpectralParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_spectral
            is not self._sensor_template.radiance_sensor_template.sensor_type_spectral
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_spectral = (
                self._sensor_template.radiance_sensor_template.sensor_type_spectral
            )
        return self._type

    @property
    def focal(self) -> float:
        """Focal value of the Radiance Sensor.

        By default, ``250``.

        Returns
        -------
        float
            Focal length of the sensor
        """
        return self._sensor_template.radiance_sensor_template.focal

    @focal.setter
    def focal(self, value: float):
        """Focal value.

        Parameters
        ----------
        value : float
            Focal (mm).
            By default, ``250``.
        """
        self._sensor_template.radiance_sensor_template.focal = value

    @property
    def integration_angle(self) -> float:
        """Integration angle.

        By default, ``5``.

        Returns
        -------
        float
            integration angle of the Radiance Sensor
        """
        return self._sensor_template.radiance_sensor_template.integration_angle

    @integration_angle.setter
    def integration_angle(self, value: float) -> SensorRadiance:
        """Integration angle.

        Parameters
        ----------
        value : float
            integration angle (degree)
            By default, ``5``.
        """
        self._sensor_template.radiance_sensor_template.integration_angle = value

    @property
    def axis_system(self) -> list[float]:
        """Position of the sensor.

        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._sensor_instance.radiance_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: list[float]):
        """Position of the sensor.

        Parameters
        ----------
        axis_system : list[float]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
        """
        self._sensor_instance.radiance_properties.axis_system[:] = axis_system

    @property
    def observer_point(self) -> SensorRadiance:
        """The position of the observer point.

        This is optional, because the focal length is used by default.
        Choosing to set an observer point will make the focal length ignored.

        By default, ``None``. None means that the focal length is used.

        Returns
        -------
        Union[None, list[float]]
            Position of the observer point [Ox Oy Oz], None means that the
            focal length is used.
        """
        return self._sensor_instance.radiance_properties.observer_point

    @observer_point.setter
    def observer_point(self, value: list[float]):
        """Position of the observer point.

        This is optional, because the focal length is used by default.
        Choosing to set an observer point will make the focal length ignored.

        Parameters
        ----------
        value : list[float]
            Position of the observer point [Ox Oy Oz].
            By default, ``None``. None means that the focal length is used.
        """
        if not value:
            self._sensor_instance.radiance_properties.ClearField("observer_point")
        else:
            self._sensor_instance.radiance_properties.observer_point[:] = value

    def set_layer_type_none(self) -> SensorRadiance:
        """Define layer separation type as None.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Radiance sensor

        """
        self._sensor_instance.radiance_properties.layer_type_none.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_source(self) -> SensorRadiance:
        """Define layer separation as by source.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Radiance sensor

        """
        self._sensor_instance.radiance_properties.layer_type_source.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_face(self) -> BaseSensor.LayerTypeFace:
        """Define layer separation as by face.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeFace
            LayerTypeFace property instance
        """
        if self._layer_type is None and self._sensor_instance.radiance_properties.HasField(
            "layer_type_face"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.radiance_properties.layer_type_face,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeFace):
            # if the _layer_type is not LayerTypeFace then we create a new type.
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.radiance_properties.layer_type_face,
                default_parameters=LayerByFaceParameters(),
                stable_ctr=True,
            )
        elif (
            self._layer_type._layer_type_face
            is not self._sensor_instance.radiance_properties.layer_type_face
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_face = (
                self._sensor_instance.radiance_properties.layer_type_face
            )
        return self._layer_type

    def set_layer_type_sequence(self) -> BaseSensor.LayerTypeSequence:
        """Define layer separation as by sequence.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
            LayerTypeSequence property instance
        """
        if self._layer_type is None and self._sensor_instance.radiance_properties.HasField(
            "layer_type_sequence"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.radiance_properties.layer_type_sequence,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeSequence):
            # if the _layer_type is not LayerTypeSequence then we create a new type.
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.radiance_properties.layer_type_sequence,
                default_parameters=LayerBySequenceParameters(),
                stable_ctr=True,
            )
        elif (
            self._layer_type._layer_type_sequence
            is not self._sensor_instance.radiance_properties.layer_type_sequence
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_sequence = (
                self._sensor_instance.radiance_properties.layer_type_sequence
            )
        return self._layer_type


class Sensor3DIrradiance(BaseSensor):
    """Sensor feature: 3D Irradiance.

    By default, regarding inherent characteristics, a 3d irradiance sensor of type photometric and
    illuminance type planar is chosen, Reflection, Transmission, and Absorption measurements
    are activated. By default, regarding properties, no layer separation and no ray file
    generation are chosen.

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
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_parameters : bool
        Uses default values when True.
        By default, ``True``.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Union[None, Irradiance3DSensorParameters] = None,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            sensor_instance=sensor_instance,
        )

        # Attribute gathering more complex irradiance type
        self._type = None

        # Attribute gathering more complex layer type
        self._layer_type = None

        if sensor_instance is None:
            if default_parameters is None:
                default_parameters = Irradiance3DSensorParameters()

            if isinstance(default_parameters.sensor_type, ColorimetricParameters):
                self._type = Sensor3DIrradiance.Colorimetric(
                    sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == "radiometric":
                self._type = Sensor3DIrradiance.Radiometric(
                    sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                    default_parameters=default_parameters,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == "photometric":
                self._type = Sensor3DIrradiance.Photometric(
                    sensor_type_photometric=self._sensor_template.irradiance_3d.type_photometric,
                    default_parameters=default_parameters,
                    stable_ctr=True,
                )
            if default_parameters.geometries:
                self.geometries = default_parameters.geometries
            if default_parameters.layer_type == "none":
                self.set_layer_type_none()
            elif default_parameters.layer_type == "by_source":
                self.set_layer_type_source()
            match default_parameters.rayfile_type:
                case "none":
                    self.set_ray_file_type_none()
                case "classic":
                    self.set_ray_file_type_classic()
                case "polarization":
                    self.set_ray_file_type_polarization()
                case "tm25":
                    self.set_ray_file_type_tm25()
                case "tm25_no_polarization":
                    self.set_ray_file_type_tm25_no_polarization()

    class Radiometric:
        """Class computing the radiant intensity (in W.sr-1).

        Generate an extended map for Virtual Photometric Lab.

        Parameters
        ----------
        illuminance_type : ansys.api.speos.sensor.v1.sensor_pb2.TypeRadiometric
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_radiometric: sensor_pb2.TypeRadiometric,
            default_parameters: Union[None, Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError("Radiometric class instantiated outside of class scope")

            self._sensor_type_radiometric = sensor_type_radiometric
            self._integration_type = None
            if default_parameters:
                match default_parameters.integration_type:
                    case "planar":
                        self.set_integration_planar()
                    case "radial":
                        self.set_integration_radial()
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_radiometric.integration_type_planar,
                    default_parameters=default_parameters.measures,
                    stable_ctr=stable_ctr,
                )
            else:
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_radiometric.integration_type_planar,
                    default_parameters=None,
                    stable_ctr=stable_ctr,
                )

        def set_integration_planar(self) -> Sensor3DIrradiance.Measures:
            """Set integration planar.

            Returns
            -------
            Sensor3DIrradiance.Measures
                measured defines transmission, reflection, absorption

            """
            if not isinstance(self._integration_type, Sensor3DIrradiance.Measures):
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_radiometric.integration_type_planar,
                    default_parameters=MeasuresParameters(),
                    stable_ctr=True,
                )
            elif (
                self._integration_type._illuminance_type
                is not self._sensor_type_radiometric.integration_type_planar
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._integration_type._illuminance_type = (
                    self._sensor_type_radiometric.integration_type_planar
                )
            return self._integration_type

        def set_integration_radial(self) -> None:
            """Set integration radial."""
            self._integration_type = "Radial"
            self._sensor_type_radiometric.integration_type_radial.SetInParent()

    class Photometric:
        """Class computing the luminous intensity (in cd).

        Generate an extended map for Virtual Photometric Lab.

        Parameters
        ----------
        illuminance_type : ansys.api.speos.sensor.v1.sensor_pb2.TypePhotometric
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_photometric: sensor_pb2.TypePhotometric,
            default_parameters: Union[None, Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError("Photometric class instantiated outside of class scope")

            self._sensor_type_photometric = sensor_type_photometric
            self._integration_type = None
            if default_parameters:
                match default_parameters.integration_type:
                    case "planar":
                        self.set_integration_planar()
                    case "radial":
                        self.set_integration_radial()
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_photometric.integration_type_planar,
                    default_parameters=default_parameters.measures,
                    stable_ctr=stable_ctr,
                )
            else:
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_photometric.integration_type_planar,
                    default_parameters=None,
                    stable_ctr=stable_ctr,
                )

        def set_integration_planar(self) -> Sensor3DIrradiance.Measures:
            """Set integration planar.

            Returns
            -------
            Sensor3DIrradiance.Measures
                measured defines transmission, reflection, absorption

            """
            if not isinstance(self._integration_type, Sensor3DIrradiance.Measures):
                self._integration_type = Sensor3DIrradiance.Measures(
                    illuminance_type=self._sensor_type_photometric.integration_type_planar,
                    default_parameters=MeasuresParameters(),
                    stable_ctr=True,
                )
            elif (
                self._integration_type._illuminance_type
                is not self._sensor_type_photometric.integration_type_planar
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._integration_type._illuminance_type = (
                    self._sensor_type_photometric.integration_type_planar
                )
            return self._integration_type

        def set_integration_radial(self) -> None:
            """Set integration radial."""
            self._integration_type = "Radial"
            self._sensor_type_photometric.integration_type_radial.SetInParent()

    class Measures:
        """Measures settings of 3D irradiance sensor : Additional Measures.

        If you selected Photometric or Radiometric, in the Additional measures section,
        define which type of contributions (transmission, absorption, reflection)
        need to be taken into account for the integrating faces of the sensor.

        Parameters
        ----------
        illuminance_type : ansys.api.speos.sensor.v1.sensor_pb2.IntegrationTypePlanar
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            illuminance_type: sensor_pb2.IntegrationTypePlanar,
            default_parameters: Union[None, MeasuresParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Measures class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._illuminance_type = illuminance_type

            if default_parameters:
                # Default values
                self.reflection = default_parameters.reflection
                self.transmission = default_parameters.transmission
                self.absorption = default_parameters.absorption

        @property
        def reflection(self) -> bool:
            """Get reflection settings.

            Returns
            -------
            bool
                True when reflection settings were set, False otherwise.
            """
            return self._illuminance_type.reflection

        @reflection.setter
        def reflection(self, value: bool) -> None:
            """Set reflection.

            Parameters
            ----------
            value: bool
                True to activate measuring reflection, False to deactivate reflection.

            Returns
            -------
            Sensor3DIrradiance.Measures
                Measured of reflection, transmission, absorption settings.

            """
            self._illuminance_type.reflection = value

        @property
        def transmission(self) -> bool:
            """Get transmission settings.

            Returns
            -------
            bool
                True when transmission settings were set, False otherwise.
            """
            return self._illuminance_type.transmission

        @transmission.setter
        def transmission(self, value: bool) -> None:
            """Transmission.

            Parameters
            ----------
            value: bool
                True to activate measuring transmission, False to deactivate transmission.

            Returns
            -------
            Sensor3DIrradiance.Measures
                Measured of reflection, transmission, absorption settings.

            """
            self._illuminance_type.transmission = value

        @property
        def absorption(self) -> bool:
            """Get absorption settings.

            Returns
            -------
            bool
                True when absorption settings were set, False otherwise.
            """
            return self._illuminance_type.absorption

        @absorption.setter
        def absorption(self, value: bool) -> None:
            """Set absorption.

            Parameters
            ----------
            value: bool
                True to activate measuring absorption, False to deactivate absorption.

            Returns
            -------
            Sensor3DIrradiance.Measures
                Measured of reflection, transmission, absorption settings.

            """
            self._illuminance_type.absorption = value

    class Colorimetric:
        """Class computing the color results.

        Result without any spectral layer separation (in cd or W.sr-1).

        Parameters
        ----------
        illuminance_type : ansys.api.speos.sensor.v1.sensor_pb2.TypeColorimetric
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_colorimetric: sensor_pb2.TypeColorimetric,
            default_parameters: Union[None, ColorimetricParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Colorimetric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Attribute to keep track of wavelength range object

            if default_parameters:
                # Default values
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_colorimetric,
                    default_parameters=default_parameters.wavelength_range,
                    stable_ctr=stable_ctr,
                )
            else:
                self._wavelengths_range = BaseSensor.WavelengthsRange(
                    wavelengths_range=self._sensor_type_colorimetric,
                    default_parameters=default_parameters,
                    stable_ctr=stable_ctr,
                )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range.
            """
            if self._wavelengths_range._wavelengths_range is not self._sensor_type_colorimetric:
                # Happens in case of feature reset (to be sure to always modify correct data)
                self._wavelengths_range._wavelengths_range = self._sensor_type_colorimetric
            return self._wavelengths_range

    @property
    def visual_data(self) -> _VisualData:
        """Property containing 3d irradiance sensor visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature faces, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            mesh_geo_paths = self.get(key="geo_paths")
            for mesh_geo_path in mesh_geo_paths:
                if len(self._project.find(name=mesh_geo_path, feature_type=core.face.Face)) != 0:
                    # the geometry is a face
                    mesh_geo = self._project.find(name=mesh_geo_path, feature_type=core.face.Face)[
                        0
                    ]
                    face_data = mesh_geo._face
                    vertices = np.array(face_data.vertices).reshape(-1, 3)
                    if isinstance(mesh_geo._parent_body._parent_part, core.part.Part.SubPart):
                        # the geometry has a local coordinate
                        part_coordinate_info = (
                            mesh_geo._parent_body._parent_part._part_instance.axis_system
                        )
                        vertices = np.array(
                            [local2absolute(vertice, part_coordinate_info) for vertice in vertices]
                        )
                    facets = np.array(face_data.facets).reshape(-1, 3)
                    temp = np.full(facets.shape[0], 3)
                    temp = np.vstack(temp)
                    facets = np.hstack((temp, facets))
                    self._visual_data.add_data_mesh(vertices=vertices, facets=facets)
                elif len(self._project.find(name=mesh_geo_path, feature_type=core.body.Body)) != 0:
                    mesh_geo = self._project.find(name=mesh_geo_path, feature_type=core.body.Body)[
                        0
                    ]
                    for mesh_geo_face in mesh_geo._geom_features:
                        face_data = mesh_geo_face._face
                        vertices = np.array(face_data.vertices).reshape(-1, 3)
                        if isinstance(mesh_geo._parent_part, core.part.Part.SubPart):
                            part_coordinate_info = mesh_geo._parent_part._part_instance.axis_system
                            vertices = np.array(
                                [
                                    local2absolute(vertice, part_coordinate_info)
                                    for vertice in vertices
                                ]
                            )
                        facets = np.array(face_data.facets).reshape(-1, 3)
                        temp = np.full(facets.shape[0], 3)
                        temp = np.vstack(temp)
                        facets = np.hstack((temp, facets))
                        self._visual_data.add_data_mesh(vertices=vertices, facets=facets)
                else:
                    raise ValueError(
                        "{} linked to Sensor 3D irradiance {} is not "
                        "a valid geometry Face or Body".format(mesh_geo_path, self._name)
                    )

            self._visual_data.updated = True
            return self._visual_data

    def set_type_photometric(self) -> Sensor3DIrradiance.Photometric:
        """Set type photometric.

        The sensor considers the visible spectrum and gets the results in lm/m2 or lx.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor.
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_photometric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Photometric(
                self._sensor_template.irradiance_3d.type_photometric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Sensor3DIrradiance.Photometric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = Sensor3DIrradiance.Photometric(
                self._sensor_template.irradiance_3d.type_photometric,
                default_parameters=Irradiance3DSensorParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_photometric
            is not self._sensor_template.irradiance_3d.type_photometric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_photometric = (
                self._sensor_template.irradiance_3d.type_photometric
            )
        return self._type

    def set_type_radiometric(self) -> Sensor3DIrradiance.Radiometric:
        """Set type radiometric.

        The sensor considers the entire spectrum and gets the results in W/m2.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_radiometric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Radiometric(
                sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Sensor3DIrradiance.Radiometric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = Sensor3DIrradiance.Radiometric(
                sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                default_parameters=Irradiance3DSensorParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_radiometric
            is not self._sensor_template.irradiance_3d.type_radiometric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_radiometric = (
                self._sensor_template.irradiance_3d.type_radiometric
            )
        return self._type

    def set_type_colorimetric(self) -> Sensor3DIrradiance.Colorimetric:
        """Set type colorimetric.

        The sensor will generate color results without any spectral data or layer separation
        in lx or W//m2.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Colorimetric
            Colorimetric type.
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_colorimetric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = Sensor3DIrradiance.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                default_parameters=ColorimetricParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.irradiance_3d.type_colorimetric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_colorimetric = (
                self._sensor_template.irradiance_3d.type_colorimetric
            )
        return self._type

    def set_ray_file_type_none(self) -> Sensor3DIrradiance:
        """Set no ray file generation.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileNone
        )
        return self

    def set_ray_file_type_classic(self) -> Sensor3DIrradiance:
        """Set ray file generation without polarization data.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileClassic
        )
        return self

    def set_ray_file_type_polarization(self) -> Sensor3DIrradiance:
        """Set ray file generation with the polarization data for each ray.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFilePolarization
        )
        return self

    def set_ray_file_type_tm25(self) -> Sensor3DIrradiance:
        """Set ray file generation: a .tm25ray file with polarization data for each ray.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25
        )
        return self

    def set_ray_file_type_tm25_no_polarization(self) -> Sensor3DIrradiance:
        """Set ray file generation: a .tm25ray file without polarization data.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization
        )
        return self

    def set_layer_type_none(self) -> Sensor3DIrradiance:
        """
        Define layer separation type as None.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            3D Irradiance sensor

        """
        self._sensor_instance.irradiance_3d_properties.layer_type_none.SetInParent()
        self._layer_type = None
        return self

    def set_layer_type_source(self) -> Sensor3DIrradiance:
        """Define layer separation as by source.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
           3D Irradiance sensor

        """
        self._sensor_instance.irradiance_3d_properties.layer_type_source.SetInParent()
        self._layer_type = None
        return self

    @property
    def geometries(self) -> list[str]:
        """Geometry faces/bodies to be defined with 3D irradiance sensor.

        Returns
        -------
        list[str]
            List of geometries that will be considered as Sensor
        """
        return self._sensor_instance.irradiance_3d_properties.geometries.geo_paths

    @geometries.setter
    def geometries(
        self, geometries: list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]
    ) -> Sensor3DIrradiance:
        """Select geometry faces to be defined with 3D irradiance sensor.

        Parameters
        ----------
        geometries : list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]
            List of geometries that will be considered as Sensor
        """
        geo_paths = []
        for gr in geometries:
            if isinstance(gr, GeoRef):
                geo_paths.append(gr)
            elif isinstance(gr, (face.Face, body.Body, part.Part.SubPart)):
                geo_paths.append(gr.geo_path)
            else:
                msg = f"Type {type(gr)} is not supported as 3D Irradiance Sensor geometry input."
                raise TypeError(msg)
        self._sensor_instance.irradiance_3d_properties.geometries.geo_paths[:] = [
            gp.to_native_link() for gp in geo_paths
        ]
