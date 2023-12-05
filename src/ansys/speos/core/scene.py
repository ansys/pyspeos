"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import Mapping, Union

from ansys.api.speos.scene.v1 import scene_pb2 as messages
from ansys.api.speos.scene.v1 import scene_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry import AxisPlane, AxisSystem, GeoPaths
from ansys.speos.core.part import PartLink
from ansys.speos.core.proto_message import protobuf_message_to_str
from ansys.speos.core.sensor_template import SensorTemplateLink
from ansys.speos.core.simulation_template import SimulationTemplateLink
from ansys.speos.core.sop_template import SOPTemplateLink
from ansys.speos.core.source_template import SourceTemplateLink
from ansys.speos.core.vop_template import VOPTemplateLink

Scene = messages.Scene


class SceneLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Scene:
        return self._stub.read(self)

    def set(self, data: Scene) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SceneStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.ScenesManagerStub(channel=channel))

    def create(self, message: Scene) -> SceneLink:
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

    def list(self) -> list[SceneLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SceneLink(self, x), guids))


class SceneFactory:
    class Properties:
        class Sensor:
            RayFileType = Enum("RayFileType", ["Classic", "Polarization", "TM25", "TM25NoPolarization"])

            class LayerType:
                class Source:
                    def __init__(self) -> None:
                        pass

                class Sequence:
                    Type = Enum("Type", ["Geometries", "Faces"])

                    def __init__(self, maximum_nb_of_sequence: int = 10, sequence_type: Type = Type.Geometries) -> None:
                        self.maximum_nb_of_sequence = maximum_nb_of_sequence
                        self.sequence_type = sequence_type

                class Polarization:
                    def __init__(self) -> None:
                        pass

                class IncidenceAngle:
                    def __init__(self, sampling: int = 9) -> None:
                        self.sampling = sampling

        class Source:
            class Intensity:
                class Library:
                    Orientation = Enum("Orientation", ["ViaAxisSystem", "NormalToSurface", "NormalToUVMap"])

    def new(
        name: str,
        part: PartLink,
        vop_instances: list[messages.Scene.VOPInstance],
        sop_instances: list[messages.Scene.SOPInstance],
        source_instances: list[messages.Scene.SourceInstance],
        sensor_instances: list[messages.Scene.SensorInstance],
        simulation_instances: list[messages.Scene.SimulationInstance],
        description: str = "",
    ) -> Scene:
        scene = Scene(name=name, description=description)
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
        geometries: GeoPaths = GeoPaths(),
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> messages.Scene.VOPInstance:
        vop_i = messages.Scene.VOPInstance(name=name, description=description)
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
    ) -> messages.Scene.SOPInstance:
        sop_i = messages.Scene.SOPInstance(name=name, description=description)
        if metadata is not None:
            sop_i.metadata.update(metadata)
        sop_i.sop_guid = sop_template.key
        sop_i.geometries.geo_paths.extend(geometries.geo_paths)
        return sop_i

    def source_instance(
        name: str,
        source_template: SourceTemplateLink,
        properties: Union[messages.Scene.SourceInstance.LuminaireProperties, messages.Scene.SourceInstance.SurfaceProperties],
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> messages.Scene.SourceInstance:
        src_i = messages.Scene.SourceInstance(name=name, description=description)
        if metadata is not None:
            src_i.metadata.update(metadata)
        src_i.source_guid = source_template.key

        if isinstance(properties, messages.Scene.SourceInstance.LuminaireProperties):
            src_i.luminaire_properties.CopyFrom(properties)
        elif isinstance(properties, messages.Scene.SourceInstance.SurfaceProperties):
            src_i.surface_properties.CopyFrom(properties)
        return src_i

    def luminaire_source_props(axis_system: AxisSystem = AxisSystem()) -> messages.Scene.SourceInstance.LuminaireProperties:
        lum_props = messages.Scene.SourceInstance.LuminaireProperties()
        lum_props.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)
        return lum_props

    def surface_source_props(
        exitance_constant_geo_paths: Mapping[str, bool] = None,
        exitance_variable_axis_plane: AxisPlane = None,
        intensity_properties: messages.Scene.SourceInstance.IntensityProperties = None,
    ) -> messages.Scene.SourceInstance.SurfaceProperties:
        surf_props = messages.Scene.SourceInstance.SurfaceProperties()
        if exitance_constant_geo_paths is not None:
            surf_props.exitance_constant_properties.geo_paths.extend(
                [
                    messages.Scene.SourceInstance.SurfaceProperties.ExitanceConstantProperties.GeoPath(geo_path=g, reverse_normal=r)
                    for g, r in exitance_constant_geo_paths.items()
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
        exit_geometries: GeoPaths = None,
        orientation: Properties.Source.Intensity.Library.Orientation = Properties.Source.Intensity.Library.Orientation.ViaAxisSystem,
        axis_system: Union[AxisSystem, None] = AxisSystem(),
    ) -> messages.Scene.SourceInstance.IntensityProperties:
        lib_intens_props = messages.Scene.SourceInstance.IntensityProperties()
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
        axis_system: AxisSystem = AxisSystem(),
    ) -> messages.Scene.SourceInstance.IntensityProperties:
        ag_intens_props = messages.Scene.SourceInstance.IntensityProperties()
        ag_intens_props.asymmetric_gaussian_properties.axis_system.extend(
            [axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect]
        )
        return ag_intens_props

    def sensor_instance(
        name: str,
        sensor_template: SensorTemplateLink,
        properties: Union[messages.Scene.SensorInstance.CameraSensorProperties, messages.Scene.SensorInstance.IrradianceSensorProperties],
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> messages.Scene.SensorInstance:
        ssr_i = messages.Scene.SensorInstance(name=name, description=description)
        if metadata is not None:
            ssr_i.metadata.update(metadata)
        ssr_i.sensor_guid = sensor_template.key
        if isinstance(properties, messages.Scene.SensorInstance.CameraSensorProperties):
            ssr_i.camera_sensor_properties.CopyFrom(properties)
        elif isinstance(properties, messages.Scene.SensorInstance.IrradianceSensorProperties):
            ssr_i.irradiance_sensor_properties.CopyFrom(properties)
        return ssr_i

    def camera_sensor_props(
        axis_system: AxisSystem = AxisSystem(),
        trajectory_file_uri: str = None,
        layer_type: Union[None, Properties.Sensor.LayerType.Source] = None,
    ) -> messages.Scene.SensorInstance.CameraSensorProperties:
        cam_props = messages.Scene.SensorInstance.CameraSensorProperties()
        cam_props.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)
        cam_props.trajectory_file_uri = trajectory_file_uri
        if layer_type is None:
            cam_props.layer_type_none.SetInParent()
        elif isinstance(layer_type, SceneFactory.Properties.Sensor.LayerType.Source):
            cam_props.layer_type_source.SetInParent()
        return cam_props

    def irradiance_sensor_props(
        axis_system: AxisSystem = AxisSystem(),
        ray_file_type: Properties.Sensor.RayFileType = None,
        layer_type: Union[
            None,
            Properties.Sensor.LayerType.Source,
            Properties.Sensor.LayerType.Sequence,
            Properties.Sensor.LayerType.Polarization,
            Properties.Sensor.LayerType.IncidenceAngle,
        ] = None,
        integration_direction: list[float] = None,
    ) -> messages.Scene.SensorInstance.IrradianceSensorProperties:
        irr_props = messages.Scene.SensorInstance.IrradianceSensorProperties()
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
        sensor_paths: list[str] = [],
        source_paths: list[str] = [],
        geometries: GeoPaths = GeoPaths(),
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> messages.Scene.SimulationInstance:
        sim_i = messages.Scene.SimulationInstance(name=name, description=description)
        if metadata is not None:
            sim_i.metadata.update(metadata)
        sim_i.simulation_guid = simulation_template.key
        sim_i.sensor_paths.extend(sensor_paths)
        sim_i.source_paths.extend(source_paths)
        sim_i.geometries.geo_paths.extend(geometries.geo_paths)
        return sim_i
