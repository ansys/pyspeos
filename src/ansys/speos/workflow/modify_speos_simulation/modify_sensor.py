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

from __future__ import annotations

import sys
import time
from typing import List, Optional

from ansys.api.speos.job.v2 import job_pb2
from ansys.api.speos.part.v1 import part_pb2
from ansys.api.speos.scene.v2 import scene_pb2
from ansys.api.speos.sensor.v1 import camera_sensor_pb2
from google.protobuf.internal.containers import RepeatedScalarFieldContainer
import numpy as np
import pyvista as pv

import ansys.speos.core as core


def clean_all_dbs(speos_client: core.SpeosClient) -> None:
    """
    Clean all databases.

    Parameters
    ----------
    speos_client : core.SpeosClient
        Speos gRPC client.
    """
    for item in (
        speos_client.jobs().list()
        + speos_client.scenes().list()
        + speos_client.simulation_templates().list()
        + speos_client.sensor_templates().list()
        + speos_client.source_templates().list()
        + speos_client.intensity_templates().list()
        + speos_client.spectrums().list()
        + speos_client.vop_templates().list()
        + speos_client.sop_templates().list()
        + speos_client.parts().list()
        + speos_client.bodies().list()
        + speos_client.faces().list()
    ):
        item.delete()


def print_progress_bar(
    iteration: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 50,
    fill: str = "█",
    printEnd: str = "\r",
):
    """
    Call in a loop to create terminal progress bar

    Parameters
    ----------
    iteration : int
        Current iteration.
    total : int
        Total iterations.
    prefix : str, optional
        Prefix string.
        By default, ``""``.
    suffix : str, optional
        Suffix string.
        By default, ``""``.
    decimals : int, optional
        Positive number of decimals in percent complete.
        By default, ``1``.
    length : int, optional
        Character length of bar.
        By default, ``50``.
    fill : str, optional
        Bar fill character.
        By default, ``"█"``.
    printEnd : str, optional
        End character (e.g. "\\r", "\\r\\n").
        By default, ``"\\r"``.
    """

    percent = ("{0:." + str(decimals) + "f}").format(100)
    filledLength = int(length)

    if total > 0:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)

    bar = fill * filledLength + "-" * (length - filledLength)

    # setup toolbar
    prog = f"{prefix} |{bar}| {percent}%"

    if iteration != 0:
        prog = f"{bar}| {percent}%"

    sys.stdout.write(prog)
    sys.stdout.flush()
    sys.stdout.write("\b" * (len(f"{bar}| {percent}%")))

    # Print New Line on Complete
    if iteration == total:
        sys.stdout.write("\n")
        sys.stdout.flush()


