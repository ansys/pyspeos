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

import os.path
import sys
import time
import uuid

import ansys.api.speos.job.v2.job_pb2 as job_pb2

import ansys.speos.core as core
import ansys.speos.workflow as workflow


class Utilities:
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


class SourceIntensity:
    def __init__(self, speos):
        self.__speos = speos
        self.__type = "lambertian"
        # lambertian property
        self.__total_angle = 180
        # symmetric gaussian property
        self.__FWHM_angle = 30
        # intensity class property
        self.__instance = None
        self.__create()

    @property
    def intensity(self):
        return self.__instance

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, intensity_type: str = "lambertian"):
        types_allowed = ["lambertian", "symmetric gaussian"]
        assert intensity_type.lower() in types_allowed
        self.__type = intensity_type.lower()
        self.__create()

    @property
    def total_angle(self):
        return self.__total_angle

    @total_angle.setter
    def total_angle(self, angle_val: float = 180):
        self.__total_angle = angle_val if 0.0 < angle_val < 180.0 else (0.0 if angle_val < 0.0 else 180.0)
        self.__create()

    @property
    def FWHM_angle(self):
        return self.__FWHM_angle

    @FWHM_angle.setter
    def FWHM_angle(self, angle_val: float = 30):
        self.__FWHM_angle = angle_val if 0.0 < angle_val < 180.0 else (0.0 if angle_val < 0.0 else 180.0)
        self.__create()

    def __create(self):
        if self.__type == "lambertian":
            self.__instance = self.__speos.client.intensity_templates().create(
                message=core.intensity_template.IntensityTemplateFactory.lambertian(
                    name="lambertian_{}".format(self.__total_angle),
                    description="lambertian intensity template {}".format(self.__total_angle),
                    total_angle=self.__total_angle,
                )
            )
        elif self.__type == "symmetric gaussian":
            self.__instance = self.__speos.client.intensity_templates().create(
                message=core.intensity_template.IntensityTemplateFactory.symmetric_gaussian(
                    name="symmetric gaussian_{}".format(self.__total_angle),
                    description="symmetric gaussian intensity template {}".format(self.__total_angle),
                    FWHM_angle=self.__FWHM_angle,
                    total_angle=self.__total_angle,
                )
            )
        else:
            raise Exception


class Spectrum:
    def __init__(self, speos):
        self.__speos = speos
        self.__type = "blackbody"
        # blackbody property
        self.__temperature = 2856
        # monochromatic property
        self.__wavelength = 555
        # spectrum class property
        self.__instance = None
        self.__create()

    @property
    def spectrum(self):
        self.__create()
        return self.__instance

    @property
    def type(self) -> str:
        return self.__type

    @type.setter
    def type(self, spectrum_type: str = "blackbody") -> None:
        types_allowed = ["blackbody", "monochromatic"]
        assert spectrum_type.lower() in types_allowed
        self.__type = spectrum_type.lower()

    @property
    def temperature(self) -> float:
        return self.__temperature

    @temperature.setter
    def temperature(self, temp_val) -> None:
        self.__temperature = temp_val if 0.0 < temp_val < 100000 else (0.0 if temp_val < 0.0 else 100000)
        self.__create()

    @property
    def wavelength(self) -> float:
        return self.__wavelength

    @wavelength.setter
    def wavelength(self, wavelength_val) -> None:
        self.__wavelength = wavelength_val if 0.0 < wavelength_val < 10000 else (0.0 if wavelength_val < 0.0 else 10000)
        self.__create()

    def __create(self):
        if self.__type == "blackbody":
            self.__instance = self.__speos.client.spectrums().create(
                message=core.spectrum.SpectrumFactory.blackbody(
                    name="blackbody_{}".format(self.__temperature),
                    description="blackbody spectrum - T {}".format(self.__temperature),
                    temperature=self.__temperature,
                )
            )
        elif self.__type == "monohromatic":
            self.__instance = self.__speos.client.spectrums().create(
                message=core.spectrum.SpectrumFactory.monochromatic(
                    name="monochromatic_{}".format(self.__wavelength),
                    description="monochromatic spectrum - W {}".format(self.__wavelength),
                    wavelength=self.__wavelength,
                )
            )
        else:
            raise Exception


