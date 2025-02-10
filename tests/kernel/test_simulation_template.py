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

"""
Test basic sop template database connection.
"""

from ansys.api.speos.simulation.v1 import simulation_template_pb2
from ansys.speos.core.kernel.simulation_template import ProtoSimulationTemplate
from ansys.speos.core.speos import Speos


def test_simulation_template(speos: Speos):
    """Test the simulation template."""
    assert speos.client.healthy is True
    # Get DB
    sim_t_db = (
        speos.client.simulation_templates()
    )  # Create simulation_templates stub from client channel

    # Direct

    direct_t = sim_t_db.create(
        message=ProtoSimulationTemplate(
            name="direct_0",
            description="Direct simulation template",
            direct_mc_simulation_template=simulation_template_pb2.DirectMCSimulationTemplate(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
                dispersion=True,
            ),
        )
    )
    assert direct_t.key != ""

    # Inverse
    inverse_t = sim_t_db.create(
        message=ProtoSimulationTemplate(
            name="inverse_0",
            description="Inverse simulation template",
            inverse_mc_simulation_template=simulation_template_pb2.InverseMCSimulationTemplate(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
                dispersion=False,
                splitting=False,
                number_of_gathering_rays_per_source=1,
                maximum_gathering_error=0,
            ),
        )
    )
    assert inverse_t.key != ""

    # Interactive
    interactive_t = sim_t_db.create(
        message=ProtoSimulationTemplate(
            name="interactive_0",
            description="Interactive simulation template",
            interactive_simulation_template=ProtoSimulationTemplate.Interactive(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
            ),
        )
    )
    assert interactive_t.key != ""

    direct_t.delete()
    inverse_t.delete()
    interactive_t.delete()
