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
from pathlib import Path

from ansys.api.speos.intensity_distributions.v1 import (
    base_map_template_pb2,
    spectral_map_template_pb2,
    xmp_pb2,
    xmp_pb2_grpc,
)
from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def createXmpIntensity():
    xmp = spectral_map_template_pb2.SpectralMap()

    # file description
    xmp.base_data.value_type = base_map_template_pb2.ValueTypes.OptisValueTypeIntensity
    xmp.base_data.unit_type = base_map_template_pb2.UnitTypes.OptisUnitTypeRadiometric
    xmp.base_data.intensity_type = base_map_template_pb2.IntensityTypes.OptisIntensityConoscopic
    # 	xmp.base_data.coordinate_unit = base_map_template_pb2.CoordinateUnits.OptisUnitDefault
    xmp.base_data.colorimetric_standard = base_map_template_pb2.CIEStandard.CIE_STANDARD_UNKNOWN
    xmp.base_data.map_type = base_map_template_pb2.MapTypes.OptisMapTypeSpectral
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

    # spectral data
    xmp.wavelength_nb = 5
    xmp.wavelength_min = 380.0
    xmp.wavelength_max = 780.0
    xmp.spectral_data_loaded = True
    xmp.depth_data_loaded = True

    # fill layer data
    for iter_layer in range(xmp.base_data.layer_nb):
        xmp.base_data.layer.add()
        xmp.base_data.layer[iter_layer].layer_name = "0" + str(iter_layer)
        xmp.base_data.layer[iter_layer].initial_source_power = 1000
        xmp.base_data.layer[iter_layer].initial_source_power_watt = 1000
        xmp.base_data.layer[iter_layer].initial_source_power_lumen = 1000
        for s in range(xmp.wavelength_nb):
            xmp.base_data.layer[iter_layer].wavelength.append(380 + 80 * s)
            xmp.base_data.layer[iter_layer].value.append(0.1)

        xmp.spectral_value.layer.add()
        for w in range(xmp.wavelength_nb):
            xmp.spectral_value.layer[iter_layer].wavelength.add()
            for y in range(xmp.base_data.y_nb):
                xmp.spectral_value.layer[iter_layer].wavelength[w].y.add()
                for x in range(xmp.base_data.x_nb):
                    xmp.spectral_value.layer[iter_layer].wavelength[w].y[y].x.append(1.0)

        xmp.color_value.layer.add()
        for y in range(xmp.base_data.y_nb):
            xmp.color_value.layer[iter_layer].y.add()
            for x in range(xmp.base_data.x_nb):
                xmp.color_value.layer[iter_layer].y[y].x.add()
                xmp.color_value.layer[iter_layer].y[y].x[x].color_x = 0.0
                xmp.color_value.layer[iter_layer].y[y].x[x].color_y = 0.0
                xmp.color_value.layer[iter_layer].y[y].x[x].color_z = 0.0
                xmp.color_value.layer[iter_layer].y[y].x[x].radio = 0.0
                if x == y:
                    xmp.color_value.layer[iter_layer].y[y].x[x].color_x = 100
                    xmp.color_value.layer[iter_layer].y[y].x[x].color_y = 100.0
                    xmp.color_value.layer[iter_layer].y[y].x[x].color_z = 100.0
                    xmp.color_value.layer[iter_layer].y[y].x[x].radio = 100.0

    for y in range(xmp.base_data.y_nb):
        xmp.depth_value.y.add()
        for x in range(xmp.base_data.x_nb):
            xmp.depth_value.y[y].x.append(1.0)

    return xmp


def compareXmpIntensityDistributions(xmp1, xmp2):
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
    if xmp1.wavelength_nb != xmp2.wavelength_nb:
        return False
    if xmp1.wavelength_min != xmp2.wavelength_min:
        return False
    if xmp1.wavelength_max != xmp2.wavelength_max:
        return False
    if xmp1.spectral_data_loaded != xmp2.spectral_data_loaded:
        return False
    if xmp1.depth_data_loaded != xmp2.depth_data_loaded:
        return False
    for iter_layer in range(xmp1.base_data.layer_nb):
        if (
            xmp1.base_data.layer[iter_layer].layer_name
            != xmp2.base_data.layer[iter_layer].layer_name
        ):
            return False
        if (
            xmp1.base_data.layer[iter_layer].initial_source_power
            != xmp2.base_data.layer[iter_layer].initial_source_power
        ):
            return False
        if (
            xmp1.base_data.layer[iter_layer].initial_source_power_watt
            != xmp2.base_data.layer[iter_layer].initial_source_power_watt
        ):
            return False
        if (
            xmp1.base_data.layer[iter_layer].initial_source_power_lumen
            != xmp2.base_data.layer[iter_layer].initial_source_power_lumen
        ):
            return False
        for w in range(xmp1.wavelength_nb):
            if (
                xmp1.base_data.layer[iter_layer].wavelength[w]
                != xmp2.base_data.layer[iter_layer].wavelength[w]
            ):
                return False
            if (
                xmp1.base_data.layer[iter_layer].value[w]
                != xmp2.base_data.layer[iter_layer].value[w]
            ):
                return False
            for y in range(xmp1.base_data.y_nb):
                for x in range(xmp1.base_data.x_nb):
                    if (
                        xmp1.spectral_value.layer[iter_layer].wavelength[w].y[y].x[x]
                        != xmp2.spectral_value.layer[iter_layer].wavelength[w].y[y].x[x]
                    ):
                        return False
        for y in range(xmp1.base_data.y_nb):
            for x in range(xmp1.base_data.x_nb):
                if (
                    xmp1.color_value.layer[iter_layer].y[y].x[x].color_x
                    != xmp2.color_value.layer[iter_layer].y[y].x[x].color_x
                ):
                    return False
                if (
                    xmp1.color_value.layer[iter_layer].y[y].x[x].color_y
                    != xmp2.color_value.layer[iter_layer].y[y].x[x].color_y
                ):
                    return False
                if (
                    xmp1.color_value.layer[iter_layer].y[y].x[x].color_z
                    != xmp2.color_value.layer[iter_layer].y[y].x[x].color_z
                ):
                    return False
                if (
                    xmp1.color_value.layer[iter_layer].y[y].x[x].radio
                    != xmp2.color_value.layer[iter_layer].y[y].x[x].radio
                ):
                    return False
        for y in range(xmp1.base_data.y_nb):
            for x in range(xmp1.base_data.x_nb):
                if xmp1.depth_value.y[y].x[x] != xmp2.depth_value.y[y].x[x]:
                    return False
    return True


def test_grpc_xmp_intensity(speos: Speos):
    stub = xmp_pb2_grpc.XmpIntensityServiceStub(speos.client.channel)
    load_request = xmp_pb2.Load_Request()
    load_request.file_uri = str(Path(test_path).joinpath("conoscopic_intensity_spectral.xmp"))
    xmp_pb2.Load_Response()
    save_request = xmp_pb2.Save_Request()
    save_request.file_uri = str(Path(test_path).joinpath("conoscopic_intensity_spectral.xmp"))
    xmp_pb2.Save_Response()

    logging.debug("Creating xmp intensity protocol buffer")
    xmp = createXmpIntensity()
    request = xmp_pb2.XmpDistribution()
    request.spectral_map.CopyFrom(xmp)

    logging.debug("Sending protocol buffer to server")
    xmp_pb2.Import_Response()
    stub.Import(request)

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
    xmp2 = distri.spectral_map

    logging.debug("Comparing xmp intensity distributions")
    assert compareXmpIntensityDistributions(xmp, xmp2)
