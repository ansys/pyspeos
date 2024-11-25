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

"""Provides a way to interact with Speos feature: Sensor."""
from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2, irradiance_sensor_pb2

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project
import ansys.speos.script.proto_message_utils as proto_message_utils


class Sensor:
    """Speos feature : Sensor.

    Parameters
    ----------
    project : ansys.speos.script.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.

    Attributes
    ----------
    sensor_template_link : ansys.speos.core.sensor_template.SensorTemplateLink
        Link object for the sensor template in database.
    """

    class WavelengthsRange:
        """Range of wavelengths.
        By default, a range from 400nm to 700nm is chosen, with a sampling of 13.

        Parameters
        ----------
        wavelengths_range : ansys.api.speos.sensor.v1.common_pb2.WavelengthsRange
            Wavelengths range protobuf object to modify.
        default_values : bool
            Uses default values when True.
        """

        def __init__(self, wavelengths_range: common_pb2.WavelengthsRange, default_values: bool = True) -> None:
            self._wavelengths_range = wavelengths_range

            if default_values:
                # Default values
                self.set_start().set_end().set_sampling()

        def set_start(self, value: float = 400) -> Sensor.WavelengthsRange:
            """Set the minimum wavelength of the range.

            Parameters
            ----------
            value : float
                Minimum wavelength (nm).
                By default, ``400``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.WavelengthsRange
                WavelengthsRange.
            """
            self._wavelengths_range.w_start = value
            return self

        def set_end(self, value: float = 700) -> Sensor.WavelengthsRange:
            """Set the maximum wavelength of the range.

            Parameters
            ----------
            value : float
                Maximum wavelength (nm).
                By default, ``700``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.WavelengthsRange
                WavelengthsRange.
            """
            self._wavelengths_range.w_end = value
            return self

        def set_sampling(self, value: int = 13) -> Sensor.WavelengthsRange:
            """Set the sampling of wavelengths range.

            Parameters
            ----------
            value : int
                Number of wavelengths to be taken into account between the minimum and maximum wavelengths range.
                By default, ``13``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.WavelengthsRange
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
        """

        def __init__(self, sensor_dimensions: common_pb2.SensorDimensions, default_values: bool = True) -> None:
            self._sensor_dimensions = sensor_dimensions

            if default_values:
                # Default values
                self.set_x_start().set_x_end().set_x_sampling().set_y_start().set_y_end().set_y_sampling()

        def set_x_start(self, value: float = -50) -> Sensor.Dimensions:
            """Set the minimum value on x axis.

            Parameters
            ----------
            value : float
                Minimum value on x axis (mm).
                By default, ``-50``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_start = value
            return self

        def set_x_end(self, value: float = 50) -> Sensor.Dimensions:
            """Set the maximum value on x axis.

            Parameters
            ----------
            value : float
                Maximum value on x axis (mm).
                By default, ``50``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_end = value
            return self

        def set_x_sampling(self, value: int = 100) -> Sensor.Dimensions:
            """Set the sampling value on x axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on x axis.
                By default, ``100``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.x_sampling = value
            return self

        def set_y_start(self, value: float = -50) -> Sensor.Dimensions:
            """Set the minimum value on y axis.

            Parameters
            ----------
            value : float
                Minimum value on y axis (mm).
                By default, ``-50``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.y_start = value
            return self

        def set_y_end(self, value: float = 50) -> Sensor.Dimensions:
            """Set the maximum value on y axis.

            Parameters
            ----------
            value : float
                Maximum value on y axis (mm).
                By default, ``50``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions.
            """
            self._sensor_dimensions.y_end = value
            return self

        def set_y_sampling(self, value: int = 100) -> Sensor.Dimensions:
            """Set the sampling value on y axis.

            Parameters
            ----------
            value : int
                The number of pixels of the XMP map on y axis.
                By default, ``100``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
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
        """

        def __init__(self, sensor_type_colorimetric: common_pb2.SensorTypeColorimetric, default_values: bool = True) -> None:
            self._sensor_type_colorimetric = sensor_type_colorimetric

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = Sensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_colorimetric.wavelengths_range, default_values=default_values
            )

            if default_values:
                # Default values
                self.set_wavelengths_range()

        def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.WavelengthsRange
                Wavelengths range.
            """
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
        """

        def __init__(self, sensor_type_spectral: common_pb2.SensorTypeSpectral, default_values: bool = True) -> None:
            self._sensor_type_spectral = sensor_type_spectral

            # Attribute to keep track of wavelength range object
            self._wavelengths_range = Sensor.WavelengthsRange(
                wavelengths_range=self._sensor_type_spectral.wavelengths_range, default_values=default_values
            )

            if default_values:
                # Default values
                self.set_wavelengths_range()

        def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
            """Set the range of wavelengths.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.WavelengthsRange
                Wavelengths range.
            """
            return self._wavelengths_range

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
        """

        class Layer:
            """Layer composed of name and geometries.

            Parameters
            ----------
            name : str
                Name of the layer.
            geometries : List[ansys.speos.script.geo_ref.GeoRef]
                List of geometries included in this layer.
            """

            def __init__(self, name: str, geometries: List[GeoRef]) -> None:
                self.name = name
                """Name of the layer"""
                self.geometries = geometries
                """List of geometries included in this layer."""

        def __init__(self, layer_type_face: core.Scene.SensorInstance.LayerTypeFace, default_values: bool = True) -> None:
            self._layer_type_face = layer_type_face

            if default_values:
                # Default values
                self.set_sca_filtering_mode_last_impact()

        def set_sca_filtering_mode_intersected_one_time(self) -> Sensor.LayerTypeFace:
            """Set the filtering mode as intersected one time.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeFace
                LayerTypeFace.
            """
            self._layer_type_face.sca_filtering_mode = self._layer_type_face.EnumSCAFilteringType.IntersectedOneTime
            return self

        def set_sca_filtering_mode_last_impact(self) -> Sensor.LayerTypeFace:
            """Set the filtering mode as last impact.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeFace
                LayerTypeFace.
            """
            self._layer_type_face.sca_filtering_mode = self._layer_type_face.EnumSCAFilteringType.LastImpact
            return self

        def set_layers(self, values: List[Sensor.LayerTypeFace.Layer]) -> Sensor.LayerTypeFace:
            """Set the layers.

            Parameters
            ----------
            values : List[ansys.speos.script.sensor.Sensor.LayerTypeFace.Layer]
                List of layers

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeFace
                LayerTypeFace.
            """
            my_list = [
                core.Scene.SensorInstance.LayerTypeFace.Layer(
                    name=layer.name, geometries=core.Scene.GeoPaths(geo_paths=[gr.to_native_link() for gr in layer.geometries])
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
        """

        def __init__(self, layer_type_sequence: core.Scene.SensorInstance.LayerTypeSequence, default_values: bool = True) -> None:
            self._layer_type_sequence = layer_type_sequence

            if default_values:
                # Default values
                self.set_maximum_nb_of_sequence().set_define_sequence_per_geometries()

        def set_maximum_nb_of_sequence(self, value: int = 10) -> Sensor.LayerTypeSequence:
            """Set the maximum number of sequences.

            Parameters
            ----------
            value : int
                Maximum number of sequences.
                By default, ``10``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.maximum_nb_of_sequence = value
            return self

        def set_define_sequence_per_geometries(self) -> Sensor.LayerTypeSequence:
            """Define sequence per geometries.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.define_sequence_per = self._layer_type_sequence.EnumSequenceType.Geometries
            return self

        def set_define_sequence_per_faces(self) -> Sensor.LayerTypeSequence:
            """Define sequence per faces.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeSequence
                LayerTypeSequence.
            """
            self._layer_type_sequence.define_sequence_per = self._layer_type_sequence.EnumSequenceType.Faces
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
        """

        def __init__(
            self, layer_type_incidence_angle: core.Scene.SensorInstance.LayerTypeIncidenceAngle, default_values: bool = True
        ) -> None:
            self._layer_type_incidence_angle = layer_type_incidence_angle

            if default_values:
                # Default values
                self.set_sampling()

        def set_sampling(self, value: int = 9) -> Sensor.LayerTypeIncidenceAngle:
            """Set the sampling for incidence angles.

            Parameters
            ----------
            value : int
                Sampling for incidence angles.
                By default, ``9``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeIncidenceAngle
                LayerTypeIncidenceAngle.
            """
            self._layer_type_incidence_angle.sampling = value
            return self

    class Camera:
        """Type of Sensor : Camera.
        By default, regarding inherent characteristics, a camera with mode photometric is chosen.
        By default, regarding properties, an axis system is selected to position the sensor, and no layer separation is chosen.

        Parameters
        ----------
        camera_template : ansys.api.speos.sensor.v1.camera_sensor_pb2.CameraSensorTemplate
            Camera sensor to complete.
        camera_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.CameraProperties
            Camera sensor properties to complete.
        default_values : bool
            Uses default values when True.
        """

        class Photometric:
            """Mode of camera sensor : Photometric.
            This allows to set every Camera Sensor parameters, including the photometric definition parameters.
            By default, a camera with mode color is chosen (vs monochromatic mode).

            Parameters
            ----------
            mode_photometric : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraModePhotometric
                SensorCameraModePhotometric protobuf object to modify.
            default_values : bool
                Uses default values when True.
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
                """

                class BalanceModeUserWhite:
                    """BalanceMode : UserWhite.
                    In addition to the basic treatment, it allows to apply specific coefficients to the red, green, blue images.
                    By default, coefficients of 1 are chosen for red, green and blue images.

                    Parameters
                    ----------
                    balance_mode_user_white : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraBalanceModeUserwhite
                        SensorCameraBalanceModeUserwhite protobuf object to modify.
                    default_values : bool
                        Uses default values when True.
                    """

                    def __init__(
                        self, balance_mode_user_white: camera_sensor_pb2.SensorCameraBalanceModeUserwhite, default_values: bool = True
                    ) -> None:
                        self._balance_mode_user_white = balance_mode_user_white

                        if default_values:
                            # Default values
                            self.set_red_gain().set_green_gain().set_blue_gain()

                    def set_red_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        """Set red gain.

                        Parameters
                        ----------
                        value : float
                            Red gain.
                            By default, ``1``.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeUserWhite
                            BalanceModeUserWhite.
                        """
                        self._balance_mode_user_white.red_gain = value
                        return self

                    def set_green_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        """Set green gain.

                        Parameters
                        ----------
                        value : float
                            Green gain.
                            By default, ``1``.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeUserWhite
                            BalanceModeUserWhite.
                        """
                        self._balance_mode_user_white.green_gain = value
                        return self

                    def set_blue_gain(self, value: float = 1) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        """Set blue gain.

                        Parameters
                        ----------
                        value : float
                            Blue gain.
                            By default, ``1``.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeUserWhite
                            BalanceModeUserWhite.
                        """
                        self._balance_mode_user_white.blue_gain = value
                        return self

                class BalanceModeDisplayPrimaries:
                    """BalanceMode : DisplayPrimaries.
                    Spectral results are converted in a three-channel result.
                    Then a post-treatment is realized to take the distortion induced by the display devices into account.
                    With this method, displayed results are similar to what the camera really gets.

                    Parameters
                    ----------
                    balance_mode_display : ansys.api.speos.sensor.v1.camera_sensor_pb2.SensorCameraBalanceModeDisplay
                        SensorCameraBalanceModeDisplay protobuf object to modify.
                    default_values : bool
                        Uses default values when True.
                    """

                    def __init__(
                        self, balance_mode_display: camera_sensor_pb2.SensorCameraBalanceModeDisplay, default_values: bool = True
                    ) -> None:
                        self._balance_mode_display = balance_mode_display

                        if default_values:
                            # Default values
                            self._balance_mode_display.SetInParent()

                    def set_red_display_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        """Set the red display file.

                        Parameters
                        ----------
                        uri : str
                            Red display file.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
                            BalanceModeDisplayPrimaries.
                        """
                        self._balance_mode_display.red_display_file_uri = uri
                        return self

                    def set_green_display_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        """Set the green display file.

                        Parameters
                        ----------
                        uri : str
                            Green display file.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
                            BalanceModeDisplayPrimaries.
                        """
                        self._balance_mode_display.green_display_file_uri = uri
                        return self

                    def set_blue_display_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        """Set the blue display file.

                        Parameters
                        ----------
                        uri : str
                            Blue display file.

                        Returns
                        -------
                        ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
                            BalanceModeDisplayPrimaries.
                        """
                        self._balance_mode_display.blue_display_file_uri = uri
                        return self

                def __init__(self, mode_color: camera_sensor_pb2.SensorCameraColorModeColor, default_values: bool = True) -> None:
                    self._mode_color = mode_color

                    # Attribute gathering more complex camera balance mode
                    self._mode = None

                    if default_values:
                        # Default values
                        self.set_balance_mode_none()

                def set_red_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    """Set the red spectrum.

                    Parameters
                    ----------
                    uri : str
                        Red spectrum file. It is expressed in a .spectrum file.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                        Color mode.
                    """
                    self._mode_color.red_spectrum_file_uri = uri
                    return self

                def set_green_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    """Set the green spectrum.

                    Parameters
                    ----------
                    uri : str
                        Green spectrum file. It is expressed in a .spectrum file.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                        Color mode.
                    """
                    self._mode_color.green_spectrum_file_uri = uri
                    return self

                def set_blue_spectrum_file_uri(self, uri: str) -> Sensor.Camera.Photometric.Color:
                    """Set the blue spectrum.

                    Parameters
                    ----------
                    uri : str
                        Blue spectrum file. It is expressed in a .spectrum file.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                        Color mode.
                    """
                    self._mode_color.blue_spectrum_file_uri = uri
                    return self

                def set_balance_mode_none(self) -> Sensor.Camera.Photometric.Color:
                    """Set the balance mode as none.
                    The spectral transmittance of the optical system and the spectral sensitivity for each channel are applied
                    to the detected spectral image before the conversion in a three-channel result.
                    This method is referred to as the basic conversion.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                        Color mode.
                    """
                    self._mode = None
                    self._mode_color.balance_mode_none.SetInParent()
                    return self

                def set_balance_mode_grey_world(self) -> Sensor.Camera.Photometric.Color:
                    """Set the balance mode as grey world.
                    The grey world assumption states that the content of the image is grey on average.
                    This method converts spectral results in a three-channel result with the basic conversion.
                    Then it computes and applies coefficients to the red, green and blue images to make sure their averages are equal.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                        Color mode.
                    """
                    self._mode = None
                    self._mode_color.balance_mode_greyworld.SetInParent()
                    return self

                def set_balance_mode_user_white(self) -> Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                    """Set the balance mode as user white.
                    In addition to the basic treatment, it allows to apply specific coefficients to the red, green, blue images.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeUserWhite
                        Balance UserWhite mode.
                    """
                    if self._mode is None and self._mode_color.HasField("balance_mode_userwhite"):
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeUserWhite(
                            balance_mode_user_white=self._mode_color.balance_mode_userwhite, default_values=False
                        )
                    elif type(self._mode) != Sensor.Camera.Photometric.Color.BalanceModeUserWhite:
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeUserWhite(
                            balance_mode_user_white=self._mode_color.balance_mode_userwhite
                        )
                    return self._mode

                def set_balance_mode_display_primaries(self) -> Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                    """Set the balance mode as display primaries.
                    Spectral results are converted in a three-channel result.
                    Then a post-treatment is realized to take the distortion induced by the display devices into account.
                    With this method, displayed results are similar to what the camera really gets.

                    Returns
                    -------
                    ansys.speos.script.sensor.Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
                        Balance DisplayPrimaries mode.
                    """
                    if self._mode is None and self._mode_color.HasField("balance_mode_display"):
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries(
                            balance_mode_display=self._mode_color.balance_mode_display, default_values=False
                        )
                    elif type(self._mode) != Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries:
                        self._mode = Sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries(
                            balance_mode_display=self._mode_color.balance_mode_display
                        )
                    return self._mode

            def __init__(self, mode_photometric: camera_sensor_pb2.SensorCameraModePhotometric, default_values: bool = True) -> None:
                self._mode_photometric = mode_photometric

                # Attribute gathering more complex camera color mode
                self._mode = None

                # Attribute to keep track of wavelength range object
                self._wavelengths_range = Sensor.WavelengthsRange(wavelengths_range=self._mode_photometric.wavelengths_range)

                if default_values:
                    # Default values
                    self.set_acquisition_integration().set_acquisition_lag_time().set_gamma_correction().set_png_bits_16().set_mode_color()
                    self.set_wavelengths_range()

            def set_acquisition_integration(self, value: float = 0.01) -> Sensor.Camera.Photometric:
                """Set the acquisition integration value.

                Parameters
                ----------
                value : float
                    Acquisition integration value (s).
                    By default, ``0.01``.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.acquisition_integration = value
                return self

            def set_acquisition_lag_time(self, value: float = 0.0) -> Sensor.Camera.Photometric:
                """Set the acquisition lag time value.

                Parameters
                ----------
                value : float
                    Acquisition lag time value (s).
                    By default, ``0.0``.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.acquisition_lag_time = value
                return self

            def set_transmittance_file_uri(self, uri: str) -> Sensor.Camera.Photometric:
                """Set the transmittance file.

                Parameters
                ----------
                uri : str
                    Amount of light of the source that passes through the lens and reaches the sensor.
                    The transmittance is expressed in a .spectrum file.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.transmittance_file_uri = uri
                return self

            def set_gamma_correction(self, value: float = 2.2) -> Sensor.Camera.Photometric:
                """Set the gamma correction.

                Parameters
                ----------
                value : float
                    Compensation of the curve before the display on the screen.
                    By default, ``2.2``.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.gamma_correction = value
                return self

            def set_png_bits_08(self) -> Sensor.Camera.Photometric:
                """Choose 08-bits for png.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
                return self

            def set_png_bits_10(self) -> Sensor.Camera.Photometric:
                """Choose 10-bits for png.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
                return self

            def set_png_bits_12(self) -> Sensor.Camera.Photometric:
                """Choose 12-bits for png.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
                return self

            def set_png_bits_16(self) -> Sensor.Camera.Photometric:
                """Choose 16-bits for png.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
                return self

            def set_wavelengths_range(self) -> Sensor.WavelengthsRange:
                """Set the range of wavelengths.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.WavelengthsRange
                    Wavelengths range.
                """
                return self._wavelengths_range

            def set_mode_monochromatic(self, spectrum_file_uri: str) -> Sensor.Camera.Photometric:
                """Set the monochromatic mode.
                Results will be available in grey scale.

                Parameters
                ----------
                spectrum_file_uri : str
                    Spectrum file uri.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric
                    Photometric mode.
                """
                self._mode = None
                self._mode_photometric.color_mode_monochromatic.spectrum_file_uri = spectrum_file_uri
                return self

            def set_mode_color(self) -> Sensor.Camera.Photometric.Color:
                """Set the color mode.
                Results will be available in color.

                Returns
                -------
                ansys.speos.script.sensor.Sensor.Camera.Photometric.Color
                    Color mode.
                """
                if self._mode is None and self._mode_photometric.HasField("color_mode_color"):
                    self._mode = Sensor.Camera.Photometric.Color(mode_color=self._mode_photometric.color_mode_color, default_values=False)
                elif type(self._mode) != Sensor.Camera.Photometric.Color:
                    self._mode = Sensor.Camera.Photometric.Color(mode_color=self._mode_photometric.color_mode_color)
                return self._mode

        def __init__(
            self,
            camera_template: camera_sensor_pb2.CameraSensorTemplate,
            camera_props: core.Scene.SensorInstance.CameraProperties,
            default_values: bool = True,
        ) -> None:
            self._camera_template = camera_template
            self._camera_props = camera_props

            # Attribute gathering more complex camera mode
            self._mode = None

            if default_values:
                # Default values template
                self.set_focal_length().set_imager_distance().set_f_number().set_horz_pixel()
                self.set_vert_pixel().set_width().set_height().set_mode_photometric()
                # Default values properties
                self.set_axis_system().set_layer_type_none()

        def set_focal_length(self, value: float = 5.0) -> Sensor.Camera:
            """Set the focal length.

            Parameters
            ----------
            value : float
                Distance between the center of the optical system and the focus. (mm)
                By default, ``5.0``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.focal_length = value
            return self

        def set_imager_distance(self, value: float = 10) -> Sensor.Camera:
            """Set the imager distance.

            Parameters
            ----------
            value : float
                Imager distance (mm). The imager is located at the focal point. The Imager distance has no impact on the result.
                By default, ``10``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.imager_distance = value
            return self

        def set_f_number(self, value: float = 20) -> Sensor.Camera:
            """Set the f number.

            Parameters
            ----------
            value : float
                F-number represents the aperture of the front lens. F number has no impact on the result.
                By default, ``20``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.f_number = value
            return self

        def set_distortion_file_uri(self, uri: str) -> Sensor.Camera:
            """Set the distortion file.

            Parameters
            ----------
            uri : str
                Optical aberration that deforms and bends straight lines. The distortion is expressed in a .OPTDistortion file.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.distortion_file_uri = uri
            return self

        def set_horz_pixel(self, value: int = 640) -> Sensor.Camera:
            """Set the horizontal pixels number corresponding to the camera resolution.

            Parameters
            ----------
            value : int
                The horizontal pixels number corresponding to the camera resolution.
                By default, ``640``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.horz_pixel = value
            return self

        def set_vert_pixel(self, value: int = 480) -> Sensor.Camera:
            """Set the vertical pixels number corresponding to the camera resolution.

            Parameters
            ----------
            value : int
                The vertical pixels number corresponding to the camera resolution.
                By default, ``480``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.vert_pixel = value
            return self

        def set_width(self, value: float = 5.0) -> Sensor.Camera:
            """Set the width of the sensor.

            Parameters
            ----------
            value : float
                Sensor's width (mm).
                By default, ``5.0``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.width = value
            return self

        def set_height(self, value: float = 5.0) -> Sensor.Camera:
            """Set the height of the sensor.

            Parameters
            ----------
            value : float
                Sensor's height (mm).
                By default, ``5.0``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_template.height = value
            return self

        def set_mode_geometric(self) -> Sensor.Camera:
            """Set mode geometric for the camera sensor.
            This is a simplified version of the Camera Sensor.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._mode = None
            self._camera_template.sensor_mode_geometric.SetInParent()
            return self

        def set_mode_photometric(self) -> Sensor.Camera.Photometric:
            """Set mode photometric for the camera sensor.
            This allows to set every Camera Sensor parameters, including the photometric definition parameters.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera.Photometric
                Photometric mode.
            """
            if self._mode is None and self._camera_template.HasField("sensor_mode_photometric"):
                self._mode = Sensor.Camera.Photometric(mode_photometric=self._camera_template.sensor_mode_photometric, default_values=False)
            elif type(self._mode) != Sensor.Camera.Photometric:
                self._mode = Sensor.Camera.Photometric(mode_photometric=self._camera_template.sensor_mode_photometric)
            return self._mode

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Sensor.Camera:
            """Set position of the sensor.

            Parameters
            ----------
            axis_system : List[float]
                Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_props.axis_system[:] = axis_system
            return self

        def set_trajectory_file_uri(self, uri: str) -> Sensor.Camera:
            """Set the trajectory file.

            Parameters
            ----------
            uri : str
                Trajectory file, used to define the position and orientations of the Camera sensor in time.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_props.trajectory_file_uri = uri
            return self

        def set_layer_type_none(self) -> Sensor.Camera:
            """Set no layer separation: includes the simulation's results in one layer.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_props.layer_type_none.SetInParent()
            return self

        def set_layer_type_source(self) -> Sensor.Camera:
            """Set layer separation by source: includes one layer per active source in the result.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Camera
                Camera sensor.
            """
            self._camera_props.layer_type_source.SetInParent()
            return self

    class Irradiance:
        """Type of Sensor : Irradiance.
        By default, regarding inherent characteristics, an irradiance sensor of type photometric and illuminance type planar is chosen.
        By default, regarding properties, an axis system is selected to position the sensor, no layer separation and no ray file generation
        are chosen.

        Parameters
        ----------
        irradiance_template : ansys.api.speos.sensor.v1.irradiance_sensor_pb2.IrradianceSensorTemplate
            Irradiance sensor to complete.
        irradiance_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.IrradianceProperties
            Irradiance sensor properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            irradiance_template: irradiance_sensor_pb2.IrradianceSensorTemplate,
            irradiance_props: core.Scene.SensorInstance.IrradianceProperties,
            default_values: bool = True,
        ) -> None:
            self._irradiance_template = irradiance_template
            self._irradiance_props = irradiance_props

            # Attribute gathering more complex irradiance type
            self._type = None

            # Attribute gathering more complex layer type
            self._layer_type = None

            # Attribute to keep track of sensor dimensions object
            self._dimensions = Sensor.Dimensions(sensor_dimensions=self._irradiance_template.dimensions, default_values=default_values)

            if default_values:
                # Default values template
                self.set_type_photometric().set_illuminance_type_planar().set_dimensions()
                # Default values properties
                self.set_axis_system().set_ray_file_type_none().set_layer_type_none()

        def set_type_photometric(self) -> Sensor.Irradiance:
            """Set type photometric.
            The sensor considers the visible spectrum and gets the results in lm/m2 or lx.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.sensor_type_photometric.SetInParent()
            self._type = None
            return self

        def set_type_colorimetric(self) -> Sensor.Colorimetric:
            """Set type colorimetric.
            The sensor will generate color results without any spectral data or layer separation (in lx or W//m2).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Colorimetric
                Colorimetric type.
            """
            if self._type is None and self._irradiance_template.HasField("sensor_type_colorimetric"):
                self._type = Sensor.Colorimetric(
                    sensor_type_colorimetric=self._irradiance_template.sensor_type_colorimetric, default_values=False
                )
            elif type(self._type) != Sensor.Colorimetric:
                self._type = Sensor.Colorimetric(sensor_type_colorimetric=self._irradiance_template.sensor_type_colorimetric)
            return self._type

        def set_type_radiometric(self) -> Sensor.Irradiance:
            """Set type radiometric.
            The sensor considers the entire spectrum and gets the results in W/m2.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.sensor_type_radiometric.SetInParent()
            self._type = None
            return self

        def set_type_spectral(self) -> Sensor.Spectral:
            """Set type spectral.
            The sensor will generate color results and spectral data separated by wavelength (in lx or W/m2).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Spectral
                Spectral type.
            """
            if self._type is None and self._irradiance_template.HasField("sensor_type_spectral"):
                self._type = Sensor.Spectral(sensor_type_spectral=self._irradiance_template.sensor_type_spectral, default_values=False)
            elif type(self._type) != Sensor.Spectral:
                self._type = Sensor.Spectral(sensor_type_spectral=self._irradiance_template.sensor_type_spectral)
            return self._type

        def set_illuminance_type_planar(self, integration_direction: Optional[List[float]] = None) -> Sensor.Irradiance:
            """Set illuminance type planar.
            The integration is made orthogonally with the sensor plane.

            Parameters
            ----------
            integration_direction : List[float], optional
                Sensor global integration direction [x,y,z].
                By default, ``None``. None means that a default direction is chosen (anti-normal of the sensor plane).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.illuminance_type_planar.SetInParent()
            if integration_direction is None or integration_direction == []:
                self._irradiance_props.ClearField("integration_direction")
            else:
                self._irradiance_props.integration_direction[:] = integration_direction
            return self

        def set_illuminance_type_radial(self) -> Sensor.Irradiance:
            """Set illuminance type radial.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.illuminance_type_radial.SetInParent()
            return self

        def set_illuminance_type_hemispherical(self) -> Sensor.Irradiance:
            """Set illuminance type hemispherical.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.illuminance_type_hemispherical.SetInParent()
            return self

        def set_illuminance_type_cylindrical(self) -> Sensor.Irradiance:
            """Set illuminance type cylindrical.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.illuminance_type_cylindrical.SetInParent()
            return self

        def set_illuminance_type_semi_cylindrical(self, integration_direction: Optional[List[float]] = None) -> Sensor.Irradiance:
            """Set illuminance type semi cylindrical.

            Parameters
            ----------
            integration_direction : List[float], optional
                Sensor global integration direction [x,y,z].
                By default, ``None``. None means that a default direction is chosen (anti-normal of the sensor plane).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_template.illuminance_type_semi_cylindrical.SetInParent()
            if integration_direction is None or integration_direction == []:
                self._irradiance_props.ClearField("integration_direction")
            else:
                self._irradiance_props.integration_direction[:] = integration_direction
            return self

        def set_dimensions(self) -> Sensor.Dimensions:
            """Set the dimensions of the sensor.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions range.
            """
            return self._dimensions

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Sensor.Irradiance:
            """Set position of the sensor.

            Parameters
            ----------
            axis_system : List[float]
                Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.axis_system[:] = axis_system
            return self

        def set_ray_file_type_none(self) -> Sensor.Irradiance:
            """Set no ray file generation.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.ray_file_type = core.Scene.SensorInstance.EnumRayFileType.RayFileNone
            return self

        def set_ray_file_type_classic(self) -> Sensor.Irradiance:
            """Set ray file generation without polarization data.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.ray_file_type = core.Scene.SensorInstance.EnumRayFileType.RayFileClassic
            return self

        def set_ray_file_type_polarization(self) -> Sensor.Irradiance:
            """Set ray file generation with the polarization data for each ray.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.ray_file_type = core.Scene.SensorInstance.EnumRayFileType.RayFilePolarization
            return self

        def set_ray_file_type_tm25(self) -> Sensor.Irradiance:
            """Set ray file generation: a .tm25ray file with polarization data for each ray.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.ray_file_type = core.Scene.SensorInstance.EnumRayFileType.RayFileTM25
            return self

        def set_ray_file_type_tm25_no_polarization(self) -> Sensor.Irradiance:
            """Set ray file generation: a .tm25ray file without polarization data.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.ray_file_type = core.Scene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization
            return self

        def set_layer_type_none(self) -> Sensor.Irradiance:
            """Set no layer separation: includes the simulation's results in one layer.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.layer_type_none.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_source(self) -> Sensor.Irradiance:
            """Set layer separation by source: includes in the result one layer per active source.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.layer_type_source.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_face(self) -> Sensor.LayerTypeFace:
            """Set layer separation by face: includes in the result one layer per surface selected.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeFace
                LayerTypeFace.
            """
            if self._layer_type is None and self._irradiance_props.HasField("layer_type_face"):
                self._layer_type = Sensor.LayerTypeFace(layer_type_face=self._irradiance_props.layer_type_face, default_values=False)
            elif type(self._layer_type) != Sensor.LayerTypeFace:
                self._layer_type = Sensor.LayerTypeFace(layer_type_face=self._irradiance_props.layer_type_face)
            return self._layer_type

        def set_layer_type_sequence(self) -> Sensor.LayerTypeSequence:
            """Set layer separation by sequence: includes in the result one layer per sequence.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeSequence
                LayerTypeSequence.
            """
            if self._layer_type is None and self._irradiance_props.HasField("layer_type_sequence"):
                self._layer_type = Sensor.LayerTypeSequence(
                    layer_type_sequence=self._irradiance_props.layer_type_sequence, default_values=False
                )
            elif type(self._layer_type) != Sensor.LayerTypeSequence:
                self._layer_type = Sensor.LayerTypeSequence(layer_type_sequence=self._irradiance_props.layer_type_sequence)
            return self._layer_type

        def set_layer_type_polarization(self) -> Sensor.Irradiance:
            """Set layer separation by polarization: includes one layer per Stokes parameter using the polarization parameter.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            self._irradiance_props.layer_type_polarization.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_incidence_angle(self) -> Sensor.LayerTypeIncidenceAngle:
            """Set layer separation by incidence angle: includes in the result one layer per range of incident angles.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeIncidenceAngle
                LayerTypeIncidenceAngle.
            """
            if self._layer_type is None and self._irradiance_props.HasField("layer_type_incidence_angle"):
                self._layer_type = Sensor.LayerTypeIncidenceAngle(
                    layer_type_incidence_angle=self._irradiance_props.layer_type_incidence_angle, default_values=False
                )
            elif type(self._layer_type) != Sensor.LayerTypeIncidenceAngle:
                self._layer_type = Sensor.LayerTypeIncidenceAngle(
                    layer_type_incidence_angle=self._irradiance_props.layer_type_incidence_angle
                )
            return self._layer_type

        def set_output_face_geometries(self, geometries: List[GeoRef] = []) -> Sensor.Irradiance:
            """Select output faces for inverse simulation optimization.

            Parameters
            ----------
            geometries : List[ansys.speos.script.geo_ref.GeoRef]
                List of geometries that will be considered as output faces.
                By default, ``[]``, ie no output faces.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Irradiance
                Irradiance sensor.
            """
            if geometries == []:
                self._irradiance_props.ClearField("output_face_geometries")
            else:
                self._irradiance_props.output_face_geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
            return self

    class Radiance:
        """Type of Sensor : Radiance.
        By default, regarding inherent characteristics, a radiance sensor of type photometric is chosen.
        By default, regarding properties, an axis system is selected to position the sensor and no layer separation is chosen.

        Parameters
        ----------
        radiance_template : ansys.api.speos.sensor.v1.sensor_pb2.SensorTemplate.Radiance
            Radiance sensor to complete.
        radiance_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SensorInstance.RadianceProperties
            Radiance sensor properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            radiance_template: core.SensorTemplate.Radiance,
            radiance_props: core.Scene.SensorInstance.RadianceProperties,
            default_values: bool = True,
        ) -> None:
            self._radiance_template = radiance_template
            self._radiance_props = radiance_props

            # Attribute gathering more complex radiance type
            self._type = None

            # Attribute gathering more complex layer type
            self._layer_type = None

            # Attribute to keep track of sensor dimensions object
            self._dimensions = Sensor.Dimensions(sensor_dimensions=self._radiance_template.dimensions, default_values=default_values)

            if default_values:
                # Default values template
                self.set_focal().set_integration_angle().set_type_photometric()
                self.set_dimensions()
                # Default values properties
                self.set_axis_system().set_layer_type_none()

        def set_type_photometric(self) -> Sensor.Radiance:
            """Set type photometric.
            The sensor considers the visible spectrum and gets the results in lm/m2 or lx.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_template.sensor_type_photometric.SetInParent()
            self._type = None
            return self

        def set_type_colorimetric(self) -> Sensor.Colorimetric:
            """Set type colorimetric.
            The sensor will generate color results without any spectral data or layer separation (in lx or W//m2).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Colorimetric
                Colorimetric type.
            """
            if self._type is None and self._radiance_template.HasField("sensor_type_colorimetric"):
                self._type = Sensor.Colorimetric(
                    sensor_type_colorimetric=self._radiance_template.sensor_type_colorimetric, default_values=False
                )
            elif type(self._type) != Sensor.Colorimetric:
                self._type = Sensor.Colorimetric(sensor_type_colorimetric=self._radiance_template.sensor_type_colorimetric)
            return self._type

        def set_type_radiometric(self) -> Sensor.Radiance:
            """Set type radiometric.
            The sensor considers the entire spectrum and gets the results in W/m2.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_template.sensor_type_radiometric.SetInParent()
            self._type = None
            return self

        def set_type_spectral(self) -> Sensor.Spectral:
            """Set type spectral.
            The sensor will generate color results and spectral data separated by wavelength (in lx or W/m2).

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Spectral
                Spectral type.
            """
            if self._type is None and self._radiance_template.HasField("sensor_type_spectral"):
                self._type = Sensor.Spectral(sensor_type_spectral=self._radiance_template.sensor_type_spectral, default_values=False)
            elif type(self._type) != Sensor.Spectral:
                self._type = Sensor.Spectral(sensor_type_spectral=self._radiance_template.sensor_type_spectral)
            return self._type

        def set_focal(self, value: float = 250) -> Sensor.Radiance:
            """Set the focal value.

            Parameters
            ----------
            value : float
                Focal (mm).
                By default, ``250``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_template.focal = value
            return self

        def set_integration_angle(self, value: float = 5) -> Sensor.Radiance:
            """Set the integration angle.

            Parameters
            ----------
            value : float
                integration angle (degree)
                By default, ``5``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_template.integration_angle = value
            return self

        def set_dimensions(self) -> Sensor.Dimensions:
            """Set the dimensions of the sensor.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Dimensions
                Dimensions range.
            """
            return self._dimensions

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Sensor.Radiance:
            """Set position of the sensor.

            Parameters
            ----------
            axis_system : List[float]
                Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_props.axis_system[:] = axis_system
            return self

        def set_observer_point(self, value: Optional[List[float]] = None) -> Sensor.Radiance:
            """Set the position of the observer point. This is optional, because the focal length is used by default.
            Choosing to set an observer point will make the focal length ignored.

            Parameters
            ----------
            value : List[float], optional
                Position of the observer point [Ox Oy Oz].
                By default, ``None``. None means that the focal length is used.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            if value is None or value == []:
                self._radiance_props.ClearField("observer_point")
            else:
                self._radiance_props.observer_point[:] = value
            return self

        def set_layer_type_none(self) -> Sensor.Radiance:
            """Set no layer separation: includes the simulation's results in one layer.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_props.layer_type_none.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_source(self) -> Sensor.Radiance:
            """Set layer separation by source: includes in the result one layer per active source.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.Radiance
                Radiance sensor.
            """
            self._radiance_props.layer_type_source.SetInParent()
            self._layer_type = None
            return self

        def set_layer_type_face(self) -> Sensor.LayerTypeFace:
            """Set layer separation by face: includes in the result one layer per surface selected.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeFace
                LayerTypeFace.
            """
            if self._layer_type is None and self._radiance_props.HasField("layer_type_face"):
                self._layer_type = Sensor.LayerTypeFace(layer_type_face=self._radiance_props.layer_type_face, default_values=False)
            elif type(self._layer_type) != Sensor.LayerTypeFace:
                self._layer_type = Sensor.LayerTypeFace(layer_type_face=self._radiance_props.layer_type_face)
            return self._layer_type

        def set_layer_type_sequence(self) -> Sensor.LayerTypeSequence:
            """Set layer separation by sequence: includes in the result one layer per sequence.

            Returns
            -------
            ansys.speos.script.sensor.Sensor.LayerTypeSequence
                LayerTypeSequence.
            """
            if self._layer_type is None and self._radiance_props.HasField("layer_type_sequence"):
                self._layer_type = Sensor.LayerTypeSequence(
                    layer_type_sequence=self._radiance_props.layer_type_sequence, default_values=False
                )
            elif type(self._layer_type) != Sensor.LayerTypeSequence:
                self._layer_type = Sensor.LayerTypeSequence(layer_type_sequence=self._radiance_props.layer_type_sequence)
            return self._layer_type

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self.sensor_template_link = None
        """Link object for the sensor template in database."""

        # Attribute representing the kind of sensor. Can be on object of type script.Sensor.Camera, script.Sensor.Irradiance, ...
        self._type = None

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
        if self._type is None and self._sensor_template.HasField("camera_sensor_template"):
            self._type = Sensor.Camera(
                camera_template=self._sensor_template.camera_sensor_template,
                camera_props=self._sensor_instance.camera_properties,
                default_values=False,
            )
        elif type(self._type) != Sensor.Camera:
            self._type = Sensor.Camera(
                camera_template=self._sensor_template.camera_sensor_template, camera_props=self._sensor_instance.camera_properties
            )
        return self._type

    def set_irradiance(self) -> Irradiance:
        """Set the sensor as irradiance.

        Returns
        -------
        ansys.speos.script.sensor.Sensor.Irradiance
            Irradiance sensor.
        """
        if self._type is None and self._sensor_template.HasField("irradiance_sensor_template"):
            self._type = Sensor.Irradiance(
                irradiance_template=self._sensor_template.irradiance_sensor_template,
                irradiance_props=self._sensor_instance.irradiance_properties,
                default_values=False,
            )
        elif type(self._type) != Sensor.Irradiance:
            self._type = Sensor.Irradiance(
                irradiance_template=self._sensor_template.irradiance_sensor_template,
                irradiance_props=self._sensor_instance.irradiance_properties,
            )
        return self._type

    def set_radiance(self) -> Radiance:
        """Set the sensor as radiance.

        Returns
        -------
        ansys.speos.script.sensor.Sensor.Radiance
            Radiance sensor.
        """
        if self._type is None and self._sensor_template.HasField("radiance_sensor_template"):
            self._type = Sensor.Radiance(
                radiance_template=self._sensor_template.radiance_sensor_template,
                radiance_props=self._sensor_instance.radiance_properties,
                default_values=False,
            )
        elif type(self._type) != Sensor.Radiance:
            self._type = Sensor.Radiance(
                radiance_template=self._sensor_template.radiance_sensor_template, radiance_props=self._sensor_instance.radiance_properties
            )
        return self._type

    def _to_dict(self) -> dict:
        out_dict = {}

        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is not None:
                out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=ssr_inst)
            else:
                out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=self._sensor_instance)
        else:
            out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=self._sensor_instance)

        if "sensor" not in out_dict.keys():
            # SensorTemplate
            if self.sensor_template_link is None:
                out_dict["sensor"] = proto_message_utils._replace_guids(speos_client=self._project.client, message=self._sensor_template)
            else:
                out_dict["sensor"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self.sensor_template_link.get()
                )

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def __str__(self) -> str:
        """Return the string representation of the sensor."""
        out_str = ""
        # SensorInstance (= sensor guid + sensor properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())

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
        elif self.sensor_template_link.get() != self._sensor_template:
            self.sensor_template_link.set(data=self._sensor_template)  # Only update if template has changed

        # Update the scene with the sensor instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            ssr_inst = next((x for x in scene_data.sensors if x.metadata["UniqueId"] == self._unique_id), None)
            if ssr_inst is not None:
                if ssr_inst != self._sensor_instance:
                    ssr_inst.CopyFrom(self._sensor_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.sensors.append(self._sensor_instance)  # if no, just add it to the list of sensor instances

            if update_scene:  # Update scene only if instance has changed
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

    def _fill(self, ssr_inst):
        self._unique_id = ssr_inst.metadata["UniqueId"]
        self._sensor_instance = ssr_inst
        self.sensor_template_link = self._project.client.get_item(key=ssr_inst.sensor_guid)
        self.reset()

        if self._sensor_template.HasField("camera_sensor_template"):
            self.set_camera()
        elif self._sensor_template.HasField("irradiance_sensor_template"):
            self.set_irradiance()
        elif self._sensor_template.HasField("radiance_sensor_template"):
            self.set_radiance()
