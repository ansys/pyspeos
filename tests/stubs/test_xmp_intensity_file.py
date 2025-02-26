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

"""Unit test for Intensity XMP service."""

import logging
import os

from ansys.api.speos.intensity_distributions.v1 import (
    base_map_template_pb2,
    extended_map_template_pb2,
    xmp_pb2,
    xmp_pb2_grpc,
)
from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def create_xmp_intensity():
    """Function to create simple intensity XMP"""
    xmp = extended_map_template_pb2.ExtendedMap()

    # file description
    xmp.base_data.value_type = base_map_template_pb2.ValueTypes.OptisValueTypeIntensity
    xmp.base_data.unit_type = base_map_template_pb2.UnitTypes.OptisUnitTypeRadiometric
    xmp.base_data.intensity_type = base_map_template_pb2.IntensityTypes.OptisIntensityConoscopic
    # 	xmp.base_data.coordinate_unit = base_map_template_pb2.CoordinateUnits.OptisUnitDefault
    xmp.base_data.colorimetric_standard = base_map_template_pb2.CIEStandard.CIE_STANDARD_UNKNOWN
    xmp.base_data.map_type = base_map_template_pb2.MapTypes.OptisMapTypeExtended
    xmp.base_data.layer_type = base_map_template_pb2.LayerTypes.OptisMapLayerTypeNone

    # file dimensions
    xmp.base_data.x_nb = 10
    xmp.base_data.y_nb = 10
    xmp.base_data.layer_nb = 1
    xmp.base_data.x_min = -5
    xmp.base_data.x_max = 5
    xmp.base_data.y_min = -5
    xmp.base_data.y_max = 5
    xmp.base_data.precision = 1

    # sensor data
    xmp.base_data.is_finite_distance = False
    xmp.base_data.finite_difference_sensor_radius = 0
    xmp.base_data.detector_extent = False
    xmp.base_data.rad_angular_resolution_radius = 0

    # fill layer data
    for l in range(xmp.base_data.layer_nb):
        xmp.base_data.layer.add()
        xmp.base_data.layer[l].layer_name = "0" + str(l)
        xmp.base_data.layer[l].initial_source_power = 1000
        xmp.base_data.layer[l].initial_source_power_watt = 1000
        xmp.base_data.layer[l].initial_source_power_lumen = 1000
        for s in range(10):
            xmp.base_data.layer[l].wavelength.append(400 + 40 * s)
            xmp.base_data.layer[l].value.append(0.1)
        xmp.value.layer.add()
        for y in range(xmp.base_data.y_nb):
            xmp.value.layer[l].y.add()
            for x in range(xmp.base_data.x_nb):
                if x == y:
                    xmp.value.layer[l].y[y].x.append(1)
                else:
                    xmp.value.layer[l].y[y].x.append(0)

    return xmp


def compare_xmp_intensity_distributions(xmp1, xmp2):
    """Function to compar 2 XMPs"""
    if xmp1.base_data.value_type != xmp2.base_data.value_type:
        return False
    if xmp1.base_data.intensity_type != xmp2.base_data.intensity_type:
        return False
    if xmp1.base_data.unit_type != xmp2.base_data.unit_type:
        return False
    # 	if xmp1.coordinate_unit != xmp2.coordinate_unit:
    # 		return False
    if xmp1.base_data.colorimetric_standard != xmp2.base_data.colorimetric_standard:
        return False
    if xmp1.base_data.map_type != xmp2.base_data.map_type:
        return False
    if xmp1.base_data.layer_type != xmp2.base_data.layer_type:
        return False
    if xmp1.base_data.x_nb != xmp2.base_data.x_nb:
        return False
    if xmp1.base_data.y_nb != xmp2.base_data.y_nb:
        return False
    if xmp1.base_data.layer_nb != xmp2.base_data.layer_nb:
        return False
    if xmp1.base_data.x_min != xmp2.base_data.x_min:
        return False
    if xmp1.base_data.x_max != xmp2.base_data.x_max:
        return False
    if xmp1.base_data.y_min != xmp2.base_data.y_min:
        return False
    if xmp1.base_data.y_max != xmp2.base_data.y_max:
        return False
    if xmp1.base_data.precision != xmp2.base_data.precision:
        return False
    for l in range(xmp1.base_data.layer_nb):
        if xmp1.base_data.layer[l].layer_name != xmp2.base_data.layer[l].layer_name:
            return False
        if (
            xmp1.base_data.layer[l].initial_source_power
            != xmp2.base_data.layer[l].initial_source_power
        ):
            return False
        if (
            xmp1.base_data.layer[l].initial_source_power_watt
            != xmp2.base_data.layer[l].initial_source_power_watt
        ):
            return False
        if (
            xmp1.base_data.layer[l].initial_source_power_lumen
            != xmp2.base_data.layer[l].initial_source_power_lumen
        ):
            return False
        for y in range(xmp1.base_data.y_nb):
            for x in range(xmp1.base_data.x_nb):
                if xmp1.value.layer[l].y[y].x[x] != xmp2.value.layer[l].y[y].x[x]:
                    return False
    return True


def test_grpc_xmp_intensity(speos: Speos):
    """Tets to check intensity xmp service"""
    stub = xmp_pb2_grpc.XmpIntensityServiceStub(speos.client.channel)
    load_request = xmp_pb2.Load_Request()
    load_request.file_uri = os.path.join(test_path, "conoscopic_intensity.xmp")
    xmp_pb2.Load_Response()
    save_request = xmp_pb2.Save_Request()
    save_request.file_uri = os.path.join(test_path, "conoscopic_intensity.xmp")
    xmp_pb2.Save_Response()

    logging.debug("Creating xmp intensity protocol buffer")
    xmp = create_xmp_intensity()
    response = xmp_pb2.XmpDistribution()
    response.extended_map.CopyFrom(xmp)

    logging.debug("Sending protocol buffer to server")
    xmp_pb2.Import_Response()
    stub.Import(response)

    logging.debug(f"Saving {save_request.file_uri}")
    stub.Save(save_request)
    assert helper.does_file_exist(save_request.file_uri)

    logging.debug(f"Reading {load_request.file_uri}")
    stub.Load(load_request)
    helper.remove_file(load_request.file_uri)

    logging.debug("Export xmp intensity protocol buffer")
    export_request = xmp_pb2.Export_Request()
    distri = xmp_pb2.XmpDistribution()
    distri = stub.Export(export_request)
    xmp2 = distri.extended_map

    logging.debug("Comparing xmp intensity distributions")
    assert compare_xmp_intensity_distributions(xmp, xmp2)
