"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum

from ansys.api.speos.sensor.v1 import camera_sensor_pb2
from ansys.api.speos.sensor.v1 import sensor_pb2 as messages
from ansys.api.speos.sensor.v1 import sensor_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub

SensorTemplate = messages.SensorTemplate


class SensorTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def get(self) -> SensorTemplate:
        return self._stub.read(self)

    def set(self, data: SensorTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SensorTemplateStub(CrudStub):
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

    def list(self) -> list[SensorTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SensorTemplateLink(self, x), guids))

    def from_key(self, key: str) -> SensorTemplateLink:
        """Retrieve entry from a key."""
        return SensorTemplateLink(self, key)


class SensorTemplateHelper:
    Type = Enum("Type", ["Photometric", "Colorimetric", "Radiometric", "Spectral"])
    IlluminanceType = Enum("IlluminanceType", ["Planar", "Radial", "Hemispherical", "Cylindrical", "SemiCylindrical"])

    class Dimensions:
        def __init__(self, x_start, x_end, x_sampling, y_start, y_end, y_sampling) -> None:
            self._x_start = x_start
            self._x_end = x_end
            self._x_sampling = x_sampling
            self._y_start = y_start
            self._y_end = y_end
            self._y_sampling = y_sampling

    class WavelengthsRange:
        def __init__(self, start, end, sampling) -> None:
            self._start = start
            self._end = end
            self._sampling = sampling

    class CameraDimensions:
        def __init__(self, horz_pixel, vert_pixel, width, height):
            self._horz_pixel = horz_pixel
            self._vert_pixel = vert_pixel
            self._width = width
            self._height = height

    class CameraSettings:
        def __init__(self, focal_length, imager_distance, f_number) -> None:
            self._focal_length = focal_length
            self._imager_distance = imager_distance
            self._f_number = f_number
            pass

    def create_irradiance(
        sensor_template_stub: SensorTemplateStub,
        name: str,
        description: str,
        type: Type,
        illuminance_type: IlluminanceType,
        dimensions: Dimensions,
        wavelengths_range: WavelengthsRange = None,
    ) -> SensorTemplateLink:
        ssr = SensorTemplate()
        ssr.name = name
        ssr.description = description
        if type == SensorTemplateHelper.Type.Photometric:
            ssr.irradiance_sensor_template.sensor_type_photometric.SetInParent()
        elif type == SensorTemplateHelper.Type.Colorimetric and wavelengths_range is not None:
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start = wavelengths_range._start
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end = wavelengths_range._end
            ssr.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling = (
                wavelengths_range._sampling
            )
        elif type == SensorTemplateHelper.Type.Radiometric:
            ssr.irradiance_sensor_template.sensor_type_radiometric.SetInParent()
        elif type == SensorTemplateHelper.Type.Spectral and wavelengths_range is not None:
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start = wavelengths_range._start
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end = wavelengths_range._end
            ssr.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling = (
                wavelengths_range._sampling
            )

        if illuminance_type == SensorTemplateHelper.IlluminanceType.Planar:
            ssr.irradiance_sensor_template.illuminance_type_planar.SetInParent()
        elif illuminance_type == SensorTemplateHelper.IlluminanceType.Radial:
            ssr.irradiance_sensor_template.illuminance_type_radial.SetInParent()
        elif illuminance_type == SensorTemplateHelper.IlluminanceType.Hemispherical:
            ssr.irradiance_sensor_template.illuminance_type_hemispherical.SetInParent()
        elif illuminance_type == SensorTemplateHelper.IlluminanceType.Cylindrical:
            ssr.irradiance_sensor_template.illuminance_type_cylindrical.SetInParent()
        elif illuminance_type == SensorTemplateHelper.IlluminanceType.SemiCylindrical:
            ssr.irradiance_sensor_template.illuminance_type_semi_cylindrical.SetInParent()

        ssr.irradiance_sensor_template.dimensions.x_start = dimensions._x_start
        ssr.irradiance_sensor_template.dimensions.x_end = dimensions._x_end
        ssr.irradiance_sensor_template.dimensions.x_sampling = dimensions._x_sampling
        ssr.irradiance_sensor_template.dimensions.y_start = dimensions._y_start
        ssr.irradiance_sensor_template.dimensions.y_end = dimensions._y_end
        ssr.irradiance_sensor_template.dimensions.y_sampling = dimensions._y_sampling

        return sensor_template_stub.create(message=ssr)

    def create_camera(
        sensor_template_stub: SensorTemplateStub,
        name: str,
        description: str,
        transmittance_file_uri: str,
        gamma_correction: float,
        spectrum_file_uris: list[str],
        wavelengths_range: WavelengthsRange,
        settings: CameraSettings,
        distorsion_file_uri: str,
        dimensions: CameraDimensions,
    ) -> SensorTemplateLink:
        ssr = SensorTemplate()
        ssr.name = name
        ssr.description = description

        ssr.camera_sensor_template.sensor_mode_photometric.acquisition_integration = 0.1
        ssr.camera_sensor_template.sensor_mode_photometric.acquisition_lag_time = 0

        ssr.camera_sensor_template.sensor_mode_photometric.transmittance_file_uri = transmittance_file_uri
        ssr.camera_sensor_template.sensor_mode_photometric.gamma_correction = gamma_correction
        ssr.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16

        if len(spectrum_file_uris) == 1:
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_monochromatic.spectrum_file_uri = (
                spectrum_file_uris[0]
            )
        elif len(spectrum_file_uris) == 3:
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.red_spectrum_file_uri = (
                spectrum_file_uris[0]
            )
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.green_spectrum_file_uri = (
                spectrum_file_uris[1]
            )
            ssr.camera_sensor_template.sensor_mode_photometric.color_mode_color.blue_spectrum_file_uri = (
                spectrum_file_uris[2]
            )
            ssr.camera_sensor_template.sensor_mode_photometric.balance_mode_none.SetInParent()
        else:
            raise ValueError(
                "One or three spectrum files are expected in spectrum_file_uris parameter: \
                [spectrum] or [red, green, blue]. \
                One = the camera has Monochrome mode. Three = the camera has Color mode."
            )

        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start = wavelengths_range._start
        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end = wavelengths_range._end
        ssr.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_sampling = wavelengths_range._sampling

        ssr.camera_sensor_template.focal_length = settings._focal_length
        ssr.camera_sensor_template.imager_distance = settings._imager_distance
        ssr.camera_sensor_template.f_number = settings._f_number
        ssr.camera_sensor_template.distorsion_file_uri = distorsion_file_uri

        ssr.camera_sensor_template.horz_pixel = dimensions._horz_pixel
        ssr.camera_sensor_template.vert_pixel = dimensions._vert_pixel
        ssr.camera_sensor_template.width = dimensions._width
        ssr.camera_sensor_template.height = dimensions._height

        return sensor_template_stub.create(message=ssr)
