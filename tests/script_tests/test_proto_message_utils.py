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

"""
Test basic using proto_message_utils from script layer.
"""
import os

from ansys.speos.core import scene
from ansys.speos.core.proto_message_utils import protobuf_message_to_dict
from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from ansys.speos.script import proto_message_utils
from conftest import test_path


def test_replace_guid_elt(speos: Speos):
    """Test _replace_guid_elt."""

    # Example with surface source : spectrum guid + intensity guid
    p = script.Project(speos=speos)
    src_feat = script.Source(project=p, name="Surface.1")
    src_feat.set_surface()
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

    # Replace guid elements for this message, by adding new key to the dict with value corresponding to database item
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
    """Test _replace_guid_elt with paraeter ignore_simple_key."""

    # Example with surface source : spectrum guid + intensity guid
    p = script.Project(speos=speos)
    src_feat = script.Source(project=p, name="Surface.1")
    src_feat.set_surface()
    src_feat.commit()

    # Retrieve source template message and transform it into dict
    src_t_dict = protobuf_message_to_dict(message=src_feat.source_template_link.get())

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity") == []

    # Replace guid elements for this message, by adding new key to the dict with value corresponding to database item
    proto_message_utils._replace_guid_elt(speos_client=speos.client, json_dict=src_t_dict, ignore_simple_key="intensity_guid")

    # Check that the ignored key is not replaced
    assert proto_message_utils._finder_by_key(dict_var=src_t_dict, key="intensity") == []


def test_replace_guid_elt_list(speos: Speos):
    """Test _replace_guid_elt in a specific case : list of guids like sop_guids."""

    # Example with material : vop guid + sop guids
    p = script.Project(speos=speos)
    mat_feat = script.OptProp(project=p, name="Material.1")
    mat_feat.set_volume_opaque()
    mat_feat.set_surface_mirror()
    mat_feat.commit()

    # Retrieve material instance message and transform it into dict
    mat_i_msg = mat_feat._material_instance
    mat_i_dict = protobuf_message_to_dict(message=mat_i_msg)

    # Check that expected guids are present
    assert mat_i_msg.HasField("vop_guid")
    assert mat_i_msg.vop_guid != ""
    assert len(mat_i_msg.sop_guids) == 1
    assert mat_i_msg.sop_guids[0] != ""

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="vop") == []
    assert proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sops") == []

    # Replace guid elements for this message, by adding new key to the dict with value corresponding to database item
    proto_message_utils._replace_guid_elt(speos_client=speos.client, json_dict=mat_i_dict)

    # Check that the new keys are added
    find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="vop")
    assert len(find) == 1
    assert find[0][0] == ".vop"
    assert find[0][1]["name"] == "Material.1.VOP"

    find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="sops")
    assert len(find) == 1
    assert find[0][0] == ".sops"
    assert len(find[0][1]) == 1
    assert find[0][1][0]["name"] == "Material.1.SOP"

    find = proto_message_utils._finder_by_key(dict_var=mat_i_dict, key="mirror")
    assert len(find) == 1
    assert find[0][0] == ".sops[.name='Material.1.SOP'].mirror"
    assert find[0][1]["reflectance"] == 100.0


def test_replace_guid_elt_complex(speos: Speos):
    """Test _replace_guid_elt in a bigger message like scene."""
    scene_link = speos.client.scenes().create(message=scene.Scene())
    scene_link.load_file(file_uri=os.path.join(test_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"))

    scene_dict = protobuf_message_to_dict(message=scene_link.get())

    # Check that the new keys are not already present before calling _replace_guid_elt
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="part") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="source") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="library") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="sensor") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="simulation") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="vop") == []
    assert proto_message_utils._finder_by_key(dict_var=scene_dict, key="sops") == []

    # To avoid a lot of replacements (part -> bodies -> faces), part_guid is set as ignore_simple_key
    proto_message_utils._replace_guid_elt(speos_client=speos.client, json_dict=scene_dict, ignore_simple_key="part_guid")

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
    assert find[0][0] == ".sources[.name='Dom Source 2 (0) in SOURCE2'].source.surface.spectrum.library"
    assert find[0][1]["file_uri"].endswith("Red Spectrum.spectrum")
    assert find[1][0] == ".sources[.name='Surface Source (0) in SOURCE1'].source.surface.spectrum.library"
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
    assert len(find) == 3
