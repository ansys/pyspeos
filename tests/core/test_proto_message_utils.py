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

"""Test basic using proto_message_utils."""

from pathlib import Path

from ansys.api.speos import __version__ as ansys_api_speos_version

from ansys.speos.core import GeoRef, OptProp, Project, Speos, proto_message_utils
from ansys.speos.core.generic.version_checker import check_version
from ansys.speos.core.kernel import scene
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_dict
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.source import SourceSurface
from tests.conftest import test_path


def test_replace_guid_elt(speos: Speos):
    """Test _replace_guid_elt."""
    # Example with surface source : spectrum guid + intensity guid
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    src_feat = SourceSurface(project=p, name="Surface.1")
    src_feat.set_exitance_constant(geometries=[(GeoRef.from_native_link("BodyB"), False)])
    src_feat.commit()

    # Retrieve source template message and transform it into dict
    src_t_msg = src_feat.source_template_link.get()
    src_t_dict = protobuf_message_to_dict(message=src_t_msg)

    # Check that expected guids are present
    assert src_t_msg.HasField("surface")
    assert src_t_msg.surface.intensity_guid != ""
    assert src_t_msg.surface.HasField("spectrum_guid")
    assert src_t_msg.surface.spectrum_guid != ""

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity") == []
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="spectrum") == []

    # Replace guid elements for this message,
    # by adding new key to the dict with value corresponding to database item
    proto_message_utils._replace_guid_elt(speos_client=speos.client, json_dict=src_t_dict)

    # Check that the new keys are added
    find = proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity")
    assert len(find) == 1
    assert find[0][0] == ".surface.intensity"
    assert find[0][1]["name"] == "Surface.1.Intensity"

    find = proto_message_utils._finder_by_key(dict_var=src_t_dict, key="spectrum")
    assert len(find) == 1
    assert find[0][0] == ".surface.spectrum"
    assert find[0][1]["name"] == "Surface.1.Spectrum"


def test_replace_guid_elt_ignore_simple_key(speos: Speos):
    """Test _replace_guid_elt with parameter ignore_simple_key."""
    # Example with surface source : spectrum guid + intensity guid
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    src_feat = SourceSurface(project=p, name="Surface.1")
    src_feat.set_exitance_constant(geometries=[(GeoRef.from_native_link("BodyB"), False)])
    src_feat.commit()

    # Retrieve source template message and transform it into dict
    src_t_dict = protobuf_message_to_dict(message=src_feat.source_template_link.get())

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity") == []

    # Replace guid elements for this message,
    # by adding new key to the dict with value corresponding to database item
    proto_message_utils._replace_guid_elt(
        speos_client=speos.client,
        json_dict=src_t_dict,
        ignore_simple_key="intensity_guid",
    )

    # Check that the ignored key is not replaced
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity") == []


def test_replace_guid_elt_list(speos: Speos):
    """Test _replace_guid_elt in a specific case : list of guids like sop_guids (before v252.1)."""
    # Example with material : vop guid + sop guids
    p = Project(speos=speos)
    mat_feat = OptProp(project=p, name="Material.1")
    mat_feat.set_volume_opaque()
    mat_feat.set_surface_mirror()
    mat_feat.commit()

    # Retrieve material instance message and transform it into dict
    mat_i_msg = mat_feat._material_instance
    mat_i_dict = protobuf_message_to_dict(message=mat_i_msg)

    # Check that expected guids are present
    assert mat_i_msg.HasField("vop_guid")
    assert mat_i_msg.vop_guid != ""

    if len(mat_i_msg.sop_guids) > 0:
        assert len(mat_i_msg.sop_guids) == 1
        assert mat_i_msg.sop_guids[0] != ""
    else:
        assert mat_i_msg.HasField("sop_guid")
        assert mat_i_msg.sop_guid != ""

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="vop") == []
    if len(mat_i_msg.sop_guids) > 0:
        assert proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sops") == []
    else:
        assert proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sop") == []

    # Replace guid elements for this message,
    # by adding new key to the dict with value corresponding to database item
    proto_message_utils._replace_guid_elt(speos_client=speos.client, json_dict=mat_i_dict)

    # Check that the new keys are added
    find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="vop")
    assert len(find) == 1
    assert find[0][0] == ".vop"
    assert find[0][1]["name"] == "Material.1.VOP"

    if len(mat_i_msg.sop_guids) > 0:
        find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sops")
        assert len(find) == 1
        assert find[0][0] == ".sops"
        assert len(find[0][1]) == 1
        assert find[0][1][0]["name"] == "Material.1.SOP"

        find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="mirror")
        assert len(find) == 1
        assert find[0][0] == ".sops[.name='Material.1.SOP'].mirror"
        assert find[0][1]["reflectance"] == 100.0
    else:
        find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sop")
        assert len(find) == 1
        assert find[0][0] == ".sop"
        assert find[0][1]["name"] == "Material.1.SOP"

        find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="mirror")
        assert len(find) == 1
        assert find[0][0] == ".sop.mirror"
        assert find[0][1]["reflectance"] == 100.0


