# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

from typing import List, Mapping, Optional
import uuid

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2, irradiance_sensor_pb2

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project


class Sensor:
    class WavelengthsRange:
        def __init__(self, wavelengths_range: common_pb2.WavelengthsRange) -> None:
            self._wavelengths_range = wavelengths_range

            # Default values
            self.set_start().set_end().set_sampling()

        def set_start(self, value: float = 400) -> Sensor.WavelengthsRange:
            self._wavelengths_range.w_start = value
            return self

        def set_end(self, value: float = 700) -> Sensor.WavelengthsRange:
            self._wavelengths_range.w_end = value
            return self

        def set_sampling(self, value: int = 13) -> Sensor.WavelengthsRange:
            self._wavelengths_range.w_sampling = value
            return self

    class Dimensions:
        def __init__(self, sensor_dimensions: common_pb2.SensorDimensions) -> None:
            self._sensor_dimensions = sensor_dimensions

            # Default values
            self.set_x_start().set_x_end().set_x_sampling().set_y_start().set_y_end().set_y_sampling()

        def set_x_start(self, value: float = -50) -> Sensor.Dimensions:
            self._sensor_dimensions.x_start = value
            return self

        def set_x_end(self, value: float = 50) -> Sensor.Dimensions:
            self._sensor_dimensions.x_end = value
            return self

        def set_x_sampling(self, value: int = 100) -> Sensor.Dimensions:
            self._sensor_dimensions.x_sampling = value
            return self

        def set_y_start(self, value: float = -50) -> Sensor.Dimensions:
            self._sensor_dimensions.y_start = value
            return self

        def set_y_end(self, value: float = 50) -> Sensor.Dimensions:
            self._sensor_dimensions.y_end = value
            return self

        def set_y_sampling(self, value: int = 100) -> Sensor.Dimensions:
            self._sensor_dimensions.y_sampling = value
            return self

    class Colorimetric:
        def __init__(self, sensor_type_colorimetric: common_pb2.SensorTypeColorimetric) -> None:
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = Sensor.WavelengthsRange(wavelengths_range=self._sensor_type_colorimetric.wavelengths_range)

            # Default values
            self.set_wavelengths_range()

        def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
            return self._wavelengths_range

    class Spectral:
        def __init__(self, sensor_type_spectral: common_pb2.SensorTypeSpectral) -> None:
            self._sensor_type_spectral = sensor_type_spectral

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = Sensor.WavelengthsRange(wavelengths_range=self._sensor_type_spectral.wavelengths_range)

            # Default values
            self.set_wavelengths_range()

        def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
            return self._wavelengths_range

    class Camera:
        class Photometric:
            class Color:
                class BalanceModeUserWhite:
                    def __init__(self, balance_mode_user_white: camera_sensor_pb2.SensorCameraBalanceModeUserwhite) -> None:
                        self._balance_mode_user_white = balance_mode_user_white

                        # Default values
                        self.set_red_gain().set_green_gain().set_blue_gain()

                    def set_red_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        self._balance_mode_user_white.red_gain = value
                        return self

                    def set_green_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        self._balance_mode_user_white.green_gain = value
                        return self

                    def set_blue_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        self._balance_mode_user_white.blue_gain = value
                        return self

                class BalanceModeDisplayPrimaries:
                    def __init__(self, balance_mode_display: camera_sensor_pb2.SensorCameraBalanceModeDisplay) -> None:
                        self._balance_mode_display = balance_mode_display

                        # Default values
                        self._balance_mode_display.SetInParent()

                    def set_red_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        self._balance_mode_display.red_display_file_uri = uri
                        return self

                    def set_green_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        self._balance_mode_display.green_display_file_uri = uri
                        return self

                    def set_blue_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        self._balance_mode_display.blue_display_file_uri = uri
                        return self

                def __init__(self, mode_color: camera_sensor_pb2.SensorCameraColorModeColor) -> None:
                    self._mode_color = mode_color

                    # Attribute gathering more complex camera balance mode
                    self._mode = None

                    # Default values
                    self.set_balance_mode_none()

                def set_red_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    self._mode_color.red_spectrum_file_uri = uri
                    return self

                def set_green_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    self._mode_color.green_spectrum_file_uri = uri
                    return self

                def set_blue_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    self._mode_color.blue_spectrum_file_uri = uri
                    return self

                def set_balance_mode_none(self) -> Sensor.Camera.Photometric.Color:
                    self._mode = None
                    self._mode_color.balance_mode_none.SetInParent()
                    return self

                def set_balance_mode_grey_world(self) -> Sensor.Camera.Photometric.Color:
                    self._mode = None
                    self._mode_color.balance_mode_greyworld.SetInParent()
                    return self

                def set_balance_mode_user_white(self) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                    if type(self._mode) != Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeUserWhite(
                            balance_mode_user_white=self._mode_color.balance_mode_userwhite
                        )
                    return self._mode

                def set_balance_mode_display_primaries(self) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                    if type(self._mode) != Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries(
                            balance_mode_display=self._mode_color.balance_mode_display
                        )
                    return self._mode

            def __init__(self, mode_photometric: camera_sensor_pb2.SensorCameraModePhotometric) -> None:
                self._mode_photometric = mode_photometric

                # Attribute gathering more complex camera color mode
                self._mode = None

                # Attribute to keep track of wavelength range object
                self._wavelengths_range = Sensor.WavelengthsRange(wavelengths_range=self._mode_photometric.wavelengths_range)

                # Default values
                self.set_acquisition_integration().set_acquisition_lag_time().set_gamma_correction().set_png_bits_16().set_mode_color()
                self.set_wavelengths_range()

            def set_acquisition_integration(self, value: float = 0.01) -> Sensor.Camera.Photometric:
                self._mode_photometric.acquisition_integration = value
                return self

            def set_acquisition_lag_time(self, value: float = 0.0) -> Sensor.Camera.Photometric:
                self._mode_photometric.acquisition_lag_time = value
                return self

            def set_transmittance_file_uri(self, uri: str) -> Sensor.Camera.Photometric:
                self._mode_photometric.transmittance_file_uri = uri
                return self

            def set_gamma_correction(self, value: float = 2.2) -> Sensor.Camera.Photometric:
                self._mode_photometric.gamma_correction = value
                return self

            def set_png_bits_08(self) -> Sensor.Camera.Photometric:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
                return self

            def set_png_bits_10(self) -> Sensor.Camera.Photometric:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
                return self

            def set_png_bits_12(self) -> Sensor.Camera.Photometric:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
                return self

            def set_png_bits_16(self) -> Sensor.Camera.Photometric:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
                return self

            def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
                return self._wavelengths_range

            def set_mode_monochromatic(self, spectrum_file_uri: str) -> Sensor.Camera.Photometric:
                self._mode = None
                self._mode_photometric.color_mode_monochromatic.spectrum_file_uri = spectrum_file_uri
                return self

            def set_mode_color(self) -> Sensor.Camera.Photometric.Color:
                if type(self._mode) != Sensor.Camera.Photometric.Color:
                    self._mode = Sensor.Camera.Photometric.Color(mode_color=self._mode_photometric.color_mode_color)
                return self._mode

        def __init__(self, camera_template: camera_sensor_pb2.CameraSensorTemplate) -> None:
            self._camera_template = camera_template

            # Attribute gathering more complex camera mode
            self._mode = None

            # Default values
            self.set_focal_length().set_imager_distance().set_f_number().set_horz_pixel()
            self.set_vert_pixel().set_width().set_height().set_mode_photometric()

        def set_focal_length(self, value: float = 5.0) -> Sensor.Camera:
            self._camera_template.focal_length = value
            return self

        def set_imager_distance(self, value: float = 10) -> Sensor.Camera:
            self._camera_template.imager_distance = value
            return self

        def set_f_number(self, value: float = 20) -> Sensor.Camera:
            self._camera_template.f_number = value
            return self

        def set_distortion_file_uri(self, uri: str) -> Sensor.Camera:
            self._camera_template.distortion_file_uri = uri
            return self

        def set_horz_pixel(self, value: int = 640) -> Sensor.Camera:
            self._camera_template.horz_pixel = value
            return self

        def set_vert_pixel(self, value: int = 480) -> Sensor.Camera:
            self._camera_template.vert_pixel = value
            return self

        def set_width(self, value: float = 5.0) -> Sensor.Camera:
            self._camera_template.width = value
            return self

        def set_height(self, value: float = 5.0) -> Sensor.Camera:
            self._camera_template.height = value
            return self

        def set_mode_geometric(self) -> Sensor.Camera:
            self._mode = None
            self._camera_template.sensor_mode_geometric.SetInParent()
            return self

        def set_mode_photometric(self) -> Sensor.Camera.Photometric:
            if type(self._mode) != Sensor.Camera.Photometric:
                self._mode = Sensor.Camera.Photometric(mode_photometric=self._camera_template.sensor_mode_photometric)
            return self._mode

    class Irradiance:
        def __init__(self, irradiance_template: irradiance_sensor_pb2.IrradianceSensorTemplate) -> None:
            self._irradiance_template = irradiance_template

            # Attribute gathering more complex irradiance type
            self._type = None

            # Attribute to keep track of sensor dimensions object
            self._dimensions = Sensor.Dimensions(sensor_dimensions=self._irradiance_template.dimensions)

            # Default values
            self.set_type_photometric().set_illuminance_type_planar().set_dimensions()

        def set_type_photometric(self) -> Sensor.Irradiance:
            self._irradiance_template.sensor_type_photometric.SetInParent()
            self._type = None
            return self

        def set_type_colorimetric(self) -> Sensor.Colorimetric:
            if type(self._type) != Sensor.Colorimetric:
                self._type = Sensor.Colorimetric(sensor_type_colorimetric=self._irradiance_template.sensor_type_colorimetric)
            return self._type

        def set_type_radiometric(self) -> Sensor.Irradiance:
            self._irradiance_template.sensor_type_radiometric.SetInParent()
            self._type = None
            return self

        def set_type_spectral(self) -> Sensor.Spectral:
            if type(self._type) != Sensor.Spectral:
                self._type = Sensor.Spectral(sensor_type_spectral=self._irradiance_template.sensor_type_spectral)
            return self._type

        def set_illuminance_type_planar(self) -> Sensor.Irradiance:
            self._irradiance_template.illuminance_type_planar.SetInParent()
            return self

        def set_illuminance_type_radial(self) -> Sensor.Irradiance:
            self._irradiance_template.illuminance_type_radial.SetInParent()
            return self

        def set_illuminance_type_hemispherical(self) -> Sensor.Irradiance:
            self._irradiance_template.illuminance_type_hemispherical.SetInParent()
            return self

        def set_illuminance_type_cylindrical(self) -> Sensor.Irradiance:
            self._irradiance_template.illuminance_type_cylindrical.SetInParent()
            return self

        def set_illuminance_type_semi_cylindrical(self) -> Sensor.Irradiance:
            self._irradiance_template.illuminance_type_semi_cylindrical.SetInParent()
            return self

        def set_dimensions(self) -> Sensor.Dimensions:
            return self._dimensions

    class LayerTypeFace:
        class Layer:
            def __init__(self, name: str, geometries: List[GeoRef]) -> None:
                self.name = name
                self.geometries = geometries

        def __init__(self, layer_type_face: core.Scene.SensorInstance.LayerTypeFace) -> None:
            self._layer_type_face = layer_type_face

            # Default values
            self.set_sca_filtering_mode_last_impact()

        def set_sca_filtering_mode_intersected_one_time(self) -> Sensor.LayerTypeFace:
            self._layer_type_face.sca_filtering_mode = self._layer_type_face.EnumSCAFilteringType.IntersectedOneTime
            return self

        def set_sca_filtering_mode_last_impact(self) -> Sensor.LayerTypeFace:
            self._layer_type_face.sca_filtering_mode = self._layer_type_face.EnumSCAFilteringType.LastImpact
            return self

        def set_layers(self, values: List[Sensor.LayerTypeFace.Layer]) -> Sensor.LayerTypeFace:
            my_list = [
                core.Scene.SensorInstance.LayerTypeFace.Layer(name=layer.name, geometries=[gr.to_native_link() for gr in layer.geometries])
                for layer in values
            ]
            self._layer_type_face.ClearField("layers")
            self._layer_type_face.layers.extend(my_list)
            return self

    class LayerTypeSequence:
        def __init__(self, layer_type_sequence: core.Scene.SensorInstance.LayerTypeSequence) -> None:
            self._layer_type_sequence = layer_type_sequence

            # Default values
            self.set_maximum_nb_of_sequence().set_define_sequence_per_geometries()

        def set_maximum_nb_of_sequence(self, value: int = 10) -> Sensor.LayerTypeSequence:
            self._layer_type_sequence.maximum_nb_of_sequence = value
            return self

        def set_define_sequence_per_geometries(self) -> Sensor.LayerTypeSequence:
            self._layer_type_sequence.define_sequence_per = self._layer_type_sequence.EnumSequenceType.Geometries
            return self

        def set_define_sequence_per_faces(self) -> Sensor.LayerTypeSequence:
            self._layer_type_sequence.define_sequence_per = self._layer_type_sequence.EnumSequenceType.Faces
            return self

    class LayerTypeIncidenceAngle:
        def __init__(self, layer_type_incidence_angle: core.Scene.SensorInstance.LayerTypeIncidenceAngle) -> None:
            self._layer_type_incidence_angle = layer_type_incidence_angle

            # Default values
            self.set_sampling()

        def set_sampling(self, value: int = 9) -> Sensor.LayerTypeIncidenceAngle:
            self._layer_type_incidence_angle.sampling = value
            return self

    class CameraProperties:
        def __init__(self, camera_props: core.Scene.SensorInstance.CameraProperties) -> None:
            self.camera_props = camera_props

            # Default values
            self.set_axis_system().set_layer_type_none()

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Sensor.CameraProperties:
            """Set position of the sensor.

            Parameters
            ----------
            axis_system : List[float]
                Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.CameraProperties
                Camera Sensor properties.
            """
            self.camera_props.axis_system[:] = axis_system
            return self

        def set_trajectory_file_uri(self, uri: str) -> Sensor.CameraProperties:
            self.camera_props.trajectory_file_uri = uri
            return self

        def set_layer_type_none(self) -> Sensor.CameraProperties:
            self.camera_props.layer_type_none.SetInParent()
            return self

        def set_layer_type_source(self) -> Sensor.CameraProperties:
            self.camera_props.layer_type_source.SetInParent()
            return self

    class IrradianceProperties:
        def __init__(self, irradiance_props: core.Scene.SensorInstance.IrradianceProperties) -> None:
            self._irradiance_props = irradiance_props

            # Attribute representing more complex sensor layer types
            self._layer_type = None

            # Default values
            self.set_axis_system().set_ray_file_type_none().set_layer_type_none()

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Sensor.IrradianceProperties:
            """Set position of the sensor.

            Parameters
            ----------
            axis_system : List[float]
                Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.IrradianceProperties
                Irradiance Sensor properties.
            """
            self._irradiance_props.axis_system[:] = axis_system
            return self

        def set_ray_file_type_none(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.ray_file_type = self._sensor_instance.EnumRayFileType.RayFileNone
            return self

        def set_ray_file_type_classic(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.ray_file_type = self._sensor_instance.EnumRayFileType.RayFileClassic
            return self

        def set_ray_file_type_polarization(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.ray_file_type = self._sensor_instance.EnumRayFileType.RayFilePolarization
            return self

        def set_ray_file_type_tm25(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.ray_file_type = self._sensor_instance.EnumRayFileType.RayFileTM25
            return self

        def set_ray_file_type_tm25_no_polarization(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.ray_file_type = self._sensor_instance.EnumRayFileType.RayFileTM25NoPolarization
            return self

        def set_layer_type_none(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.layer_type_none.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_source(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.layer_type_source.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_face(self) -> Sensor.LayerTypeFace:
            if type(self._layer_type) != Sensor.LayerTypeFace:
                self._layer_type = Sensor.LayerTypeFace(layer_type_face=self._irradiance_props.layer_type_face)
            return self._layer_type

        def set_layer_type_sequence(self) -> Sensor.LayerTypeSequence:
            if type(self._layer_type) != Sensor.LayerTypeSequence:
                self._layer_type = Sensor.LayerTypeSequence(layer_type_face=self._irradiance_props.layer_type_sequence)
            return self._layer_type

        def set_layer_type_polarization(self) -> Sensor.IrradianceProperties:
            self._irradiance_props.layer_type_polarization.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_incidence_angle(self) -> Sensor.LayerTypeIncidenceAngle:
            if type(self._layer_type) != Sensor.LayerTypeIncidenceAngle:
                self._layer_type = Sensor.LayerTypeIncidenceAngle(layer_type_face=self._irradiance_props.layer_type_incidence_angle)
            return self._layer_type

        def set_integration_direction(self, value: Optional[List[float]] = None) -> Sensor.IrradianceProperties:
            if value is None or value == []:
                self._irradiance_props.ClearField("integration_direction")
            else:
                self._irradiance_props.integration_direction[:] = value
            return self

        def set_output_face_geometries(self, geometries: List[GeoRef] = []) -> Sensor.IrradianceProperties:
            if geometries == []:
                self._irradiance_props.ClearField("output_face_geometries")
            else:
                self._irradiance_props.output_face_geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._unique_id = None
        self.sensor_template_link = None
        """Link object for the sensor template in database."""

        # Attribute representing the kind of sensor. Can be on object of type script.Sensor.Camera, script.Sensor.Irradiance, ...
        self._type = None
        # Attribute gathering more complex sensor properties
        self._props = None

        # Create local SensorTemplate
        self._sensor_template = core.SensorTemplate(name=name, description=description, metadata=metadata)

        # Create local SensorInstance
        self._sensor_instance = core.Scene.SensorInstance(name=name, description=description, metadata=metadata)

    def set_camera(self) -> Camera:
        """Set the sensor as camera.

        Returns
        -------
        ansys.speos.script.sensor.Sensor.Camera
            Camera sensor.
        """
        if type(self._type) != Sensor.Camera:
            self._type = Sensor.Camera(camera_template=self._sensor_template.camera_sensor_template)
        return self._type

    def set_irradiance(self) -> Irradiance:
        """Set the sensor as irradiance.

        Returns
        -------
        ansys.speos.script.sensor.Sensor.Irradiance
            Irradiance sensor.
        """
        if type(self._type) != Sensor.Irradiance:
            self._type = Sensor.Irradiance(irradiance_template=self._sensor_template.irradiance_sensor_template)
        return self._type

    def set_camera_properties(self) -> Sensor.CameraProperties:
        if type(self._props) != Sensor.CameraProperties:
            self._props = Sensor.CameraProperties(camera_props=self._sensor_instance.camera_properties)
        return self._props

    def set_irradiance_properties(self) -> Sensor.IrradianceProperties:
        if type(self._props) != Sensor.IrradianceProperties:
            self._props = Sensor.IrradianceProperties(irradiance_props=self._sensor_instance.irradiance_properties)
        return self._props

    def __str__(self) -> str:
        """Return the string representation of the sensor."""
        out_str = ""
        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is not None:
                out_str += core.protobuf_message_to_str(ssr_inst)
            else:
                out_str += f"local: " + core.protobuf_message_to_str(self._sensor_instance)
        else:
            out_str += f"local: " + core.protobuf_message_to_str(self._sensor_instance)

        # SensorTemplate
        if self.sensor_template_link is None:
            out_str += f"\nlocal: {self._sensor_template}"
        else:
            out_str += "\n" + str(self.sensor_template_link)

        return out_str

    def commit(self) -> Sensor:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.sensor.Sensor
            Sensor feature.
        """
        # The _unique_id will help to find correct item in the scene.sensors (the list of SensorInstance)
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._sensor_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the sensor template (depending on if it was already saved before)
        if self.sensor_template_link is None:
            self.sensor_template_link = self._project.client.sensor_templates().create(message=self._sensor_template)
            self._sensor_instance.sensor_guid = self.sensor_template_link.key
        else:
            self.sensor_template_link.set(data=self._sensor_template)

        # Update the scene with the sensor instance
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is not None:
                ssr_inst.CopyFrom(self._sensor_instance)  # if yes, just replace
            else:
                scene_data.sensors.append(self._sensor_instance)  # if no, just add it to the list of sensor instances

            self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> Sensor:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.sensor.Sensor
            Sensor feature.
        """
        # Reset sensor template
        if self.sensor_template_link is not None:
            self._sensor_template = self.sensor_template_link.get()

        # Reset sensor instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is not None:
                self._sensor_instance = ssr_inst
        return self

    def delete(self) -> Sensor:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.sensor.Sensor
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
        ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
        if ssr_inst is not None:
            scene_data.sensors.remove(ssr_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._sensor_instance.metadata.pop("UniqueId")
        return self
