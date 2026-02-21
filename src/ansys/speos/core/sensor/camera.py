
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
from ansys.speos.core.sensor import BaseSensor

class Camera(BaseSensor):
    """Sensor feature: Camera.
    By default, regarding inherent characteristics, a camera with mode photometric is chosen.
    By default, regarding properties, an axis system is selected to position the sensor, and no layer separation is chosen.

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


    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        sensor_instance: Optional[ProtoScene.SensorInstance] = None,
        default_values: bool = True,
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
        if default_values:
            # Default values template
            # self.set_focal_length().set_imager_distance().set_f_number().set_horz_pixel()
            self.focal_length = 5.0
            self.imager_distance = 10.0
            self.f_number = 20.0
            self.horz_pixel = 640
            self.vert_pixel = 480
            self.width = 5.0
            self.height = 5.0
            self.set_mode_photometric()
            # self.set_vert_pixel().set_width().set_height().set_mode_photometric()
            # Default values properties
            # self.set_axis_system()
            self.axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    @property
    def photometric(self) -> Union[Camera.Photometric, None]:
        """
        Property containing the instance of Camera.Photometric used to build the sensor

        Returns
        -------
        Union[ansys.speos.core.sensor.Camera.Photometric, None]
            Photometric class instance if it exists

        """
        return self._type

    @property
    def focal_length(self) -> float:
        """ """
        res = self._sensor_template.camera_sensor_template.focal_length
        return res

    @focal_length.setter
    # def focal_length(self, value: float = 5.0):
    def focal_length(self, value: float):
        """Set the focal length.

        Parameters
        ----------
        value : float
            Distance between the center of the optical system and the focus. (mm)
        """
        self._sensor_template.camera_sensor_template.focal_length = value

    @property
    def imager_distance(self):
        """ """
        res = self._sensor_template.camera_sensor_template.imager_distance
        return res

    @imager_distance.setter
    def imager_distance(self, value: float):
        """Set the imager distance.

        Parameters
        ----------
        value : float
            Imager distance (mm). The imager is located at the focal point. The Imager distance has no impact on the result.
        """
        self._sensor_template.camera_sensor_template.imager_distance = value

    @property
    def f_number(self) -> float:
        """ """
        res = self._sensor_template.camera_sensor_template.f_number
        return res

    @f_number.setter
    def f_number(self, value):
        """Set the f number.

        Parameters
        ----------
        value : float
            F-number represents the aperture of the front lens. F number has no impact on the result.
        """
        self._sensor_template.camera_sensor_template.f_number = value

    @property
    def distortion_file_uri(self) -> str:
        """ """
        res = self._sensor_template.camera_sensor_template.distortion_file_uri
        return res

    @distortion_file_uri.setter
    def distortion_file_uri(self, uri: str):
        """Set the distortion file.

        Parameters
        ----------
        uri : str
            Optical aberration that deforms and bends straight lines.
            The distortion is expressed in a .OPTDistortion file.

        """
        self._sensor_template.camera_sensor_template.distortion_file_uri = uri

    @property
    def horz_pixel(self) -> int:
        """ """
        res = self._sensor_template.camera_sensor_template.horz_pixel
        return res

    @horz_pixel.setter
    def horz_pixel(self, value):
        """Set the horizontal pixels number corresponding to the camera resolution.

        Parameters
        ----------
        value : int
            The horizontal pixels number corresponding to the camera resolution.
            By default, ``640``.

        Returns
        -------
        ansys.speos.core.sensor.Camera
            Camera feature
        """
        self._sensor_template.camera_sensor_template.horz_pixel = value

    @property
    def vert_pixel(self) -> int:
        """ """
        res = self._sensor_template.camera_sensor_template.vert_pixel
        return res

    @vert_pixel.setter
    def set_vert_pixel(self, value: int):
        """Set the vertical pixels number corresponding to the camera resolution.

        Parameters
        ----------
        value : int
            The vertical pixels number corresponding to the camera resolution.
        """
        self._sensor_template.camera_sensor_template.vert_pixel = value

    @property
    def width(self) -> float:
        """ """
        res = self._sensor_template.camera_sensor_template.width
        return res

    @width.setter
    def width(self, value: float):
        """Set the width of the sensor.

        Parameters
        ----------
        value : float
            Sensor's width (mm).
        """
        self._sensor_template.camera_sensor_template.width = value

    @property
    def height(self) -> float:
        """ """
        res = self._sensor_template.camera_sensor_template.height
        return res

    @height.setter
    def height(self, value: float):
        """Set the height of the sensor.

        Parameters
        ----------
        value : float
            Sensor's height (mm).
        """
        self._sensor_template.camera_sensor_template.height = value

    def set_mode_geometric(self) -> Camera:
        """Set mode geometric for the camera sensor.
        This is a simplified version of the Camera Sensor.

        Returns
        -------
        ansys.speos.core.sensor.Camera
            Geometric Camera feature
        """
        self._type = None
        self._sensor_template.camera_sensor_template.sensor_mode_geometric.SetInParent()
        return self

    def create_photometric(self, default_values: bool=True, stable_ctr: bool=False):
        photometric = Photometric._create(
            mode_photometric=self._sensor_template.camera_sensor_template.sensor_mode_photometric,
            camera_props=self._sensor_instance.camera_properties,
            default_values=default_values,
            stable_ctr=stable_ctr,
        )
        return photometric

    def set_mode_photometric(self) -> Camera.Photometric:
        """Set mode photometric for the camera sensor.
        This allows setting every Camera Sensor parameter, including the photometric definition parameters.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric
            Photometric Camera Sensor feature
        """
        if self._type is None and self._sensor_template.camera_sensor_template.HasField(
            "sensor_mode_photometric"
        ):
            # Happens in case of project created via load of speos file
            self._type = self.create_photometric(
                default_values=False,
                stable_ctr=True,
            )
        elif type(self._type) != Camera.Photometric:
            # if the _type is not Photometric then we create a new type.
            self._type = self.create_photometric(
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

    @property
    def axis_system(self) -> List[float]:
        """ """
        res = self._sensor_instance.camera_properties.axis_system[:]
        return res

    @axis_system.setter
    def axis_system(self, axis_system: List[float]):
        """Set the position of the sensor.

        Parameters
        ----------
        axis_system : Optional[List[float]]
            Position of the sensor [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        self._sensor_instance.camera_properties.axis_system[:] = axis_system
        return self

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
    stable_ctr : bool
        Variable to indicate if usage is inside class scope
    """

    def __init__(self) -> None:
        # Only here for IDE purpose
        self._mode_photometric: Optional[camera_sensor_pb2.SensorCameraModePhotometric] = None
        self._camera_props: Optional[ProtoScene.SensorInstance.CameraProperties] = None
        self._mode: Optional[Color] = None
        self._wavelengths_range: Optional[Camera.WavelengthsRange] = None

        raise RuntimeError("Use Camera.create_photometric() instead of instanciating Photometric directly.")

    @classmethod
    def _create(
        cls,
        mode_photometric: camera_sensor_pb2.SensorCameraModePhotometric,
        camera_props: ProtoScene.SensorInstance.CameraProperties,
        default_values: bool = True,
        stable_ctr: bool = False,
    ):
        if not stable_ctr:
            msg = "Photometric class instantiated outside of class scope"
            raise RuntimeError(msg)

        instance = cls.__new__(cls)

        instance._mode_photometric = mode_photometric
        instance._camera_props = camera_props

        # Attribute gathering more complex camera color mode
        instance._mode = None

        # Attribute to keep track of wavelength range object
        instance._wavelengths_range = Camera.WavelengthsRange(
            wavelengths_range=instance._mode_photometric.wavelengths_range, stable_ctr=stable_ctr
        )

        if default_values:
            # Default values
            instance.acquisition_integration = 0.01
            instance.acquisition_lag_time = 0.0
            instance.gamma_correction = 2.2
            instance.set_png_bits(16)
            instance.set_mode_color()
            # self.set_acquisition_integration().set_acquisition_lag_time().set_gamma_correction().set_png_bits_16().set_mode_color()
            instance.set_wavelengths_range()
            # Default values properties
            instance.set_layer_type_none()

    def create_color(
        self,
        default_values=False,
        stable_ctr=True
    ):
        color = Color._create(
            mode_color=self._mode_photometric.color_mode_color,
            default_values=default_values,
            stable_ctr=stable_ctr
        )
        return color

    @property
    def acquisition_integration(self) -> float:
        """ """
        res = self._mode_photometric.acquisition_integration
        return res

    @acquisition_integration.setter
    def acquisition_integration(self, value: float):
        """Set the acquisition integration value.

        Parameters
        ----------
        value : float
            Acquisition integration value (s).
        """
        self._mode_photometric.acquisition_integration = value

    @property
    def acquisition_lag_time(self) -> float:
        """ """
        res = self._mode_photometric.acquisition_lag_time
        return res

    @acquisition_lag_time.setter
    def acquisition_lag_time(self, value: float):
        """Set the acquisition lag time value.

        Parameters
        ----------
        value : float
            Acquisition lag time value (s).
        """
        self._mode_photometric.acquisition_lag_time = value

    @property
    def transmittance_file_uri(self) -> str:
        """ """
        res = self._mode_photometric.transmittance_file_uri
        return res

    @transmittance_file_uri.setter
    def transmittance_file_uri(self, uri: str):
        """Set the transmittance file.

        Parameters
        ----------
        uri : str
            Amount of light of the source that passes through the lens and reaches the sensor.
            The transmittance is expressed in a .spectrum file.
        """
        self._mode_photometric.transmittance_file_uri = uri

    @property
    def gamma_correction(self) -> float:
        """Set the gamma correction.

        Parameters
        ----------
        value : float
            Compensation of the curve before the display on the screen.
        """
        res = self._mode_photometric.gamma_correction
        return res

    @gamma_correction.setter
    def gamma_correction(self, value: float):
        """Set the gamma correction.

        Parameters
        ----------
        value : float
            Compensation of the curve before the display on the screen.
        """
        self._mode_photometric.gamma_correction = value


    def set_png_bits(self, bits: int):
        """Choose bits for png."""
        match bits:
            case 8:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
            case 10:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
            case 12:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
            case 16:
                self._mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
            case _:
                raise RuntimeError(f"Bits for PNG must be 8, 10, 12 or 16. Provided value: {bits}")

    # NOTE: This method name / use is a bit difficult to understand, should it be renamed "reset" / "refresh" ?
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

    def set_mode_monochromatic(self, spectrum_file_uri: str) -> Photometric:
        """Set the monochromatic mode.
        Results will be available in grey scale.

        Parameters
        ----------
        spectrum_file_uri : str
            Spectrum file uri.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric
            Photometric mode.
        """
        self._mode = None
        self._mode_photometric.color_mode_monochromatic.spectrum_file_uri = spectrum_file_uri
        return self

    def set_mode_color(self) -> Color:
        """Set the color mode.
        Results will be available in color.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        if self._mode is None and self._mode_photometric.HasField("color_mode_color"):
            # Happens in case of project created via load of speos file
            self._mode = self.create_color(
                mode_color=self._mode_photometric.color_mode_color,
                default_values=False,
                stable_ctr=True,
            )
        elif type(self._mode) != Color:
            # if the _mode is not Color then we create a new type.
            self._mode = self.create_color(
                mode_color=self._mode_photometric.color_mode_color, stable_ctr=True
            )
        elif self._mode._mode_color is not self._mode_photometric.color_mode_color:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._mode._mode_color = self._mode_photometric.color_mode_color
        return self._mode

    @property
    def trajectory_file_uri(self) -> str:
        """ """
        res = self._camera_props.trajectory_file_uri
        return res

    @trajectory_file_uri.setter
    def trajectory_file_uri(self, uri: str):
        """Set the trajectory file.

        Parameters
        ----------
        uri : str
            Trajectory file, used to define the position and orientations of the Camera sensor in time.

        """
        self._camera_props.trajectory_file_uri = uri

    def set_layer_type_none(self) -> Photometric:
        """Set no layer separation: includes the simulation's results in one layer.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric
            Photometric mode.
        """
        self._camera_props.layer_type_none.SetInParent()
        return self

    def set_layer_type_source(self) -> Photometric:
        """Set layer separation by source: includes one layer per active source in the result.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric
            Photometric mode.
        """
        self._camera_props.layer_type_source.SetInParent()
        return self

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
    **Do not instantiate this class yourself**, use set_mode_color method available in photometric class.

    """

    def __init__(self) -> None:
        # Only here for IDE purpose
        self._mode: Optional[Union[BalanceModeDisplayPrimaries, BalanceModeUserWhite]] = None
        self._mode_color: Optional[camera_sensor_pb2.SensorCameraColorModeColor] = None
        raise RuntimeError("Use Photometric.create_color() instead of instanciating Color directly.")

    @classmethod
    def _create(
            cls,
            mode_color: camera_sensor_pb2.SensorCameraColorModeColor,
            default_values: bool = True,
            stable_ctr: bool = False
        ):
        if not stable_ctr:
            msg = "Color class instantiated outside of class scope"
            raise RuntimeError(msg)

        instance = cls.__new__(cls)
        instance._mode_color = mode_color

        # Attribute gathering more complex camera balance mode
        instance._mode = None

        if default_values:
            # Default values
            instance.set_balance_mode_none()

    @property
    def red_spectrum_file_uri(self) -> str:
        """
        """
        res = self._mode_color.red_spectrum_file_uri
        return res

    @red_spectrum_file_uri.setter
    def set_red_spectrum_file_uri(self, uri: str):
        """Set the red spectrum.

        Parameters
        ----------
        uri : str
            Red spectrum file. It is expressed in a .spectrum file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        self._mode_color.red_spectrum_file_uri = uri

    @property
    def green_spectrum_file_uri(self) -> str:
        """
        """
        res = self._mode_color.green_spectrum_file_uri
        return res

    @green_spectrum_file_uri.setter
    def green_spectrum_file_uri(self, uri: str):
        """Set the green spectrum.

        Parameters
        ----------
        uri : str
            Green spectrum file. It is expressed in a .spectrum file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        self._mode_color.green_spectrum_file_uri = uri

    @property
    def blue_spectrum_file_uri(self) -> str:
        """
        """
        res = self._mode_color.blue_spectrum_file_uri
        return res

    @blue_spectrum_file_uri.setter
    def blue_spectrum_file_uri(self, uri: str):
        """Set the blue spectrum.

        Parameters
        ----------
        uri : str
            Blue spectrum file. It is expressed in a .spectrum file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        self._mode_color.blue_spectrum_file_uri = uri

    # NOTE: Is return value needed ?
    def set_balance_mode_none(self) -> Color:
        """Set the balance mode as none.
        The spectral transmittance of the optical system and the spectral sensitivity for each channel are applied
        to the detected spectral image before the conversion in a three-channel result.
        This method is referred to as the basic conversion.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        self._mode = None
        self._mode_color.balance_mode_none.SetInParent()
        return self

    # NOTE: Is return value needed ?
    def set_balance_mode_grey_world(self) -> Color:
        """Set the balance mode as grey world.
        The grey world assumption states that the content of the image is grey on average.
        This method converts spectral results in a three-channel result with the basic conversion.
        Then it computes and applies coefficients to the red, green and blue images to make sure their averages are equal.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color
            Color mode.
        """
        self._mode = None
        self._mode_color.balance_mode_greyworld.SetInParent()
        return self

    def set_balance_mode_user_white(self) -> BalanceModeUserWhite:
        """Set the balance mode as user white.
        In addition to the basic treatment, it allows to apply specific coefficients to the red, green, blue images.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeUserWhite
            Balance UserWhite mode.
        """
        if self._mode is None and self._mode_color.HasField("balance_mode_userwhite"):
            # Happens in case of project created via load of speos file
            self._mode = self.create_balance_mode_user_white(
                balance_mode_user_white=self._mode_color.balance_mode_userwhite,
                default_values=False,
                stable_ctr=True,
            )
        elif type(self._mode) != BalanceModeUserWhite:
            # if the _mode is not BalanceModeUserWhite then we create a new type.
            self._mode = self.create_balance_mode_user_white(
                balance_mode_user_white=self._mode_color.balance_mode_userwhite,
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
    ) -> BalanceModeDisplayPrimaries:
        """Set the balance mode as display primaries.
        Spectral results are converted in a three-channel result.
        Then a post-treatment is realized to take the distortion induced by the display devices into account.
        With this method, displayed results are similar to what the camera really gets.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
            Balance DisplayPrimaries mode.
        """
        if self._mode is None and self._mode_color.HasField("balance_mode_display"):
            # Happens in case of project created via load of speos file
            self._mode = self.create_balance_mode_display_primaries(default_values=False, stable_ctr=True,)
        elif type(self._mode) != BalanceModeDisplayPrimaries:
            # if the _mode is not BalanceModeDisplayPrimaries then we create a new type.
            self._mode = self.create_balance_mode_user_white(stable_ctr=True)
        elif self._mode._balance_mode_display is not self._mode_color.balance_mode_display:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._mode._balance_mode_display = self._mode_color.balance_mode_display
        return self._mode

    def create_balance_mode_user_white(self, default_values, stable_ctr) -> BalanceModeUserWhite:
        balance_mode_user_white = BalanceModeUserWhite._create(
            balance_mode_display=self._mode_color.balance_mode_display,
            default_values=default_values,
            stable_ctr=stable_ctr,
        )
        return balance_mode_user_white

    def create_balance_mode_display_primaries(self, default_values, stable_ctr) -> BalanceModeDisplayPrimaries:
        balance_mode_user_white = BalanceModeDisplayPrimaries._create(
            balance_mode_display=self._mode_color.balance_mode_display,
            default_values=default_values,
            stable_ctr=stable_ctr,
        )
        return balance_mode_user_white

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
    stable_ctr : bool
        Variable to indicate if usage is inside class scope

    Notes
    -----
    **Do not instantiate this class yourself**, use set_balance_mode_user_white method available in color class.

    """

    def __init__(self) -> None:
        # IDE
        self._balance_mode_user_white: Optional[camera_sensor_pb2.SensorCameraBalanceModeUserwhite] = None
        raise RuntimeError("Use Color.create_balance_mode_user_white() instead of instanciating BalanceModeUserWhite directly.")
        
    @classmethod
    def _create(
        cls,
        balance_mode_user_white: camera_sensor_pb2.SensorCameraBalanceModeUserwhite,
        default_values: bool = True,
        stable_ctr: bool = False,
    ):
        if not stable_ctr:
            msg = "BalanceModeUserWhite class instantiated outside of class scope"
            raise RuntimeError(msg)

        instance = cls.__new__(cls)
        instance._balance_mode_user_white = balance_mode_user_white

        if default_values:
            # Default values
            instance.red_gain = 1.0
            instance.green_gain = 1.0
            instance.blue_gain = 1.0

    @property
    def red_gain(self) -> float:
        """"""
        res = self._balance_mode_user_white.red_gain
        return res

    @red_gain.setter
    def red_gain(self, value):
        """Set red gain.

        Parameters
        ----------
        value : float
            Red gain.
            By default, ``1``.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeUserWhite
            BalanceModeUserWhite.
        """
        self._balance_mode_user_white.red_gain = value

    @property
    def green_gain(self) -> float:
        """
        """
        res = self._balance_mode_user_white.green_gain
        return res

    @green_gain.setter
    def green_gain(self, value: float):
        """Set green gain.

        Parameters
        ----------
        value : float
            Green gain.
            By default, ``1``.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeUserWhite
            BalanceModeUserWhite.
        """
        self._balance_mode_user_white.green_gain = value

    @property
    def blue_gain(self) -> float:
        """"""
        res = self._balance_mode_user_white.blue_gain
        return res

    @blue_gain.setter
    def blue_gain(self, value: float):
        """Set blue gain.

        Parameters
        ----------
        value : float
            Blue gain.
            By default, ``1``.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeUserWhite
            BalanceModeUserWhite.
        """
        self._balance_mode_user_white.blue_gain = value

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

    Notes
    -----
    **Do not instantiate this class yourself**, use set_balance_mode_display_primaries method available in color class.

    """

    def __init__(self) -> None:
        # IDE
        self._balance_mode_display: Optional[camera_sensor_pb2.SensorCameraBalanceModeDisplay] = None
        raise RuntimeError("Use Color.create_balance_mode_display_primaries() instead of instanciating BalanceModeUserWhite directly.")

    @classmethod
    def _create(
        cls,
        balance_mode_display: camera_sensor_pb2.SensorCameraBalanceModeDisplay,
        default_values: bool = True,
        stable_ctr: bool = False,
    ) -> None:
        if not stable_ctr:
            msg = (
                "BalanceModeDisplayPrimaries class instantiated outside of class scope"
            )
            raise RuntimeError(msg)

        instance = cls.__new__(cls)
        instance._balance_mode_display = balance_mode_display

        if default_values:
            # Default values
            instance._balance_mode_display.SetInParent()

    @property
    def red_display_file_uri(self) -> str:
        """Set the red display file.

        Parameters
        ----------
        uri : str
            Red display file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
            BalanceModeDisplayPrimaries.
        """
        res = self._balance_mode_display.red_display_file_uri
        return res

    @red_display_file_uri.setter
    def red_display_file_uri(self, uri: str):
        """Set the red display file.

        Parameters
        ----------
        uri : str
            Red display file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
            BalanceModeDisplayPrimaries.
        """
        self._balance_mode_display.red_display_file_uri = uri

    @property
    def green_display_file_uri(self) -> str:
        """
        """
        res = self._balance_mode_display.green_display_file_uri
        return res

    @green_display_file_uri.setter
    def green_display_file_uri(self, uri: str):
        """Set the green display file.

        Parameters
        ----------
        uri : str
            Green display file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
            BalanceModeDisplayPrimaries.
        """
        self._balance_mode_display.green_display_file_uri = uri

    @property
    def blue_display_file_uri(self) -> str:
        """
        """
        res = self._balance_mode_display.blue_display_file_uri
        return res

    @blue_display_file_uri.setter
    def blue_display_file_uri(self, uri: str):
        """Set the blue display file.

        Parameters
        ----------
        uri : str
            Blue display file.

        Returns
        -------
        ansys.speos.core.sensor.Camera.Photometric.Color.BalanceModeDisplayPrimaries
            BalanceModeDisplayPrimaries.
        """
        self._balance_mode_display.blue_display_file_uri = uri
