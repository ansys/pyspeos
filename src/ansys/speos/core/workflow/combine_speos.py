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
"""Import geometries and materials from several SPEOS files to a project."""

from pathlib import Path
from typing import List, Optional

from ansys.speos.core.kernel.part import PartLink, ProtoPart
from ansys.speos.core.project import Project
from ansys.speos.core.speos import Speos


class SpeosFileInstance:
    """Represents a SPEOS file containing geometries and materials.

    Geometries are placed in the root part of a project, and oriented according to the axis_system
    argument.

    Parameters
    ----------
    speos_file : str
        SPEOS file to be loaded.
    axis_system : Optional[List[float]]
        Location and orientation to define for the geometry of the SPEOS file,
        [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    name : str
        Name chosen for the imported geometry. This name is used as subpart name under the root part
        of the project.
        By default, "" (meaning user has not defined a name), then the name of the SPEOS file
        without extension is taken.
        Note: Materials are named after the name. For instance name.material.1 representing the
        first material of the imported geometry.
    """

    def __init__(
        self,
        speos_file: str,
        axis_system: Optional[List[float]] = None,
        name: str = "",
    ) -> None:
        self.speos_file = speos_file
        """SPEOS file."""
        if axis_system is None:
            axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
        self.axis_system = axis_system
        """Location and orientation to define for the geometry of the SPEOS file."""
        self.name = name
        """Name for the imported geometry, and used to name the materials."""

        if self.name == "":
            self.name = Path(speos_file).stem


def insert_speos(project: Project, speos_to_insert: List[SpeosFileInstance]) -> None:
    """Import geometries and materials from the selected SPEOS files to the existing project.

    Geometries and materials are placed in the root part, and orientated thanks to the
    SpeosFileInstance object.

    Notes
    -----
    Sources, Sensors and Simulations are not imported to the project.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which to import geometries and materials from SPEOS files.
    speos_to_combine : List[ansys.speos.core.workflow.combine_speos.SpeosFileInstance]
        List of SPEOS files, location and orientation of geometries to be imported to the project.
    """
    # Part link : either create it empty if none is present in the project's scene
    # or just retrieve it from project's scene
    part_link = None
    if project.scene_link.get().part_guid == "":
        part_link = project.client.parts().create(message=ProtoPart())
    else:
        part_link = project.client[project.scene_link.get().part_guid]

    # Combine all speos_to_insert into the project
    _combine(project=project, part_link=part_link, speos_to_combine=speos_to_insert)


def combine_speos(speos: Speos, speos_to_combine: List[SpeosFileInstance]) -> Project:
    """Create a project by combining geometries and materials from the selected SPEOS files.

    Geometries and materials are placed in the root part,
    and orientated thanks to the SpeosFileInstance object.

    Notes
    -----
        Sources, Sensors and Simulations are not imported to the project.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos session (connected to gRPC server).
    speos_to_combine : List[ansys.speos.core.workflow.combine_speos.SpeosFileInstance]
        List of SPEOS files, location and orientation of geometries to be imported to the project.

    Returns
    -------
    ansys.speos.core.project.Project
        Project created by combining the input list of SPEOS files.
    """
    # Create an empty project and an empty part link
    p = Project(speos=speos)
    part_link = speos.client.parts().create(message=ProtoPart())

    # Combine all speos_to_combine into the project
    _combine(project=p, part_link=part_link, speos_to_combine=speos_to_combine)

    return p


def _combine(
    project: Project,
    part_link: PartLink,
    speos_to_combine: List[SpeosFileInstance],
):
    scene_data = project.scene_link.get()
    part_data = part_link.get()

    for spc in speos_to_combine:
        scene_tmp = project.client.scenes().create()
        scene_tmp.load_file(file_uri=spc.speos_file)
        scene_tmp_data = scene_tmp.get()

        part_inst = ProtoPart.PartInstance(name=spc.name)
        part_inst.axis_system[:] = spc.axis_system
        part_inst.part_guid = scene_tmp_data.part_guid
        part_data.parts.append(part_inst)

        for mat in scene_tmp_data.materials:
            if mat.HasField("sop_guid") or mat.HasField("texture") or len(mat.sop_guids) > 0:
                mat.name = spc.name + "." + mat.name
                mat.geometries.geo_paths[:] = [spc.name + "/" + x for x in mat.geometries.geo_paths]
                scene_data.materials.append(mat)

    part_link.set(data=part_data)
    scene_data.part_guid = part_link.key
    project.scene_link.set(data=scene_data)

    project._fill_features()