class IrradianceSensorParameters:
    """
    Irradiance sensor with its parameters.

    name = name of the sensor
    integration_type
    type
    x_range_start
    x_range_end
    x_range_sampling
    y_range_start
    y_range_end
    y_range_sampling
    wavelengths_start
    wavelengths_end
    wavelengths_sampling
    """

    def __init__(self) -> None:
        self.name = "irradiance sensor"
        self.integration_type = core.SensorTemplateFactory.IlluminanceType.Planar
        self.type = core.SensorTemplateFactory.Type.Photometric
        self.x_range_start = -50
        self.x_range_end = 50
        self.x_range_sampling = 100
        self.y_range_start = -50
        self.y_range_end = 50
        self.y_range_sampling = 100
        self.wavelengths_start = 400
        self.wavelengths_end = 700
        self.wavelengths_sampling = 13

    def copy(self) -> IrradianceSensorParameters:
        """
        Copy current object into a new one.

        Returns
        -------
        IrradianceSensorParameters
            Parameters copied.
        """
        copied_parameters = IrradianceSensorParameters()
        copied_parameters.name = self.name
        copied_parameters.integration_type = self.integration_type
        copied_parameters.type = self.type
        copied_parameters.x_range_start = self.x_range_start
        copied_parameters.x_range_start = self.x_range_start
        copied_parameters.x_range_sampling = self.x_range_sampling
        copied_parameters.y_range_start = self.y_range_start
        copied_parameters.y_range_end = self.y_range_end
        copied_parameters.y_range_sampling = self.y_range_sampling
        copied_parameters.wavelengths_start = self.wavelengths_start
        copied_parameters.wavelengths_end = self.wavelengths_end
        copied_parameters.wavelengths_sampling = self.wavelengths_sampling
        return copied_parameters

    def create_template(self) -> core.SensorTemplate:
        """
        Create protobuf message SensorTemplate from current object.

        Returns
        -------
        core.SensorTemplate
            Protobuf message created.
        """

        w_range = None
        if self.type == core.SensorTemplateFactory.Type.Colorimetric or self.type == core.SensorTemplateFactory.Type.Spectral:
            w_range = core.SensorTemplateFactory.WavelengthsRange(
                start=self.wavelengths_start, end=self.wavelengths_end, sampling=self.wavelengths_sampling
            )
        return core.SensorTemplateFactory.irradiance(
            name=self.name,
            type=self.type,
            illuminance_type=self.integration_type,
            dimensions=core.SensorTemplateFactory.Dimensions(
                x_start=self.x_range_start,
                x_end=self.x_range_end,
                x_sampling=self.x_range_sampling,
                y_start=self.y_range_start,
                y_end=self.y_range_end,
                y_sampling=self.y_range_sampling,
            ),
            wavelengths_range=w_range,
        )


class IrradianceSensorProperties(core.AxisSystem):
    """
    Properties for irradiance sensor.

    PositionProperties
    layer_type: "None", "Source"
    """

    def __init__(self) -> None:
        super().__init__()
        self.layer_type = "None"

    def create_properties(self) -> core.Scene.SensorInstance.IrradianceProperties:
        """
        Create protobuf message IrradianceProperties from current object.

        Returns
        -------
        core.Scene.SensorInstance.IrradianceProperties
            Protobuf message created.
        """
        irradiance_sensor_axis_system = core.AxisSystem(origin=self.origin, x_vect=self.x_vect, y_vect=self.y_vect, z_vect=self.z_vect)

        layer_type = None
        if self.layer_type == "Source":
            layer_type = core.SceneFactory.Properties.Sensor.LayerType.Source

        properties = core.SceneFactory.irradiance_sensor_props(axis_system=irradiance_sensor_axis_system, layer_type=layer_type)

        return properties