def test_replace_guid_elt_complex(speos: Speos):
    """Test _replace_guid_elt in a bigger message like scene."""
    scene_link = speos.client.scenes().create(message=scene.ProtoScene())
    scene_link.load_file(
        file_uri=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        )
    )

    scene_dict = protobuf_message_to_dict(message=scene_link.get())

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="part") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="source") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="library") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="sensor") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="simulation") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="vop") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="sops") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="sop") == []

    # To avoid a lot of replacements (part->bodies->faces), part_guid is set as ignore_simple_key
    proto_message_utils._replace_guid_elt(
        speos_client=speos.client,
        json_dict=scene_dict,
        ignore_simple_key="part_guid",
    )

    # Check that the part_guid was correctly ignored
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="part") == []

    # Two sources correctly replaced
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="source")
    assert len(find) == 2
    assert find[0][0] == ".sources[.name='Dom Source 2 (0) in SOURCE2'].source"
    assert find[0][1]["name"] == "Dom Source 2 (0) in SOURCE2"
    assert find[1][0] == ".sources[.name='Surface Source (0) in SOURCE1'].source"
    assert find[1][1]["name"] == "Surface Source (0) in SOURCE1"

    # And their spectrums + intensities
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="library")
    assert len(find) == 2
    assert (
        find[0][0]
        == ".sources[.name='Dom Source 2 (0) in SOURCE2'].source.surface.spectrum.library"
    )
    assert find[0][1]["file_uri"].endswith("Red Spectrum.spectrum")
    assert (
        find[1][0]
        == ".sources[.name='Surface Source (0) in SOURCE1'].source.surface.spectrum.library"
    )
    assert find[1][1]["file_uri"].endswith("Blue Spectrum.spectrum")

    # Sensor correctly replaced
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="sensor")
    assert len(find) == 1
    assert find[0][0] == ".sensors[.name='Dom Irradiance Sensor (0)'].sensor"
    assert find[0][1]["name"] == "Dom Irradiance Sensor (0)"

    # Simulation correctly replaced
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="simulation")
    assert len(find) == 1
    assert find[0][0] == ".simulations[.name='ASSEMBLY1.DS (0)'].simulation"
    assert find[0][1]["name"] == "ASSEMBLY1.DS (0)"

    # vop/sops correctly replaced
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="vop")
    assert len(find) == 3
    find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="sops")
    if len(find) != 3:
        find = proto_message_utils._finder_by_key(dict_var=scene_dict, key="sop")
        assert len(find) == 3


def test_value_finder_key_startswith(speos: Speos):
    """Test _value_finder_key_startswith."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    src_feat = SourceSurface(project=p, name="Surface.1")
    src_feat.set_exitance_constant(geometries=[(GeoRef.from_native_link("BodyB"), False)])
    src_feat.commit()

    # Retrieve source instance message and transform it into dict
    src_i_dict = protobuf_message_to_dict(message=src_feat._source_instance)

    keys = []
    for key, val in proto_message_utils._value_finder_key_startswith(
        dict_var=src_i_dict, key="surface"
    ):
        keys.append(key)
    assert keys == ["surface_properties"]


def test__value_finder_key_endswith(speos: Speos):
    """Test _value_finder_key_endswith."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    src_feat = SourceSurface(project=p, name="Surface.1")
    src_feat.set_exitance_constant(geometries=[(GeoRef.from_native_link("BodyB"), False)])
    src_feat.commit()

    # Retrieve source instance message and transform it into dict
    src_i_dict = protobuf_message_to_dict(message=src_feat._source_instance)

    keys = []
    for key, val, parent in proto_message_utils._value_finder_key_endswith(
        dict_var=src_i_dict, key="_properties"
    ):
        keys.append(key)
    assert keys == [
        "surface_properties",
        "exitance_constant_properties",
        "intensity_properties",
    ]