class SourceSurface:
    def __init__(self, speos, emissive_faces: list[str], name: str = "surface_source_" + uuid.uuid4().hex):
        self.__speos = speos
        self.name = name
        self.__emissive_faces = emissive_faces
        self.__intensity = SourceIntensity(self.__speos)
        self.__spectrum = Spectrum(self.__speos)
        self.__instance = None
        self.__create()

    @property
    def source(self):
        self.__create()
        return self.__instance

    @property
    def emissive_faces(self):
        return self.__emissive_faces

    @emissive_faces.setter
    def emissive_faces(self, faces_list: list[str]):
        assert isinstance(faces_list, list)
        self.__emissive_faces = faces_list
        self.__create()

    @property
    def spectrum(self):
        return self.__spectrum

    @property
    def intensity(self):
        return self.__intensity

    def __create(self):
        surface_source = self.__speos.client.source_templates().create(
            message=core.source_template.SourceTemplateFactory.surface(
                name=self.name,
                description="Surface source intensity as {} with spectrum as {}".format(self.__intensity.type, self.__spectrum.type),
                intensity_template=self.__intensity.intensity,
                flux=core.source_template.SourceTemplateFactory.Flux(),
                spectrum=self.__spectrum.spectrum,
            )
        )

        self.__instance = core.scene.SceneFactory.source_instance(
            name=self.name,
            source_template=surface_source,
            properties=core.scene.SceneFactory.surface_source_props(
                exitance_constant_geo_paths=[core.geometry_utils.GeoPathWithReverseNormal(face) for face in self.__emissive_faces]
            ),
        )


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

    def __init__(self, speos) -> None:
        self.__speos = speos
        self.__integration_type = "planar"
        self.__type = "photometric"
        self.x_range_start = -50
        self.x_range_end = 50
        self.x_range_sampling = 100
        self.y_range_start = -50
        self.y_range_end = 50
        self.y_range_sampling = 100
        self.wavelengths_start = 400
        self.wavelengths_end = 700
        self.wavelengths_sampling = 13
        self.__instance = None
        self.__create()

    @property
    def parameters(self):
        self.__create()
        return self.__instance

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, sensor_type: str = "planar"):
        types_allowed = ["photometric", "colorimetric", "spectral"]
        assert sensor_type.lower() in types_allowed
        self.__type = sensor_type.lower()
        self.__create()

    @property
    def integration_type(self):
        return self.__integration_type

    @integration_type.setter
    def integration_type(self, integration_type):
        types_allowed = ["planar"]
        assert integration_type.lower() in types_allowed
        self.__integration_type = integration_type
        self.__create()

    def copy(self) -> IrradianceSensorParameters:
        """
        Copy current object into a new one.

        Returns
        -------
        IrradianceSensorParameters
            Parameters copied.
        """
        copied_parameters = IrradianceSensorParameters(self.__speos)
        copied_parameters.integration_type = self.__integration_type
        copied_parameters.type = self.__type
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

    def __create(self) -> None:
        """
        Create protobuf message SensorTemplate from current object.

        Returns
        -------
        core.SensorTemplate
            Protobuf message created.
        """

        w_range = None
        sensor_type = core.SensorTemplateFactory.Type.Photometric
        if self.__type == "colorimetric":
            sensor_type = core.SensorTemplateFactory.Type.Colorimetric
        elif self.__type == "spectral":
            sensor_type = core.SensorTemplateFactory.Type.Spectral

        integration_type = core.SensorTemplateFactory.IlluminanceType.Planar

        if self.type == "chorimetric" or self.type == "spectral":
            w_range = core.SensorTemplateFactory.WavelengthsRange(
                start=self.wavelengths_start, end=self.wavelengths_end, sampling=self.wavelengths_sampling
            )
        self.__instance = self.__speos.client.sensor_templates().create(
            message=core.SensorTemplateFactory.irradiance(
                name="irradiance property with type {} and integration type {}".format(self.__type, self.__integration_type),
                type=sensor_type,
                illuminance_type=integration_type,
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
        self.__instance = None
        self.__create()

    @property
    def properties(self):
        self.__create()
        return self.__instance

    def __create(self) -> None:
        """
        Create protobuf message IrradianceSensorProperties from current object.

        Returns
        -------
        core.Scene.SensorInstance.IrradianceSensorProperties
            Protobuf message created.
        """
        irradiance_sensor_axis_system = core.AxisSystem(origin=self.origin, x_vect=self.x_vect, y_vect=self.y_vect, z_vect=self.z_vect)

        layer_type = None
        if self.layer_type == "Source":
            layer_type = core.SceneFactory.Properties.Sensor.LayerType.Source

        self.__instance = core.SceneFactory.irradiance_sensor_props(axis_system=irradiance_sensor_axis_system, layer_type=layer_type)


class SensorIrradiance:
    def __init__(self, speos, name: str = "irradiance_sensor_" + uuid.uuid4().hex):
        self.name = name
        self.__speos = speos
        self.__parameters = IrradianceSensorParameters(self.__speos)
        self.__properties = IrradianceSensorProperties()
        self.__instance = None
        self.__create()

    @property
    def sensor(self):
        self.__create()
        return self.__instance

    @property
    def parameters(self):
        return self.__parameters

    @property
    def properties(self):
        return self.__properties

    def __create(self):
        self.__instance = core.scene.SceneFactory.sensor_instance(
            name=self.name, sensor_template=self.__parameters.parameters, properties=self.__properties.properties
        )


class OptFacetMesh:
    def __init__(self, id):
        self.facet_id = id
        self.vertice_ids = []


class OptFaceMesh:
    def __init__(self, id, facets_number, vertices_number):
        self.face_id = id
        self.facets_nb = facets_number
        self.facets = []
        self.vertices_nb = vertices_number
        self.vertice_coordinates = []
        self.vertice_normals = []


class OptBodyMesh:
    def __init__(self, body_name):
        self.name = body_name
        self.faces_nb = 0
        self.faces = []


class OpticalBody:
    def __init__(self, speos, opt_body_mesh: OptBodyMesh):
        self.__speos = speos
        # surface properties
        self.__opt_sop_instance = None
        self.__opt_sop_type = "mirror"
        self.__opt_sop_reflection = 100
        self.__opt_sop_file_path = None
        # vop properties
        self.__opt_vop_instance = None
        self.__opt_vop_type = "none"
        self.__opt_vop_index = 1.5
        self.__opt_vop_absorption = 0.0
        self.__opt_vop_constringence = None
        self.__opt_vop_file_path = None
        # pySpeos properties
        self.__opt_face_list = []
        self.__opt_body_list = []
        self.__opt_face_geopath_list = []
        self.__opt_body_geopath_list = []
        self.__verify(opt_body_mesh)
        self.__body_instance = opt_body_mesh
        self.__body_instance_updated = True
        self.name = opt_body_mesh.name
        self.__create()

    @staticmethod
    def __verify(mesh):
        assert isinstance(mesh, OptBodyMesh)
        assert mesh.faces_nb != 0 and mesh.faces_nb == len(mesh.faces)
        assert all([isinstance(item, OptFaceMesh) for item in mesh.faces])
        for face in mesh.faces:
            assert face.facets_nb != 0 and face.facets_nb == len(face.facets)
            assert face.vertices_nb != 0 and 3 * face.vertices_nb == len(face.vertice_coordinates)
            assert len(face.vertice_coordinates) == len(face.vertice_normals)
            assert all([isinstance(item, OptFacetMesh) for item in face.facets])
        return True

    @property
    def surface_properties_type(self):
        return self.__opt_sop_type

    @surface_properties_type.setter
    def surface_properties_type(self, properties_type: str = "mirror"):
        types_allowed = [
            "mirror",
            "optical_polished",
            "library",
        ]
        assert properties_type.lower() in types_allowed
        self.__opt_sop_type = properties_type.lower()
        self.__create()

    @property
    def surface_properties_reflection(self):
        return self.__opt_sop_reflection

    @surface_properties_reflection.setter
    def surface_properties_reflection(self, reflection: float = 100):
        self.__opt_sop_reflection = reflection if 0.0 < reflection < 100.0 else (0.0 if reflection < 0.0 else 100.0)
        self.__create()

    @property
    def surface_properties_file_path(self):
        return self.__opt_sop_file_path

    @surface_properties_file_path.setter
    def surface_properties_file_path(self, file_path):
        assert os.path.isfile(file_path)
        self.__opt_sop_file_path = file_path

    @property
    def volume_properties_type(self):
        return self.__opt_vop_type

    @volume_properties_type.setter
    def volume_properties_type(self, properties_type: str = "none"):
        types_allowed = [
            "none",
            "optic",
            "library",
            "opaque",
        ]
        assert properties_type.lower() in types_allowed
        self.__opt_vop_type = properties_type.lower()

    @property
    def volume_properties_index(self):
        return self.__opt_vop_index

    @volume_properties_index.setter
    def volume_properties_index(self, optical_index: float = 1.5):
        self.__opt_vop_index = optical_index if 0.0 < optical_index < 100.0 else (0.0 if optical_index < 0.0 else 100.0)
        self.__create()

    @property
    def volume_properties_absorption(self):
        return self.__opt_vop_absorption

    @volume_properties_absorption.setter
    def volume_properties_absorption(self, absorption: float = 0):
        self.__opt_vop_absorption = max(absorption, 0.0)
        self.__create()

    @property
    def volume_properties_constringence(self):
        return self.__opt_vop_constringence

    @volume_properties_constringence.setter
    def volume_properties_constringence(self, constringence: float = 60):
        self.__opt_vop_constringence = constringence if 20.0 < constringence < 100.0 else (20 if constringence < 20 else 100.0)
        self.__create()

    @property
    def volume_properties_file_path(self):
        return self.__opt_vop_file_path

    @volume_properties_file_path.setter
    def volume_properties_file_path(self, file_path: str):
        assert os.path.isfile(file_path)
        self.__opt_vop_file_path = file_path

    @property
    def optical_body(self):
        return self.__opt_body_geopath_list

    @property
    def optical_faces(self):
        return self.__opt_face_geopath_list

    @property
    def body_mesh(self):
        return self.__body_instance

    @body_mesh.setter
    def body_mesh(self, mesh: OptBodyMesh):
        if self.__verify(mesh):
            self.__body_instance = mesh

    def __create(self):
        if self.__body_instance_updated:
            if len(self.__opt_face_list) != 0:
                [item.delete() for item in self.__opt_face_list]
                self.__opt_face_list.clear()
            if len(self.__opt_body_list) != 0:
                [item.delete() for item in self.__opt_body_list]
                self.__opt_body_list.clear()
            for face_id in range(self.__body_instance.faces_nb):
                self.__opt_face_list.append(
                    self.__speos.client.faces().create(
                        message=core.face.FaceFactory.new(
                            name="face_{}".format(face_id),
                            description="face idx {} of body {}".format(face_id, self.name),
                            vertices=self.__body_instance.faces[face_id].vertice_coordinates,
                            facets=sum([facet.vertice_ids for facet in self.__body_instance.faces[face_id].facets], []),
                            normals=self.__body_instance.faces[face_id].vertice_normals,
                        )
                    )
                )
                self.__opt_face_geopath_list.append("body_{}/face_{}".format(self.name, face_id))
            self.__opt_body_list.append(
                self.__speos.client.bodies().create(
                    message=core.body.BodyFactory.new(
                        name="body_{}".format(self.name), description="body {}".format(self.name), faces=self.__opt_face_list
                    )
                )
            )
            self.__opt_body_geopath_list.append("body_{}".format(self.name))
            self.__body_instance_updated = False

        if self.__opt_vop_type == "none":
            self.__opt_vop_instance = None
        elif self.__opt_vop_type == "optic":
            self.__opt_vop_instance = core.scene.SceneFactory.vop_instance(
                name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                vop_template=self.__speos.client.vop_templates().create(
                    message=core.vop_template.VOPTemplateFactory.optic(
                        name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                        index=self.__opt_vop_index,
                        absorption=self.__opt_vop_absorption,
                        constringence=self.__opt_vop_constringence,
                    )
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_body_geopath_list),
            )
        elif self.__opt_vop_type == "opaque":
            self.__opt_vop_instance = core.scene.SceneFactory.vop_instance(
                name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                vop_template=self.__speos.client.vop_templates().create(
                    message=core.vop_template.VOPTemplateFactory.opaque(
                        name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                    )
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_body_geopath_list),
            )
        elif self.__opt_vop_type == "library":
            self.__opt_vop_instance = core.scene.SceneFactory.vop_instance(
                name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                vop_template=self.__speos.client.vop_templates().create(
                    message=core.vop_template.VOPTemplateFactory.library(
                        name="vop of body {}: {}".format(self.name, self.__opt_vop_type),
                        material_file_uri=self.__opt_vop_file_path,
                    )
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_body_geopath_list),
            )

        if self.__opt_sop_type == "optical_polished":
            self.__opt_sop_instance = core.scene.SceneFactory.sop_instance(
                name="sop of body {}: {}".format(self.name, self.__opt_sop_type),
                sop_template=speos.client.sop_templates().create(
                    message=core.sop_template.SOPTemplateFactory.optical_polished(
                        name="sop of body {}: {}".format(self.name, self.__opt_sop_type)
                    ),
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_face_geopath_list),
            )
        elif self.__opt_sop_type == "mirror":
            self.__opt_sop_instance = core.scene.SceneFactory.sop_instance(
                name="sop of body {}: {}".format(self.name, self.__opt_sop_type),
                sop_template=speos.client.sop_templates().create(
                    message=core.sop_template.SOPTemplateFactory.mirror(
                        name="sop of body {}: {}".format(self.name, self.__opt_sop_type),
                        reflectance=self.__opt_sop_reflection,
                    ),
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_face_geopath_list),
            )
        elif self.__opt_sop_type == "library":
            self.__opt_sop_instance = core.scene.SceneFactory.sop_instance(
                name="sop of body {}: {}".format(self.name, self.__opt_sop_type),
                sop_template=speos.client.sop_templates().create(
                    message=core.sop_template.SOPTemplateFactory.library(
                        name="sop of body {}: {}".format(self.name, self.__opt_sop_type),
                        sop_file_uri=self.__opt_sop_file_path,
                    ),
                ),
                geometries=core.geometry_utils.GeoPaths(geo_paths=self.__opt_face_geopath_list),
            )


class DirectSimulation:
    def __init__(
        self,
        speos,
        name="direct_simulation_" + uuid.uuid4().hex,
        body_list: list[OpticalBody] = None,
        source_list: list = None,
        sensor_list: list = None,
    ):
        self.__speos = speos
        self.name = name
        # simulation properties
        self.__stop_condition_rays = True
        self.__bodies = body_list
        self.__sources = source_list
        self.__sensors = sensor_list
        self.__number_of_rays = 200000
        self.__duration = 30 * 60
        # pySpeos properties
        self.__simulation_scene = None
        self.__instance = None
        self.__create()

    @property
    def geometries(self):
        return self.__bodies

    @property
    def sources(self):
        return self.__sources

    @property
    def sensors(self):
        return self.__sensors

    @property
    def number_of_rays(self):
        return self.__stop_condition_rays

    @number_of_rays.setter
    def number_of_rays(self, rays_nb: int = 200000):
        self.__stop_condition_rays = True
        self.__number_of_rays = rays_nb
        self.__create()

    @property
    def duration(self):
        return self.__duration

    @duration.setter
    def duration(self, duration_time: int = 30 * 60):
        self.__stop_condition_rays = False
        self.__duration = duration_time
        self.__create()

    def __create(self):
        assemble_part = self.__speos.client.parts().create(
            message=core.part.PartFactory.new(
                name="pySpeos simulation {}'s assemble with {} bodies".format(self.name, len(self.__bodies)),
                description="pySpeos part with {} number of bodies".format(len(self.__bodies)),
                bodies=sum([body._OpticalBody__opt_body_list for body in self.__bodies], []),
            )
        )
        simulation_paramters = self.__speos.client.simulation_templates().create(
            message=core.simulation_template.SimulationTemplateFactory.direct_mc(
                name="pySpeos direct simulation", description="pySpeos Direct simulation template with default parameters"
            )
        )

        self.__simulation_scene = self.__speos.client.scenes().create(
            message=core.scene.SceneFactory.new(
                name="pySpeos direct simulation {}'s scene with {} bodies, {} sources, {} sensors".format(
                    self.name, len(self.__bodies), len(self.__sources), len(self.__sensors)
                ),
                description="scene created from pySpeos",
                part=assemble_part,
                vop_instances=[
                    body._OpticalBody__opt_vop_instance for body in self.__bodies if body._OpticalBody__opt_vop_instance is not None
                ],
                sop_instances=[body._OpticalBody__opt_sop_instance for body in self.__bodies],
                source_instances=[source.source for source in self.__sources],
                sensor_instances=[sensor.sensor for sensor in self.__sensors],
                simulation_instances=[
                    core.scene.SceneFactory.simulation_instance(
                        name="pySpeos direction simulation {}'s instance".format(self.name),
                        simulation_template=simulation_paramters,
                        source_paths=[source.name for source in self.__sources],
                        sensor_paths=[sensor.name for sensor in self.__sensors],
                        geometries=core.geometry_utils.GeoPaths(sum([body.optical_body for body in self.__bodies], [])),
                    )
                ],
            )
        )

    def __compute(self, cpu_compute: bool = True):
        self.__create()
        simulation_properties = core.JobFactory.direct_mc_props(stop_condition_rays_nb=self.__number_of_rays)
        if not self.__stop_condition_rays:
            simulation_properties = core.JobFactory.direct_mc_props(stop_condition_duration=self.__duration)
        new_job = self.__speos.client.jobs().create(
            message=core.JobFactory.new(
                name=self.name,
                scene=self.__simulation_scene,
                simulation_path="pySpeos direction simulation {}'s instance".format(self.name),
                # path
                type=core.JobFactory.Type.CPU if cpu_compute else core.JobFactory.Type.GPU,
                properties=simulation_properties,
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
            Utilities.print_progress_bar(new_job.get_progress_status().progress, 1, "Processing: ")

            job_state_res = new_job.get_state()
            if job_state_res.state == job_pb2.Job.State.IN_ERROR:
                core.LOG.error(core.protobuf_message_to_str(new_job.get_error()))

        return new_job

    def gpu_compute(self):
        self.__compute(cpu_compute=False)

    def cpu_compute(self):
        self.__compute(cpu_compute=True)


class SpeosProject:
    def __init__(self, speos, name: str = "design_" + uuid.uuid4().hex):
        self.__speos = speos
        self.project_name = name
        self.opt_sources = []
        self.opt_sensors = []
        self.opt_bodies = []

    def create_source_surface(self, faces_list: list[str], name: str = "surface_source_" + uuid.uuid4().hex):
        new_surface_source = SourceSurface(speos=self.__speos, emissive_faces=faces_list, name=name)
        self.opt_sources.append(new_surface_source)
        return new_surface_source

    def create_sensor_irradiance(self, name: str = "irradiance_sensor_" + uuid.uuid4().hex):
        new_irradiance_sensor = SensorIrradiance(speos=self.__speos, name=name)
        self.opt_sensors.append(new_irradiance_sensor)
        return new_irradiance_sensor

    def add_optical_body(self, mesh: OptBodyMesh):
        new_body = OpticalBody(self.__speos, mesh)
        self.opt_bodies.append(new_body)
        return new_body

    def create_direction_simulation(
        self,
        body_list: list[OpticalBody] = None,
        source_list: list = None,
        sensor_list: list = None,
        name: str = "direct_" + uuid.uuid4().hex,
    ):
        simulation = DirectSimulation(
            self.__speos,
            name=name,
            body_list=self.opt_bodies if body_list is None else body_list,
            source_list=self.opt_sources if source_list is None else source_list,
            sensor_list=self.opt_sensors if sensor_list is None else sensor_list,
        )
        return simulation


speos = core.Speos(host="localhost", port=50051)
workflow.clean_all_dbs(speos.client)

Debug_Solid_Mesh = OptBodyMesh(body_name="Solid")
Debug_Solid_Mesh.faces_nb = 6
for face_id in range(Debug_Solid_Mesh.faces_nb):
    face_info = OptFaceMesh(id=face_id, facets_number=2, vertices_number=4)
    Debug_Solid_Mesh.faces.append(face_info)
    for facet_id in range(face_info.facets_nb):
        facet_info = OptFacetMesh(facet_id)
        face_info.facets.append(facet_info)
        if facet_id == 0:
            facet_info.vertice_ids = [1, 2, 0]
        else:
            facet_info.vertice_ids = [2, 3, 0]
    if face_id == 0:
        face_info.vertice_coordinates = [
            -0.0050000000000000001,
            0.0,
            0.0050000000000000001,
            -0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.0,
            0.0050000000000000001,
        ]
        face_info.vertice_normals = [-0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0, -0.0, -1.0, -0.0]
    elif face_id == 1:
        face_info.vertice_coordinates = [
            0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            0.0050000000000000001,
            0.0,
            0.0050000000000000001,
        ]
        face_info.vertice_normals = [1.0, -0.0, 0.0, 1.0, -0.0, 0.0, 1.0, -0.0, 0.0, 1.0, -0.0, 0.0]
    elif face_id == 2:
        face_info.vertice_coordinates = [
            -0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
            -0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
        ]
        face_info.vertice_normals = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0]
    elif face_id == 3:
        face_info.vertice_coordinates = [
            -0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
            -0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
            0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
        ]
        face_info.vertice_normals = [0.0, 0.0, -1.0, 0.0, 0.0, -1.0, 0.0, 0.0, -1.0, 0.0, 0.0, -1.0]
    elif face_id == 4:
        face_info.vertice_coordinates = [
            -0.0050000000000000001,
            0.0,
            0.0050000000000000001,
            -0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            -0.0050000000000000001,
            0.01,
            -0.0050000000000000001,
            -0.0050000000000000001,
            0.0,
            -0.0050000000000000001,
        ]
        face_info.vertice_normals = [-1.0, 0.0, 0.0, -1.0, 0.0, 0.0, -1.0, 0.0, 0.0, -1.0, 0.0, 0.0]
    elif face_id == 5:
        face_info.vertice_coordinates = [
            0.0050000000000000001,
            0.0,
            0.0050000000000000001,
            0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            -0.0050000000000000001,
            0.01,
            0.0050000000000000001,
            -0.0050000000000000001,
            0.0,
            0.0050000000000000001,
        ]
        face_info.vertice_normals = [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    face_info.vertice_coordinates = [item * 1000 for item in face_info.vertice_coordinates]
Debug_Surface_Mesh = OptBodyMesh(body_name="Surface")
Debug_Surface_Mesh.faces_nb = 1
for face_id in range(Debug_Surface_Mesh.faces_nb):
    face_info = OptFaceMesh(id=face_id, facets_number=2, vertices_number=4)
    Debug_Surface_Mesh.faces.append(face_info)
    for facet_id in range(face_info.facets_nb):
        facet_info = OptFacetMesh(facet_id)
        face_info.facets.append(facet_info)
        if facet_id == 0:
            facet_info.vertice_ids = [1, 2, 0]
        else:
            facet_info.vertice_ids = [2, 3, 0]
    if face_id == 0:
        face_info.vertice_coordinates = [
            -0.0050000000000000001,
            -0.011228,
            0.0050000000000000001,
            0.0050000000000000001,
            -0.011228,
            0.0050000000000000001,
            0.0050000000000000001,
            -0.011228,
            -0.0050000000000000001,
            -0.0050000000000000001,
            -0.011228,
            -0.0050000000000000001,
        ]
        face_info.vertice_normals = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0]
    face_info.vertice_coordinates = [item * 1000 for item in face_info.vertice_coordinates]

""" Create an empty Speos project """
Sim = SpeosProject(speos, "pySpeos test")

""" Add geometries into Speos project """
""" to be compatible with pyGeometry  """
solid = Sim.add_optical_body(Debug_Solid_Mesh)  # default material property as VOP none and SOP Mirror
solid.volume_properties_type = "optic"  # default optic as index 1.5 with absorption 0
solid.surface_properties_type = "optical_polished"
surface = Sim.add_optical_body(Debug_Surface_Mesh)
surface.volume_properties_type = "opaque"
surface.surface_properties_type = "mirror"  # default mirror as 100% reflectance

""" Add surface source int Speos project """
"""   surface source default as lambertian 180 and monochromatic 555 nm """
surface_source = Sim.create_source_surface(name="pySpeos surface source", faces_list=surface.optical_faces)
surface_source.spectrum.type = "blackbody"  # change spectrum type to blackbody: default blackbody as 2856k
surface_source.intensity.type = "symmetric gaussian"  # change intensity to symmetric gaussian default with total
# angle 180 and 30 FWHM
surface_source.intensity.total_angle = 180
surface_source.intensity.FWHM_angle = 35

""" Add irradiance sensor into Speos project """
"""  photometric plannar irradiance sensor and other default values from Speos """
irradiance_sensor = Sim.create_sensor_irradiance(name="pySpeos irradiance sensor")
irradiance_sensor.parameters.type = "spectral"  # change parameter type to spectral
irradiance_sensor.properties.origin = [0, 20, 0]  # update sensor position
irradiance_sensor.properties.x_vect = [1, 0, 0]
irradiance_sensor.properties.y_vect = [0, 0, 1]
irradiance_sensor.properties.z_vect = [0, 1, 0]

""" Create simulation inside Speos project """
"""  default with all the bodies, sources, and sensors and 200000 rays as stop condition """
direct_sim = Sim.create_direction_simulation(name="pySpeos direction simulation")
direct_sim.cpu_compute()

# Update simulation with new material property
solid.volume_properties_type = "opaque"  # update material from optic to opaque
solid.surface_properties_type = "mirror"
direct_sim.cpu_compute()

# Update simulation with new source intensity
surface_source.intensity.type = "lambertian"  # update source intensity from symmetric gaussian to lambertian
surface_source.intensity.total_angle = 10
direct_sim.cpu_compute()

# Update simulation with new sensor property
irradiance_sensor.parameters.x_range_start *= 0.5  # update sensor dimension and sampling
irradiance_sensor.parameters.x_range_end *= 0.5
irradiance_sensor.parameters.x_range_sampling *= 2
irradiance_sensor.parameters.y_range_start *= 0.5
irradiance_sensor.parameters.y_range_end *= 0.5
irradiance_sensor.parameters.y_range_sampling *= 2
direct_sim.gpu_compute()
