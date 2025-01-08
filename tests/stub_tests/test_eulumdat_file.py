# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""This module allows pytest to perform unit testing.
Usage:
.. code::
   $ pytest
   $ pytest -vx
With coverage.
.. code::
   $ pytest --cov ansys.speos.core
"""
import logging
import os

from ansys.api.speos.intensity_distributions.v1 import eulumdat_pb2, eulumdat_pb2_grpc

from ansys.speos.core.speos import Speos
from conftest import test_path
import helper


def createEulumdatIntensity():
    eulumdat = eulumdat_pb2.EulumdatIntensityDistribution()

    # file information
    eulumdat.file_info.company_identification = "Ansys"
    eulumdat.file_info.measurement_report_number = ""
    eulumdat.file_info.luminaire_name = "Luminaire"
    eulumdat.file_info.luminaire_number = "0000"
    eulumdat.file_info.file_name = ""
    eulumdat.file_info.date = ""

    # angular information
    eulumdat.type_indicator = 3
    eulumdat.symmetry_indicator = 0
    eulumdat.c_plane_number = 24
    eulumdat.distance_c_planes = 10
    eulumdat.g_angle_number = 19
    eulumdat.distance_g_angle = 10

    # luminaire parameters
    eulumdat.diameter_luminaire = 0.0
    eulumdat.width_luminaire = 0.0
    eulumdat.height_luminaire = 0.0

    # luminous area
    eulumdat.diameter_luminous_area = 0.0
    eulumdat.width_luminous_area = 0.0
    eulumdat.height_luminous_area_c0 = 0
    eulumdat.height_luminous_area_c90 = 0
    eulumdat.height_luminous_area_c180 = 0
    eulumdat.height_luminous_area_c270 = 0
    eulumdat.downward_flux_fraction = 50
    eulumdat.light_ouput_ratio = 100
    eulumdat.conversion_factor = 1
    eulumdat.measurement_tilt = 0

    # lamp distribution
    eulumdat.number_standard_set_lamps = 1
    for lmp in range(eulumdat.number_standard_set_lamps):
        lamp_distribution = eulumdat.lamp_distribution.add()
        lamp_distribution.number_lamps = 1
        lamp_distribution.type_lamps = ""
        lamp_distribution.total_luminous_flux = 1
        lamp_distribution.color_temperature = ""
        lamp_distribution.color_rendering_index = ""
        lamp_distribution.wattage_including_ballast = 1.0

    # polar distribution data
    for d in range(10):
        eulumdat.direct_ratio.append(1)
    for cp in range(eulumdat.c_plane_number):
        eulumdat.c_plane.append(1.0)
    for ga in range(eulumdat.g_angle_number):
        eulumdat.g_angle.append(1.0)
    cp_used = eulumdat.c_plane_number
    if eulumdat.symmetry_indicator == 1:
        cp_used = 1
    if eulumdat.symmetry_indicator == 2:
        int(cp_used=eulumdat.c_plane_number / 2) + 1
    if eulumdat.symmetry_indicator == 3:
        int(cp_used=eulumdat.c_plane_number / 2) + 1
    if eulumdat.symmetry_indicator == 4:
        int(cp_used=eulumdat.c_plane_number / 4) + 1
    for cp in range(cp_used):
        for ga in range(eulumdat.g_angle_number):
            eulumdat.luminous_intensity_per_klm.append(1.0)

    return eulumdat


def compareEulumdatIntensities(eulumdat1, eulumdat2):
    # file information
    if eulumdat1.file_info.company_identification != eulumdat2.file_info.company_identification:
        return False
    if eulumdat1.file_info.measurement_report_number != eulumdat2.file_info.measurement_report_number:
        return False
    if eulumdat1.file_info.luminaire_name != eulumdat2.file_info.luminaire_name:
        return False
    if eulumdat1.file_info.luminaire_number != eulumdat2.file_info.luminaire_number:
        return False
    if eulumdat1.file_info.file_name != eulumdat2.file_info.file_name:
        return False
    if eulumdat1.file_info.date != eulumdat2.file_info.date:
        return False

    # angular information
    if eulumdat1.type_indicator != eulumdat2.type_indicator:
        return False
    if eulumdat1.symmetry_indicator != eulumdat2.symmetry_indicator:
        return False
    if eulumdat1.c_plane_number != eulumdat2.c_plane_number:
        return False
    if eulumdat1.distance_c_planes != eulumdat2.distance_c_planes:
        return False
    if eulumdat1.g_angle_number != eulumdat2.g_angle_number:
        return False
    if eulumdat1.distance_g_angle != eulumdat2.distance_g_angle:
        return False

    # luminaire parameters
    if eulumdat1.diameter_luminaire != eulumdat2.diameter_luminaire:
        return False
    if eulumdat1.width_luminaire != eulumdat2.width_luminaire:
        return False
    if eulumdat1.height_luminaire != eulumdat2.height_luminaire:
        return False

    # luminous area
    if eulumdat1.diameter_luminous_area != eulumdat2.diameter_luminous_area:
        return False
    if eulumdat1.width_luminous_area != eulumdat2.width_luminous_area:
        return False
    if eulumdat1.height_luminous_area_c0 != eulumdat2.height_luminous_area_c0:
        return False
    if eulumdat1.height_luminous_area_c90 != eulumdat2.height_luminous_area_c90:
        return False
    if eulumdat1.height_luminous_area_c180 != eulumdat2.height_luminous_area_c180:
        return False
    if eulumdat1.height_luminous_area_c270 != eulumdat2.height_luminous_area_c270:
        return False
    if eulumdat1.downward_flux_fraction != eulumdat2.downward_flux_fraction:
        return False
    if eulumdat1.light_ouput_ratio != eulumdat2.light_ouput_ratio:
        return False
    if eulumdat1.conversion_factor != eulumdat2.conversion_factor:
        return False
    if eulumdat1.measurement_tilt != eulumdat2.measurement_tilt:
        return False

    # lamp distribution
    if eulumdat1.number_standard_set_lamps != eulumdat2.number_standard_set_lamps:
        return False
    for lmp in range(eulumdat1.number_standard_set_lamps):
        if eulumdat1.lamp_distribution[lmp].number_lamps != eulumdat2.lamp_distribution[lmp].number_lamps:
            return False
        if eulumdat1.lamp_distribution[lmp].type_lamps != eulumdat2.lamp_distribution[lmp].type_lamps:
            return False
        if eulumdat1.lamp_distribution[lmp].total_luminous_flux != eulumdat2.lamp_distribution[lmp].total_luminous_flux:
            return False
        if eulumdat1.lamp_distribution[lmp].color_temperature != eulumdat2.lamp_distribution[lmp].color_temperature:
            return False
        if eulumdat1.lamp_distribution[lmp].color_rendering_index != eulumdat2.lamp_distribution[lmp].color_rendering_index:
            return False
        if eulumdat1.lamp_distribution[lmp].wattage_including_ballast != eulumdat2.lamp_distribution[lmp].wattage_including_ballast:
            return False

    # polar distribution data
    for d in range(10):
        if eulumdat1.direct_ratio[d] != eulumdat2.direct_ratio[d]:
            return False
    for cp in range(eulumdat1.c_plane_number):
        if eulumdat1.c_plane[cp] != eulumdat2.c_plane[cp]:
            return False
    for ga in range(eulumdat1.g_angle_number):
        if eulumdat1.g_angle[ga] != eulumdat2.g_angle[ga]:
            return False
    if len(eulumdat1.luminous_intensity_per_klm) != len(eulumdat2.luminous_intensity_per_klm):
        return False
    for lm in range(len(eulumdat1.luminous_intensity_per_klm)):
        if eulumdat1.luminous_intensity_per_klm[lm] != eulumdat2.luminous_intensity_per_klm[lm]:
            return False

    return True


def test_grpc_eulumdat_intensity(speos: Speos):
    stub = eulumdat_pb2_grpc.EulumdatIntensityServiceStub(speos.client.channel)
    save_name = eulumdat_pb2.Save_Request()
    save_name.file_uri = os.path.join(test_path, "eulumdat_tmp00.ldt")
    load_name = eulumdat_pb2.Load_Request()
    load_name.file_uri = os.path.join(test_path, "eulumdat_tmp00.ldt")

    logging.debug("Creating eulumdat intensity protocol buffer")
    eulumdat = createEulumdatIntensity()

    logging.debug("Sending protocol buffer to server")
    import_response = eulumdat_pb2.Import_Response()
    import_response = stub.Import(eulumdat)

    logging.debug("Writing as {save_name.file_uri}")
    save_response = eulumdat_pb2.Save_Response()
    save_response = stub.Save(save_name)
    assert helper.does_file_exist(save_name.file_uri)

    logging.debug("Reading {load_name.file_uri} back")
    load_response = eulumdat_pb2.Load_Response()
    load_response = stub.Load(load_name)
    helper.remove_file(load_name.file_uri)

    logging.debug("Exporting eulumdat intensity protocol buffer")
    export_request = eulumdat_pb2.Export_Request()
    eulumdat2 = stub.Export(export_request)

    logging.debug("Check equal")
    assert compareEulumdatIntensities(eulumdat, eulumdat2)
