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
from typing import List, Mapping, Optional, Union
import uuid

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sensor_template import ProtoSensorTemplate
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
        else:
            self._unique_id = sensor_instance.metadata["UniqueId"]
            self.sensor_template_link = self._project.client.get_item(
                key=sensor_instance.sensor_guid
            )
            # reset will fill _sensor_instance and _sensor_template from respectively project (using _unique_id) and sensor_template_link
            self.reset()

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
        **Do not instantiate this class yourself**, use set_wavelengths_range method available in sensor classes.

        """

        def __init__(
            self,
            wavelengths_range: common_pb2.WavelengthsRange,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "WavelengthsRange class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._wavelengths_range = wavelengths_range

            if default_values:
                # Default values
                self.set_start().set_end().set_sampling()

        def set_start(self, value: float = 400) -> BaseSensor.WavelengthsRange:
            """Set the minimum wavelength of the range.

            Parameters
            ----------
            value : float
                Minimum wavelength (nm).
                By default, ``400``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                WavelengthsRange.
            """
            self._wavelengths_range.w_start = value
            return self

        def set_end(self, value: float = 700) -> BaseSensor.WavelengthsRange:
            """Set the maximum wavelength of the range.

            Parameters
            ----------
            value : float
                Maximum wavelength (nm).
                By default, ``700``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                WavelengthsRange.
            """
            self._wavelengths_range.w_end = value
            return self

        def set_sampling(self, value: int = 13) -> BaseSensor.WavelengthsRange:
            """Set the sampling of wavelengths range.

            Parameters
            ----------
            value : int
                Number of wavelengths to be taken into account between the minimum and maximum wavelengths range.
                By default, ``13``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.WavelengthsRange
                WavelengthsRange.
            """
            self._wavelengths_range.w_sampling = value
            return self

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
        **Do not instantiate this class yourself**, use set_dimensions method available in sensor classes.
        """

        def __init__(
            self,
            sensor_dimensions: common_pb2.SensorDimensions,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Dimension class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_dimensions = sensor_dimensions

            if default_values:
                # Default values
                self.set_x_start().set_x_end().set_x_sampling().set_y_start().set_y_end().set_y_sampling()

        def set_x_start(self, value: float = -50) -> BaseSensor.Dimensions:
            """Set the minimum value on x axis.

            Parameters
            ----------
            value : float
                Minimum value on x axis (mm).
                By default, ``-50``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_start = value
            return self

        def set_x_end(self, value: float = 50) -> BaseSensor.Dimensions:
            """Set the maximum value on x axis.

            Parameters
            ----------
            value : float
                Maximum value on x axis (mm).
                By default, ``50``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_end = value
            return self

        def set_x_sampling(self, value: int = 100) -> BaseSensor.Dimensions:
            """Set the sampling value on x axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on x axis.
                By default, ``100``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_sampling = value
            return self

        def set_y_start(self, value: float = -50) -> BaseSensor.Dimensions:
            """Set the minimum value on y axis.

            Parameters
            ----------
            value : float
                Minimum value on y axis (mm).
                By default, ``-50``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.y_start = value
            return self

        def set_y_end(self, value: float = 50) -> BaseSensor.Dimensions:
            """Set the maximum value on y axis.

            Parameters
            ----------
            value : float
                Maximum value on y axis (mm).
                By default, ``50``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.y_end = value
            return self

        def set_y_sampling(self, value: int = 100) -> BaseSensor.Dimensions:
            """Set the sampling value on y axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on y axis.
                By default, ``100``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.y_sampling = value
            return self

    class Colorimetric:
        """Type of sensor : Colorimetric.
        This kind of sensor will generate color results without any spectral data or layer separation (in lx or W//m2).
        By default, it uses a default wavelengths range.

        Parameters
        ----------
        sensor_type_colorimetric : ansys.api.speos.sensor.v1.common_pb2.SensorTypeColorimetric
            SensorTypeColorimetric protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_type_colorimetric method available in sensor classes.
        """

        def __init__(
            self,
            sensor_type_colorimetric: common_pb2.SensorTypeColorimetric,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Colorimetric class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = BaseSensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_colorimetric.wavelengths_range,
                default_values=default_values,
                stable_ctr=stable_ctr,
            )

            if default_values:
                # Default values
                self.set_wavelengths_range()

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
        This kind of sensor will generate color results and spectral data separated by wavelength (in lx or W/m2).
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
        **Do not instantiate this class yourself**, use set_type_spectral method available in sensor classes.
        """

        def __init__(
            self,
            sensor_type_spectral: common_pb2.SensorTypeSpectral,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Spectral class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sensor_type_spectral = sensor_type_spectral

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = BaseSensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_spectral.wavelengths_range,
                default_values=default_values,
                stable_ctr=stable_ctr,
            )

            if default_values:
                # Default values
                self.set_wavelengths_range()

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
        geometries : List[ansys.speos.core.geo_ref.GeoRef]
            List of geometries included in this layer.

        """

        def __init__(self, name: str, geometries: List[GeoRef]) -> None:
            self.name = name
            """Name of the layer"""
            self.geometries = geometries
            """List of geometries included in this layer."""

    class LayerTypeFace:
        """Type of layer : Face.
        Includes in the result one layer per surface selected.
        By default, a filtering mode by last impact is chosen.

        Parameters
        ----------
        layer_type_face : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeFace
            LayerTypeFace protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_face method available in sensor classes.
        """

        def __init__(
            self,
            layer_type_face: ProtoScene.SensorInstance.LayerTypeFace,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeFace class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_face = layer_type_face

            if default_values:
                # Default values
                self.set_sca_filtering_mode_last_impact()

        def set_sca_filtering_mode_intersected_one_time(self) -> BaseSensor.LayerTypeFace:
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

        def set_sca_filtering_mode_last_impact(self) -> BaseSensor.LayerTypeFace:
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

        def set_layers(self, values: List[BaseSensor.FaceLayer]) -> BaseSensor.LayerTypeFace:
            """Set the layers.

            Parameters
            ----------
            values : List[ansys.speos.core.sensor.BaseSensor.FaceLayer]
                List of layers

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeFace
                LayerTypeFace.
            """
            my_list = [
                ProtoScene.SensorInstance.LayerTypeFace.Layer(
                    name=layer.name,
                    geometries=ProtoScene.GeoPaths(
                        geo_paths=[gr.to_native_link() for gr in layer.geometries]
                    ),
                )
                for layer in values
            ]
            self._layer_type_face.ClearField("layers")
            self._layer_type_face.layers.extend(my_list)
            return self

    class LayerTypeSequence:
        """Type of layer : Sequence.
        Includes in the result one layer per sequence.
        By default, the sequence is defined per geometries, with a maximum number of 10 sequences.

        Parameters
        ----------
        layer_type_sequence : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeSequence
            LayerTypeSequence protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_sequence method available in sensor classes.
        """

        def __init__(
            self,
            layer_type_sequence: ProtoScene.SensorInstance.LayerTypeSequence,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeSequence class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_sequence = layer_type_sequence

            if default_values:
                # Default values
                self.set_maximum_nb_of_sequence().set_define_sequence_per_geometries()

        def set_maximum_nb_of_sequence(self, value: int = 10) -> BaseSensor.LayerTypeSequence:
            """Set the maximum number of sequences.

            Parameters
            ----------
            value : int
                Maximum number of sequences.
                By default, ``10``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.maximum_nb_of_sequence = value
            return self

        def set_define_sequence_per_geometries(self) -> BaseSensor.LayerTypeSequence:
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
        layer_type_incidence_angle : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.LayerTypeIncidenceAngle
            LayerTypeIncidenceAngle protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_layer_type_incidence_angle method available in sensor classes.
        """

        def __init__(
            self,
            layer_type_incidence_angle: ProtoScene.SensorInstance.LayerTypeIncidenceAngle,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "LayerTypeIncidenceAngle class instantiated outside of class scope"
                raise RuntimeError(msg)

            self._layer_type_incidence_angle = layer_type_incidence_angle

            if default_values:
                # Default values
                self.set_sampling()

        def set_sampling(self, value: int = 9) -> BaseSensor.LayerTypeIncidenceAngle:
            """Set the sampling for incidence angles.

            Parameters
            ----------
            value : int
                Sampling for incidence angles.
                By default, ``9``.

            Returns
            -------
            ansys.speos.core.sensor.BaseSensor.LayerTypeIncidenceAngle
                LayerTypeIncidenceAngle.
            """
            self._layer_type_incidence_angle.sampling = value
            return self

    def _to_dict(self) -> dict:
        out_dict = {}

        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next(
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None
            )
            if ssr_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=ssr_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self._sensor_instance
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._sensor_instance
            )

        if "sensor" not in out_dict.keys():
            # SensorTemplate
            if self.sensor_template_link is None:
                out_dict["sensor"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self._sensor_template
                )
            else:
                out_dict["sensor"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self.sensor_template_link.get()
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
            content.sort(key=lambda x: SequenceMatcher(None, x[0], key).ratio(), reverse=True)
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
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None
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
        # The _unique_id will help to find the correct item in the scene.sensors (the list of SensorInstance)
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
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None
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
                (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None
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
            (x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None
        )
        if ssr_inst is not None:
            scene_data.sensors.remove(ssr_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._sensor_instance.metadata.pop("UniqueId")
        return self

