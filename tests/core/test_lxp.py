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

"""Test basic using lxp."""

import os
from pathlib import Path

import ansys.speos.core.lxp as lxp
from ansys.speos.core.speos import Speos
from tests.conftest import test_path


def test_light_path_finder_direct(speos: Speos):
    """Test for direct simulation lpf."""
    path = str(Path(test_path) / "basic_DirectSimu.lpf")
    lpf = lxp.LightPathFinder(speos=speos, path=path)
    expected_ray = {
        "nb_impacts": 4,
        "impacts": [
            [0.0, 0.0, 0.0],
            [1.6715503931045532, 15.0, 6.686765193939209],
            [2.4986863136291504, 27.193265914916992, 9.995587348937988],
            [5.421861171722412, 65.0, 21.68793296813965],
        ],
        "wl": 779.0769653320312,
        "body_ids": [2001802324, 2001802324, 2001802324, 3601101451],
        "face_ids": [1815582994, 1815582994, 2122462972, 3866239813],
        "last_direction": [
            0.07366610318422318,
            -0.9527596235275269,
            0.2946563959121704,
        ],
        "intersection_type": [5, 1, 1, -1],
        "sensor_contribution": None,
    }
    assert lpf.nb_traces == 24817
    assert lpf.nb_xmps == 3
    assert lpf.has_sensor_contributions is False  # No contributions stored in Direct simu
    assert len(lpf.sensor_names) == 3
    assert lpf.sensor_names[0] == "Irradiance Sensor (0)"
    assert lpf.sensor_names[2] == "Irradiance Sensor (2)"
    lpf.filter_by_body_ids([3601101451])
    assert len(lpf.filtered_rays) == 18950
    lpf.filter_by_face_ids([3866239813], new=False)
    assert len(lpf.filtered_rays) == 11747
    lpf.filter_error_rays()
    assert len(lpf.filtered_rays) == 0
    assert lpf.rays[50].get() == expected_ray


def test_light_path_finder_inverse(speos: Speos):
    """Test for inverse simulation lpf."""
    path = str(Path(test_path) / "basic_InverseSimu.lpf")
    lpf = lxp.LightPathFinder(speos=speos, path=path)
    expected_ray = {
        "nb_impacts": 7,
        "impacts": [
            [-0.0030556267593055964, 2.9730305671691895, 3.4751179218292236],
            [-0.09766837954521179, 2.7782351970672607, 3.700000047683716],
            [-0.20417508482933044, 2.5589513778686523, 4.164291858673096],
            [-1.4956624507904053, -0.10005591064691544, 7.233987808227539],
            [-0.630171537399292, -0.6335462927818298, 2.9642910957336426],
            [-0.4706628918647766, -0.731867790222168, 1.771950602531433],
            [0.31212788820266724, -0.2756119668483734, 0.19500020146369934],
        ],
        "wl": 564.40966796875,
        "body_ids": [
            3960786643,
            3744252339,
            3744252339,
            2356544899,
            3744252339,
            3744252339,
            3960786643,
        ],
        "face_ids": [
            898898403,
            82490460,
            2224221720,
            4045863240,
            4073137513,
            3944298668,
            2350472451,
        ],
        "last_direction": [0.0, 0.0, 0.0],
        "intersection_type": [5, 1, 1, -1, 1, 1, -1],
        "sensor_contribution": [
            {
                "sensor_id": 0,
                "position": [-0.14824546764179047, 0.3064812525259446],
            }
        ],
    }

    assert lpf.nb_traces == 21044
    assert lpf.nb_xmps == 1
    assert lpf.has_sensor_contributions is True  # No contributions stored in Direct simu
    assert len(lpf.sensor_names) == 1
    assert lpf.sensor_names[0] == "Camera_Perfect_Lens_System_V2:3"
    lpf.filter_by_body_ids([3744252339])
    assert len(lpf.filtered_rays) == 21044
    lpf.filter_by_face_ids([2224221720], new=False)
    assert len(lpf.filtered_rays) == 10422
    lpf.filter_error_rays()
    assert len(lpf.filtered_rays) == 0
    assert lpf.rays[50].get() == expected_ray
