"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import Iterator, List, Mapping, Optional, Union

from ansys.api.speos.results.v1.ray_path_pb2 import RayPath
from ansys.api.speos.scene.v1 import scene_pb2 as messages
from ansys.api.speos.scene.v1 import scene_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry_utils import (
    AxisPlane,
    AxisSystem,
    GeoPaths,
    GeoPathWithReverseNormal,
)
from ansys.speos.core.part import PartLink
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.sensor_template import SensorTemplateLink
from ansys.speos.core.simulation_template import SimulationTemplateLink
from ansys.speos.core.sop_template import SOPTemplateLink
from ansys.speos.core.source_template import SourceTemplateLink
from ansys.speos.core.vop_template import VOPTemplateLink

Scene = messages.Scene


class SceneLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Scene:
        return self._stub.read(self)

    def set(self, data: Scene) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)

    # Actions
    def load_file(self, file_uri: str) -> None:
        self._actions_stub.LoadFile(messages.LoadFile_Request(guid=self.key, file_uri=file_uri))

    def get_source_ray_paths(self, source_path: str, rays_nb: int = None) -> Iterator[RayPath]:
        for rp in self._actions_stub.GetSourceRayPaths(
            messages.GetSourceRayPaths_Request(guid=self.key, source_path=source_path, rays_nb=rays_nb)
        ):
            yield rp


class SceneStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.ScenesManagerStub(channel=channel))
        self._actions_stub = service.SceneActionsStub(channel=channel)

    def create(self, message: Scene = Scene()) -> SceneLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(scene=message))
        return SceneLink(self, resp.guid)

    def read(self, ref: SceneLink) -> Scene:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.scene

    def update(self, ref: SceneLink, data: Scene):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, scene=data))

    def delete(self, ref: SceneLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SceneLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SceneLink(self, x), guids))


