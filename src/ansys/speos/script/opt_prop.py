from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project


class OptProp:
    """Represent a Speos optical properties"""

    def __init__(self, project: project.Project, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = {}):
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

    def set_volume_optic(self, index: float, absorption: float, constringence: Optional[float]) -> OptProp:
        self._vop_template.optic.index = index
        self._vop_template.optic.absorption = absorption
        if constringence is not None:
            self._vop_template.optic.constringence = constringence
        else:
            del self._vop_template.optic.constringence
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

    def __str__(self):
        return (
            f"SOP template: {self._sop_template}\n"
            + f"SOP instance: {self._sop_instance}\n"
            + f"VOP template: {self._vop_template}\n"
            + f"VOP instance: {self._vop_instance}"
        )

    def commit(self) -> OptProp:
        """Save feature"""
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._vop_template.metadata["UniqueId"] = self._unique_id
            self._vop_template_link = self._project.client.vop_templates().create(message=self._vop_template)
            self._vop_instance.metadata["UniqueId"] = self._unique_id
            self._vop_instance.vop_guid = self._vop_template_link.key
            self._sop_template.metadata["UniqueId"] = self._unique_id
            self._sop_template_link = self._project.client.sop_templates().create(message=self._sop_template)
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