class PhotometricCameraSensorParameters:
    """
    Photometric camera sensor with its parameters.

    name = name of the sensor
    focal_length
    imager_distance
    f_number
    distortion_file
    transmittance_file
    horizontal_pixel
    vertical_pixel
    width
    height
    acquisition_integration
    acquisition_lag_time
    gamma_correction
    png_bits: 8, 10, 12, 16
    color_mode_balance_mode: "None", "Grey world", "User white balance", "Display primaries"
    color_mode_red_spectrum_file
    color_mode_green_spectrum_file
    color_mode_blue_spectrum_file
    wavelengths_start
    wavelengths_end
    wavelengths_sampling
    """

    def __init__(self) -> None:
        self.name = "camera sensor"

        self.focal_length = 5
        self.imager_distance = 10
        self.f_number = 20

        self.distortion_file = ""
        self.transmittance_file = ""

        self.horizontal_pixel = 640
        self.vertical_pixel = 480
        self.width = 5.0
        self.height = 5.0

        self.acquisition_integration = 0.01
        self.acquisition_lag_time = 0.0

        self.gamma_correction = 2.2
        self.png_bits = 16
        self.color_mode_balance_mode = ""
        self.color_mode_red_spectrum_file = ""
        self.color_mode_green_spectrum_file = ""
        self.color_mode_blue_spectrum_file = ""

        self.color_balance_mode_red_spectrum_file = ""
        self.color_balance_mode_green_spectrum_file = ""
        self.color_balance_mode_blue_spectrum_file = ""

        self.color_balance_mode_red_gain = 1
        self.color_balance_mode_green_gain = 1
        self.color_balance_mode_blue_gain = 1

        self.wavelengths_start = 400
        self.wavelengths_end = 700
        self.wavelengths_sampling = 13

    def copy(self) -> PhotometricCameraSensorParameters:
        """
        Copy current object into a new one.

        Returns
        -------
        PhotometricCameraSensorParameters
            Parameters copied.
        """
        copied_parameters = PhotometricCameraSensorParameters()

        copied_parameters.name = self.name

        copied_parameters.focal_length = self.focal_length
        copied_parameters.imager_distance = self.imager_distance
        copied_parameters.f_number = self.f_number

        copied_parameters.distortion_file = self.distortion_file
        copied_parameters.transmittance_file = self.transmittance_file

        copied_parameters.horizontal_pixel = self.horizontal_pixel
        copied_parameters.vertical_pixel = self.vertical_pixel
        copied_parameters.width = self.width
        copied_parameters.height = self.height

        copied_parameters.acquisition_integration = self.acquisition_integration
        copied_parameters.acquisition_lag_time = self.acquisition_lag_time

        copied_parameters.gamma_correction = self.gamma_correction
        copied_parameters.png_bits = self.png_bits
        copied_parameters.color_mode_balance_mode = self.color_mode_balance_mode
        copied_parameters.color_mode_red_spectrum_file = self.color_mode_red_spectrum_file
        copied_parameters.color_mode_green_spectrum_file = self.color_mode_green_spectrum_file
        copied_parameters.color_mode_blue_spectrum_file = self.color_mode_blue_spectrum_file

        copied_parameters.color_balance_mode_red_spectrum_file = self.color_balance_mode_red_spectrum_file
        copied_parameters.color_balance_mode_green_spectrum_file = self.color_balance_mode_green_spectrum_file
        copied_parameters.color_balance_mode_blue_spectrum_file = self.color_balance_mode_blue_spectrum_file

        copied_parameters.color_balance_mode_red_gain = self.color_balance_mode_red_gain
        copied_parameters.color_balance_mode_green_gain = self.color_balance_mode_green_gain
        copied_parameters.color_balance_mode_blue_gain = self.color_balance_mode_blue_gain

        copied_parameters.wavelengths_start = self.wavelengths_start
        copied_parameters.wavelengths_end = self.wavelengths_end
        copied_parameters.wavelengths_sampling = self.wavelengths_sampling

        return copied_parameters

    def create_template(self) -> core.SensorTemplate:
        """
        Create protobuf message SensorTemplate from current object.

        Returns
        -------
        core.SensorTemplate
            Protobuf message created.
        """
        sensor_t_data = core.SensorTemplate(name=self.name)

        sensor_t_data.camera_sensor_template.distorsion_file_uri = self.distortion_file
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.transmittance_file_uri = self.transmittance_file

        sensor_t_data.camera_sensor_template.focal_length = self.focal_length
        sensor_t_data.camera_sensor_template.imager_distance = self.imager_distance
        sensor_t_data.camera_sensor_template.f_number = self.f_number

        sensor_t_data.camera_sensor_template.horz_pixel = self.horizontal_pixel
        sensor_t_data.camera_sensor_template.vert_pixel = self.vertical_pixel
        sensor_t_data.camera_sensor_template.width = self.width
        sensor_t_data.camera_sensor_template.height = self.height

        sensor_t_data.camera_sensor_template.sensor_mode_photometric.acquisition_integration = self.acquisition_integration
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.acquisition_lag_time = self.acquisition_lag_time

        sensor_t_data.camera_sensor_template.sensor_mode_photometric.gamma_correction = self.gamma_correction

        if self.png_bits == 8:
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
        elif self.png_bits == 10:
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
        elif self.png_bits == 12:
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
        elif self.png_bits == 16:
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.png_bits = camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16

        sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.red_spectrum_file_uri = (
            self.color_mode_red_spectrum_file
        )
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.green_spectrum_file_uri = (
            self.color_mode_green_spectrum_file
        )
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.blue_spectrum_file_uri = (
            self.color_mode_blue_spectrum_file
        )

        if self.color_mode_balance_mode == "None":
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_none.SetInParent()
        elif self.color_mode_balance_mode == "Grey world":
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_greyworld.SetInParent()
        elif self.color_mode_balance_mode == "User white balance":
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.SetInParent()
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.red_gain = (
                self.color_balance_mode_red_gain
            )
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.green_gain = (
                self.color_balance_mode_green_gain
            )
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain = (
                self.color_balance_mode_blue_gain
            )
        elif self.color_mode_balance_mode == "Display primaries":
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_display.SetInParent()
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri = (
                self.color_balance_mode_red_spectrum_file
            )
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri = (
                self.color_balance_mode_green_spectrum_file
            )
            sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri = (
                self.color_balance_mode_blue_spectrum_file
            )

        sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start = self.wavelengths_start
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end = self.wavelengths_end
        sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_sampling = self.wavelengths_sampling

        return sensor_t_data