class SceneFactory:
    """Class to help creating Scene message"""

    class Properties:
        """Class to gather different properties needed for instances in the scene."""

        class Sensor:
            """Class to gather sensor instance properties."""

            RayFileType = Enum("RayFileType", ["Classic", "Polarization", "TM25", "TM25NoPolarization"])

            class LayerType:
                """Class to gather sensor instance layer types."""

                class Source:
                    """Layers separated by source."""

                    def __init__(self) -> None:
                        pass

                class Sequence:
                    Type = Enum("Type", ["Geometries", "Faces"])

                    def __init__(self, maximum_nb_of_sequence: Optional[int] = 10, sequence_type: Optional[Type] = Type.Geometries) -> None:
                        """
                        Layers separated by sequence.

                        Parameters
                        ----------
                        maximum_nb_of_sequence : int, optional
                            Maximum number of sequences.
                            By default, ``10``.
                        sequence_type : Sequence.Type, optional
                            Type of sequences.
                            By default, ``Sequence.Type.Geometries``.
                        """
                        self.maximum_nb_of_sequence = maximum_nb_of_sequence
                        self.sequence_type = sequence_type

                class Polarization:
                    """Layers separated by polarization."""

                    def __init__(self) -> None:
                        pass

                class IncidenceAngle:
                    """
                    Layers separated by incidence angle.

                    Parameters
                    ----------
                    sampling : int, optional
                        Sampling for incidence angles
                        By default, ``9``.
                    """

                    def __init__(self, sampling: Optional[int] = 9) -> None:
                        self.sampling = sampling

        class Source:
            """Class to gather source instance properties."""

            class Intensity:
                class Library:
                    Orientation = Enum("Orientation", ["ViaAxisSystem", "NormalToSurface", "NormalToUVMap"])

    def new(
        name: str,
        part: PartLink,
        vop_instances: List[Scene.VOPInstance],
        sop_instances: List[Scene.SOPInstance],
        source_instances: List[Scene.SourceInstance],
        sensor_instances: List[Scene.SensorInstance],
        simulation_instances: List[Scene.SimulationInstance],
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Scene:
        """
        Create a Scene message.

        Parameters
        ----------
        name : str
            Name of the scene.
        part : PartLink
            Part to be referenced as root part in the scene.
        vop_instances : List[Scene.VOPInstance]
            list of volume optical properties instantiated in the scene
        sop_instances : List[Scene.SOPInstance]
            list of surface optical properties instantiated in the scene
        source_instances : List[Scene.SourceInstance]
            list of sources instantiated in the scene
        sensor_instances : List[Scene.SourceInstance]
            list of sensors instantiated in the scene
        simulation_instances : List[Scene.SourceInstance]
            list of simulations instantiated in the scene
        description : str, optional
            Description of the scene.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the scene.
            By default, ``None``.

        Returns
        -------
        Scene
            Scene message created.
        """
        scene = Scene(name=name, description=description)
        if metadata is not None:
            scene.metadata.update(metadata)
        scene.part_guid = part.key
        scene.vops.extend(vop_instances)
        scene.sops.extend(sop_instances)
        scene.sources.extend(source_instances)
        scene.sensors.extend(sensor_instances)
        scene.simulations.extend(simulation_instances)
        return scene

    def vop_instance(
        name: str,
        vop_template: VOPTemplateLink,
        geometries: Optional[GeoPaths] = GeoPaths(),
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Scene.VOPInstance:
        """
        Create a VOPInstance message. Volume Optical Property instance.

        Parameters
        ----------
        name : str
            Name of the vop instance.
        vop_template : VOPTemplateLink
            Vop template used as a base of this instance.
        geometries : ansys.speos.core.geometry_utils.GeoPaths, optional
            Geometries that will use this material.
            By default, ``ansys.speos.core.geometry_utils.GeoPaths()``, ie all geometries.
        description : str, optional
            Description of the vop instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the vop instance.
            By default, ``None``.

        Returns
        -------
        Scene.VOPInstance
            VOPInstance message created.
        """
        vop_i = Scene.VOPInstance(name=name, description=description)
        if metadata is not None:
            vop_i.metadata.update(metadata)
        vop_i.vop_guid = vop_template.key
        vop_i.geometries.geo_paths.extend(geometries.geo_paths)
        return vop_i

    def sop_instance(
        name: str,
        sop_template: SOPTemplateLink,
        geometries: GeoPaths = GeoPaths(),
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> Scene.SOPInstance:
        """
        Create a SOPInstance message. Surface Optical Property instance.

        Parameters
        ----------
        name : str
            Name of the sop instance.
        sop_template : SOPTemplateLink
            Sop template used as a base of this instance.
        geometries : ansys.speos.core.geometry_utils.GeoPaths, optional
            Geometries that will use this material.
            By default, ``ansys.speos.core.geometry_utils.GeoPaths()``, ie all geometries.
        description : str, optional
            Description of the sop instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sop instance.
            By default, ``None``.

        Returns
        -------
        Scene.SOPInstance
            SOPInstance message created.
        """
        sop_i = Scene.SOPInstance(name=name, description=description)
        if metadata is not None:
            sop_i.metadata.update(metadata)
        sop_i.sop_guid = sop_template.key
        sop_i.geometries.geo_paths.extend(geometries.geo_paths)
        return sop_i

    def source_instance(
        name: str,
        source_template: SourceTemplateLink,
        properties: Union[Scene.SourceInstance.LuminaireProperties, Scene.SourceInstance.SurfaceProperties],
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> Scene.SourceInstance:
        """
        Create a SourceInstance message.

        Parameters
        ----------
        name : str
            Name of the source instance.
        source_template : SourceTemplateLink
            Source template used as a base of this instance.
        properties : Union[Scene.SourceInstance.LuminaireProperties, Scene.SourceInstance.SurfaceProperties]
            Properties to apply to this source instance.
            Choose the correct properties type depending on the source template type.
            Example:
            In case source_template.get().HasField("luminaire") is True, use LuminaireProperties
            In case source_template.get().HasField("surface") is True, use SurfaceProperties
            Some methods can help to build needed messages: SceneFactory.luminaire_source_props(...), SceneFactory.surface_source_props(...)
        description : str, optional
            Description of the source instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the source instance.
            By default, ``None``.

        Returns
        -------
        Scene.SourceInstance
            SourceInstance message created.
        """
        src_i = Scene.SourceInstance(name=name, description=description)
        if metadata is not None:
            src_i.metadata.update(metadata)
        src_i.source_guid = source_template.key

        if isinstance(properties, Scene.SourceInstance.LuminaireProperties):
            src_i.luminaire_properties.CopyFrom(properties)
        elif isinstance(properties, Scene.SourceInstance.SurfaceProperties):
            src_i.surface_properties.CopyFrom(properties)
        return src_i

    def luminaire_source_props(axis_system: Optional[AxisSystem] = AxisSystem()) -> Scene.SourceInstance.LuminaireProperties:
        """
        Create a LuminaireProperties message.

        Parameters
        ----------
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            Position of the source.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.

        Returns
        -------
        Scene.SourceInstance.LuminaireProperties
            LuminaireProperties message created.
        """
        lum_props = Scene.SourceInstance.LuminaireProperties()
        lum_props.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)
        return lum_props

    def surface_source_props(
        exitance_constant_geo_paths: Optional[List[GeoPathWithReverseNormal]] = None,
        exitance_variable_axis_plane: Optional[AxisPlane] = None,
        intensity_properties: Optional[Scene.SourceInstance.IntensityProperties] = None,
    ) -> Scene.SourceInstance.SurfaceProperties:
        """
        Create a SurfaceProperties message, according to expected characteristics.

        Parameters
        ----------
        exitance_constant_geo_paths : List[ansys.speos.core.geometry_utils.GeoPathWithReverseNormal], optional
            In case the surface source has constant exitance, precise the geometry that will use this surface source.
            Example: parameter to be filled if source_template.get().surface.HasField("exitance_constant")
            By default, ``None``.
        exitance_variable_axis_plane : ansys.speos.core.geometry_utils.AxisPlane, optional
            In case the surface source has variable exitance, precise the position of the exitance map.
            Example: parameter to be filled if source_template.get().surface.HasField("exitance_variable")
            By default, ``None``.
        intensity_properties : Scene.SourceInstance.IntensityProperties, optional
            To be filled in case the intensity template used is library or asymmetric gaussian.
            Example if speos.client.get_item(src_t_surface.get().surface.intensity_guid).get().HasField("library")
            Or speos.client.get_item(src_t_surface.get().surface.intensity_guid).get().HasField("asymmetric_gaussian")
            Some methods can help to build needed messages:
            SceneFactory.library_intensity_props(...), SceneFactory.asymm_gaussian_intensity_props(...)
            By default, ``None``.

        Returns
        -------
        Scene.SourceInstance.SurfaceProperties
            SurfaceProperties message created.
        """
        surf_props = Scene.SourceInstance.SurfaceProperties()
        if exitance_constant_geo_paths is not None:
            surf_props.exitance_constant_properties.geo_paths.extend(
                [
                    Scene.SourceInstance.SurfaceProperties.ExitanceConstantProperties.GeoPath(
                        geo_path=g.geo_path, reverse_normal=g.reverse_normal
                    )
                    for g in exitance_constant_geo_paths
                ]
            )
        elif exitance_variable_axis_plane is not None:
            surf_props.exitance_variable_properties.axis_plane.extend(
                exitance_variable_axis_plane.origin + exitance_variable_axis_plane.x_vect + exitance_variable_axis_plane.y_vect
            )

        if intensity_properties is not None:
            surf_props.intensity_properties.CopyFrom(intensity_properties)

        return surf_props

    def library_intensity_props(
        exit_geometries: Optional[GeoPaths] = None,
        orientation: Optional[
            Properties.Source.Intensity.Library.Orientation
        ] = Properties.Source.Intensity.Library.Orientation.ViaAxisSystem,
        axis_system: Optional[AxisSystem] = AxisSystem(),
    ) -> Scene.SourceInstance.IntensityProperties:
        """
        Create a IntensityProperties message, corresponding to library intensity template.

        Parameters
        ----------
        exit_geometries : GeoPaths, optional
            Exit geometries for the source.
            By default, ``None``, ie no exit geometries.
        orientation : Properties.Source.Intensity.Library.Orientation, optional
            Orientation of the source intensity distribution.
            By default, ``Properties.Source.Intensity.Library.Orientation.ViaAxisSystem``.
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            To be filled if the orientation ViaAxisSystem is chosen.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.

        Returns
        -------
        Scene.SourceInstance.IntensityProperties
            IntensityProperties message created.
        """
        lib_intens_props = Scene.SourceInstance.IntensityProperties()
        if exit_geometries is not None:
            lib_intens_props.library_properties.exit_geometries.geo_paths.extend(exit_geometries.geo_paths)

        if orientation == SceneFactory.Properties.Source.Intensity.Library.Orientation.ViaAxisSystem and axis_system is not None:
            lib_intens_props.library_properties.axis_system.values.extend(
                [axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect]
            )
        elif orientation == SceneFactory.Properties.Source.Intensity.Library.Orientation.NormalToSurface:
            lib_intens_props.library_properties.normal_to_surface.SetInParent()
        elif orientation == SceneFactory.Properties.Source.Intensity.Library.Orientation.NormalToUVMap:
            lib_intens_props.library_properties.normal_to_uv_map.SetInParent()

        return lib_intens_props

    def asymm_gaussian_intensity_props(
        axis_system: Optional[AxisSystem] = AxisSystem(),
    ) -> Scene.SourceInstance.IntensityProperties:
        """
        Create a IntensityProperties message, corresponding to asymmetric_gaussian intensity template.

        Parameters
        ----------
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            Orientation of the intensity distribution.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.

        Returns
        -------
        Scene.SourceInstance.IntensityProperties
            IntensityProperties message created.
        """
        ag_intens_props = Scene.SourceInstance.IntensityProperties()
        ag_intens_props.asymmetric_gaussian_properties.axis_system.extend(
            axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect
        )
        return ag_intens_props

    def sensor_instance(
        name: str,
        sensor_template: SensorTemplateLink,
        properties: Union[Scene.SensorInstance.CameraSensorProperties, Scene.SensorInstance.IrradianceSensorProperties],
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Scene.SensorInstance:
        """
        Create a SensorInstance message.

        Parameters
        ----------
        name : str
            Name of the sensor instance.
        sensor_template : SensorTemplateLink
            Sensor template used as a base of this instance.
        properties : Union[Scene.SensorInstance.CameraSensorProperties, Scene.SensorInstance.IrradianceSensorProperties]
            Properties to apply to this sensor instance.
            Choose the correct properties type depending on the sensor template.
            Example:
            In case sensor_template.get().HasField("camera_sensor_template") is True, use CameraSensorProperties
            In case sensor_template.get().HasField("irradiance_sensor_template") is True, use IrradianceSensorProperties
        description : str, optional
            Description of the sensor instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sensor instance.
            By default, ``None``.

        Returns
        -------
        Scene.SensorInstance
            SensorInstance message created.
        """
        ssr_i = Scene.SensorInstance(name=name, description=description)
        if metadata is not None:
            ssr_i.metadata.update(metadata)
        ssr_i.sensor_guid = sensor_template.key
        if isinstance(properties, Scene.SensorInstance.CameraSensorProperties):
            ssr_i.camera_sensor_properties.CopyFrom(properties)
        elif isinstance(properties, Scene.SensorInstance.IrradianceSensorProperties):
            ssr_i.irradiance_sensor_properties.CopyFrom(properties)
        return ssr_i

    def camera_sensor_props(
        axis_system: Optional[AxisSystem] = AxisSystem(),
        trajectory_file_uri: Optional[str] = None,
        layer_type: Optional[Properties.Sensor.LayerType.Source] = None,
    ) -> Scene.SensorInstance.CameraSensorProperties:
        """
        Create a CameraSensorProperties message.

        Parameters
        ----------
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            Position of the sensor.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.
        trajectory_file_uri : str, optional
            Trajectory file, used to define the position and orientations of the Camera sensor in time.
            By default, ``None``.
        layer_type : Properties.Sensor.LayerType.Source, optional
            Layer type for the sensor.
            By default, ``None``, ie no layers.

        Returns
        -------
        Scene.SensorInstance.CameraSensorProperties
            CameraSensorProperties message created.
        """
        cam_props = Scene.SensorInstance.CameraSensorProperties()
        cam_props.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)
        if trajectory_file_uri is not None:
            cam_props.trajectory_file_uri = trajectory_file_uri
        if layer_type is None:
            cam_props.layer_type_none.SetInParent()
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.Source):
            cam_props.layer_type_source.SetInParent()
        return cam_props

    def irradiance_sensor_props(
        axis_system: Optional[AxisSystem] = AxisSystem(),
        ray_file_type: Optional[Properties.Sensor.RayFileType] = None,
        layer_type: Optional[
            Union[
                Properties.Sensor.LayerType.Source,
                Properties.Sensor.LayerType.Sequence,
                Properties.Sensor.LayerType.Polarization,
                Properties.Sensor.LayerType.IncidenceAngle,
            ]
        ] = None,
        integration_direction: Optional[List[float]] = None,
    ) -> Scene.SensorInstance.IrradianceSensorProperties:
        """
        Create a IrradianceSensorProperties message.

        Parameters
        ----------
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            Position of the sensor.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.
        ray_file_type : Properties.Sensor.RayFileType, optional
            Type of ray file generated after the simulation.
            By default, ``None``, ie no ray file type generated.
        layer_type : Union[Properties.Sensor.LayerType.Source,
                        Properties.Sensor.LayerType.Sequence,
                        Properties.Sensor.LayerType.Polarization,
                        Properties.Sensor.LayerType.IncidenceAngle], optional
            Layer type for the sensor.
            By default, ``None``, ie no layers.
        integration_direction : List[float]
            Sensor global integration direction [x,y,z]
            Only settable if sensor_template.get().irradiance_sensor_template.HasField("illuminance_type_planar")
            Or sensor_template.get().irradiance_sensor_template.HasField("illuminance_type_semi_cylindrical")
            By default, ``None``, ie anti-normal of the sensor.

        Returns
        -------
        Scene.SensorInstance.IrradianceSensorProperties
            IrradianceSensorProperties message created.
        """
        irr_props = Scene.SensorInstance.IrradianceSensorProperties()
        irr_props.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)

        if ray_file_type is None:
            irr_props.ray_file_type = Scene.SensorInstance.EnumRayFileType.RayFileNone
        elif isinstance(ray_file_type, SceneFactory.Properties.Sensor.RayFileType.Classic):
            irr_props.ray_file_type = Scene.SensorInstance.EnumRayFileType.RayFileClassic
        elif isinstance(ray_file_type, SceneFactory.Properties.Sensor.RayFileType.Polarization):
            irr_props.ray_file_type = Scene.SensorInstance.EnumRayFileType.RayFilePolarization
        elif isinstance(ray_file_type, SceneFactory.Properties.Sensor.RayFileType.TM25):
            irr_props.ray_file_type = Scene.SensorInstance.EnumRayFileType.RayFileTM25
        elif isinstance(ray_file_type, SceneFactory.Properties.Sensor.RayFileType.TM25NoPolarization):
            irr_props.ray_file_type = Scene.SensorInstance.EnumRayFileType.RayFileTM25NoPolarization

        if layer_type is None:
            irr_props.layer_type_none.SetInParent()
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.Source):
            irr_props.layer_type_source.SetInParent()
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.Sequence):
            irr_props.layer_type_sequence.maximum_nb_of_sequence = layer_type.maximum_nb_of_sequence
            if layer_type.sequence_type == SceneFactory.Properties.Sensor.LayerType.Sequence.Type.Geometries:
                irr_props.layer_type_sequence.define_sequence_per = Scene.SensorInstance.LayerTypeSequence.EnumSequenceType.Geometries
            elif layer_type.sequence_type == SceneFactory.Properties.Sensor.LayerType.Sequence.Type.Faces:
                irr_props.layer_type_sequence.define_sequence_per = Scene.SensorInstance.LayerTypeSequence.EnumSequenceType.Faces
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.Polarization):
            irr_props.layer_type_polarization.SetInParent()
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.IncidenceAngle):
            irr_props.layer_type_incidence_angle.sampling = layer_type.sampling

        if integration_direction is not None:
            irr_props.integration_direction.extend(integration_direction)

        return irr_props

    def simulation_instance(
        name: str,
        simulation_template: SimulationTemplateLink,
        sensor_paths: Optional[List[str]] = [],
        source_paths: Optional[List[str]] = [],
        geometries: Optional[GeoPaths] = GeoPaths(),
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Scene.SimulationInstance:
        """
        Create a SimulationInstance message.

        Parameters
        ----------
        name : str
            Name of the simulation instance.
        simulation_template : SimulationTemplateLink
            Simulation template used as a base of this instance.
        sensor_paths : List[str], optional
            Sensor paths to select some SensorInstances.
            Example: "sensor_instance_name", "subscene_name/sensor_instance_name"
            By default, ``[]``, means all sensor instances.
        source_paths : List[str], optional
            Source paths to select some SourceInstances.
            Example: "source_instance_name", "subscene_name/source_instance_name"
            By default, ``[]``, means all source instances.
        geometries : ansys.speos.core.geometry_utils.GeoPaths, optional
            Geometries that will be needed.
            By default, ``ansys.speos.core.geometry_utils.GeoPaths()``, ie all geometries.
        description : str, optional
            Description of the simulation instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the simulation instance.
            By default, ``None``.

        Returns
        -------
        Scene.SimulationInstance
            SimulationInstance message created.
        """
        sim_i = Scene.SimulationInstance(name=name, description=description)
        if metadata is not None:
            sim_i.metadata.update(metadata)
        sim_i.simulation_guid = simulation_template.key
        sim_i.sensor_paths.extend(sensor_paths)
        sim_i.source_paths.extend(source_paths)
        sim_i.geometries.geo_paths.extend(geometries.geo_paths)
        return sim_i