def test_replace_properties(speos: Speos):
    """Test _replace_properties."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    src_feat = SourceSurface(project=p, name="Surface.1")
    src_feat.set_exitance_constant(geometries=[(GeoRef.from_native_link("BodyB"), False)])
    src_feat.set_intensity().set_gaussian().set_axis_system([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    src_feat.commit()

    # First replace guids
    src_i_dict = proto_message_utils._replace_guids(
        speos_client=speos.client, message=src_feat._source_instance
    )

    # Then replace properties in correct elements
    proto_message_utils._replace_properties(json_dict=src_i_dict)

    # Check that properties elements are no more there
    assert proto_message_utils._finder_by_key(dict_var=src_i_dict, key="surface_properties") == []
    assert (
        proto_message_utils._finder_by_key(dict_var=src_i_dict, key="exitance_constant_properties")
        == []
    )
    assert proto_message_utils._finder_by_key(dict_var=src_i_dict, key="gaussian_properties") == []

    # Check that they are copied at correct place
    find = proto_message_utils._finder_by_key(dict_var=src_i_dict, key="axis_system")
    assert len(find) == 1
    assert find[0][0] == ".source.surface.intensity.gaussian.axis_system"

    find = proto_message_utils._finder_by_key(dict_var=src_i_dict, key="geo_paths")
    assert len(find) == 1
    assert find[0][0] == ".source.surface.exitance_constant.geo_paths"


def test_replace_special_props(speos: Speos):
    """Test _replace_properties with a property that shouldn't be replaced."""
    p = Project(speos=speos)

    # Create a sensor with light expert activated
    ssr_feat = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr_feat.lxp_path_number = 150

    # First replace guids
    ssr_i_dict = proto_message_utils._replace_guids(
        speos_client=speos.client, message=ssr_feat._sensor_instance
    )

    # Then replace properties in correct elements
    proto_message_utils._replace_properties(json_dict=ssr_i_dict)

    # Check that lxp_properties and nb_max_paths are still there
    find = proto_message_utils._finder_by_key(dict_var=ssr_i_dict, key="nb_max_paths")
    assert len(find) == 1
    assert find[0][0] == ".lxp_properties.nb_max_paths"


def test_finder_by_key(speos: Speos):
    """Test _finder_by_key."""
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    scene_dict = p._to_dict()
    expected_res = (
        ".sources[.name='Dom Source 2 (0) in SOURCE2'].source.surface.radiant_flux.radiant_value"
    )
    # key at root
    res = proto_message_utils._finder_by_key(dict_var=scene_dict, key="part_guid")
    assert len(res) == 1
    assert res[0][0] == ".part_guid"

    # key in a list elt (with name property : sources[.name='XXXX'])
    res = proto_message_utils._finder_by_key(dict_var=scene_dict, key="radiant_value")
    assert len(res) == 2
    expected_res = (
        ".sources[.name='Dom Source 2 (0) in SOURCE2'].source.surface.radiant_flux.radiant_value"
    )
    assert res[0][0] == expected_res
    assert res[0][1] == 6.590041607465698
    expected_res = (
        ".sources[.name='Surface Source (0) in SOURCE1'].source.surface.radiant_flux.radiant_value"
    )
    assert res[1][0] == expected_res
    assert res[1][1] == 9.290411220389682

    # key in a list (without name property : geo_paths[0])
    res = proto_message_utils._finder_by_key(dict_var=scene_dict, key="geo_path")
    assert len(res) == 2
    expected_res = (
        ".sources[.name='Dom Source 2 (0) in SOURCE2']"
        ".source.surface.exitance_constant.geo_paths[0].geo_path"
    )
    assert res[0][0] == expected_res
    assert res[0][1] == "Solid Body in SOURCE2:2920204960/Face in SOURCE2:222"
    expected_res = (
        ".sources[.name='Surface Source (0) in SOURCE1']"
        ".source.surface.exitance_constant.geo_paths[0].geo_path"
    )
    assert res[1][0] == expected_res
    assert res[1][1] == "Solid Body in SOURCE1:2494956811/Face in SOURCE1:187"


def test_flatten_dict(speos: Speos):
    """proto_message_utils test of '_flatten_dict' method."""
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    scene_dict = p._to_dict()
    res = proto_message_utils._flatten_dict(dict_var=scene_dict)
    expected_keys = [
        "name",
        "description",
        "part_guid",
        "sources",
        "sensors",
        "simulations",
        "materials",
        "metadata",
        "scenes",
    ]
    if check_version(ansys_api_speos_version, 0, 16, 0):
        expected_keys.append("sub_scene_anchor_axis_system")
    assert all(True if key in expected_keys else False for key in res.keys())
