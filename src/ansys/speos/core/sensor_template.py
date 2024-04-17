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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import List, Mapping, Optional

from ansys.api.speos.sensor.v1 import camera_sensor_pb2
from ansys.api.speos.sensor.v1 import sensor_pb2 as messages
from ansys.api.speos.sensor.v1 import sensor_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

SensorTemplate = messages.SensorTemplate
SensorTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SensorTemplateLink(CrudItem):
    """
    Link object for sensor template in database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.sensor_template import SensorTemplateFactory
    >>> speos = Speos(host="localhost", port=50051)
    >>> ssr_t_db = speos.client.sensor_templates()
    >>> ssr_t_link = ssr_t_db.create(message=SensorTemplateFactory.irradiance(name="Irradiance_Default"))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return str(self.get())

    def get(self) -> SensorTemplate:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: SensorTemplate) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SensorTemplateStub(CrudStub):
    """
    Database interactions for sensor templates.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> ssr_t_db = speos.client.sensor_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SensorTemplatesManagerStub(channel=channel))

    def create(self, message: SensorTemplate) -> SensorTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(sensor_template=message))
        return SensorTemplateLink(self, resp.guid)

    def read(self, ref: SensorTemplateLink) -> SensorTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.sensor_template

    def update(self, ref: SensorTemplateLink, data: SensorTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, sensor_template=data))

    def delete(self, ref: SensorTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SensorTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SensorTemplateLink(self, x), guids))


