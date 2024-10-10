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

from typing import Mapping

import ansys.speos.core as core
import ansys.speos.script.opt_prop as opt_prop
import ansys.speos.script.simulation as simulation
import ansys.speos.script.source as source


class Project:
    """Stored in a file, a Project describe all Speos features (optical properties, sources, sensors, simulations)
    that user can fill in. Extension .scdocx refer to Speos for SpaceClaim.
    From Speos for NX, input file must have extension .prt or .asm.
    From pySpeos, input file is related to Scene filename.
    Project provide functions to get Speos Tree representation as a list of Features and to make actions on them.

    Create from empty or load from a specific file.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos session (connected to gRPC server).
    path : str
        The project will be loaded from this file
        By default, ``""``, means create from empty.

    Attributes
    ----------
    scene_link : ansys.speos.core.scene.SceneLink
        Link object for the scene in database.
    """

    def __init__(self, speos: core.Speos, path: str = ""):
        self.client = speos.client
        """Speos instance client."""
        self.scene_link = speos.client.scenes().create()
        """Link object for the scene in database."""
        if len(path):
            self.scene_link.load_file(path)
        return

    def list(self):
        """Return all feature key as a tree, can be used to list all features- Not yet implemented"""
        pass

    def create_optical_property(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> opt_prop.OptProp:
        """Create a new feature, to associate to main ribbon commands"""
        return opt_prop.OptProp(project=self, name=name, description=description, metadata=metadata)

    def create_source(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> source.Source:
        """Create a new Source feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        return source.Source(project=self, name=name, description=description, metadata=metadata)

    def create_simulation(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> simulation.Simulation:
        return simulation.Simulation(project=self, name=name, description=description, metadata=metadata)

    def find(self, name: str, id: str = ""):
        """Get details about a feature - Not yet implemented"""
        pass

    def action(self, name: str):
        """Act on feature: update, hide/show, copy, ... - Not yet implemented"""
        pass

    def save(self):
        """Save class state in file given at construction - Not yet implemented"""
        pass

    def __str__(self):
        """Return the string representation of the project's scene."""
        return str(self.scene_link)
