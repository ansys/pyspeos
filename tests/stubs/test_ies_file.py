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

"""Unit test for IES service."""

import logging
from pathlib import Path

from ansys.api.speos.intensity_distributions.v1 import ies_pb2, ies_pb2_grpc

from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def create_ies_intensity():
    """Create simple IES file."""
    ies = ies_pb2.IesIntensityDistribution()

    ies.norme_version = 1
    ies.key_words.append("IESNA:LM-63-95")
    ies.key_words.append("[TEST]  \t  \tTest report number and laboratory")
    ies.key_words.append("[MANUFAC]   \tManufacturer of luminaire")
    ies.key_words.append("[LUMCAT]    \tLuminaire catalog number")
    ies.key_words.append("[LUMINAIRE] \tLuminaire description")
    ies.key_words.append("[LAMPCAT]   \tLamp catalogue number")
    ies.key_words.append("[LAMP]      \tLamp description")
    ies.unit = 1
    ies.nb_vertical_angle = 2
    ies.nb_horizontal_angle = 2
    ies.tilt_type = 1
    ies.tilt_geometry = 1
    ies.tilt_nb_pair_angle = 2
    ies.nb_lamp = 1
    ies.photo_type = 1
    ies.lumen_lamp = 4000
    ies.multiplier = 1
    ies.width = 0
    ies.length = 0
    ies.height = 0
    ies.ballast = 1
    ies.future_use = 1
    ies.input_watt = 500
    for i in range(int(ies.nb_vertical_angle)):
        ies.vertical_angle.append(0 + i * 180 / (ies.nb_vertical_angle - 1))
    for i in range(int(ies.nb_horizontal_angle)):
        ies.horizontal_angle.append(0 + i * 360 / (ies.nb_horizontal_angle - 1))
        for j in range(int(ies.nb_vertical_angle)):
            ies.candela_value.append(1000)
    for i in range(int(ies.tilt_nb_pair_angle)):
        ies.tilt_angle.append(0 + i * 90 / (ies.tilt_nb_pair_angle - 1))
        ies.tilt_mult_factor.append(1)
    ies.local_vert = 0

    return ies


def compare_ies_intensities(ies1, ies2):
    """Compare two ies files."""
    if ies1.norme_version != ies2.norme_version:
        return False
    if len(ies1.key_words) != len(ies2.key_words):
        return False
    for i in range(len(ies1.key_words)):
        if ies1.key_words[i] != ies2.key_words[i]:
            return False
    if ies1.unit != ies2.unit:
        return False
    if ies1.nb_vertical_angle != ies2.nb_vertical_angle:
        return False
    if ies1.nb_horizontal_angle != ies2.nb_horizontal_angle:
        return False
    if ies1.tilt_type != ies2.tilt_type:
        return False
    if ies1.tilt_geometry != ies2.tilt_geometry:
        return False
    if ies1.tilt_nb_pair_angle != ies2.tilt_nb_pair_angle:
        return False
    if ies1.nb_lamp != ies2.nb_lamp:
        return False
    if ies1.photo_type != ies2.photo_type:
        return False
    if ies1.lumen_lamp != ies2.lumen_lamp:
        return False
    if ies1.multiplier != ies2.multiplier:
        return False
    if ies1.width != ies2.width:
        return False
    if ies1.length != ies2.length:
        return False
    if ies1.height != ies2.height:
        return False
    if ies1.ballast != ies2.ballast:
        return False
    if ies1.future_use != ies2.future_use:
        return False
    if ies1.input_watt != ies2.input_watt:
        return False
    for i in range(int(ies1.nb_vertical_angle)):
        if ies1.vertical_angle[i] != ies2.vertical_angle[i]:
            return False
    for i in range(int(ies1.nb_horizontal_angle)):
        if ies1.horizontal_angle[i] != ies2.horizontal_angle[i]:
            return False
        for j in range(int(ies1.nb_vertical_angle)):
            if (
                ies1.candela_value[i * ies1.nb_vertical_angle + j]
                != ies2.candela_value[i * ies1.nb_vertical_angle + j]
            ):
                return False
    for i in range(int(ies1.tilt_nb_pair_angle)):
        if ies1.tilt_angle[i] != ies2.tilt_angle[i]:
            return False
        if ies1.tilt_mult_factor[i] != ies2.tilt_mult_factor[i]:
            return False
    if ies1.local_vert != ies2.local_vert:
        return False
    return True


def test_grpc_ies_intensity(speos: Speos):
    """Test to check ies intensity service."""
    stub = ies_pb2_grpc.IesIntensityServiceStub(speos.client.channel)
    save_request = ies_pb2.Save_Request()
    save_request.file_uri = str(Path(test_path) / "tmp2_file.ies")
    load_request = ies_pb2.Load_Request()
    load_request.file_uri = str(Path(test_path) / "tmp2_file.ies")

    logging.debug("Creating ies intensity protocol buffer")
    ies = create_ies_intensity()

    logging.debug("Sending protocol buffer to server")
    ies_pb2.Import_Response()
    stub.Import(ies)

    logging.debug("Writing as {save_request.file_uri}")
    ies_pb2.Save_Response()
    stub.Save(save_request)
    assert helper.does_file_exist(save_request.file_uri)

    logging.debug("Reading {load_response.file_uri}")
    ies_pb2.Load_Response()
    stub.Load(load_request)
    helper.remove_file(load_request.file_uri)

    logging.debug("Exporting ies intensity protocol buffer")
    export_request = ies_pb2.Export_Request()
    ies_pb2.IesIntensityDistribution()
    ies2 = stub.Export(export_request)

    logging.debug("Comparing ies intensity distributions")
    assert compare_ies_intensities(ies, ies2)
