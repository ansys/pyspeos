"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import Mapping, Union

from ansys.api.speos.scene.v1 import scene_pb2 as messages
from ansys.api.speos.scene.v1 import scene_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry import AxisPlane, AxisSystem, GeoPathReverseNormal, GeoPaths
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
        class Luminaire:
            def __init__(self, axis_system: AxisSystem = AxisSystem()) -> None:
                self.axis_system = axis_system

        class Surface:
            class ExitanceConstant:
                def __init__(self, geo_paths: list[GeoPathReverseNormal]) -> None:
                    self.geo_paths = geo_paths

            class ExitanceVariable:
                def __init__(self, axis_plane: AxisPlane = AxisPlane()) -> None:
                    self.axis_plane = axis_plane

            class Intensity:
                class Library:
                    Orientation = Enum("Orientation", ["AxisSystem", "NormalToSurface", "NormalToUVMap"])

                    def __init__(
                        self,
                        exit_geometries: GeoPaths = None,
                        orientation: Orientation = Orientation.AxisSystem,
                        axis_system: AxisSystem = AxisSystem(),
                    ) -> None:
                        self.exit_geometries = exit_geometries
                        self.orientation = orientation
                        self.axis_system = axis_system

                class AsymmetricGaussian:
                    def __init__(self, axis_system: AxisSystem = AxisSystem()) -> None:
                        self.axis_system = axis_system

                def __init__(self, props: Union[Library, AsymmetricGaussian]) -> None:
                    self.props = props

            def __init__(
                self, exitance_props: Union[ExitanceConstant, ExitanceVariable], intensity_props: Intensity = None
            ) -> None:
                self.exitance_props = exitance_props
                self.intensity_props = intensity_props

    def scene(
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
        properties: Union[Properties.Luminaire, Properties.Surface],
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> messages.Scene.SourceInstance:
        src_i = messages.Scene.SourceInstance(name=name, description=description)
        if metadata is not None:
            src_i.metadata.update(metadata)
        src_i.source_guid = source_template.key
        if isinstance(properties, SceneFactory.Properties.Luminaire):
            src_i.luminaire_properties.axis_system.extend(
                properties.axis_system.origin
                + properties.axis_system.x_vect
                + properties.axis_system.y_vect
                + properties.axis_system.z_vect
            )
        elif isinstance(properties, SceneFactory.Properties.Surface):
            if isinstance(properties.exitance_props, SceneFactory.Properties.Surface.ExitanceConstant):
                src_i.surface_properties.exitance_constant_properties.geo_paths.extend(
                    [
                        messages.Scene.SourceInstance.SurfaceProperties.ExitanceConstantProperties.GeoPath(
                            geo_path=g.geo_path, reverse_normal=g.reverse_normal
                        )
                        for g in properties.exitance_props.geo_paths
                    ]
                )
            elif isinstance(properties.exitance_props, SceneFactory.Properties.Surface.ExitanceVariable):
                src_i.surface_properties.exitance_variable_properties.axis_plane.extend(
                    [
                        properties.exitance_props.axis_plane.origin
                        + properties.exitance_props.axis_plane.x_vect
                        + properties.exitance_props.axis_plane.y_vect
                    ]
                )
            if isinstance(properties.intensity_props, SceneFactory.Properties.Surface.Intensity.Library):
                if properties.intensity_props.exit_geometries is not None:
                    src_i.surface_properties.intensity_properties.library_properties.exit_geometries.geo_paths.extend(
                        properties.intensity_props.exit_geometries
                    )
                if (
                    properties.intensity_props.orientation
                    == SceneFactory.Properties.Surface.Intensity.Library.Orientation.AxisSystem
                ):
                    src_i.surface_properties.intensity_properties.library_properties.axis_system.values.extend(
                        [
                            properties.intensity_props.axis_system.origin
                            + properties.intensity_props.axis_system.x_vect
                            + properties.intensity_props.axis_system.y_vect
                            + properties.intensity_props.axis_system.z_vect
                        ]
                    )
                elif (
                    properties.intensity_props.orientation
                    == SceneFactory.Properties.Surface.Intensity.Library.Orientation.NormalToSurface
                ):
                    src_i.surface_properties.intensity_properties.library_properties.normal_to_surface.SetInParent()
                elif (
                    properties.intensity_props.orientation
                    == SceneFactory.Properties.Surface.Intensity.Library.Orientation.NormalToUVMap
                ):
                    src_i.surface_properties.intensity_properties.library_properties.normal_to_uv_map.SetInParent()
            elif isinstance(properties.intensity_props, SceneFactory.Properties.Surface.Intensity.AsymmetricGaussian):
                src_i.surface_properties.intensity_properties.asymmetric_gaussian_properties.axis_system.extend(
                    [
                        properties.intensity_props.axis_system.origin
                        + properties.intensity_props.axis_system.x_vect
                        + properties.intensity_props.axis_system.y_vect
                        + properties.intensity_props.axis_system.z_vect
                    ]
                )
        return src_i

    def sensor_instance(
        name: str,
        sensor_template: SensorTemplateLink,
        properties: Union[
            messages.Scene.SensorInstance.CameraSensorProperties, messages.Scene.SensorInstance.IrradianceSensorProperties
        ],
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
