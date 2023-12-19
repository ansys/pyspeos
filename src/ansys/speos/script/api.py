#
# Example of abstraction layer for Speos scripting
#
from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

import ansys.speos.core as core

speos = core.Speos()


#
# Fluent approach
# - functions for option menu
# - function's parameter with data corresponding to option
#
class GeoRef:
    """Represent a CAD object"""

    def __init__(self, name: str, description: Optional[str], metadata: Mapping[str, str]):
        self.name = name
        self.description = description
        self.metadata = metadata
        return

    @staticmethod
    def from_native_link(geopath: str) -> GeoRef:
        return GeoRef("", "", {"GeoPath": geopath})

    def to_native_link(self) -> str:
        return self.metadata["GeoPath"]


class Project:
    """Stored in a file, a Project describe all Speos features (optical properties, sources, sensors, simulations)
    that user can fill in. Extension .scdocx refer to Speos for SpaceClaim.
    From Speos for NX, input file must have extension .prt or .asm.
    From pySpeos, input file is related to Scene filename.
    Project provide functions to get Speos Tree representation as a list of Features and to make actions on them."""

    def __init__(self, path: str = ""):
        self.scene = speos.client.scenes().create()
        if len(path):
            self.scene.load_file(path)
        return

    def list(self):
        """Return all feature key as a tree, can be used to list all features"""
        return

    def create_optical_property(self, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = {}) -> OptProp:
        """Create a new feature, to associate to main ribbon commands"""
        return OptProp(project=self, name=name, description=description if description else "", metadata=metadata if metadata else {})

    def find(self, name: str, id: Optional[str]):
        """Get details about a feature"""

    def action(self, name: str):
        """Act on feature: update, hide/show, copy, ..."""

    def save(self):
        """Save class state in file given at construction"""


#
# Fluent approach
# - functions for option menu
# - function's parameter with data corresponding to option
#


class OptProp:
    """Represent a Speos optical properties"""

    def __init__(self, project: Project, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = {}):
        # Create SOP template and instance
        self._project = project
        self._unique_id = None
        self._sop_template = core.SOPTemplate(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )
        self._sop_instance = core.Scene.SOPInstance(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )
        # Create VOP template and instance
        self._vop_template = core.VOPTemplate(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )
        self._vop_instance = core.Scene.VOPInstance(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )
        return

    def set_surface_mirror(self, reflectance: float) -> OptProp:
        self._sop_template.mirror.reflectance = reflectance
        return self

    def set_surface_opticalpolished(self) -> OptProp:
        self._sop_template.optical_polished.SetInParent()
        return self

    def set_surface_library(self, path: str) -> OptProp:
        self._sop_template.library.sop_file_uri = path
        return self

    def set_volume_opaque(self) -> OptProp:
        self._vop_template.opaque.SetInParent()
        return self

    def set_volume_optic(self, index: float, absorption: float, constringence: float) -> OptProp:
        self._vop_template.optic.index = index
        self._vop_template.optic.absorption = absorption
        self._vop_template.optic.constringence = constringence
        return self

    def set_volume_nonhomogeneous(self, path: str, coordsys: GeoRef) -> OptProp:
        self._vop_template.non_homogeneous.gradedmaterial_file_uri = path
        return self

    def set_volume_library(self, path: str) -> OptProp:
        self._vop_template.library.material_file_uri = path
        return self

    def set_geometries(self, geometries: List[GeoRef]) -> OptProp:
        """Takes all geometries if nothing provided"""
        self._vop_instance.geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
        self._sop_instance.geometries.geo_paths[:] = self._vop_instance.geometries.geo_paths
        return self

    def commit(self, project) -> OptProp:
        """Save feature"""
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._vop_template.metadata["UniqueId"] = self._unique_id
            self._vop_template_link = speos.client.vop_templates().create(message=self._vop_template)
            self._vop_instance.metadata["UniqueId"] = self._unique_id
            self._vop_instance.vop_guid = self._vop_template_link.key
            self._sop_template.metadata["UniqueId"] = self._unique_id
            self._sop_template_link = speos.client.sop_templates().create(message=self._sop_template)
            self._sop_instance.metadata["UniqueId"] = self._unique_id
            self._sop_instance.sop_guid = self._sop_template_link.key
            if self._project.scene:
                scene_data = self._project.scene.get()  # retrieve scene data
                scene_data.vops.append(self._vop_instance)
                scene_data.sops.append(self._sop_instance)
                self._project.scene.set(data=scene_data)
        else:
            self._vop_template_link.set(data=self._vop_template)
            self._sop_template_link.set(data=self._sop_template)
            if self._project.scene:
                scene_data = self._project.scene.get()  # retrieve scene data
                vopinst = next((x for x in scene_data.vops if x.metadata["UniqueId"] == self._unique_id), None)
                if vopinst:
                    vopinst = self._vop_instance
                sopinst = next((x for x in scene_data.sops if x.metadata["UniqueId"] == self._unique_id), None)
                if sopinst:
                    sopinst = self._sop_instance
                self._project.scene.set(data=scene_data)
        return self
