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

"""Sensors module.

This module provides classes to create and manipulate Speos sensors inside a
project: base sensor behaviors and specialized sensors (camera, irradiance,
radiance, 3D irradiance and intensity XMP).

The public classes in this module are:
- BaseSensor: internal common behaviour and small nested helper classes.
- SensorCamera
- SensorIrradiance
- SensorRadiance
- Sensor3DIrradiance
- SensorXMPIntensity

Notes
-----
Docstrings use the NumPy style and include fully-qualified types for public API
parameters (for documentation tooling).
"""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Mapping, Optional, Union
import uuid
import warnings

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2, sensor_pb2
import grpc
import numpy as np

import ansys.speos.core as core
import ansys.speos.core.body as body
import ansys.speos.core.face as face
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.parameters import (
    BalanceModeDisplayPrimariesParameters,
    BalanceModeUserWhiteParameters,
    CameraSensorParameters,
    ColorBalanceModeTypes,
    ColorimetricParameters,
    ColorParameters,
    DimensionsParameters,
    IntegrationTypes,
    IntensitySensorDimensionsConoscopicParameters,
    IntensitySensorDimensionsXAsMeridianParameters,
    IntensitySensorDimensionsXAsParallelParameters,
    IntensitySensorOrientationTypes,
    IntensitySensorViewingTypes,
    IntensityXMPSensorParameters,
    Irradiance3DSensorParameters,
    IrradianceSensorParameters,
    LayerByFaceParameters,
    LayerByIncidenceAngleParameters,
    LayerBySequenceParameters,
    LayerTypes,
    MeasuresParameters,
    MonoChromaticParameters,
    NearfieldParameters,
    PhotometricCameraParameters,
    RadianceSensorParameters,
    RayfileTypes,
    SensorTypes,
    SpectralParameters,
    WavelengthsRangeParameters,
)
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
    description : str, optional
        Description of the feature. By default, ``""``.
    metadata : Mapping[str, str], optional
        Metadata of the feature. By default, ``{}``.
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from
        scratch. By default, ``None`` which creates the feature locally.

    Attributes
    ----------
    sensor_template_link : ansys.speos.core.kernel.sensor_template.SensorTemplateLink
        Link object for the sensor template in database.

    Notes
    -----
    This is a super class. Do not instantiate this class directly.
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

        Parameters
        ----------
        value : int
            Integer value defining number of rays stored. If ``None`` or falsy, the
            ``lxp_properties`` field is cleared.

        Returns
        -------
        Union[None, int]
            Number of rays stored in the LXP file for this sensor, or ``None`` if
            the feature does not have LXP properties set.
        """
        if self._sensor_instance.HasField("lxp_properties"):
            return self._sensor_instance.lxp_properties.nb_max_paths
        return None

    @lxp_path_number.setter
    def lxp_path_number(self, value: int) -> None:
        """Set number of LXP rays to store."""
        if value:
            self._sensor_instance.lxp_properties.nb_max_paths = int(value)
        else:
            self._sensor_instance.ClearField("lxp_properties")

    class WavelengthsRange:
        """Range of wavelengths.

        By default a range from 400 nm to 700 nm with a sampling of 13 is chosen.

        Parameters
        ----------
        wavelengths_range : ansys.api.speos.sensor.v1.common_pb2.WavelengthsRange or \