class CameraSensorProperties(core.AxisSystem):
    """
    Properties for camera sensor.

    PositionProperties
    trajectory_file
    layer_type: "None", "Source"
    """

    def __init__(self) -> None:
        super().__init__()
        self.trajectory_file = ""
        self.layer_type = "None"

    def create_properties(self) -> core.Scene.SensorInstance.CameraProperties:
        """
        Create protobuf message CameraProperties from current object.

        Returns
        -------
        core.Scene.SensorInstance.CameraProperties
            Protobuf message created.
        """
        camera_axis_system = core.AxisSystem(origin=self.origin, x_vect=self.x_vect, y_vect=self.y_vect, z_vect=self.z_vect)

        temp_trajectory_file = None
        if self.trajectory_file != "":
            temp_trajectory_file = self.trajectory_file

        layer_type = None
        if self.layer_type == "Source":
            layer_type = core.SceneFactory.Properties.Sensor.LayerType.Source

        properties = core.SceneFactory.camera_sensor_props(
            axis_system=camera_axis_system, trajectory_file_uri=temp_trajectory_file, layer_type=layer_type
        )

        return properties


class SpeosSimulationUpdate:
    """
    Class to load ".speos" simulation file in order to update it.

    Parameters
    ----------
    speos : core.Speos
        Speos session (connected to gRPC server).
    file_name : str
        ".speos" simulation file name.
        By Default , ``""`` (this means empty speos simulation).
    """

    def __init__(self, speos: core.Speos, file_name: str = "", clean_dbs: bool = True):
        self._speos = speos
        if clean_dbs:
            clean_all_dbs(self._speos.client)

        self._scene = self._speos.client.scenes().create()
        self._status = ""
        self._modified = False
        self._preview_mesh = None
        self._part = core.Part()

        # Create empty scene and load file
        if len(file_name) != 0:
            self._scene.load_file(file_uri=file_name)

        self._status = "Opened"

    @property
    def scene(self) -> core.SceneLink:
        """The scene."""
        return self._scene

    @property
    def status(self) -> str:
        """The status."""
        return self._status

    def preview(self) -> None:
        """preview cad bodies inside the scene."""

        p = pv.Plotter()
        if self._preview_mesh is not None and self._modified is False:
            p.add_mesh(self._preview_mesh, show_edges=True)
            p.show()
            return
        root_part_data = self._speos.client.get_item(self._scene.get().part_guid).get()
        if len(root_part_data.parts) != 0:
            for part_idx, part_item in enumerate(root_part_data.parts):
                part_item_data = self._speos.client.get_item(part_item.part_guid).get()
                if self._preview_mesh is None:
                    self._preview_mesh = self.__extract_part_mesh_info(part_item_data, part_item.axis_system)
                else:
                    self._preview_mesh = self._preview_mesh.append_polydata(
                        self.__extract_part_mesh_info(part_item_data, part_item.axis_system)
                    )
        else:
            self._preview_mesh = self.__extract_part_mesh_info(root_part_data)
        self._modified = False
        p.add_mesh(self._preview_mesh, show_edges=True)
        p.show()

    def __extract_part_mesh_info(self, part_data: part_pb2, part_coordinate_info: RepeatedScalarFieldContainer = None) -> pv.PolyData:
        """
        extract mesh data info from a part.

        Parameters
        ----------
        part_data: ansys.api.speos.part.v1.part_pb2
            Part from scene.
        part_coordinate_info: RepeatedScalarFieldContainer
            message contains part coordinate info: origin, x_vector, y_vector, z_vector
        Returns
        -------
        pv.PolyData
            mesh data extracted.

        """

        def local2absolute(local_vertice: np.ndarray) -> np.ndarray:
            """
            convert local coordinate to global coordinate.

            Parameters
            ----------
            local_vertice: np.ndarray
                numpy array includes x, y, z info.

            Returns
            -------
            np.ndarray
             numpy array includes x, y, z info

            """
            global_origin = np.array(part_coordinate.origin)
            global_x = np.array(part_coordinate.x_vect) * local_vertice[0]
            global_y = np.array(part_coordinate.y_vect) * local_vertice[1]
            global_z = np.array(part_coordinate.z_vect) * local_vertice[2]
            return global_origin + global_x + global_y + global_z

        part_coordinate = core.AxisSystem()
        part_coordinate.origin = [0.0, 0.0, 0.0]
        part_coordinate.x_vect = [1.0, 0.0, 0.0]
        part_coordinate.y_vect = [0.0, 1.0, 0.0]
        part_coordinate.z_vect = [0.0, 0.0, 1.0]
        if part_coordinate_info is not None:
            part_coordinate.origin = part_coordinate_info[:3]
            part_coordinate.x_vect = part_coordinate_info[3:6]
            part_coordinate.y_vect = part_coordinate_info[6:9]
            part_coordinate.z_vect = part_coordinate_info[9:]
        part_mesh_info = None
        for body_idx, body_guid in enumerate(part_data.body_guids):
            body_item_data = self._speos.client.get_item(body_guid).get()
            for face_idx, face_guid in enumerate(body_item_data.face_guids):
                face_item_data = self._speos.client.get_item(face_guid).get()
                vertices = np.array(face_item_data.vertices)
                facets = np.array(face_item_data.facets)
                vertices = vertices.reshape(-1, 3)
                vertices = np.array([local2absolute(vertice) for vertice in vertices])
                facets = facets.reshape(-1, 3)
                temp = np.full(facets.shape[0], 3)
                temp = np.vstack(temp)
                facets = np.hstack((temp, facets))
                face_mesh_data = pv.PolyData(vertices, facets)
                if part_mesh_info is None:
                    part_mesh_info = face_mesh_data
                else:
                    part_mesh_info = part_mesh_info.append_polydata(face_mesh_data)
        return part_mesh_info

    def add_camera_sensor(
        self,
        sensor_parameters: PhotometricCameraSensorParameters,
        sensor_properties: CameraSensorProperties,
        simulation_idxs: List[int] = [0],
    ) -> None:
        """
        Add a camera sensor template to the scene with the corresponding properties, and reference it in the chosen simulations.

        Parameters
        ----------
        sensor_parameters : PhotometricCameraSensorParameters
            Sensor parameters.
        sensor_properties : CameraSensorProperties
            Sensor properties.
        simulation_idxs : List[int]
            List of the chosen simulation indexes where the sensor will be referenced.
            By default, ``[0]``, ie the first simulation.
        """
        sensor_template_db = self._speos.client.sensor_templates()

        # Store SensorTemplate protobuf message in db and retrieve SensorTemplateLink
        sensor_template_link = sensor_template_db.create(message=sensor_parameters.create_template())

        # Retrieve scene datamodel
        scene_data = self._scene.get()

        # Create camera instance
        camera_sensor_instance = core.SceneFactory.sensor_instance(
            name=sensor_template_link.get().name + ".1",
            sensor_template=sensor_template_link,
            properties=sensor_properties.create_properties(),
        )

        # Modify scene datamodel
        scene_data.sensors.append(camera_sensor_instance)

        # Reference camera sensor instance in the chosen simulation instances
        for simu_idx in simulation_idxs:
            if camera_sensor_instance.name not in scene_data.simulations[simu_idx].sensor_paths:
                scene_data.simulations[simu_idx].sensor_paths.append(camera_sensor_instance.name)

        # Update value in db
        self._scene.set(scene_data)

    def add_irradiance_sensor(
        self, sensor_parameters: IrradianceSensorParameters, sensor_properties: IrradianceSensorProperties, simulation_idxs: List[int] = [0]
    ) -> None:
        """
        Add an irradiance sensor template to the scene with the corresponding properties.

        Parameters
        ----------
        sensor_parameters : IrradianceSensorParameters
            Sensor parameters.
        sensor_properties : IrradianceSensorProperties
            Sensor properties.
        simulation_idxs : List[int]
            List of the chosen simulation indexes where the sensor will be referenced.
            By default, ``[0]``, ie the first simulation.
        """
        sensor_template_db = self._speos.client.sensor_templates()

        # Store SensorTemplate protobuf message in db and retrieve SensorTemplateLink
        sensor_template_link = sensor_template_db.create(message=sensor_parameters.create_template())

        # Retrieve scene datamodel
        scene_data = self._scene.get()

        # Create camera instance
        sensor_instance = core.SceneFactory.sensor_instance(
            name=sensor_template_link.get().name + ".1",
            sensor_template=sensor_template_link,
            properties=sensor_properties.create_properties(),
        )

        # Modify scene datamodel
        scene_data.sensors.append(sensor_instance)

        # Reference camera sensor instance in the chosen simulation instances
        for simu_idx in simulation_idxs:
            if sensor_instance.name not in scene_data.simulations[simu_idx].sensor_paths:
                scene_data.simulations[simu_idx].sensor_paths.append(sensor_instance.name)

        # Update value in db
        self._scene.set(scene_data)

    def update_sensor(
        self,
        template_parameters: IrradianceSensorParameters or PhotometricCameraSensorParameters,
        template_properties: IrradianceSensorProperties or CameraSensorProperties,
    ) -> None:
        """
        Update sensor to the scene with the sensor parameter and properties.

        Parameters
        ----------
        template_parameters : IrradianceSensorParameters or PhotometricCameraSensorParameters,
            Sensor parameters.
        template_properties : IrradianceSensorProperties or CameraSensorProperties
            Sensor properties.
        """
        if isinstance(template_parameters, IrradianceSensorParameters) and isinstance(template_properties, IrradianceSensorProperties):
            ssr_template = template_parameters.create_template()
            ssr = self._speos.client.sensor_templates().create(message=ssr_template)

            scene_data = self._scene.get()
            for sensor in scene_data.sensors:
                if sensor.name == template_parameters.name + ".1":
                    sensor.sensor_guid = ssr.key
                    sensor.irradiance_properties.ClearField("axis_system")
                    sensor.irradiance_properties.axis_system.extend(
                        template_properties.origin + template_properties.x_vect + template_properties.y_vect + template_properties.z_vect
                    )
                    sensor.irradiance_properties.layer_type_none.SetInParent()
            self._scene.set(scene_data)
        elif isinstance(template_parameters, PhotometricCameraSensorParameters) and isinstance(template_properties, CameraSensorProperties):
            ssr_template = template_parameters.create_template()
            ssr = self._speos.client.sensor_templates().create(message=ssr_template)
            scene_data = self._scene.get()
            for sensor in scene_data.sensors:
                if sensor.name == template_parameters.name + ".1":
                    sensor.sensor_guid = ssr.key
                    sensor.camera_properties.ClearField("axis_system")
                    sensor.camera_properties.axis_system.extend(
                        template_properties.origin + template_properties.x_vect + template_properties.y_vect + template_properties.z_vect
                    )
                    sensor.camera_properties.layer_type_none.SetInParent()
            self._scene.set(scene_data)

    def update_scene_part_position(self, new_part_positions: {str: core.AxisSystem}) -> None:
        """
        update component position with given dictionary of component_part name with corresponding position.

        Parameters
        ----------
        new_part_positions: {str: core.AxisSystem}
            dictionary with key of component_part name and value of corresponding position
        """
        root_part = self._speos.client.get_item(self._scene.get().part_guid)
        root_part_data = root_part.get()
        assert len(root_part_data.parts) != 0
        for part_item in root_part_data.parts:
            if part_item.name in new_part_positions:
                print("Update {} position".format(part_item.name))
                position_properties = new_part_positions[part_item.name]
                part_item.ClearField("axis_system")
                part_item.axis_system.extend(
                    position_properties.origin + position_properties.x_vect + position_properties.y_vect + position_properties.z_vect
                )
        root_part.set(root_part_data)
        self._modified = True

    def add_scene(self, simulation_scene: SpeosSimulationUpdate, position_info: core.AxisSystem, only_geometry: bool = False) -> None:
        """
        assemble simulation scene into an assembly scene.

        Parameters
        ----------
        simulation_scene: SpeosSimulationUpdate
            simulation scene
        position_info: core.AxisSystem
            position information origin x, origin y, origin z, axis-x, axis-y, axis-z
        only_geometry: bool
            In case only the geometry need to be added (no sources, sensors, simulations), set this boolean to True.
            By default, ``False``.
        """
        simulation_scene_data = simulation_scene.scene.get()

        # Create new part instance from the part of simulation_scene_data + place it to the selected position
        new_part_instance = core.Part.PartInstance()
        new_part_instance.name = simulation_scene_data.name
        new_part_instance.part_guid = simulation_scene_data.part_guid
        new_part_instance.axis_system.extend(position_info.origin + position_info.x_vect + position_info.y_vect + position_info.z_vect)

        # Append to the SSU root part + create the corresponding part link
        self._part.parts.append(new_part_instance)
        part_link = self._speos.client.parts().create(message=self._part)

        # Retrieve scene data + use new part_link
        data = self._scene.get()
        data.part_guid = part_link.key

        # Adapt vops and sops geo_paths (geo_path="part_instance_name/" + geo_path)
        self.__adapt_materials(simulation_scene, data)

        # In case only the geometry is needed, don't take care of sources, sensors, simulations
        if not only_geometry:
            # Retrieve all sensor instances and add them to the scene
            for ssr in simulation_scene_data.sensors:
                data.sensors.append(ssr)

            # Retrieve all source instances and add them to the scene
            for simu in simulation_scene_data.simulations:
                data.simulations.append(simu)

            # Retrieve all source instances and add them to the scene
            for src in simulation_scene_data.sources:
                # Adapt srcs geo_path (in case of surface source)
                self.__adapt_source(source_instance=src, simulation_scene_name=simulation_scene_data.name)
                data.sources.append(src)

                if src.name not in data.simulations[0].source_paths:
                    data.simulations[0].source_paths.append(src.name)

        self._scene.set(data)
        self._modified = True

    def __adapt_materials(self, simulation_scene: SpeosSimulationUpdate, data: scene_pb2.Scene) -> None:
        """
        adapt materials geometry path on the inserted scene.

        Parameters
        ----------
        simulation_scene: SpeosSimulationUpdate
            simulation scene
        data: ansys.api.speos.scene.v2.scene_pb2.Scene
            scene data
        """
        adapt_path_name = simulation_scene.scene.get().name
        for mat in simulation_scene.scene.get().materials:
            new_mat = core.Scene.MaterialInstance()
            new_mat.CopyFrom(mat)
            if mat.HasField("geometries"):
                new_mat.geometries.Clear()
                for g_path in mat.geometries.geo_paths:
                    g_path = adapt_path_name + "/" + g_path
                    new_mat.geometries.geo_paths.append(g_path)
            data.materials.append(new_mat)

    def __adapt_source(self, source_instance: core.Scene.SourceInstance, simulation_scene_name: str) -> None:
        """
        adapt source geometry path on the inserted scene.

        Parameters
        ----------
        source_instance: core.Scene.SourceInstance
            Source instance to adapt geometry path
        simulation_scene_name: str
            Simulation scene name to be added to the geometry path so that it is correct
        """
        if source_instance.surface_properties.HasField("exitance_constant_properties"):
            for g in source_instance.surface_properties.exitance_constant_properties.geo_paths:
                g.geo_path = simulation_scene_name + "/" + g.geo_path

    def compute(
        self,
        job_name="new_job",
        stop_condition_duration: Optional[int] = None,
        compute_type: Optional[str] = "cpu",
        simulation_idx: int = 0,
    ) -> core.JobLink:
        """Compute selected simulation.

        Parameters
        ----------

        job_name : str
            Name of the job.
            By default, ``"new_job"``.
        stop_condition_duration : int, optional
            Duration in s to be used as stop condition.
            By default, ``None``.
        compute_type: str, optional
            compute using CPU or GPU
            By default, ``"cpu"``.
        simulation_idx: int, optional
            index of the simulation to compute.
            By default, ``0``, ie the first simulation.

        Returns
        -------
        core.JobLink
            Job who launched the simulation.
        """

        scene_data = self._scene.get()
        if len(scene_data.simulations) == 0:
            raise ValueError("At least one simulation is needed in the scene.")
        if simulation_idx >= len(scene_data.simulations):
            raise ValueError("Issue with a too high simulation_idx. The scene does not contain as many simulations.")

        simu_t_link = self._speos.client.get_item(scene_data.simulations[simulation_idx].simulation_guid)
        props = None
        if isinstance(simu_t_link, core.SimulationTemplateLink):
            simu_t_data = simu_t_link.get()
            if simu_t_data.HasField("direct_mc_simulation_template"):
                props = core.JobFactory.direct_mc_props(stop_condition_duration=stop_condition_duration)
            elif simu_t_data.HasField("inverse_mc_simulation_template"):
                props = core.JobFactory.inverse_mc_props(stop_condition_duration=stop_condition_duration)
            elif simu_t_data.HasField("interactive_simulation_template"):
                props = core.JobFactory.interactive_props()

        if props is None:
            raise KeyError(core.SimulationTemplateLink)

        compute_type = core.JobFactory.Type.GPU if compute_type.lower() == "gpu" else core.JobFactory.Type.CPU

        new_job = self._speos.client.jobs().create(
            message=core.JobFactory.new(
                name=job_name,
                scene=self._scene,
                simulation_path=scene_data.simulations[simulation_idx].name,
                properties=props,
                type=compute_type,
            )
        )

        new_job.start()

        job_state_res = new_job.get_state()
        while (
            job_state_res.state != job_pb2.Job.State.FINISHED
            and job_state_res.state != job_pb2.Job.State.STOPPED
            and job_state_res.state != job_pb2.Job.State.IN_ERROR
        ):
            time.sleep(5)
            print_progress_bar(new_job.get_progress_status().progress, 1, "Processing: ")

            job_state_res = new_job.get_state()
            if job_state_res.state == job_pb2.Job.State.IN_ERROR:
                core.LOG.error(core.protobuf_message_to_str(new_job.get_error()))

        return new_job

    def close(self):
        """Clean SpeosSimulationUpdate before closing"""

        self._scene.delete()
        self._status = "Closed"
        clean_all_dbs(self._speos.client)
