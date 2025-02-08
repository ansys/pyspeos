# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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
"""Provides a way to combine several speos files into one project feature (of script layer)."""

import os
from typing import List, Optional

from ansys.speos.core.kernel.part import Part, PartLink
from ansys.speos.core.speos import Speos
from ansys.speos.core.project import Project


class SpeosFileInstance:
    """Represents a speos file that is placed and oriented in a specific way

    Parameters
    ----------
    speos_file : str
        Speos file to be loaded.
    axis_system : Optional[List[float]]
        Location and orientation wished for speos file, [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    name : str
        Name chosen, this name will be used as sub part name in the root part feature of the project.
        By default, ``""``, empty means that the name from speos_file basename without extension will be taken.
    """

    def __init__(
        self, speos_file: str, axis_system: Optional[List[float]] = None, name: str = ""
    ) -> None:
        self.speos_file = speos_file
        """Speos file."""
        if axis_system is None:
            axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
        self.axis_system = axis_system
        """Location/Orientation wished for speos file."""
        self.name = name
        """Name for the entity (speos file + location/orientation)."""

        if self.name == "":
            self.name = os.path.splitext(os.path.basename(speos_file))[0]


def insert_speos(project: Project, speos_to_insert: List[SpeosFileInstance]) -> None:
    """Complete a project feature with one or several speos files, placing/orienting them in the root part.
    All the features from the input project are kept.
    Only geometry and materials are taken from the speos files to combine.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project feature to be completed with geometry and materials data.
    speos_to_combine : List[ansys.speos.core.workflow.combine_speos.SpeosFileInstance]
        List of speos + location/orientation to insert into the project
    """
    # Part link : either create it empty if none is present in the project's scene
    # or just retrieve it from project's scene
    part_link = None
    if project.scene_link.get().part_guid == "":
        part_link = project.client.parts().create(message=Part())
    else:
        part_link = project.client.get_item(project.scene_link.get().part_guid)

    # Combine all speos_to_insert into the project
    _combine(project=project, part_link=part_link, speos_to_combine=speos_to_insert)


def combine_speos(speos: Speos, speos_to_combine: List[SpeosFileInstance]) -> Project:
    """Creates a project feature (from script layer) by combining several speos files, and place/orient them in the root part.
    This only combine geometry and materials.

    Parameters
    ----------
    speos : ansys.speos.core.kernel.speos.Speos
        Speos session (connected to gRPC server).
    speos_to_combine : List[ansys.speos.core.workflow.combine_speos.SpeosFileInstance]
        List of speos + location/orientation to combine into a single project

    Returns
    -------
    ansys.speos.core.project.Project
        Project feature created by combining the input list.
    """
    # Create an empty project and an empty part link
    p = Project(speos=speos)
    part_link = speos.client.parts().create(message=Part())

    # Combine all speos_to_combine into the project
    _combine(project=p, part_link=part_link, speos_to_combine=speos_to_combine)

    return p


def _combine(project: Project, part_link: PartLink, speos_to_combine: List[SpeosFileInstance]):
    scene_data = project.scene_link.get()
    part_data = part_link.get()

    for spc in speos_to_combine:
        scene_tmp = project.client.scenes().create()
        scene_tmp.load_file(file_uri=spc.speos_file)
        scene_tmp_data = scene_tmp.get()

        part_inst = Part.PartInstance(name=spc.name)
        part_inst.axis_system[:] = spc.axis_system
        part_inst.part_guid = scene_tmp_data.part_guid
        part_data.parts.append(part_inst)

        for mat in scene_tmp_data.materials:
            if len(mat.sop_guids) > 0:
                mat.name = spc.name + "." + mat.name
                mat.geometries.geo_paths[:] = [spc.name + "/" + x for x in mat.geometries.geo_paths]
                scene_data.materials.append(mat)

    part_link.set(data=part_data)
    scene_data.part_guid = part_link.key
    project.scene_link.set(data=scene_data)

    project._fill_features()