ansys.api.speos.sensor.v1.sensor_pb2.TypeColorimetric
            Wavelengths range protobuf object to modify.
        default_parameters : ansys.speos.core.generic.parameters.WavelengthsRangeParameters,\
        optional
            If defined, the values in the sensor instance will be overwritten by the
            values of the data class.
        stable_ctr : bool, optional
            Internal flag that prevents external instantiation. Default ``False``.

        Notes
        -----
        Do not instantiate this class directly; use a sensor's
        `set_wavelengths_range` method instead.
        """

        def __init__(
            self,
            wavelengths_range: Union[common_pb2.WavelengthsRange, sensor_pb2.TypeColorimetric],
            default_parameters: Optional[WavelengthsRangeParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "WavelengthsRange class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._wavelengths_range = wavelengths_range
            self._fill_parameters(default_parameters)

        def _fill_parameters(
            self, default_parameters: Optional[WavelengthsRangeParameters] = None
        ) -> None:
            if not default_parameters:
                return
            self.start = default_parameters.start
            self.end = default_parameters.end
            self.sampling = default_parameters.sampling

        @property
        def start(self) -> float:
            """Minimum wavelength of the range (nm).

            Parameters
            ----------
            value : float
                Minimum wavelength in nanometers.

            Returns
            -------
            float
                Lower bound of the wavelength range in nanometers.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_start
            else:
                return self._wavelengths_range.wavelength_start

        @start.setter
        def start(self, value: float):
            """Set minimum wavelength of the range."""
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_start = value
            else:
                self._wavelengths_range.wavelength_start = value

        @property
        def end(self) -> float:
            """Maximum wavelength of the range (nm).

            Parameters
            ----------
            value : float
                Maximum wavelength in nanometers.

            Returns
            -------
            float
                Upper bound of the wavelength range in nanometers.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_end
            else:
                return self._wavelengths_range.wavelength_end

        @end.setter
        def end(self, value: float):
            """Set maximum wavelength of the range."""
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_end = value
            else:
                self._wavelengths_range.wavelength_end = value

        @property
        def sampling(self) -> int:
            """Wavelength sampling between start and end.

            Parameters
            ----------
            value : int
                Number of sampling points between start and end.

            Returns
            -------
            int
                Number of samples used to split the wavelength range.
            """
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                return self._wavelengths_range.w_sampling

        @sampling.setter
        def sampling(self, value: int):
            """Set number of wavelength samples."""
            if isinstance(self._wavelengths_range, common_pb2.WavelengthsRange):
                self._wavelengths_range.w_sampling = value

    class Dimensions:
        """Sensor sampling and extent along X and Y.

        By default X/Y range is [-50, 50] mm with sampling 100.

        Parameters
        ----------
        sensor_dimensions : ansys.api.speos.sensor.v1.common_pb2.SensorDimensions
            SensorDimensions protobuf object to modify.
        default_parameters : ansys.speos.core.generic.parameters.DimensionsParameters, optional
            If provided, overwrite the template defaults.
        stable_ctr : bool, optional
            Internal flag to prevent external instantiation.
        """

        def __init__(
            self,
            sensor_dimensions: common_pb2.SensorDimensions,
            default_parameters: Optional[DimensionsParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Dimension class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_dimensions = sensor_dimensions
            self._fill_parameters(default_parameters)

        def _fill_parameters(
            self, default_parameters: Optional[DimensionsParameters] = None
        ) -> None:
            if not default_parameters:
                return
            self.x_start = default_parameters.x_start
            self.y_start = default_parameters.y_start
            self.x_end = default_parameters.x_end
            self.y_end = default_parameters.y_end
            self.x_sampling = default_parameters.x_sampling
            self.y_sampling = default_parameters.y_sampling

        @property
        def x_start(self) -> float:
            """Minimum value on X axis (mm).

            Parameters
            ----------
            value : float
                Minimum x coordinate in millimeters.

            Returns
            -------
            float
                Minimum x coordinate in millimeters.
            """
            return self._sensor_dimensions.x_start

        @x_start.setter
        def x_start(self, value: float):
            """Set minimum value on X axis."""
            self._sensor_dimensions.x_start = value

        @property
        def x_end(self) -> float:
            """Maximum value on X axis (mm).

            Parameters
            ----------
            value : float
                Maximum x coordinate in millimeters.

            Returns
            -------
            float
                Maximum x coordinate in millimeters.
            """
            return self._sensor_dimensions.x_end

        @x_end.setter
        def x_end(self, value: float):
            """Set maximum value on X axis."""
            self._sensor_dimensions.x_end = value

        @property
        def x_sampling(self) -> int:
            """Sampling along X axis (pixels).

            Parameters
            ----------
            value : int
                Number of samples along the X axis.

            Returns
            -------
            int
                Number of samples along the X axis.
            """
            return self._sensor_dimensions.x_sampling

        @x_sampling.setter
        def x_sampling(self, value: int):
            """Set sampling along X axis."""
            self._sensor_dimensions.x_sampling = value

        @property
        def y_start(self) -> float:
            """Minimum value on Y axis (mm).

            Parameters
            ----------
            value : float
                Minimum y coordinate in millimeters.

            Returns
            -------
            float
                Minimum y coordinate in millimeters.
            """
            return self._sensor_dimensions.y_start

        @y_start.setter
        def y_start(self, value: float):
            """Set minimum value on Y axis."""
            self._sensor_dimensions.y_start = value

        @property
        def y_end(self) -> float:
            """Maximum value on Y axis (mm).

            Parameters
            ----------
            value : float
                Maximum y coordinate in millimeters.

            Returns
            -------
            float
                Maximum y coordinate in millimeters.
            """
            return self._sensor_dimensions.y_end

        @y_end.setter
        def y_end(self, value: float):
            """Set maximum value on Y axis."""
            self._sensor_dimensions.y_end = value

        @property
        def y_sampling(self) -> int:
            """Sampling along Y axis (pixels).

            Parameters
            ----------
            value : int
                Number of samples along the Y axis.

            Returns
            -------
            int
                Number of samples along the Y axis.
            """
            return self._sensor_dimensions.y_sampling

        @y_sampling.setter
        def y_sampling(self, value: int):
            """Set sampling along Y axis."""
            self._sensor_dimensions.y_sampling = value

    class Colorimetric:
        """Class computing the color results.

        Result without any spectral layer separation.

        Parameters
        ----------
        sensor_type_colorimetric : ansys.api.speos.sensor.v1.common_pb2.SensorTypeColorimetric
            SensorTypeColorimetric protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.ColorimetricParameters] = None
            If defined the values in the sensor instance will be overwritten by the values of the
            data class
        stable_ctr : bool, optional
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_colorimetric: common_pb2.SensorTypeColorimetric,
            default_parameters: Optional[ColorimetricParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Colorimetric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Attribute to keep track of wavelength range object

            self._wavelengths_range = BaseSensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_colorimetric.wavelengths_range,
                default_parameters=default_parameters.wavelength_range
                if default_parameters
                else None,
                stable_ctr=stable_ctr,
            )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Return the wavelengths range helper for this colorimetric sensor.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range helper object.
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
        """Class computing the spectral data in a separated way.

        This class allows to define specific parameters for spectral data retrieval.

        Parameters
        ----------
        sensor_type_spectral : ansys.api.speos.sensor.v1.common_pb2.SensorTypeSpectral
            SensorTypeSpectral protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.SpectralParameters] = None
            If defined the values in the sensor instance will be overwritten by the values of
            the data class
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_spectral method available in
        sensor classes.
        """

        def __init__(
            self,
            sensor_type_spectral: sensor_pb2.SensorTypeSpectral,
            default_parameters: Optional[SpectralParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Spectral class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_spectral = sensor_type_spectral

            # Attribute to keep track of wavelength range object

            self._wavelengths_range = BaseSensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_spectral.wavelengths_range,
                default_parameters=default_parameters.wavelength_range
                if default_parameters
                else None,
                stable_ctr=stable_ctr,
            )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Return the wavelengths range helper for this spectral sensor.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range helper object.
            """
            if (
                self._wavelengths_range._wavelengths_range
                is not self._sensor_type_spectral.wavelengths_range
            ):
                # Happens in case of feature reset (to be sure to always modify correct data)
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
        geometries : List[ansys.speos.core.geo_ref.GeoRef]
            List of geometries included in this layer.
        """

        def __init__(self, name: str, geometries: List[GeoRef]) -> None:
            self.name = name
            """Name of the layer"""
            self.geometry = geometries

        @property
        def geometry(self):
            """List of geometries included in this layer.

            Parameters
            ----------
            value : Optional[List[Union[ansys.speos.core.geo_ref.GeoRef,
                ansys.speos.core.body.Body, ansys.speos.core.face.Face,
                ansys.speos.core.part.Part.SubPart]]]
                List of geometry references (GeoRef, Face, Body or SubPart). Each
                entry is converted to a GeoRef internal representation.

            Returns
            -------
            List[ansys.speos.core.geo_ref.GeoRef]
                List of geometries contained in the FaceLayer group.
            """
            return self._geometry

        @geometry.setter
        def geometry(
            self, value: Optional[List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]]
        ):
            """Set geometries for this face layer."""
            geo_paths = []
            for gr in value:
                if isinstance(gr, GeoRef):
                    geo_paths.append(gr)
                elif isinstance(gr, (face.Face, body.Body, part.Part.SubPart)):
                    geo_paths.append(gr.geo_path)
            self._geometry = geo_paths

    class LayerTypeFace:
        """Layer separation by face configuration.

        Produces one layer per selected face. Default filtering is "last impact".

        Parameters
        ----------
        layer_type_face : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeFace
            LayerTypeFace protobuf object to modify.
        default_parameters : ansys.speos.core.generic.parameters.LayerByFaceParameters, optional
            If defined the values in the sensor instance will be overwritten by the values of the
            data class
        stable_ctr : bool, optional
            Internal flag to prevent external instantiation.
        """

        def __init__(
            self,
            layer_type_face: ProtoScene.SensorInstance.LayerTypeFace,
            default_parameters: Optional[LayerByFaceParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeFace class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_face = layer_type_face
            self._fill_parameters(default_parameters)

        def _fill_parameters(
            self, default_parameters: Optional[LayerByFaceParameters] = None
        ) -> None:
            if not default_parameters:
                return
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
            """Set the SCA filtering mode to IntersectedOneTime.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace
                Self to allow chaining.
            """
            self._layer_type_face.sca_filtering_mode = (
                self._layer_type_face.EnumSCAFilteringType.IntersectedOneTime
            )
            return self

        def set_sca_filtering_mode_last_impact(
            self,
        ) -> BaseSensor.LayerTypeFace:
            """Set the SCA filtering mode to LastImpact.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace
                Self to allow chaining.
            """
            self._layer_type_face.sca_filtering_mode = (
                self._layer_type_face.EnumSCAFilteringType.LastImpact
            )
            return self

        @property
        def layers(self) -> List[BaseSensor.FaceLayer]:
            """List of face layers for this sensor.

            Parameters
            ----------
            values : list[ansys.speos.core.sensor.BaseSensor.FaceLayer]
                List of FaceLayer objects to assign.

            Returns
            -------
            List[ansys.speos.core.sensor.BaseSensor.FaceLayer]
                Layers currently configured for this layer type.
            """
            layer_data = []
            for layer in self._layer_type_face.layers:
                if isinstance(layer.geometries, list):
                    layer_data.append(BaseSensor.FaceLayer(layer.name, layer.geometries))
                else:
                    layer_data.append(BaseSensor.FaceLayer(layer.name, [layer.geometries]))
            return layer_data

        @layers.setter
        def layers(self, values: list[BaseSensor.FaceLayer]):
            """Set list of layers."""
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
        """Layer separation by sequence configuration.

        Produces one layer per sequence. The sequence can be created per face or per
        geometry.

        Parameters
        ----------
        layer_type_sequence : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeSequence
            LayerTypeSequence protobuf object to modify.
        default_parameters : ansys.speos.core.generic.parameters.LayerBySequenceParameters, optional
            If defined the values in the sensor instance will be overwritten by the values of the
            data class
        stable_ctr : bool, optional
            Internal flag to prevent external instantiation.
        """

        def __init__(
            self,
            layer_type_sequence: ProtoScene.SensorInstance.LayerTypeSequence,
            default_parameters: Optional[LayerBySequenceParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeSequence class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_sequence = layer_type_sequence
            self._fill_parameters(default_parameters)

        def _fill_parameters(
            self, default_parameters: Optional[LayerBySequenceParameters] = None
        ) -> None:
            if not default_parameters:
                return
            self.maximum_nb_of_sequence = default_parameters.maximum_nb_of_sequence
            match default_parameters.sequence_type:
                case "by_face":
                    self.set_define_sequence_per_faces()
                case "by_geometry":
                    self.set_define_sequence_per_geometries()

        @property
        def maximum_nb_of_sequence(self) -> int:
            """Maximum number of sequences.

            Parameters
            ----------
            value : int
                Maximum number of sequences to allow.

            Returns
            -------
            int
                Maximum allowed number of sequences.
            """
            return self._layer_type_sequence.maximum_nb_of_sequence

        @maximum_nb_of_sequence.setter
        def maximum_nb_of_sequence(self, value: int) -> None:
            """Set maximum number of sequences."""
            self._layer_type_sequence.maximum_nb_of_sequence = value

        def set_define_sequence_per_geometries(
            self,
        ) -> BaseSensor.LayerTypeSequence:
            """Define sequences per geometry (rather than per face).

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
                Self to allow chaining.
            """
            self._layer_type_sequence.define_sequence_per = (
                self._layer_type_sequence.EnumSequenceType.Geometries
            )
            return self

        def set_define_sequence_per_faces(self) -> BaseSensor.LayerTypeSequence:
            """Define sequences per face.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
                Self to allow chaining.
            """
            self._layer_type_sequence.define_sequence_per = (
                self._layer_type_sequence.EnumSequenceType.Faces
            )
            return self

    class LayerTypeIncidenceAngle:
        """Layer separation by incidence angle.

        Produces one layer per incident angle range.

        Parameters
        ----------
        layer_type_incidence_angle : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeIncidenceAngle
            LayerTypeIncidenceAngle protobuf object to modify.
        default_parameters : ansys.speos.core.generic.parameters.LayerByIncidenceAngleParameters,\
optional
            If defined the values in the sensor instance will be overwritten by the values of the
            data class
        stable_ctr : bool, optional
            Internal flag to prevent external instantiation.
        """

        def __init__(
            self,
            layer_type_incidence_angle: ProtoScene.SensorInstance.LayerTypeIncidenceAngle,
            default_parameters: Optional[LayerByIncidenceAngleParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeIncidenceAngle class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_incidence_angle = layer_type_incidence_angle
            self._fill_parameters(default_parameters)

        def _fill_parameters(
            self, default_parameters: Optional[LayerByIncidenceAngleParameters] = None
        ) -> None:
            if not default_parameters:
                return
            self.sampling = default_parameters.incidence_sampling

        @property
        def sampling(self) -> int:
            """Sampling for incidence angles.

            Parameters
            ----------
            value : int
                Sampling value for incidence angles.

            Returns
            -------
            int
                Sampling used to split the incidence angle range.
            """
            return self._layer_type_incidence_angle.sampling

        @sampling.setter
        def sampling(self, value: int):
            """Set sampling for incidence angles."""
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
        key : str, optional
            If provided, search keys that start with `key` and return the best match.
            By default, ``""`` which returns the full dictionary.

        Returns
        -------
        str | dict
            Full sensor dictionary or the value corresponding to the best-matching key.
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
        """Return the string representation of the sensor.

        Returns
        -------
        str
            Human readable string with local or remote indicator and sensor contents.
        """
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
        """Save feature: send the local data to the Speos server database.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            The sensor instance after commit.
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
        """Reset local data from the Speos server database.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            The sensor instance after reset.
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
        """Delete feature from the Speos server database.

        Local data remain available until discarded.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor
            The sensor instance after deletion (local only).
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

    Camera sensor supporting photometric (color/monochrome) and geometric modes.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature. By default, ``{}``.
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from
        scratch. By default, ``None``.
    default_parameters : ansys.speos.core.generic.parameters.CameraSensorParameters, optional
        Optional default values to initialize the camera.
    """

    class Photometric:
        """Photometric camera mode and helpers.

        This class wraps photometric-specific parameters (color/monochrome modes,
        gamma, transmittance, PNG bit depth, wavelength range, layer type, etc.).

        Parameters
        ----------
        mode_photometric : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraModePhotometric
            Photometric mode protobuf to modify.
        camera_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.CameraProperties
            Per-instance camera properties.
        default_parameters : ansys.speos.core.generic.parameters.PhotometricCameraParameters,\
optional
            Optional defaults.
        stable_ctr : bool, optional
            Internal flag to prevent external instantiation.
        """

        class Color:
            """Color photometric sub-mode and balance mode helpers.

            Parameters
            ----------
            mode_color : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraColorModeColor
                Camera Color mode protobuf object to modify.
            default_parameters : ansys.speos.core.generic.parameters.ColorParameters, optional
                Optional defaults for the color mode.
            stable_ctr : bool, optional
                Internal flag to prevent external instantiation.
            """

            class BalanceModeUserWhite:
                """User-specified white balance mode.

                Parameters
                ----------
                balance_mode_user_white :\
                ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraBalanceModeUserwhite
                    Protobuf object to modify.
                default_parameters :\
                ansys.speos.core.generic.parameters.BalanceModeUserWhiteParameters, optional
                    Optional defaults.
                stable_ctr : bool, optional
                    Internal flag to prevent external instantiation.
                """

                def __init__(
                    self,
                    balance_mode_user_white: camera_sensor_pb2.SensorCameraBalanceModeUserwhite,
                    default_parameters: Optional[BalanceModeUserWhiteParameters] = None,
                    stable_ctr: bool = False,
                ) -> None:
                    if not stable_ctr:
                        msg = "BalanceModeUserWhite class instantiated outside of class scope"
                        raise RuntimeError(msg)
                    self._balance_mode_user_white = balance_mode_user_white
                    self._fill_parameters(default_parameters)

                def _fill_parameters(
                    self, default_parameters: Optional[BalanceModeUserWhiteParameters] = None
                ) -> None:
                    if not default_parameters:
                        return
                    self._balance_mode_user_white.SetInParent()
                    self.red_gain = default_parameters.red_gain
                    self.green_gain = default_parameters.green_gain
                    self.blue_gain = default_parameters.blue_gain

                @property
                def red_gain(self) -> float:
                    """Red channel gain.

                    Parameters
                    ----------
                    value : float
                        Red gain coefficient.

                    Returns
                    -------
                    float
                        Red gain coefficient.
                    """
                    return self._balance_mode_user_white.red_gain

                @red_gain.setter
                def red_gain(self, value: float) -> None:
                    """Set red channel gain."""
                    self._balance_mode_user_white.red_gain = value

                @property
                def green_gain(self) -> float:
                    """Green channel gain.

                    Parameters
                    ----------
                    value : float
                        Green gain coefficient.

                    Returns
                    -------
                    float
                        Green gain coefficient.
                    """
                    return self._balance_mode_user_white.green_gain

                @green_gain.setter
                def green_gain(self, value: float) -> None:
                    """Set green channel gain."""
                    self._balance_mode_user_white.green_gain = value

                @property
                def blue_gain(self) -> float:
                    """Blue channel gain.

                    Parameters
                    ----------
                    value : float
                        Blue gain coefficient.

                    Returns
                    -------
                    float
                        Blue gain coefficient.
                    """
                    return self._balance_mode_user_white.blue_gain

                @blue_gain.setter
                def blue_gain(self, value: float) -> None:
                    """Set blue channel gain."""
                    self._balance_mode_user_white.blue_gain = value

            class BalanceModeDisplayPrimaries:
                """Display primaries balance mode.

                Parameters
                ----------
                balance_mode_display :\
                ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraBalanceModeDisplay
                    Protobuf object to modify.
                default_parameters :\
                ansys.speos.core.generic.parameters.BalanceModeDisplayPrimariesParameters, optional
                    Optional defaults.
                stable_ctr : bool, optional
                    Internal flag to prevent external instantiation.
                """

                def __init__(
                    self,
                    balance_mode_display: camera_sensor_pb2.SensorCameraBalanceModeDisplay,
                    default_parameters: Optional[BalanceModeDisplayPrimariesParameters] = None,
                    stable_ctr: bool = False,
                ) -> None:
                    if not stable_ctr:
                        msg = (
                            "BalanceModeDisplayPrimaries class instantiated outside of class scope"
                        )
                        raise RuntimeError(msg)

                    self._balance_mode_display = balance_mode_display
                    self._fill_parameters(default_parameters)

                def _fill_parameters(
                    self,
                    default_parameters: Optional[BalanceModeDisplayPrimariesParameters] = None,
                ) -> None:
                    if not default_parameters:
                        return
                    self._balance_mode_display.SetInParent()
                    if default_parameters.red_display_file_uri:
                        self.red_display_file_uri = default_parameters.red_display_file_uri
                    if default_parameters.green_display_file_uri:
                        self.green_display_file_uri = default_parameters.green_display_file_uri
                    if default_parameters.blue_display_file_uri:
                        self.blue_display_file_uri = default_parameters.blue_display_file_uri

                @property
                def red_display_file_uri(self) -> str:
                    """Location of the red display file.

                    Parameters
                    ----------
                    uri : Union[str, pathlib.Path]
                        Red display file.

                    Returns
                    -------
                    str
                        Red display file path or URI.
                    """
                    return self._balance_mode_display.red_display_file_uri

                @red_display_file_uri.setter
                def red_display_file_uri(self, uri: Union[str, Path]) -> None:
                    """Set red display file path."""
                    self._balance_mode_display.red_display_file_uri = str(Path(uri))

                @property
                def green_display_file_uri(self) -> str:
                    """Location of the green display file.

                    Parameters
                    ----------
                    uri : Union[str, pathlib.Path]
                        Green display file.

                    Returns
                    -------
                    str
                        Green display file path or URI.
                    """
                    return self._balance_mode_display.green_display_file_uri

                @green_display_file_uri.setter
                def green_display_file_uri(self, uri: Union[str, Path]) -> None:
                    """Set green display file path."""
                    self._balance_mode_display.green_display_file_uri = str(Path(uri))

                @property
                def blue_display_file_uri(self) -> str:
                    """Location of the blue display file.

                    Parameters
                    ----------
                    uri : Union[str, pathlib.Path]
                        Blue display file.

                    Returns
                    -------
                    str
                        Blue display file path or URI.
                    """
                    return self._balance_mode_display.blue_display_file_uri

                @blue_display_file_uri.setter
                def blue_display_file_uri(self, uri: Union[str, Path]) -> None:
                    """Set blue display file path."""
                    self._balance_mode_display.blue_display_file_uri = str(Path(uri))

            def __init__(
                self,
                mode_color: camera_sensor_pb2.SensorCameraColorModeColor,
                default_parameters: Optional[ColorParameters] = None,
                stable_ctr: bool = False,
            ) -> None:
                if not stable_ctr:
                    msg = "Color class instantiated outside of class scope"
                    raise RuntimeError(msg)
                self._mode_color = mode_color

                # Attribute gathering more complex camera balance mode
                self._mode = None
                self._fill_parameters(default_parameters)

            def _fill_parameters(
                self, default_parameters: Optional[ColorParameters] = None
            ) -> None:
                if not default_parameters:
                    return
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
                elif default_parameters.balance_mode == ColorBalanceModeTypes.grey_world:
                    self.set_balance_mode_grey_world()
                elif default_parameters.balance_mode == ColorBalanceModeTypes.none:
                    self.set_balance_mode_none()
                if default_parameters.red_spectrum_file_uri:
                    self.red_spectrum_file_uri = default_parameters.red_spectrum_file_uri
                if default_parameters.green_spectrum_file_uri:
                    self.green_spectrum_file_uri = default_parameters.green_spectrum_file_uri
                if default_parameters.blue_spectrum_file_uri:
                    self.blue_spectrum_file_uri = default_parameters.blue_spectrum_file_uri

            @property
            def red_spectrum_file_uri(self) -> str:
                """Location of the red spectrum file.

                Returns
                -------
                str
                    Red spectrum file path (usually ``.spectrum``).
                """
                return self._mode_color.red_spectrum_file_uri

            @red_spectrum_file_uri.setter
            def red_spectrum_file_uri(self, uri: Union[str, Path]) -> None:
                """Set the red spectrum file path.

                Parameters
                ----------
                uri : Union[str, pathlib.Path]
                    Red spectrum file.
                """
                self._mode_color.red_spectrum_file_uri = str(Path(uri))

            @property
            def blue_spectrum_file_uri(self) -> str:
                """Location of the blue spectrum file.

                Returns
                -------
                str
                    Blue spectrum file path.
                """
                return self._mode_color.blue_spectrum_file_uri

            @blue_spectrum_file_uri.setter
            def blue_spectrum_file_uri(self, uri: Union[str, Path]) -> None:
                """Set the blue spectrum file path.

                Parameters
                ----------
                uri : Union[str, pathlib.Path]
                    Blue spectrum file.
                """
                self._mode_color.blue_spectrum_file_uri = str(Path(uri))

            @property
            def green_spectrum_file_uri(self) -> str:
                """Location of the green spectrum file.

                Returns
                -------
                str
                    Green spectrum file path.
                """
                return self._mode_color.green_spectrum_file_uri

            @green_spectrum_file_uri.setter
            def green_spectrum_file_uri(self, uri: Union[str, Path]) -> None:
                """Set the green spectrum file path.

                Parameters
                ----------
                uri : Union[str, pathlib.Path]
                    Green spectrum file.
                """
                self._mode_color.green_spectrum_file_uri = str(Path(uri))

            def set_balance_mode_none(self) -> SensorCamera.Photometric.Color:
                """Use basic conversion (no white balance).

                The spectral transmittance of the optical system and the spectral sensitivity for
                each channel are applied to the detected spectral image before the conversion in
                a three-channel result. This method is referred to as the basic conversion.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color
                    Color mode instance.
                """
                self._mode = None
                self._mode_color.balance_mode_none.SetInParent()
                return self

            def set_balance_mode_grey_world(
                self,
            ) -> SensorCamera.Photometric.Color:
                """Use grey-world white balance.

                The grey world assumption states that the content of the image is grey on average.
                This method converts spectral results in a three-channel result with the basic
                conversion. Then it computes and applies coefficients to the red, green and blue
                images to make sure their averages are equal.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color
                    Color mode instance.
                """
                self._mode = None
                self._mode_color.balance_mode_greyworld.SetInParent()
                return self

            def set_balance_mode_user_white(
                self,
            ) -> SensorCamera.Photometric.Color.BalanceModeUserWhite:
                """Select user-white balance mode and return helper.

                In addition to the basic treatment, it allows to apply specific coefficients to the
                red, green, blue images

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color.BalanceModeUserWhite
                    Helper to modify user-white gains.
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
                """Select display-primaries balance mode and return helper.

                Spectral results are converted in a three-channel result.
                Then a post-treatment is realized to take the distortion induced by the display
                devices into account. With this method, displayed results are similar to what the
                camera really gets.

                Returns
                -------
                ansys.speos.core.sensor.SensorCamera.Photometric.Color.BalanceModeDisplayPrimaries
                    Helper for display primaries configuration.
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
            default_parameters: Optional[PhotometricCameraParameters] = None,
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
            self._fill_parameters(default_parameters, stable_ctr)

        def _fill_parameters(
            self,
            default_parameters: Optional[PhotometricCameraParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if default_parameters:
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
                return

            self._wavelengths_range = SensorCamera.WavelengthsRange(
                wavelengths_range=self._mode_photometric.wavelengths_range,
                default_parameters=None,
                stable_ctr=stable_ctr,
            )

        @property
        def acquisition_integration(self) -> float:
            """Acquisition integration time (s).

            Returns
            -------
            float
                Integration time in seconds.
            """
            return self._mode_photometric.acquisition_integration

        @acquisition_integration.setter
        def acquisition_integration(self, value: float) -> None:
            """Set acquisition integration time.

            Parameters
            ----------
            value : float
                Integration time in seconds.
            """
            self._mode_photometric.acquisition_integration = value

        @property
        def acquisition_lag_time(self) -> float:
            """Acquisition lag time (s).

            Returns
            -------
            float
                Acquisition lag time in seconds.
            """
            return self._mode_photometric.acquisition_lag_time

        @acquisition_lag_time.setter
        def acquisition_lag_time(self, value: float) -> None:
            """Set acquisition lag time.

            Parameters
            ----------
            value : float
                Acquisition lag time in seconds.
            """
            self._mode_photometric.acquisition_lag_time = value

        @property
        def transmittance_file_uri(self) -> str:
            """Transmittance spectrum file path or URI.

            Returns
            -------
            str
                Transmittance spectrum file path (``.spectrum``).
            """
            return self._mode_photometric.transmittance_file_uri

        @transmittance_file_uri.setter
        def transmittance_file_uri(self, uri: Union[str, Path]) -> None:
            """Set transmittance spectrum file.

            Parameters
            ----------
            uri : Union[str, pathlib.Path]
                Spectrum file used to represent the optical transmittance.
            """
            self._mode_photometric.transmittance_file_uri = str(Path(uri))

        @property
        def gamma_correction(self) -> float:
            """Gamma correction value.

            Returns
            -------
            float
                Gamma correction factor.
            """
            return self._mode_photometric.gamma_correction

        @gamma_correction.setter
        def gamma_correction(self, value: float) -> None:
            """Set gamma correction factor.

            Parameters
            ----------
            value : float
                Gamma correction factor to apply.
            """
            self._mode_photometric.gamma_correction = value

        def set_png_bits_08(self) -> SensorCamera.Photometric:
            """Use 8-bit PNG export."""
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
            return self

        def set_png_bits_10(self) -> SensorCamera.Photometric:
            """Use 10-bit PNG export."""
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
            return self

        def set_png_bits_12(self) -> SensorCamera.Photometric:
            """Use 12-bit PNG export."""
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
            return self

        def set_png_bits_16(self) -> SensorCamera.Photometric:
            """Use 16-bit PNG export."""
            self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
            return self

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Return the wavelengths range helper for the photometric camera.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Wavelengths range helper object.
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
            """Set monochromatic (grayscale) mode using a spectrum file.

            Parameters
            ----------
            spectrum_file_uri : Union[str, pathlib.Path]
                Spectrum file URI to use for monochromatic sensitivity.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric
                Photometric mode instance.
            """
            self._mode = None
            self._mode_photometric.color_mode_monochromatic.spectrum_file_uri = str(
                Path(spectrum_file_uri)
            )
            return self

        def set_mode_color(self) -> SensorCamera.Photometric.Color:
            """Set photometric color mode and return helper.

            Returns
            -------
            ansys.speos.core.sensor.SensorCamera.Photometric.Color
                Color mode helper instance.
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
            """Trajectory file path or URI.

            Returns
            -------
            str
                Trajectory file used to animate the camera pose.
            """
            return self._camera_props.trajectory_file_uri

        @trajectory_file_uri.setter
        def trajectory_file_uri(self, uri: Union[str, Path]) -> None:
            """Set the trajectory file path.

            Parameters
            ----------
            uri : Union[str, pathlib.Path]
                Trajectory file used to define camera pose over time.
            """
            self._camera_props.trajectory_file_uri = str(Path(uri))

        def set_layer_type_none(self) -> SensorCamera.Photometric:
            """Disable layer separation (single-layer results)."""
            self._camera_props.layer_type_none.SetInParent()
            return self

        def set_layer_type_source(self) -> SensorCamera.Photometric:
            """Enable layer separation by source (one layer per active source)."""
            self._camera_props.layer_type_source.SetInParent()
            return self

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Optional[CameraSensorParameters] = None,
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
        self._fill_parameters(default_parameters)

    def _fill_parameters(self, default_parameters: Optional[CameraSensorParameters] = None) -> None:
        if not default_parameters:
            return
        if isinstance(default_parameters.sensor_type_parameters, PhotometricCameraParameters):
            self._type = SensorCamera.Photometric(
                mode_photometric=self._sensor_template.camera_sensor_template.sensor_mode_photometric,
                camera_props=self._sensor_instance.camera_properties,
                default_parameters=default_parameters.sensor_type_parameters,
                stable_ctr=True,
            )
        else:
            self.set_mode_geometric()
        if default_parameters.distortion_file_uri:
            self.distortion_file_uri = default_parameters.distortion_file_uri
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
        """Visual geometry for camera sensor for visualization tools.

        Returns
        -------
        ansys.speos.core.generic.visualization_methods._VisualData
            Visual data helper instance describing geometry and axis system.
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
        """Photometric helper instance when camera is in photometric mode.

        Returns
        -------
        Union[ansys.speos.core.sensor.SensorCamera.Photometric, None]
            Photometric helper instance or None if camera is geometric.
        """
        return self._type

    @property
    def focal_length(self) -> float:
        """Focal length of the optical system (mm).

        Returns
        -------
        float
            Distance between the center of the optical system and the focus in mm.
        """
        return self._sensor_template.camera_sensor_template.focal_length

    @focal_length.setter
    def focal_length(self, value: float) -> None:
        """Set focal length.

        Parameters
        ----------
        value : float
            Focal length in millimeters.
        """
        self._sensor_template.camera_sensor_template.focal_length = value

    @property
    def imager_distance(self) -> float:
        """Imager distance (mm).

        Returns
        -------
        float
            Distance from optical center to imager in millimeters.
        """
        return self._sensor_template.camera_sensor_template.imager_distance

    @imager_distance.setter
    def imager_distance(self, value: float) -> None:
        """Set imager distance.

        Parameters
        ----------
        value : float
            Imager distance in millimeters.
        """
        self._sensor_template.camera_sensor_template.imager_distance = value

    @property
    def f_number(self) -> float:
        """F-number (aperture) of the optical system.

        Returns
        -------
        float
            F-number (unitless).
        """
        return self._sensor_template.camera_sensor_template.f_number

    @f_number.setter
    def f_number(self, value: float = 20) -> None:
        """Set F-number.

        Parameters
        ----------
        value : float
            F-number to set.
        """
        self._sensor_template.camera_sensor_template.f_number = value

    @property
    def distortion_file_uri(self) -> str:
        """Distortion file path or URI (optical aberration definition).

        Returns
        -------
        str
            Distortion definition file path (``.OPTDistortion``).
        """
        return self._sensor_template.camera_sensor_template.distortion_file_uri

    @distortion_file_uri.setter
    def distortion_file_uri(self, uri: Union[str, Path]) -> None:
        """Set distortion file path.

        Parameters
        ----------
        uri : Union[str, pathlib.Path]
            Distortion file URI (``.OPTDistortion``).
        """
        self._sensor_template.camera_sensor_template.distortion_file_uri = str(Path(uri))

    @property
    def horz_pixel(self) -> int:
        """Horizontal pixel count of the camera.

        Returns
        -------
        int
            Horizontal pixel resolution.
        """
        return self._sensor_template.camera_sensor_template.horz_pixel

    @horz_pixel.setter
    def horz_pixel(self, value: int) -> None:
        """Set horizontal pixel count.

        Parameters
        ----------
        value : int
            Horizontal pixel resolution.
        """
        self._sensor_template.camera_sensor_template.horz_pixel = value

    @property
    def vert_pixel(self) -> int:
        """Vertical pixel count of the camera.

        Returns
        -------
        int
            Vertical pixel resolution.
        """
        return self._sensor_template.camera_sensor_template.vert_pixel

    @vert_pixel.setter
    def vert_pixel(self, value: int) -> None:
        """Set vertical pixel count.

        Parameters
        ----------
        value : int
            Vertical pixel resolution.
        """
        self._sensor_template.camera_sensor_template.vert_pixel = value

    @property
    def width(self) -> float:
        """Sensor imager width (mm).

        Returns
        -------
        float
            Width of the imager in millimeters.
        """
        return self._sensor_template.camera_sensor_template.width

    @width.setter
    def width(self, value: float) -> None:
        """Set imager width.

        Parameters
        ----------
        value : float
            Width in millimeters.
        """
        self._sensor_template.camera_sensor_template.width = value

    @property
    def height(self) -> float:
        """Sensor imager height (mm).

        Returns
        -------
        float
            Height of the imager in millimeters.
        """
        return self._sensor_template.camera_sensor_template.height

    @height.setter
    def height(self, value: float) -> None:
        """Set imager height.

        Parameters
        ----------
        value : float
            Height in millimeters.
        """
        self._sensor_template.camera_sensor_template.height = value

    @property
    def axis_system(self) -> List[float]:
        """The position and orientation of the sensor as a 12-element axis system.

        Returns
        -------
        List[float]
            Position and orientation as [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._sensor_instance.camera_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: List[float]) -> None:
        """Set the sensor axis system.

        Parameters
        ----------
        axis_system : List[float]
            Axis system value [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        self._sensor_instance.camera_properties.axis_system[:] = axis_system

    def set_mode_geometric(self) -> SensorCamera:
        """Set camera to geometric (simplified) mode.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera
            Self for chaining.
        """
        self._type = None
        self._sensor_template.camera_sensor_template.sensor_mode_geometric.SetInParent()
        return self

    def set_mode_photometric(self) -> SensorCamera.Photometric:
        """Set camera to photometric (full) mode and return helper.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera.Photometric
            Photometric helper instance.
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
        """Save the camera; handle known server-side constraints with distortion files.

        Returns
        -------
        ansys.speos.core.sensor.SensorCamera
            Camera instance after commit.
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

    Planar/radial/hemispherical/cylindrical irradiance sensor supporting
    photometric, radiometric, colorimetric and spectral modes and layer
    separation.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature. By default, ``{}``.
    sensor_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance, optional
        Sensor instance to provide if the feature does not has to be created from
        scratch. By default, ``None``.
    default_parameters : ansys.speos.core.generic.parameters.IrradianceSensorParameters, optional
        Optional defaults to initialize irradiance sensor.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Optional[IrradianceSensorParameters] = None,
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
        self._fill_parameters(default_parameters)

    def _fill_parameters(
        self, default_parameters: Optional[IrradianceSensorParameters] = None
    ) -> None:
        if default_parameters:
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
            elif default_parameters.sensor_type == SensorTypes.radiometric:
                self.set_type_radiometric()
            elif default_parameters.sensor_type == SensorTypes.photometric:
                self.set_type_photometric()

            match default_parameters.integration_type:
                case IntegrationTypes.planar:
                    self.set_illuminance_type_planar()
                    self.integration_direction = default_parameters.integration_direction
                case IntegrationTypes.radial:
                    self.set_illuminance_type_radial()
                case IntegrationTypes.hemispherical:
                    self.set_illuminance_type_hemispherical()
                case IntegrationTypes.cylindrical:
                    self.set_illuminance_type_cylindrical()
                case IntegrationTypes.semi_cylindrical:
                    self.set_illuminance_type_semi_cylindrical()
                    self.integration_direction = default_parameters.integration_direction

            match default_parameters.rayfile_type:
                case RayfileTypes.none:
                    self.set_ray_file_type_none()
                case RayfileTypes.classic:
                    self.set_ray_file_type_classic()
                case RayfileTypes.polarization:
                    self.set_ray_file_type_polarization()
                case RayfileTypes.tm25:
                    self.set_ray_file_type_tm25()
                case RayfileTypes.tm25_no_polarization:
                    self.set_ray_file_type_tm25_no_polarization()

            if default_parameters.layer_type == LayerTypes.none:
                self.set_layer_type_none()
            elif default_parameters.layer_type == LayerTypes.by_source:
                self.set_layer_type_source()
            elif default_parameters.layer_type == LayerTypes.by_polarization:
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

            self.axis_system = default_parameters.axis_system
            self.output_face_geometries = default_parameters.outpath_face_geometry
            return

        self._sensor_dimensions = self.Dimensions(
            sensor_dimensions=self._sensor_template.irradiance_sensor_template.dimensions,
            default_parameters=None,
            stable_ctr=True,
        )
        template = self._sensor_template.irradiance_sensor_template
        if template.HasField("sensor_type_photometric"):
            self.set_type_photometric()
        elif template.HasField("sensor_type_colorimetric"):
            self.set_type_colorimetric()
        elif template.HasField("sensor_type_radiometric"):
            self.set_type_radiometric()
        elif template.HasField("sensor_type_spectral"):
            self.set_type_spectral()
        properties = self._sensor_instance.irradiance_properties
        if properties.HasField("layer_type_none"):
            self._layer_type = LayerTypes.none
        elif properties.HasField("layer_type_source"):
            self._layer_type = LayerTypes.by_source
        elif properties.HasField("layer_type_polarization"):
            self._layer_type = LayerTypes.by_polarization
        elif properties.HasField("layer_type_incidence_angle"):
            self.set_layer_type_incidence_angle()
        elif properties.HasField("layer_type_sequence"):
            self.set_layer_type_sequence()
        elif properties.HasField("layer_type_face"):
            self.set_layer_type_face()

    @property
    def visual_data(self) -> _VisualData:
        """Visual geometry for irradiance sensor.

        Returns
        -------
        ansys.speos.core.generic.visualization_methods._VisualData
            Visual data helper instance describing geometry and axis system.
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
        """Dimensions helper for irradiance sensor.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimensions helper instance.
        """
        return self._sensor_dimensions

    @property
    def type(self) -> str:
        """Sensor type as string.

        Returns
        -------
        str
            Sensor type (e.g. "Colorimetric", "Spectral", "Photometric", "Radiometric").
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
        """Colorimetric helper when sensor is colorimetric.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Colorimetric]
            Colorimetric helper instance or ``None``.
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return self._type

    @property
    def spectral(self) -> Union[None, BaseSensor.Spectral]:
        """Spectral helper when sensor is spectral.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Spectral]
            Spectral helper instance or ``None``.
        """
        if isinstance(self._type, BaseSensor.Spectral):
            return self._type

    @property
    def layer(
        self,
    ) -> Union[
        LayerTypes,
        BaseSensor.LayerTypeFace,
        BaseSensor.LayerTypeSequence,
        BaseSensor.LayerTypeIncidenceAngle,
    ]:
        """Property containing all options in regard to the layer separation properties.

        Returns
        -------
        Union[\
            None,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence,\
            ansys.speos.core.sensor.BaseSensor.LayerTypeIncidenceAngle\
        ]
            Instance of Layertype Class for this sensor feature
        """
        return self._layer_type

    def set_dimensions(self) -> BaseSensor.Dimensions:
        """Return the current dimensions helper bound to the template.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimensions instance.
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
        """Select photometric sensor type (visible spectrum -> lx / lm/m2)."""
        self._sensor_template.irradiance_sensor_template.sensor_type_photometric.SetInParent()
        self._type = SensorTypes.photometric.capitalize()
        return self

    def set_type_colorimetric(self) -> BaseSensor.Colorimetric:
        """Select colorimetric sensor type and return helper."""
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
        """Select radiometric sensor type (full spectrum -> W/m2)."""
        self._sensor_template.irradiance_sensor_template.sensor_type_radiometric.SetInParent()
        self._type = SensorTypes.radiometric.capitalize()
        return self

    def set_type_spectral(self) -> BaseSensor.Spectral:
        """Select spectral sensor type and return helper."""
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
        """Integration direction for planar/semi-cylindrical illuminance sensors.

        Returns
        -------
        List[float]
            Sensor global integration direction as [x, y, z]. If not set, Z axis
            of the axis_system is used.

        Notes
        -----
        Contrary to any visualization of integration directions within Speos Software or its
        documentation the integration direction must be set in the anti-rays direction to integrate
        their signal.
        Integration direction is only settable for sensor template with IlluminanceTypePlanar or
        IlluminanceTypeSemiCylindrical as illuminance_type
        """
        return self._sensor_instance.irradiance_properties.integration_direction

    @integration_direction.setter
    def integration_direction(self, value: List[float]) -> None:
        """Set integration direction for the sensor.

        Parameters
        ----------
        value : List[float]
            Integration direction [x, y, z]. If falsy the field will be cleared.

        Raises
        ------
        TypeError
            If the sensor template is not planar or semi-cylindrical.
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
        """Select planar illuminance integration and clear integration_direction.

        Returns
        -------
        ansys.speos.core.sensor.SensorIrradiance
            Self for chaining.
        """
        self._sensor_template.irradiance_sensor_template.illuminance_type_planar.SetInParent()
        self._sensor_instance.irradiance_properties.ClearField("integration_direction")
        return self

    def set_illuminance_type_radial(self) -> SensorIrradiance:
        """Select radial illuminance integration."""
        self._sensor_template.irradiance_sensor_template.illuminance_type_radial.SetInParent()
        return self

    def set_illuminance_type_hemispherical(self) -> SensorIrradiance:
        """Select hemispherical illuminance integration."""
        self._sensor_template.irradiance_sensor_template.illuminance_type_hemispherical.SetInParent()
        return self

    def set_illuminance_type_cylindrical(self) -> SensorIrradiance:
        """Select cylindrical illuminance integration."""
        self._sensor_template.irradiance_sensor_template.illuminance_type_cylindrical.SetInParent()
        return self

    def set_illuminance_type_semi_cylindrical(self) -> SensorIrradiance:
        """Select semi-cylindrical illuminance integration and clear integration_direction."""
        self._sensor_template.irradiance_sensor_template.illuminance_type_semi_cylindrical.SetInParent()
        self._sensor_instance.irradiance_properties.ClearField("integration_direction")
        return self

    @property
    def axis_system(self) -> List[float]:
        """Sensor axis system (position + orientation).

        Returns
        -------
        List[float]
            Axis system as [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._sensor_instance.irradiance_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: List[float]) -> None:
        """Set sensor axis system.

        Parameters
        ----------
        axis_system : List[float]
            Axis system data as [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        self._sensor_instance.irradiance_properties.axis_system[:] = axis_system

    def set_ray_file_type_none(self) -> SensorIrradiance:
        """Disable ray file generation for irradiance sensor."""
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileNone
        )
        return self

    def set_ray_file_type_classic(self) -> SensorIrradiance:
        """Enable classic ray file generation (no polarization)."""
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileClassic
        )
        return self

    def set_ray_file_type_polarization(self) -> SensorIrradiance:
        """Enable ray file generation with polarization information."""
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFilePolarization
        )
        return self

    def set_ray_file_type_tm25(self) -> SensorIrradiance:
        """Enable TM25 ray file generation with polarization."""
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25
        )
        return self

    def set_ray_file_type_tm25_no_polarization(self) -> SensorIrradiance:
        """Enable TM25 ray file generation without polarization."""
        self._sensor_instance.irradiance_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization
        )
        return self

    def set_layer_type_none(self) -> SensorIrradiance:
        """Define layer separation as None (single result layer)."""
        self._sensor_instance.irradiance_properties.layer_type_none.SetInParent()
        self._layer_type = LayerTypes.none
        return self

    def set_layer_type_source(self) -> SensorIrradiance:
        """Define layer separation by source (one layer per active source)."""
        self._sensor_instance.irradiance_properties.layer_type_source.SetInParent()
        self._layer_type = LayerTypes.by_source
        return self

    def set_layer_type_face(self) -> BaseSensor.LayerTypeFace:
        """Define layer separation by face and return helper."""
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
        """Define layer separation by sequence and return helper."""
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
        """Define layer separation by polarization."""
        self._sensor_instance.irradiance_properties.layer_type_polarization.SetInParent()
        self._layer_type = LayerTypes.by_polarization
        return self

    def set_layer_type_incidence_angle(
        self,
    ) -> BaseSensor.LayerTypeIncidenceAngle:
        """Define layer separation by incidence angle and return helper."""
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
    def output_face_geometries(self):
        """Get output faces for inverse simulation optimization.

        Returns
        -------
        List[str]
            List of output face geo-paths if set, otherwise ``None``.
        """
        if self._sensor_instance.irradiance_properties.HasField("output_face_geometries"):
            return self._sensor_instance.irradiance_properties.output_face_geometries.geo_paths

    @output_face_geometries.setter
    def output_face_geometries(
        self,
        geometries: Optional[List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]] = None,
    ) -> None:
        """Select output faces for inverse simulation optimization.

        Parameters
        ----------
        geometries : Optional[List[Union[\
        ansys.speos.core.geo_ref.GeoRef,\
        ansys.speos.core.body.Body,\
        ansys.speos.core.face.Face,\
        ansys.speos.core.part.Part.SubPart]]], optional
            List of geometries that will be considered as output faces. If falsy the
            field will be cleared. By default, ``None`` (no output faces).
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
    """Radiance sensor feature.

    The radiance sensor can operate in photometric, colorimetric, radiometric
    or spectral modes. By default the sensor uses a photometric template and an
    axis system is available to position the sensor. Layer separation options
    (none, by source, by face, by sequence) are available through helpers.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. Default is ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature. Default is ``{}``.
    sensor_instance : Optional[ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance]
        Sensor instance to provide if the feature should be created from an
        existing instance. Default is ``None`` which creates the feature
        locally.
    default_parameters : Optional[ansys.speos.core.generic.parameters.RadianceSensorParameters]
        If provided, use these parameters to initialize the sensor template and
        instance.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Optional[RadianceSensorParameters] = None,
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
        self._fill_parameters(default_parameters)

    def _fill_parameters(
        self, default_parameters: Optional[RadianceSensorParameters] = None
    ) -> None:
        if default_parameters:
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
            elif default_parameters.sensor_type == SensorTypes.radiometric:
                self.set_type_radiometric()
            elif default_parameters.sensor_type == SensorTypes.photometric:
                self.set_type_photometric()

            if default_parameters.layer_type == LayerTypes.none:
                self.set_layer_type_none()
            elif default_parameters.layer_type == LayerTypes.by_source:
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
            return

        self._sensor_dimensions = self.Dimensions(
            sensor_dimensions=self._sensor_template.radiance_sensor_template.dimensions,
            default_parameters=None,
            stable_ctr=True,
        )
        template = self._sensor_template.radiance_sensor_template
        if template.HasField("sensor_type_photometric"):
            self.set_type_photometric()
        elif template.HasField("sensor_type_colorimetric"):
            self.set_type_colorimetric()
        elif template.HasField("sensor_type_radiometric"):
            self.set_type_radiometric()
        elif template.HasField("sensor_type_spectral"):
            self.set_type_spectral()
        properties = self._sensor_instance.radiance_properties
        if properties.HasField("layer_type_none"):
            self._layer_type = LayerTypes.none
        elif properties.HasField("layer_type_source"):
            self._layer_type = LayerTypes.by_source
        elif properties.HasField("layer_type_sequence"):
            self.set_layer_type_sequence()
        elif properties.HasField("layer_type_face"):
            self.set_layer_type_face()

    @property
    def visual_data(self) -> _VisualData:
        """Radiance sensor visualization data.

        Returns
        -------
        ansys.speos.core.generic.visualization_methods._VisualData
            VisualData containing mesh/triangles and axis system for rendering.
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

            # radiance sensor geometry
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

            # radiance axis system
            self._visual_data.coordinates.origin = feature_radiance_pos
            self._visual_data.coordinates.x_axis = feature_radiance_x_dir
            self._visual_data.coordinates.y_axis = feature_radiance_y_dir

            self._visual_data.updated = True
            return self._visual_data

    @property
    def dimensions(self) -> BaseSensor.Dimensions:
        """Dimensions helper for the radiance sensor.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimensions helper attached to the sensor template.
        """
        return self._sensor_dimensions

    @property
    def type(self) -> str:
        """Sensor type.

        Returns
        -------
        str
            Sensor type as a human-readable string (e.g. 'Colorimetric', 'Spectral',
            'Photometric', 'Radiometric').
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
        """Colorimetric helper when sensor is colorimetric.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Colorimetric]
            Colorimetric helper instance or ``None`` if the sensor is not
            colorimetric.
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return self._type

    @property
    def spectral(self) -> Union[None, BaseSensor.Spectral]:
        """Spectral helper when sensor is spectral.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Spectral]
            Spectral helper instance or ``None`` if the sensor is not spectral.
        """
        if isinstance(self._type, BaseSensor.Spectral):
            return self._type

    @property
    def layer(
        self,
    ) -> Union[str, BaseSensor.LayerTypeFace, BaseSensor.LayerTypeSequence]:
        """Layer separation configuration.

        Returns
        -------
        Union[str, ansys.speos.core.sensor.BaseSensor.LayerTypeFace,
              ansys.speos.core.sensor.BaseSensor.LayerTypeSequence]
            Current layer separation helper or mode (e.g. "none", "by_source")
        """
        return self._layer_type

    def set_dimensions(self) -> BaseSensor.Dimensions:
        """Return the dimensions helper bound to the radiance template.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Dimensions
            Dimensions instance bound to the radiance sensor template.
        """
        if (
            self._sensor_dimensions._sensor_dimensions
            is not self._sensor_template.radiance_sensor_template.dimensions
        ):
            # Happens in case of feature reset (ensure correct binding)
            self._sensor_dimensions._sensor_dimensions = (
                self._sensor_template.radiance_sensor_template.dimensions
            )
        return self._sensor_dimensions

    def set_type_photometric(self) -> SensorRadiance:
        """Set the sensor to photometric mode.

        The sensor uses the visible spectrum and results are in lm/m2 or lx.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Self for chaining.
        """
        self._sensor_template.radiance_sensor_template.sensor_type_photometric.SetInParent()
        self._type = SensorTypes.photometric.capitalize()
        return self

    def set_type_colorimetric(self) -> BaseSensor.Colorimetric:
        """Set the sensor to colorimetric mode and return helper.

        The sensor generates color results without spectral splitting.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Colorimetric
            Colorimetric helper instance.
        """
        if self._type is None and self._sensor_template.radiance_sensor_template.HasField(
            "sensor_type_colorimetric"
        ):
            # Happens when loading from an existing project
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.radiance_sensor_template.sensor_type_colorimetric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.radiance_sensor_template.sensor_type_colorimetric,
                default_parameters=ColorimetricParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.radiance_sensor_template.sensor_type_colorimetric
        ):
            # Re-bind after reset
            self._type._sensor_type_colorimetric = (
                self._sensor_template.radiance_sensor_template.sensor_type_colorimetric
            )
        return self._type

    def set_type_radiometric(self) -> SensorRadiance:
        """Set the sensor to radiometric mode.

        The sensor considers the full spectrum and results are in W/m2.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Self for chaining.
        """
        self._sensor_template.radiance_sensor_template.sensor_type_radiometric.SetInParent()
        self._type = SensorTypes.radiometric.capitalize()
        return self

    def set_type_spectral(self) -> BaseSensor.Spectral:
        """Set the sensor to spectral mode and return helper.

        The sensor produces spectral data separated by wavelength.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Spectral
            Spectral helper instance.
        """
        if self._type is None and self._sensor_template.radiance_sensor_template.HasField(
            "sensor_type_spectral"
        ):
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.radiance_sensor_template.sensor_type_spectral,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Spectral):
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.radiance_sensor_template.sensor_type_spectral,
                default_parameters=SpectralParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_spectral
            is not self._sensor_template.radiance_sensor_template.sensor_type_spectral
        ):
            self._type._sensor_type_spectral = (
                self._sensor_template.radiance_sensor_template.sensor_type_spectral
            )
        return self._type

    @property
    def focal(self) -> float:
        """Focal length (mm).

        Returns
        -------
        float
            Distance between the sensor plane and the focal point in millimeters.
        """
        return self._sensor_template.radiance_sensor_template.focal

    @focal.setter
    def focal(self, value: float) -> None:
        """Set the focal length.

        Parameters
        ----------
        value : float
            Focal length in millimeters.
        """
        self._sensor_template.radiance_sensor_template.focal = value

    @property
    def integration_angle(self) -> float:
        """Integration angle (degrees).

        Returns
        -------
        float
            Integration angle used for radiance integration (degrees).
        """
        return self._sensor_template.radiance_sensor_template.integration_angle

    @integration_angle.setter
    def integration_angle(self, value: float) -> None:
        """Set the integration angle.

        Parameters
        ----------
        value : float
            Integration angle in degrees.
        """
        self._sensor_template.radiance_sensor_template.integration_angle = value

    @property
    def axis_system(self) -> List[float]:
        """Axis system describing sensor position and orientation.

        Returns
        -------
        List[float]
            Axis system as a 12-element list:
            [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        """
        return self._sensor_instance.radiance_properties.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: List[float]) -> None:
        """Set the sensor axis system.

        Parameters
        ----------
        axis_system : List[float]
            Axis system as a 12-element list:
            [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        """
        self._sensor_instance.radiance_properties.axis_system[:] = axis_system

    @property
    def observer_point(self) -> Union[None, List[float]]:
        """Observer point position.

        Notes
        -----
        If an observer point is set, it overrides the focal length.

        Returns
        -------
        Union[None, List[float]]
            The observer point [Ox, Oy, Oz], or ``None`` if not set.
        """
        return self._sensor_instance.radiance_properties.observer_point

    @observer_point.setter
    def observer_point(self, value: List[float]) -> None:
        """Set or clear the observer point.

        Parameters
        ----------
        value : List[float]
            Position of the observer point [Ox, Oy, Oz]. If falsy, the field is
            cleared and the focal length will be used instead.
        """
        if not value:
            self._sensor_instance.radiance_properties.ClearField("observer_point")
        else:
            self._sensor_instance.radiance_properties.observer_point[:] = value

    def set_layer_type_none(self) -> SensorRadiance:
        """Disable layer separation (single result layer).

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Self for chaining.
        """
        self._sensor_instance.radiance_properties.layer_type_none.SetInParent()
        self._layer_type = LayerTypes.none
        return self

    def set_layer_type_source(self) -> SensorRadiance:
        """Set layer separation to one layer per active source.

        Returns
        -------
        ansys.speos.core.sensor.SensorRadiance
            Self for chaining.
        """
        self._sensor_instance.radiance_properties.layer_type_source.SetInParent()
        self._layer_type = LayerTypes.by_source
        return self

    def set_layer_type_face(self) -> BaseSensor.LayerTypeFace:
        """Define layer separation by face and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeFace
            LayerTypeFace helper instance.
        """
        if self._layer_type is None and self._sensor_instance.radiance_properties.HasField(
            "layer_type_face"
        ):
            # Loaded from existing project
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
            # Re-bind after reset
            self._layer_type._layer_type_face = (
                self._sensor_instance.radiance_properties.layer_type_face
            )
        return self._layer_type

    def set_layer_type_sequence(self) -> BaseSensor.LayerTypeSequence:
        """Define layer separation by sequence and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
            LayerTypeSequence helper instance.
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
            # Re-bind after reset
            self._layer_type._layer_type_sequence = (
                self._sensor_instance.radiance_properties.layer_type_sequence
            )
        return self._layer_type


class Sensor3DIrradiance(BaseSensor):
    """Sensor feature: 3D Irradiance.

    By default, a 3D irradiance sensor uses a photometric template and planar
    integration. Reflection, transmission and absorption measures are enabled
    by default. By default there is no layer separation and no ray-file
    generation.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. Default is ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata for the feature. Default is ``{}``.
    sensor_instance : Optional[ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance]
        Optional existing sensor instance to initialize from. Default is
        ``None`` to create a new local instance.
    default_parameters : Optional[ansys.speos.core.generic.parameters.Irradiance3DSensorParameters]
        Optional defaults to initialize the sensor template and instance.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Optional[Irradiance3DSensorParameters] = None,
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
        self._fill_parameters(default_parameters)

    def _fill_parameters(
        self, default_parameters: Optional[Irradiance3DSensorParameters] = None
    ) -> None:
        if default_parameters:
            if isinstance(default_parameters.sensor_type, ColorimetricParameters):
                self._type = Sensor3DIrradiance.Colorimetric(
                    sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == SensorTypes.radiometric:
                self._type = Sensor3DIrradiance.Radiometric(
                    sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                    default_parameters=default_parameters,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == SensorTypes.photometric:
                self._type = Sensor3DIrradiance.Photometric(
                    sensor_type_photometric=self._sensor_template.irradiance_3d.type_photometric,
                    default_parameters=default_parameters,
                    stable_ctr=True,
                )
            if default_parameters.geometries:
                self.geometries = default_parameters.geometries
            if default_parameters.layer_type == LayerTypes.none:
                self.set_layer_type_none()
            elif default_parameters.layer_type == LayerTypes.by_source:
                self.set_layer_type_source()
            match default_parameters.rayfile_type:
                case RayfileTypes.none:
                    self.set_ray_file_type_none()
                case RayfileTypes.classic:
                    self.set_ray_file_type_classic()
                case RayfileTypes.polarization:
                    self.set_ray_file_type_polarization()
                case RayfileTypes.tm25:
                    self.set_ray_file_type_tm25()
                case RayfileTypes.tm25_no_polarization:
                    self.set_ray_file_type_tm25_no_polarization()
            return

        template = self._sensor_template.irradiance_3d
        if template.HasField("type_photometric"):
            self.set_type_photometric()
        elif template.HasField("type_colorimetric"):
            self.set_type_colorimetric()
        elif template.HasField("type_radiometric"):
            self.set_type_radiometric()
        properties = self._sensor_instance.irradiance_3d_properties
        if properties.HasField("layer_type_none"):
            self._layer_type = LayerTypes.none
        elif properties.HasField("layer_type_source"):
            self._layer_type = LayerTypes.by_source

    class Radiometric:
        """Radiometric measures helper for 3D irradiance.

        This helper configures radiant intensity measures (W sr^-1) and the
        integration type used for 3D irradiance (planar or radial).

        Parameters
        ----------
        sensor_type_radiometric : ansys.api.speos.sensor.v1.sensor_pb2.TypeRadiometric
            Protobuf object representing radiometric type settings.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.Irradiance3DSensorParameters], optional
            Optional default values to apply.
        stable_ctr : bool, optional
            Internal flag preventing external instantiation.

        Notes
        -----
        Do not instantiate this helper directly; use the enclosing sensor's
        methods to select radiometric mode.
        """

        def __init__(
            self,
            sensor_type_radiometric: sensor_pb2.TypeRadiometric,
            default_parameters: Optional[Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError("Radiometric class instantiated outside of class scope")

            self._sensor_type_radiometric = sensor_type_radiometric
            self._integration_type = None
            self._fill_parameters(default_parameters, stable_ctr)

        def _fill_parameters(
            self,
            default_parameters: Optional[Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if default_parameters:
                match default_parameters.integration_type:
                    case IntegrationTypes.planar:
                        self.set_integration_planar()
                        self._integration_type = Sensor3DIrradiance.Measures(
                            illuminance_type=self._sensor_type_radiometric.integration_type_planar,
                            default_parameters=default_parameters.measures,
                            stable_ctr=stable_ctr,
                        )
                    case IntegrationTypes.radial:
                        self.set_integration_radial()
                return

            self._integration_type = Sensor3DIrradiance.Measures(
                illuminance_type=self._sensor_type_radiometric.integration_type_planar,
                default_parameters=None,
                stable_ctr=stable_ctr,
            )

        def set_integration_planar(self) -> Sensor3DIrradiance.Measures:
            """Select planar integration and return the measures helper.

            Returns
            -------
            ansys.speos.core.sensor.Sensor3DIrradiance.Measures
                Measures helper tied to planar integration settings.
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
                # Rebind after reset
                self._integration_type._illuminance_type = (
                    self._sensor_type_radiometric.integration_type_planar
                )
            return self._integration_type

        def set_integration_radial(self) -> None:
            """Select radial integration.

            Notes
            -----
            This sets a textual marker ("Radial") and updates the underlying
            protobuf to use radial integration.
            """
            self._integration_type = "Radial"
            self._sensor_type_radiometric.integration_type_radial.SetInParent()

    class Photometric:
        """Photometric measures helper for 3D irradiance.

        This helper configures luminous intensity (cd) integration and which
        additional measures (reflection, transmission, absorption) are active.

        Parameters
        ----------
        sensor_type_photometric : ansys.api.speos.sensor.v1.sensor_pb2.TypePhotometric
            Protobuf object representing photometric type settings.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.Irradiance3DSensorParameters] = None
            Optional default values to apply.
        stable_ctr : bool, optional
            Internal flag preventing external instantiation.

        Notes
        -----
        Do not instantiate this helper directly; use the enclosing sensor's
        methods to select photometric mode.
        """

        def __init__(
            self,
            sensor_type_photometric: sensor_pb2.TypePhotometric,
            default_parameters: Optional[Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError("Photometric class instantiated outside of class scope")

            self._sensor_type_photometric = sensor_type_photometric
            self._integration_type = None
            self._fill_parameters(default_parameters, stable_ctr)

        def _fill_parameters(
            self,
            default_parameters: Optional[Irradiance3DSensorParameters] = None,
            stable_ctr: bool = True,
        ) -> None:
            if default_parameters:
                match default_parameters.integration_type:
                    case IntegrationTypes.planar:
                        self.set_integration_planar()
                        self._integration_type = Sensor3DIrradiance.Measures(
                            illuminance_type=self._sensor_type_photometric.integration_type_planar,
                            default_parameters=default_parameters.measures,
                            stable_ctr=stable_ctr,
                        )
                    case IntegrationTypes.radial:
                        self.set_integration_radial()
                return

            self._integration_type = Sensor3DIrradiance.Measures(
                illuminance_type=self._sensor_type_photometric.integration_type_planar,
                default_parameters=None,
                stable_ctr=stable_ctr,
            )

        def set_integration_planar(self) -> Sensor3DIrradiance.Measures:
            """Select planar integration and return the measures helper.

            Returns
            -------
            ansys.speos.core.sensor.Sensor3DIrradiance.Measures
                Measures helper tied to planar integration settings.
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
                # Rebind after reset
                self._integration_type._illuminance_type = (
                    self._sensor_type_photometric.integration_type_planar
                )
            return self._integration_type

        def set_integration_radial(self) -> None:
            """Select radial integration for photometric measures."""
            self._integration_type = "Radial"
            self._sensor_type_photometric.integration_type_radial.SetInParent()

    class Measures:
        """Additional measures for 3D irradiance sensors.

        When photometric or radiometric integration is selected, this helper
        controls whether reflection, transmission and absorption are measured.

        Parameters
        ----------
        illuminance_type : ansys.api.speos.sensor.v1.sensor_pb2.IntegrationTypePlanar
            Protobuf object describing planar integration measure flags.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.MeasuresParameters]] = None
            Default flags to initialize the helper.
        stable_ctr : bool, optional
            Internal flag preventing external instantiation.

        Notes
        -----
        Do not instantiate this class directly; obtain it through the enclosing
        Photometric or Radiometric helper.
        """

        def __init__(
            self,
            illuminance_type: sensor_pb2.IntegrationTypePlanar,
            default_parameters: Optional[MeasuresParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Measures class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._illuminance_type = illuminance_type
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[MeasuresParameters] = None) -> None:
            if not default_parameters:
                return
            self.reflection = default_parameters.reflection
            self.transmission = default_parameters.transmission
            self.absorption = default_parameters.absorption

        @property
        def reflection(self) -> bool:
            """Whether reflection is measured.

            Returns
            -------
            bool
                True when reflection measurement is enabled, False otherwise.
            """
            return self._illuminance_type.reflection

        @reflection.setter
        def reflection(self, value: bool) -> None:
            """Enable or disable reflection measurement.

            Parameters
            ----------
            value : bool
                True to enable reflection measurement, False to disable.
            """
            self._illuminance_type.reflection = value

        @property
        def transmission(self) -> bool:
            """Whether transmission is measured.

            Returns
            -------
            bool
                True when transmission measurement is enabled, False otherwise.
            """
            return self._illuminance_type.transmission

        @transmission.setter
        def transmission(self, value: bool) -> None:
            """Enable or disable transmission measurement.

            Parameters
            ----------
            value : bool
                True to enable transmission measurement, False to disable.
            """
            self._illuminance_type.transmission = value

        @property
        def absorption(self) -> bool:
            """Whether absorption is measured.

            Returns
            -------
            bool
                True when absorption measurement is enabled, False otherwise.
            """
            return self._illuminance_type.absorption

        @absorption.setter
        def absorption(self, value: bool) -> None:
            """Enable or disable absorption measurement.

            Parameters
            ----------
            value : bool
                True to enable absorption measurement, False to disable.
            """
            self._illuminance_type.absorption = value

    class Colorimetric:
        """Colorimetric helper for 3D irradiance.

        Controls colorimetric-specific settings including wavelength range.

        Parameters
        ----------
        sensor_type_colorimetric : ansys.api.speos.sensor.v1.sensor_pb2.TypeColorimetric
            Protobuf object representing colorimetric settings.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.ColorimetricParameters] = None
            Optional defaults to initialize wavelength range.
        stable_ctr : bool, optional
            Internal flag preventing external instantiation.

        Notes
        -----
        Do not instantiate directly; use sensor helper methods.
        """

        def __init__(
            self,
            sensor_type_colorimetric: sensor_pb2.TypeColorimetric,
            default_parameters: Optional[ColorimetricParameters] = None,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Colorimetric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Wavelengths helper
            self._wavelengths_range = BaseSensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_colorimetric,
                default_parameters=default_parameters.wavelength_range
                if default_parameters
                else None,
                stable_ctr=stable_ctr,
            )

        def set_wavelengths_range(self) -> BaseSensor.WavelengthsRange:
            """Return the wavelengths range helper.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                Helper to read/write wavelength range values.
            """
            if self._wavelengths_range._wavelengths_range is not self._sensor_type_colorimetric:
                # Rebind after reset
                self._wavelengths_range._wavelengths_range = self._sensor_type_colorimetric
            return self._wavelengths_range

    @property
    def type(self) -> str:
        """Sensor type for 3D irradiance.

        Returns
        -------
        str
            One of "Colorimetric", "Radiometric", "Photometric" depending on the
            active helper type.
        """
        if isinstance(self._type, self.Colorimetric):
            return "Colorimetric"
        elif isinstance(self._type, self.Radiometric):
            return "Radiometric"
        elif isinstance(self._type, self.Photometric):
            return "Photometric"

    @property
    def colorimetric(self) -> Colorimetric:
        """Return the Colorimetric helper if active.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Colorimetric
            Colorimetric helper instance when applicable.
        """
        if isinstance(self._type, self.Colorimetric):
            return self._type

    @property
    def photometric(self) -> Photometric:
        """Return the Photometric helper if active.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Photometric
            Photometric helper instance when applicable.
        """
        if isinstance(self._type, self.Photometric):
            return self._type

    @property
    def radiometric(self) -> Radiometric:
        """Return the Radiometric helper if active.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Radiometric
            Radiometric helper instance when applicable.
        """
        if isinstance(self._type, self.Radiometric):
            return self._type

    @property
    def layer(
        self,
    ) -> Union[str, BaseSensor.LayerTypeFace]:
        """Layer separation configuration.

        Returns
        -------
        Union[str, ansys.speos.core.sensor.BaseSensor.LayerTypeFace]
            Current layer separation helper or mode.
        """
        return self._layer_type

    @property
    def visual_data(self) -> _VisualData:
        """Visualize 3D irradiance sensor target geometries.

        Returns
        -------
        ansys.speos.core.generic.visualization_methods._VisualData
            VisualData containing mesh geometry to render the 3D sensor surfaces.

        Raises
        ------
        ValueError
            If a linked geo-path is not a valid Face or Body.
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
        """Select photometric mode.

        The sensor uses the visible spectrum and results are in lm/m2 or lx.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Photometric
            Photometric helper instance.
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_photometric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Photometric(
                self._sensor_template.irradiance_3d.type_photometric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Sensor3DIrradiance.Photometric):
            # if the _type is not Photometric then we create a new type.
            self._type = Sensor3DIrradiance.Photometric(
                self._sensor_template.irradiance_3d.type_photometric,
                default_parameters=Irradiance3DSensorParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_photometric
            is not self._sensor_template.irradiance_3d.type_photometric
        ):
            # Rebind after reset
            self._type._sensor_type_photometric = (
                self._sensor_template.irradiance_3d.type_photometric
            )
        return self._type

    def set_type_radiometric(self) -> Sensor3DIrradiance.Radiometric:
        """Select radiometric mode.

        The sensor considers the full spectrum and results are in W/m2.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Radiometric
            Radiometric helper instance.
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_radiometric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Radiometric(
                sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Sensor3DIrradiance.Radiometric):
            self._type = Sensor3DIrradiance.Radiometric(
                sensor_type_radiometric=self._sensor_template.irradiance_3d.type_radiometric,
                default_parameters=Irradiance3DSensorParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_radiometric
            is not self._sensor_template.irradiance_3d.type_radiometric
        ):
            self._type._sensor_type_radiometric = (
                self._sensor_template.irradiance_3d.type_radiometric
            )
        return self._type

    def set_type_colorimetric(self) -> Sensor3DIrradiance.Colorimetric:
        """Select colorimetric mode.

        The sensor generates color results without spectral splitting.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance.Colorimetric
            Colorimetric helper instance.
        """
        if self._type is None and self._sensor_template.irradiance_3d.HasField("type_colorimetric"):
            # Happens in case of project created via load of speos file
            self._type = Sensor3DIrradiance.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            self._type = Sensor3DIrradiance.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.irradiance_3d.type_colorimetric,
                default_parameters=ColorimetricParameters(),
                stable_ctr=True,
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.irradiance_3d.type_colorimetric
        ):
            self._type._sensor_type_colorimetric = (
                self._sensor_template.irradiance_3d.type_colorimetric
            )
        return self._type

    def set_ray_file_type_none(self) -> Sensor3DIrradiance:
        """Disable ray-file generation for the 3D irradiance sensor.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileNone
        )
        return self

    def set_ray_file_type_classic(self) -> Sensor3DIrradiance:
        """Enable classic ray-file generation (no polarization).

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileClassic
        )
        return self

    def set_ray_file_type_polarization(self) -> Sensor3DIrradiance:
        """Enable ray-file generation with polarization information.

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFilePolarization
        )
        return self

    def set_ray_file_type_tm25(self) -> Sensor3DIrradiance:
        """Enable TM25 ray-file generation (with polarization).

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25
        )
        return self

    def set_ray_file_type_tm25_no_polarization(self) -> Sensor3DIrradiance:
        """Enable TM25 ray-file generation (without polarization).

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.ray_file_type = (
            ProtoScene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization
        )
        return self

    def set_layer_type_none(self) -> Sensor3DIrradiance:
        """Disable layer separation (single layer only).

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.layer_type_none.SetInParent()
        self._layer_type = LayerTypes.none
        return self

    def set_layer_type_source(self) -> Sensor3DIrradiance:
        """Enable layer separation by source (one layer per active source).

        Returns
        -------
        ansys.speos.core.sensor.Sensor3DIrradiance
            Self for chaining.
        """
        self._sensor_instance.irradiance_3d_properties.layer_type_source.SetInParent()
        self._layer_type = LayerTypes.by_source
        return self

    @property
    def geometries(self) -> List[str]:
        """Geo-paths of faces or bodies used by the 3D irradiance sensor.

        Returns
        -------
        List[str]
            List of geo-path strings referencing faces or bodies used as the
            integrating geometries for the 3D irradiance sensor.
        """
        return self._sensor_instance.irradiance_3d_properties.geometries.geo_paths

    @geometries.setter
    def geometries(
        self, geometries: List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]
    ) -> None:
        """Assign geometries (faces/bodies) to the 3D irradiance sensor.

        Parameters
        ----------
        geometries : List[Union[ansys.speos.core.geo_ref.GeoRef, ansys.speos.core.body.Body,
                                ansys.speos.core.face.Face, ansys.speos.core.part.Part.SubPart]]
            List of geometry references (GeoRef, Face, Body or SubPart) to be
            considered by the 3D irradiance sensor.

        Raises
        ------
        TypeError
            If any entry in `geometries` is not an accepted geometry type.
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


class SensorXMPIntensity(BaseSensor):
    """XMP intensity sensor feature.

    Wraps configuration and helpers for an XMP intensity sensor. Supports
    photometric, radiometric, colorimetric and spectral modes, several
    orientation types (conoscopic, X-as-meridian, X-as-parallel), viewing
    directions, layer separation and optional near-field detector settings.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Feature description. Default is ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata for the feature. Default is ``{}``.
    sensor_instance : Optional[ansys.speos.core.kernel.scene.ProtoScene.SensorInstance]
        Optional existing sensor instance to initialize from. Default is ``None``.
    default_parameters : Optional[ansys.speos.core.generic.parameters.IntensityXMPSensorParameters]
        Optional defaults to initialize the sensor template and instance.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_parameters: Optional[IntensityXMPSensorParameters] = None,
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

        # Attribute gathering more complex intensity type
        self._type = None
        self._layer_type = None
        self._cell_diameter = None
        self._vis_radius = 1000
        self._fill_parameters(default_parameters)

    def _fill_parameters(
        self, default_parameters: Optional[IntensityXMPSensorParameters] = None
    ) -> None:
        if default_parameters:
            match default_parameters.orientation:
                case IntensitySensorOrientationTypes.conoscopic:
                    self.set_orientation_conoscopic()
                case IntensitySensorOrientationTypes.x_as_meridian:
                    self.set_orientation_x_as_meridian()
                case IntensitySensorOrientationTypes.x_as_parallel:
                    self.set_orientation_x_as_parallel()

            self._set_dimension_values(default_parameters.dimensions)
            self.axis_system = default_parameters.axis_system

            match default_parameters.viewing_direction:
                case IntensitySensorViewingTypes.from_sensor:
                    self.set_viewing_direction_from_sensor()
                case IntensitySensorViewingTypes.from_source:
                    self.set_viewing_direction_from_source()

            if isinstance(default_parameters.sensor_type, ColorimetricParameters):
                self._type = BaseSensor.Colorimetric(
                    sensor_type_colorimetric=self._sensor_template.intensity_sensor_template.sensor_type_colorimetric,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.sensor_type, SpectralParameters):
                self._type = BaseSensor.Spectral(
                    sensor_type_spectral=self._sensor_template.intensity_sensor_template.sensor_type_spectral,
                    default_parameters=default_parameters.sensor_type,
                    stable_ctr=True,
                )
            elif default_parameters.sensor_type == SensorTypes.radiometric:
                self.set_type_radiometric()
            elif default_parameters.sensor_type == SensorTypes.photometric:
                self.set_type_photometric()

            if default_parameters.layer_type == LayerTypes.none:
                self.set_layer_type_none()
            elif default_parameters.layer_type == LayerTypes.by_source:
                self.set_layer_type_source()
            elif isinstance(default_parameters.layer_type, LayerByFaceParameters):
                self._layer_type = BaseSensor.LayerTypeFace(
                    layer_type_face=self._sensor_instance.intensity_properties.layer_type_face,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            elif isinstance(default_parameters.layer_type, LayerBySequenceParameters):
                self._layer_type = BaseSensor.LayerTypeSequence(
                    layer_type_sequence=self._sensor_instance.intensity_properties.layer_type_sequence,
                    default_parameters=default_parameters.layer_type,
                    stable_ctr=True,
                )
            if default_parameters.near_field_parameters:
                self.near_field = True
                self.cell_distance = default_parameters.near_field_parameters.cell_distance
                self.cell_diameter = default_parameters.near_field_parameters.cell_diameter
            return

        template = self._sensor_template.intensity_sensor_template
        if template.HasField("sensor_type_photometric"):
            self.set_type_photometric()
        elif template.HasField("sensor_type_colorimetric"):
            self.set_type_colorimetric()
        elif template.HasField("sensor_type_radiometric"):
            self.set_type_radiometric()
        elif template.HasField("sensor_type_spectral"):
            self.set_type_spectral()
        properties = self._sensor_instance.intensity_properties
        if properties.HasField("layer_type_none"):
            self._layer_type = LayerTypes.none
        elif properties.HasField("layer_type_source"):
            self._layer_type = LayerTypes.by_source
        elif properties.HasField("layer_type_sequence"):
            self.set_layer_type_sequence()
        elif properties.HasField("layer_type_face"):
            self.set_layer_type_face()

    @property
    def visual_data(self) -> _VisualData:
        """Intensity sensor visualization geometry.

        Returns
        -------
        ansys.speos.core.generic.visualization_methods._VisualData
            VisualData used by visualizers (mesh/triangles, coordinates).

        Notes
        -----
        Visualization depends on sensor orientation (conoscopic vs angular grid)
        and on template dimension fields.
        """

        def rm(theta, u):
            # make sure u is normalized
            norm = np.linalg.norm(u)
            ux, uy, uz = u / norm

            # build and return the rotation matrix
            r11 = np.cos(theta) + ux * ux * (1 - np.cos(theta))
            r12 = ux * uy * (1 - np.cos(theta)) - uz * np.sin(theta)
            r13 = ux * uz * (1 - np.cos(theta)) + uy * np.sin(theta)
            r21 = ux * uy * (1 - np.cos(theta)) + uz * np.sin(theta)
            r22 = np.cos(theta) + uy * uy * (1 - np.cos(theta))
            r23 = uy * uz * (1 - np.cos(theta)) - ux * np.sin(theta)
            r31 = ux * uz * (1 - np.cos(theta)) - uy * np.sin(theta)
            r32 = uy * uz * (1 - np.cos(theta)) + ux * np.sin(theta)
            r33 = np.cos(theta) + uz * uz * (1 - np.cos(theta))
            return np.array([[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]])

        if self._visual_data.updated:
            return self._visual_data

        feature_pos_info = self.get(key="axis_system")
        feature_pos = np.array(feature_pos_info[:3])
        feature_x_dir = np.array(feature_pos_info[3:6])
        feature_y_dir = np.array(feature_pos_info[6:9])
        feature_z_dir = np.array(feature_pos_info[9:12])
        feature_vis_radius = self._vis_radius

        if self._sensor_template.intensity_sensor_template.HasField(
            "intensity_orientation_conoscopic"
        ):
            # conoscopic visualization (radial / azimuth sampling)
            feature_theta = float(self.get(key="theta_max"))
            coord_transform = np.transpose(np.array([feature_x_dir, feature_y_dir, feature_z_dir]))
            samp_1 = 30  # azimuth sampling
            samp_2 = 15  # radial sampling
            vertices = np.zeros(((samp_2 * samp_1), 3))
            thetas = (np.pi / 180) * np.linspace(0, feature_theta, num=samp_2, endpoint=False)
            phis = np.linspace(0, 2 * np.pi, num=samp_1, endpoint=False)

            # compute all the vertices
            iter = 0
            for theta in thetas:
                for phi in phis:
                    # spherical to cartesian
                    x = feature_vis_radius * np.sin(theta) * np.cos(phi)
                    y = feature_vis_radius * np.sin(theta) * np.sin(phi)
                    z = feature_vis_radius * np.cos(theta)
                    # transform to intensity sensor coords
                    vertices[iter, :] = np.matmul(coord_transform, [x, y, z])
                    iter += 1

            # shift all vertices by the intensity sensor origin
            vertices = vertices + feature_pos

            # add "wrap around" squares to the visualizer
            for j in range(0, (samp_2 - 1)):
                p1 = vertices[j * samp_1 + (samp_1 - 1), :]
                p2 = vertices[j * samp_1, :]
                p3 = vertices[(j + 1) * samp_1 + (samp_1 - 1), :]
                p4 = vertices[(j + 1) * samp_1, :]
                self._visual_data.add_data_triangle([p1, p2, p3])
                self._visual_data.add_data_triangle([p2, p3, p4])

        else:
            # angular-grid visualization (x/y tilt sampling)
            feature_x_start = float(self.get(key="x_start"))
            feature_x_end = float(self.get(key="x_end"))
            feature_y_start = float(self.get(key="y_start"))
            feature_y_end = float(self.get(key="y_end"))
            samp_1 = 15  # x sampling
            samp_2 = 15  # y sampling
            x_tilts = (np.pi / 180) * np.linspace(
                feature_y_start, feature_y_end, num=samp_1, endpoint=True
            )
            y_tilts = (np.pi / 180) * np.linspace(
                feature_x_start, feature_x_end, num=samp_2, endpoint=True
            )
            vertices = np.zeros((int(samp_1 * samp_2), 3))
            u = feature_vis_radius * feature_z_dir

            # compute all the vertices
            iter = 0
            if self._sensor_template.intensity_sensor_template.HasField(
                "intensity_orientation_x_as_meridian"
            ):
                for x_tilt in x_tilts:
                    tilted_x = np.matmul(rm(x_tilt, feature_x_dir), u)
                    for y_tilt in y_tilts:
                        vertices[iter, :] = np.matmul(rm(y_tilt, feature_y_dir), tilted_x)
                        iter += 1
            else:
                for y_tilt in y_tilts:
                    tilted_y = np.matmul(rm(y_tilt, feature_y_dir), u)
                    for x_tilt in x_tilts:
                        vertices[iter, :] = np.matmul(rm(x_tilt, feature_x_dir), tilted_y)
                        iter += 1

            # shift all vertices by the intensity sensor origin
            vertices = vertices + feature_pos

        # add squares to the visualizer
        for j in range(0, (samp_2 - 1)):
            for i in range(0, (samp_1 - 1)):
                index1 = j * samp_1 + i
                index2 = j * samp_1 + (i + 1)
                index3 = (j + 1) * samp_1 + i
                index4 = (j + 1) * samp_1 + (i + 1)
                p1 = vertices[index1, :]
                p2 = vertices[index2, :]
                p3 = vertices[index3, :]
                p4 = vertices[index4, :]
                self._visual_data.add_data_triangle([p1, p2, p3])
                self._visual_data.add_data_triangle([p2, p3, p4])

        # intensity direction
        self._visual_data.coordinates.origin = feature_pos
        self._visual_data.coordinates.x_axis = feature_x_dir
        self._visual_data.coordinates.y_axis = feature_y_dir

        self._visual_data.updated = True
        return self._visual_data

    @property
    def near_field(self) -> bool:
        """Whether near-field detector is enabled.

        Returns
        -------
        bool
            True if near-field detector settings exist on the template.
        """
        return self._sensor_template.intensity_sensor_template.HasField("near_field")

    @near_field.setter
    def near_field(self, value: bool) -> None:
        """Enable or disable near-field detector.

        Parameters
        ----------
        value : bool
            True to enable near-field detector (will create the near_field
            sub-message on the template if missing), False to remove it.

        Notes
        -----
        Enabling near-field initializes detector defaults from
        ``NearfieldParameters`` and assigns default ``cell_distance`` and
        ``cell_diameter`` unless overridden afterwards.
        """
        if value:
            if not self._sensor_template.intensity_sensor_template.HasField("near_field"):
                self._sensor_template.intensity_sensor_template.near_field.SetInParent()
                near_field = NearfieldParameters()
                self.cell_distance = near_field.cell_distance
                self.cell_diameter = near_field.cell_diameter
        elif self._sensor_template.intensity_sensor_template.HasField("near_field"):
            self._sensor_template.intensity_sensor_template.ClearField("near_field")

    @property
    def cell_distance(self) -> Union[float, None]:
        """Distance from detector to origin.

        Returns
        -------
        Union[None, float]
            Detector cell distance in millimeters when near-field is active,
            otherwise ``None``.
        """
        if self.near_field:
            return self._sensor_template.intensity_sensor_template.near_field.cell_distance

    @cell_distance.setter
    def cell_distance(self, value: float) -> None:
        """Set detector cell distance.

        Parameters
        ----------
        value : float
            Distance of the measurement cell from the sensor origin in millimeters.

        Raises
        ------
        TypeError
            If near-field is not active on the sensor template.
        """
        if self.near_field:
            self._sensor_template.intensity_sensor_template.near_field.cell_distance = value
        else:
            raise TypeError("Sensor position is not in near field")

    @property
    def cell_diameter(self) -> Union[None, float]:
        """Computed detector cell diameter.

        The diameter is computed from the current ``cell_distance`` and the
        stored ``cell_integration_angle`` in the near-field template.

        Returns
        -------
        Union[None, float]
            Diameter in millimeters when near-field is active, otherwise ``None``.
        """
        if self.near_field:
            diameter = (
                2
                * self.cell_distance
                * np.tan(
                    np.radians(
                        self._sensor_template.intensity_sensor_template.near_field.cell_integration_angle
                    )
                )
            )
            return diameter

    @cell_diameter.setter
    def cell_diameter(self, value: float) -> None:
        """Set detector cell diameter by updating the integration angle.

        Parameters
        ----------
        value : float
            Desired cell diameter in millimeters.

        Raises
        ------
        TypeError
            If near-field is not active on the sensor template.
        """
        if self.near_field:
            self._sensor_template.intensity_sensor_template.near_field.cell_integration_angle = (
                np.degrees(np.arctan(value / 2 / self.cell_distance))
            )
        else:
            raise TypeError("Sensor position is not in nearfield")

    @property
    def type(self) -> str:
        """Sensor data type.

        Returns
        -------
        str
            One of "Colorimetric", "Spectral" or the current type-name.
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return "Colorimetric"
        elif isinstance(self._type, BaseSensor.Spectral):
            return "Spectral"
        else:
            return self._type

    @property
    def colorimetric(self) -> Union[None, BaseSensor.Colorimetric]:
        """Colorimetric helper when enabled.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Colorimetric]
            Colorimetric helper instance or ``None`` if not active.
        """
        if isinstance(self._type, BaseSensor.Colorimetric):
            return self._type

    @property
    def spectral(self) -> Union[None, BaseSensor.Spectral]:
        """Spectral helper when enabled.

        Returns
        -------
        Union[None, ansys.speos.core.sensor.BaseSensor.Spectral]
            Spectral helper instance or ``None`` if not active.
        """
        if isinstance(self._type, BaseSensor.Spectral):
            return self._type

    @property
    def layer(
        self,
    ) -> Union[
        LayerTypes,
        BaseSensor.LayerTypeFace,
        BaseSensor.LayerTypeSequence,
    ]:
        """Layer separation configuration for intensity sensor.

        Returns
        -------
        Union[\
        ansys.speos.core.generic.parameters.LayerTypes,\
        ansys.speos.core.sensor.BaseSensor.LayerTypeFace,\
        ansys.speos.core.sensor.BaseSensor.LayerTypeSequence]
            Instance of Layertype Class for this sensor feature
        """
        return self._layer_type

    def set_orientation_x_as_meridian(self) -> None:
        """Set orientation: X as meridian, Y as parallel and reset dimensions."""
        self._sensor_template.intensity_sensor_template.intensity_orientation_x_as_meridian.SetInParent()
        self._set_dimension_values(IntensitySensorDimensionsXAsMeridianParameters())

    def set_orientation_x_as_parallel(self) -> None:
        """Set orientation: X as parallel, Y as meridian and reset dimensions."""
        self._sensor_template.intensity_sensor_template.intensity_orientation_x_as_parallel.SetInParent()
        self._set_dimension_values(IntensitySensorDimensionsXAsParallelParameters())

    def set_orientation_conoscopic(self) -> None:
        """Set orientation to conoscopic and reset dimensions."""
        self._sensor_template.intensity_sensor_template.intensity_orientation_conoscopic.SetInParent()
        self._set_dimension_values(IntensitySensorDimensionsConoscopicParameters())

    def set_viewing_direction_from_source(self) -> None:
        """Set viewing direction from source looking at sensor."""
        self._sensor_template.intensity_sensor_template.from_source_looking_at_sensor.SetInParent()

    def set_viewing_direction_from_sensor(self) -> None:
        """Set viewing direction from sensor looking at source."""
        self._sensor_template.intensity_sensor_template.from_sensor_looking_at_source.SetInParent()

    def _set_dimension_values(
        self,
        dimension: Union[
            IntensitySensorDimensionsXAsMeridianParameters,
            IntensitySensorDimensionsXAsParallelParameters,
            IntensitySensorDimensionsConoscopicParameters,
        ],
    ):
        template = self._sensor_template.intensity_sensor_template
        warning_msg = (
            "Mismatch of dimensions and sensor orientation was detected. "
            "The sensor dimension are reset to the orientation types default values"
        )
        if template.HasField("intensity_orientation_conoscopic"):
            if not isinstance(dimension, IntensitySensorDimensionsConoscopicParameters):
                warnings.warn(warning_msg)
                dimension = IntensitySensorDimensionsConoscopicParameters()
            self.theta_max = dimension.theta_max
            self.theta_sampling = dimension.theta_sampling
        else:
            if template.HasField("intensity_orientation_conoscopic"):
                if not isinstance(dimension, IntensitySensorDimensionsXAsParallelParameters):
                    warnings.warn(warning_msg)
                    dimension = IntensitySensorDimensionsXAsParallelParameters()
            elif template.HasField("intensity_orientation_x_as_meridian"):
                if not isinstance(dimension, IntensitySensorDimensionsXAsMeridianParameters):
                    warnings.warn(warning_msg)
                    dimension = IntensitySensorDimensionsXAsMeridianParameters()
            self.x_start = dimension.x_start
            self.x_end = dimension.x_end
            self.x_sampling = dimension.x_sampling
            self.y_start = dimension.y_start
            self.y_end = dimension.y_end
            self.y_sampling = dimension.y_sampling

    @property
    def x_start(self) -> Union[None, float]:
        """Minimum tilt on X axis (degrees) when applicable.

        Returns
        -------
        Union[None, float]
            Minimum x tilt in degrees, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.x_start
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.x_start

    @x_start.setter
    def x_start(self, value: float) -> None:
        """Set minimum X tilt (degrees).

        Parameters
        ----------
        value : float
            Minimum tilt on X axis in degrees.

        Raises
        ------
        TypeError
            If current orientation does not support X-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no x_start dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.x_start = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.x_start = value

    @property
    def x_end(self) -> Union[None, float]:
        """Maximum tilt on X axis (degrees) when applicable.

        Returns
        -------
        Union[None, float]
            Maximum x tilt in degrees, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.x_end
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.x_end

    @x_end.setter
    def x_end(self, value: float) -> None:
        """Set maximum X tilt (degrees).

        Parameters
        ----------
        value : float
            Maximum tilt on X axis in degrees.

        Raises
        ------
        TypeError
            If current orientation does not support X-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no x_end dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.x_end = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.x_end = value

    @property
    def x_sampling(self) -> Union[None, int]:
        """Sampling (pixels) along X axis when applicable.

        Returns
        -------
        Union[None, int]
            Number of samples along X axis, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.x_sampling
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.x_sampling

    @x_sampling.setter
    def x_sampling(self, value: int) -> None:
        """Set sampling along X axis.

        Parameters
        ----------
        value : int
            Number of samples (pixels) along X axis.

        Raises
        ------
        TypeError
            If current orientation does not support X-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no x_sampling dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.x_sampling = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.x_sampling = value

    @property
    def y_end(self) -> Union[None, float]:
        """Maximum tilt on Y axis (degrees) when applicable.

        Returns
        -------
        Union[None, float]
            Maximum y tilt in degrees, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.y_end
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.y_end

    @y_end.setter
    def y_end(self, value: float) -> None:
        """Set maximum Y tilt (degrees).

        Parameters
        ----------
        value : float
            Maximum tilt on Y axis in degrees.

        Raises
        ------
        TypeError
            If current orientation does not support Y-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no y_end dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.y_end = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.y_end = value

    @property
    def y_start(self) -> Union[None, float]:
        """Minimum tilt on Y axis (degrees) when applicable.

        Returns
        -------
        Union[None, float]
            Minimum y tilt in degrees, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.y_start
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.y_start

    @y_start.setter
    def y_start(self, value: float) -> None:
        """Set minimum Y tilt (degrees).

        Parameters
        ----------
        value : float
            Minimum tilt on Y axis in degrees.

        Raises
        ------
        TypeError
            If current orientation does not support Y-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no y_start dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.y_start = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.y_start = value

    @property
    def y_sampling(self) -> Union[None, int]:
        """Sampling (pixels) along Y axis when applicable.

        Returns
        -------
        Union[None, int]
            Number of samples along Y axis, or ``None`` for conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            warnings.warn("This property doesn't exist with the current orientation")
            return None
        elif template.HasField("intensity_orientation_x_as_parallel"):
            return template.intensity_orientation_x_as_parallel.intensity_dimensions.y_sampling
        elif template.HasField("intensity_orientation_x_as_meridian"):
            return template.intensity_orientation_x_as_meridian.intensity_dimensions.y_sampling

    @y_sampling.setter
    def y_sampling(self, value: int) -> None:
        """Set sampling along Y axis.

        Parameters
        ----------
        value : int
            Number of samples (pixels) along Y axis.

        Raises
        ------
        TypeError
            If current orientation does not support Y-axis angular dimensions.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            raise TypeError("Conoscopic Sensor has no y_sampling dimension")
        elif template.HasField("intensity_orientation_x_as_parallel"):
            template.intensity_orientation_x_as_parallel.intensity_dimensions.y_sampling = value
        elif template.HasField("intensity_orientation_x_as_meridian"):
            template.intensity_orientation_x_as_meridian.intensity_dimensions.y_sampling = value

    @property
    def theta_max(self) -> Union[None, float]:
        """Maximum theta angle for conoscopic orientation (degrees).

        Returns
        -------
        Union[None, float]
            Maximum theta in degrees for conoscopic maps, otherwise ``None``.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            return (
                template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.theta_max
            )
        else:
            warnings.warn("This property doesn't exist with the current orientation")
            return None

    @theta_max.setter
    def theta_max(self, value: float) -> None:
        """Set maximum theta for conoscopic orientation.

        Parameters
        ----------
        value : float
            Maximum theta angle in degrees.

        Raises
        ------
        TypeError
            If sensor is not configured in conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.theta_max = (
                value
            )
        else:
            raise TypeError("Only Conoscopic Sensor has theta_max dimension")

    @property
    def theta_sampling(self) -> Union[None, int]:
        """Sampling along theta axis for conoscopic orientation.

        Returns
        -------
        Union[None, int]
            Theta sampling (number of radial samples) for conoscopic maps, or
            ``None`` if not in conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            return (
                template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.sampling
            )
        else:
            warnings.warn("This property doesn't exist with the current orientation")
            return None

    @theta_sampling.setter
    def theta_sampling(self, value: int) -> None:
        """Set sampling along theta axis for conoscopic orientation.

        Parameters
        ----------
        value : int
            Number of radial samples (theta sampling).

        Raises
        ------
        TypeError
            If sensor is not configured in conoscopic orientation.
        """
        template = self._sensor_template.intensity_sensor_template
        if template.HasField("intensity_orientation_conoscopic"):
            template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.sampling = (
                value
            )
        else:
            raise TypeError("Only Conoscopic Sensor has theta_max dimension")

    def set_type_photometric(self) -> SensorXMPIntensity:
        """Select photometric sensor type (visible spectrum -> cd / lm).

        Returns
        -------
        ansys.speos.core.sensor.SensorXMPIntensity
            self for chaining
        """
        self._sensor_template.intensity_sensor_template.sensor_type_photometric.SetInParent()
        self._type = SensorTypes.photometric.capitalize()
        return self

    def set_type_colorimetric(self) -> BaseSensor.Colorimetric:
        """Select colorimetric sensor type and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Colorimetric
            Colorimetric helper.
        """
        if self._type is None and self._sensor_template.intensity_sensor_template.HasField(
            "sensor_type_colorimetric"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.intensity_sensor_template.sensor_type_colorimetric,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Colorimetric):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSensor.Colorimetric(
                sensor_type_colorimetric=self._sensor_template.intensity_sensor_template.sensor_type_colorimetric,
                stable_ctr=True,
                default_parameters=ColorimetricParameters(),
            )
        elif (
            self._type._sensor_type_colorimetric
            is not self._sensor_template.intensity_sensor_template.sensor_type_colorimetric
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_colorimetric = (
                self._sensor_template.intensity_sensor_template.sensor_type_colorimetric
            )
        return self._type

    def set_type_radiometric(self) -> SensorXMPIntensity:
        """Select radiometric sensor type (full spectrum -> W/m2).

        Returns
        -------
        ansys.speos.core.sensor.SensorXMPIntensity
            self for chaining
        """
        self._sensor_template.intensity_sensor_template.sensor_type_radiometric.SetInParent()
        self._type = SensorTypes.radiometric.capitalize()
        return self

    def set_type_spectral(self) -> BaseSensor.Spectral:
        """Select spectral sensor type and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.Spectral
            Spectral helper.
        """
        if self._type is None and self._sensor_template.intensity_sensor_template.HasField(
            "sensor_type_spectral"
        ):
            # Happens in case of project created via load of speos file
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.intensity_sensor_template.sensor_type_spectral,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSensor.Spectral):
            # if the _type is not Spectral then we create a new type.
            self._type = BaseSensor.Spectral(
                sensor_type_spectral=self._sensor_template.intensity_sensor_template.sensor_type_spectral,
                stable_ctr=True,
                default_parameters=SpectralParameters(),
            )
        elif (
            self._type._sensor_type_spectral
            is not self._sensor_template.intensity_sensor_template.sensor_type_spectral
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sensor_type_spectral = (
                self._sensor_template.intensity_sensor_template.sensor_type_spectral
            )
        return self._type

    def set_layer_type_none(self) -> SensorXMPIntensity:
        """Disable layer separation (single-layer results).

        Returns
        -------
        ansys.speos.core.sensor.SensorXMPIntensity
            self for chaining
        """
        self._sensor_instance.intensity_properties.layer_type_none.SetInParent()
        self._layer_type = LayerTypes.none
        return self

    def set_layer_type_source(self) -> SensorXMPIntensity:
        """Enable layer separation by source (one layer per active source).

        Returns
        -------
        ansys.speos.core.sensor.SensorXMPIntensity
            self for chaining
        """
        self._sensor_instance.intensity_properties.layer_type_source.SetInParent()
        self._layer_type = LayerTypes.by_source
        return self

    def set_layer_type_face(self) -> BaseSensor.LayerTypeFace:
        """Define layer separation by face and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeFace
            LayerTypeFace helper
        """
        if self._layer_type is None and self._sensor_instance.intensity_properties.HasField(
            "layer_type_face"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.intensity_properties.layer_type_face,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeFace):
            # if the _layer_type is not LayerTypeFace then we create a new type.
            self._layer_type = BaseSensor.LayerTypeFace(
                layer_type_face=self._sensor_instance.intensity_properties.layer_type_face,
                stable_ctr=True,
                default_parameters=LayerByFaceParameters(),
            )
        elif (
            self._layer_type._layer_type_face
            is not self._sensor_instance.intensity_properties.layer_type_face
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_face = (
                self._sensor_instance.intensity_properties.layer_type_face
            )
        return self._layer_type

    def set_layer_type_sequence(self) -> BaseSensor.LayerTypeSequence:
        """Define layer separation by sequence and return helper.

        Returns
        -------
        ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
            LayerTypeSequence helper
        """
        if self._layer_type is None and self._sensor_instance.intensity_properties.HasField(
            "layer_type_sequence"
        ):
            # Happens in case of project created via load of speos file
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.intensity_properties.layer_type_sequence,
                stable_ctr=True,
            )
        elif not isinstance(self._layer_type, BaseSensor.LayerTypeSequence):
            # if the _layer_type is not LayerTypeSequence then we create a new type.
            self._layer_type = BaseSensor.LayerTypeSequence(
                layer_type_sequence=self._sensor_instance.intensity_properties.layer_type_sequence,
                stable_ctr=True,
                default_parameters=LayerBySequenceParameters(),
            )
        elif (
            self._layer_type._layer_type_sequence
            is not self._sensor_instance.intensity_properties.layer_type_sequence
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._layer_type._layer_type_sequence = (
                self._sensor_instance.intensity_properties.layer_type_sequence
            )
        return self._layer_type

    @property
    def axis_system(self) -> list[float]:
        """Sensor axis system (position + orientation).

        Returns
        -------
        list[float]
            Axis system as [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        """
        return self._sensor_instance.intensity_properties.axis_system

    @axis_system.setter
    def axis_system(self, value: list[float]):
        """Set the sensor axis system.

        Parameters
        ----------
        value : list[float]
            Axis system array [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        """
        self._sensor_instance.intensity_properties.axis_system[:] = value