class SensorTemplateFactory:
    """Class to help creating SensorTemplate message"""

    Type = Enum("Type", ["Photometric", "Colorimetric", "Radiometric", "Spectral"])
    IlluminanceType = Enum("IlluminanceType", ["Planar", "Radial", "Hemispherical", "Cylindrical", "SemiCylindrical"])

    class Dimensions:
        """
        Represents sensor dimensions.

        Parameters
        ----------
        x_start : float, optional
            Start of the sensor regarding x axis.
            By default, ``-50``.
        x_end : float, optional
            End of the sensor regarding x axis.
            By default, ``50``.
        x_sampling : int, optional
            Sampling on x axis.
            By default, ``100``.
        y_start : float, optional
            Start of the sensor regarding y axis.
            By default, ``-50``.
        y_end : float, optional
            End of the sensor regarding y axis.
            By default, ``50``.
        y_sampling : int, optional
            Sampling on y axis.
            By default, ``100``.
        """

        def __init__(
            self,
            x_start: Optional[float] = -50,
            x_end: Optional[float] = 50,
            x_sampling: Optional[int] = 100,
            y_start: Optional[float] = -50,
            y_end: Optional[float] = 50,
            y_sampling: Optional[int] = 100,
        ) -> None:
            self.x_start = x_start
            self.x_end = x_end
            self.x_sampling = x_sampling
            self.y_start = y_start
            self.y_end = y_end
            self.y_sampling = y_sampling

    class WavelengthsRange:
        """
        Represents range of wavelenths.

        Parameters
        ----------
        start : float, optional
            Minimum wavelength. (nm)
            By default, ``400``.
        end : float, optional
            Maximum wavelength. (nm)
            By default, ``700``.
        sampling : int, optional
            Number of wavelength to be taken into account between the minimum and minimum wavelengths set.
            By default, ``13``.
        """

        def __init__(self, start: Optional[float] = 400, end: Optional[float] = 700, sampling: Optional[int] = 13) -> None:
            self.start = start
            self.end = end
            self.sampling = sampling

    class CameraDimensions:
        """
        Represents camera sensor dimensions.

        Parameters
        ----------
        horz_pixel : int, optional
            Horizontal pixels number corresponding to the camera resolution.
            By default, ``640``.
        vert_pixel : int, optional
            Vertical pixels number corresponding to the camera resolution.
            By default, ``480``.
        width : float, optional
            Sensor's width in mm.
            By default, ``5``.
        height : float, optional
            Sensor's height in mm.
            By default, ``5``.
        """

        def __init__(
            self, horz_pixel: Optional[int] = 640, vert_pixel: Optional[int] = 480, width: Optional[float] = 5, height: Optional[float] = 5
        ) -> None:
            self.horz_pixel = horz_pixel
            self.vert_pixel = vert_pixel
            self.width = width
            self.height = height

    class CameraSettings:
        """
        Represents camera settings.

        Parameters
        ----------
        gamma_correction : float, optional
            Compensation of the curve before the display on the screen.
            By default, ``2.2``.
        focal_length : float, optional
            Distance between the center of the optical system and the focus. (mm)
            By default, ``5``.
        imager_distance : float, optional
            Imager distance in mm, the imager is located at the focal point. The Imager distance has no impact on the result.
            By default, ``10``.
        f_number : float, optional
            F-number represent the aperture of the front lens. F number has no impact on the result.
            By default, ``20``.
        """

        def __init__(
            self,
            gamma_correction: Optional[float] = 2.2,
            focal_length: Optional[float] = 5,
            imager_distance: Optional[float] = 10,
            f_number: Optional[float] = 20,
        ) -> None:
            self.gamma_correction = gamma_correction
            self.focal_length = focal_length
            self.imager_distance = imager_distance
            self.f_number = f_number

    class CameraBalanceMode:
        Type = Enum("Type", ["GreyWorld", "UserWhiteBalance", "DisplayPrimaries"])

        def __init__(self, type: Optional[Type] = None, values: Optional[List] = []) -> None:
            """
            Represents camera balance mode.

            Parameters
            ----------
            type : SensorTemplateFactory.CameraBalanceMode.Type, optional
                Type of balance mode.
                By default, ``None``.
            values : List, optional
                To be filled in case of types UserWhiteBalance and DisplayPrimaries
                If UserWhiteBalance, gains are expected. List[float] : [red_gain, green_gain, blue_gain]
                If DisplayPrimaries, display files are expected. List[str] :
                [red_display_file_uri, green_display_file_uri, blue_display_file_uri]
                By default, ``[]``.

            Raises
            ------
            ValueError
                Raised when the expected values are not given in input.
            """
            if type == SensorTemplateFactory.CameraBalanceMode.Type.UserWhiteBalance and len(values) != 3:
                raise ValueError("For userwhite balance mode, three values are expected: [red_gain, green_gain, blue_gain]")
            if type == SensorTemplateFactory.CameraBalanceMode.Type.DisplayPrimaries and len(values) != 3:
                raise ValueError(
                    "For display balance mode, three values are expected: \
                    [red_display_file_uri, green_display_file_uri, blue_display_file_uri]"
                )
            self.type = type
            self.value = values

    def irradiance(
        name: str,
        type: Optional[Type] = Type.Photometric,
        illuminance_type: Optional[IlluminanceType] = IlluminanceType.Planar,
        dimensions: Optional[Dimensions] = Dimensions(),
        wavelengths_range: Optional[WavelengthsRange] = None,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SensorTemplate:
        """
        Create a SensorTemplate message, with irradiance type.

        Parameters
        ----------
        name : str
            Name of the sensor template.
        type : SensorTemplateFactory.Type, optional
            Type of the sensor.
            By default, ``SensorTemplateFactory.Type.Photometric``.
        illuminance_type : SensorTemplateFactory.IlluminanceType, optional
            Select how the light should be integrated to the sensor.
            By default, ``SensorTemplateFactory.IlluminanceType.Planar``.
        dimensions : SensorTemplateFactory.Dimensions, optional
            Dimensions of the sensor.
            By default, ``SensorTemplateFactory.Dimensions()``.
        wavelengths_range : SensorTemplateFactory.WavelengthsRange, optional
            Range of wavelengths.
            To be filled in case of type Colorimetric or Spectral
            By default, ``None``.
        description : str, optional
            Description of the sensor template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sensor template.
            By default, ``None``.

        Returns
        -------
        SensorTemplate
            SensorTemplate message created.

        Raises
        ------
        ValueError
            Raised when wavelengths_range is not given but expected.
        """
        ssr = SensorTemplate(name=name, description=description)
        if metadata is not None:
            ssr.metadata.update(metadata)
        if type == SensorTemplateFactory.Type.Photometric:
            ssr.irradiance_sensor_template.sensor_type_photometric.SetInParent()
        elif type == SensorTemplateFactory.Type.Colorimetric:
            if wavelengths_range is None:
                raise ValueError("For colorimetric type, please provide wavelengths_range parameter")
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start = wavelengths_range.start
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end = wavelengths_range.end
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling = wavelengths_range.sampling
        elif type == SensorTemplateFactory.Type.Radiometric:
            ssr.irradiance_sensor_template.sensor_type_radiometric.SetInParent()
        elif type == SensorTemplateFactory.Type.Spectral:
            if wavelengths_range is None:
                raise ValueError("For spectral type, please provide wavelengths_range parameter")
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start = wavelengths_range.start
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end = wavelengths_range.end
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling = wavelengths_range.sampling

        if illuminance_type == SensorTemplateFactory.IlluminanceType.Planar:
            ssr.irradiance_sensor_template.illuminance_type_planar.SetInParent()
        elif illuminance_type == SensorTemplateFactory.IlluminanceType.Radial:
            ssr.irradiance_sensor_template.illuminance_type_radial.SetInParent()
        elif illuminance_type == SensorTemplateFactory.IlluminanceType.Hemispherical:
            ssr.irradiance_sensor_template.illuminance_type_hemispherical.SetInParent()
        elif illuminance_type == SensorTemplateFactory.IlluminanceType.Cylindrical:
            ssr.irradiance_sensor_template.illuminance_type_cylindrical.SetInParent()
        elif illuminance_type == SensorTemplateFactory.IlluminanceType.SemiCylindrical:
            ssr.irradiance_sensor_template.illuminance_type_semi_cylindrical.SetInParent()

        ssr.irradiance_sensor_template.dimensions.x_start = dimensions.x_start
        ssr.irradiance_sensor_template.dimensions.x_end = dimensions.x_end
        ssr.irradiance_sensor_template.dimensions.x_sampling = dimensions.x_sampling
        ssr.irradiance_sensor_template.dimensions.y_start = dimensions.y_start
        ssr.irradiance_sensor_template.dimensions.y_end = dimensions.y_end
        ssr.irradiance_sensor_template.dimensions.y_sampling = dimensions.y_sampling

        return ssr

    def camera(
        name: str,
        distortion_file_uri: str,
        transmittance_file_uri: str,
        spectrum_file_uris: List[str],
        settings: Optional[CameraSettings] = CameraSettings(),
        dimensions: Optional[CameraDimensions] = CameraDimensions(),
        wavelengths_range: Optional[WavelengthsRange] = WavelengthsRange(),
        camera_balance_mode: Optional[CameraBalanceMode] = None,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SensorTemplate:
        """
        Create a SensorTemplate message, with camera type.

        Parameters
        ----------
        name : str
            Name of the sensor template.
        distortion_file_uri : str
            Optical aberration that deforms and bend straight lines. The distortion is expressed in a .OPTDistortion file.
        transmittance_file_uri : str
            Amount of light of the source that passes through the lens and reaches the sensor.
            The transmittance is expressed in a .spectrum file.
        spectrum_file_uris : List[str]
            Spectrum files.
            To get the sensor in color mode : [red_spectrum_file_uri, green_spectrum_file_uri, blue_spectrum_file_uri]
            To get the sensor in monochromatic mode : [spectrum_file_uri]
        settings : SensorTemplateFactory.CameraSettings, optional
            Settings for the camera.
            By default, ``SensorTemplateFactory.CameraSettings()``.
        dimensions : SensorTemplateFactory.CameraDimensions, optional
            Dimensions of the camera.
            By default, ``SensorTemplateFactory.CameraDimensions()``.
        wavelengths_range : SensorTemplateFactory.WavelengthsRange, optional
            Range of wavelengths.
            By default, ``SensorTemplateFactory.WavelengthsRange()``.
        camera_balance_mode : SensorTemplateFactory.CameraBalanceMode, optional
            Camera balance mode.
            Can be filled if the camera is in color mode.
            By default, ``None``.
        description : str, optional
            Description of the sensor template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sensor template.
            By default, ``None``.

        Returns
        -------
        SensorTemplate
            SensorTemplate message created.

        Raises
        ------
        ValueError
            Raised when incorrect number of spectrum_file_uris is given.
        """
        ssr = SensorTemplate(name=name, description=description)
        if metadata is not None:
            ssr.metadata.update(metadata)
        ssr.camera_sensor_template.sensor_mode_photometric.acquisition_integration = 0.01
        ssr.camera_sensor_template.sensor_mode_photometric.acquisition_lag_time = 0

        ssr.camera_sensor_template.sensor_mode_photometric.transmittance_file_uri = transmittance_file_uri
        ssr.camera_sensor_template.sensor_mode_photometric.gamma_correction = settings.gamma_correction
        ssr.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16

        if len(spectrum_file_uris) == 1:
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_monochromatic.spectrum_file_uri = spectrum_file_uris[0]
        elif len(spectrum_file_uris) == 3:
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.red_spectrum_file_uri = spectrum_file_uris[0]
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.green_spectrum_file_uri = spectrum_file_uris[1]
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.blue_spectrum_file_uri = spectrum_file_uris[2]
            if camera_balance_mode is None or camera_balance_mode.type == None:
                ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_none.SetInParent()
            elif camera_balance_mode.type == SensorTemplateFactory.CameraBalanceMode.Type.GreyWorld:
                ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_greyworld.SetInParent()
            elif camera_balance_mode.type == SensorTemplateFactory.CameraBalanceMode.Type.UserWhiteBalance:
                mode_userwhite = camera_sensor_pb2.SensorCameraBalanceModeUserwhite()
                mode_userwhite.red_gain = camera_balance_mode.value[0]
                mode_userwhite.green_gain = camera_balance_mode.value[1]
                mode_userwhite.blue_gain = camera_balance_mode.value[2]
                ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.CopyFrom(mode_userwhite)

            elif camera_balance_mode.type == SensorTemplateFactory.CameraBalanceMode.Type.DisplayPrimaries:
                mode_display = camera_sensor_pb2.SensorCameraBalanceModeDisplay()
                mode_display.red_display_file_uri = camera_balance_mode.value[0]
                mode_display.green_display_file_uri = camera_balance_mode.value[1]
                mode_display.blue_display_file_uri = camera_balance_mode.value[2]
                ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_display.CopyFrom(mode_display)
        else:
            raise ValueError(
                "One or three spectrum files are expected in spectrum_file_uris parameter: \
                [spectrum] or [red, green, blue]. \
                One = the camera has Monochrome mode. Three = the camera has Color mode."
            )

        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start = wavelengths_range.start
        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end = wavelengths_range.end
        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_sampling = wavelengths_range.sampling

        ssr.camera_sensor_template.focal_length = settings.focal_length
        ssr.camera_sensor_template.imager_distance = settings.imager_distance
        ssr.camera_sensor_template.f_number = settings.f_number
        ssr.camera_sensor_template.distorsion_file_uri = distortion_file_uri

        ssr.camera_sensor_template.horz_pixel = dimensions.horz_pixel
        ssr.camera_sensor_template.vert_pixel = dimensions.vert_pixel
        ssr.camera_sensor_template.width = dimensions.width
        ssr.camera_sensor_template.height = dimensions.height

        return ssr
