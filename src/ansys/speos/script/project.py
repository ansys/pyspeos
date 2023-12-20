from __future__ import annotations

from typing import Mapping, Optional

import ansys.speos.core as core
import ansys.speos.script.opt_prop as opt_prop

speos = core.Speos()


class Project:
    """Stored in a file, a Project describe all Speos features (optical properties, sources, sensors, simulations)
    that user can fill in. Extension .scdocx refer to Speos for SpaceClaim.
    From Speos for NX, input file must have extension .prt or .asm.
    From pySpeos, input file is related to Scene filename.
    Project provide functions to get Speos Tree representation as a list of Features and to make actions on them."""

    def __init__(self, path: str = ""):
        """Create from empty or load from file"""
        self.client = speos.client
        self.scene = speos.client.scenes().create()
        if len(path):
            self.scene.load_file(path)
        return

    def list(self):
        """Return all feature key as a tree, can be used to list all features"""
        pass

    def create_optical_property(
        self, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = {}
    ) -> opt_prop.OptProp:
        """Create a new feature, to associate to main ribbon commands"""
        return opt_prop.OptProp(
            project=self, name=name, description=description if description else "", metadata=metadata if metadata else {}
        )

    def find(self, name: str, id: Optional[str]):
        """Get details about a feature"""

    def action(self, name: str):
        """Act on feature: update, hide/show, copy, ..."""
        pass

    def save(self):
        """Save class state in file given at construction"""
        pass

    def __str__(self):
        return str(self.scene)
