# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

from typing import List

from ansys.api.speos.scene.v2.scene_pb2 import Scene

from ansys.speos.core.kernel.part import PartLink, ProtoPart
from ansys.speos.core.project import Project, SpeosFileInstance
from ansys.speos.core.speos import Speos


def insert_speos(project: Project, speos_to_insert: List[SpeosFileInstance]) -> None:
    """Import geometries and materials from the selected SPEOS files to the existing project.

    Geometries and materials are placed in the root part, and orientated thanks to the
    SpeosFileInstance object.

    Notes
    -----
    Sensors and Simulations are not imported to the project.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which to import geometries and materials from SPEOS files.
    speos_to_combine : List[ansys.speos.core.project.SpeosFileInstance]
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
        Sensors and Simulations are not imported to the project.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos session (connected to gRPC server).
    speos_to_combine : List[ansys.speos.core.project.SpeosFileInstance]
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
        scene_tmp.load_file(file_uri=spc.speos_file, password=spc.password)
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

        for src in scene_tmp_data.sources:
            src.name = spc.name + "." + src.name
            if src.name in [source.name for source in scene_data.sources]:
                msg = "Lightbox {}: {} has a conflict name with an existing feature.".format(
                    spc.name, src.name
                )
                raise ValueError(msg)
            if src.HasField("surface_properties"):
                if src.surface_properties.HasField("exitance_constant_properties"):
                    paths = src.surface_properties.exitance_constant_properties.geo_paths
                    src.surface_properties.exitance_constant_properties.ClearField("geo_paths")
                    geo_paths = []
                    for path in paths:
                        geo_paths.append(
                            Scene.GeoPath(
                                geo_path=spc.name + "/" + path.geo_path,
                                reverse_normal=path.reverse_normal,
                            )
                        )
                    src.surface_properties.exitance_constant_properties.geo_paths.extend(geo_paths)
            if src.HasField("rayfile_properties"):
                if src.rayfile_properties.HasField("exit_geometries"):
                    paths = src.rayfile_properties.exit_geometries.geo_paths
                    src.rayfile_properties.ClearField("exit_geometries")
                    src.rayfile_properties.exit_geometries.geo_paths[:] = [
                        spc.name + "/" + gr for gr in paths
                    ]
            scene_data.sources.append(src)

    part_link.set(data=part_data)
    scene_data.part_guid = part_link.key
    project.scene_link.set(data=scene_data)

    project._fill_features()
