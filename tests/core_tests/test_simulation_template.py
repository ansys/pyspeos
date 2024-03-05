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
Test basic sop template database connection.
"""
import pytest

from ansys.speos.core.simulation_template import SimulationTemplateFactory
from ansys.speos.core.speos import Speos


def test_simulation_template_factory_default(speos: Speos):
    """Test the simulation template factory - default parameters."""
    assert speos.client.healthy is True
    # Get DB
    sim_t_db = speos.client.simulation_templates()  # Create simulation_templates stub from client channel

    # Direct
    direct_t = sim_t_db.create(
        message=SimulationTemplateFactory.direct_mc(name="direct_0", description="Direct simulation template with default parameters")
    )
    assert direct_t.key != ""

    # Inverse
    inverse_t = sim_t_db.create(
        message=SimulationTemplateFactory.inverse_mc(name="inverse_0", description="Inverse simulation template with default parameters")
    )
    assert inverse_t.key != ""

    # Interactive
    interactive_t = sim_t_db.create(
        message=SimulationTemplateFactory.interactive(
            name="interactive_0", description="Interactive simulation template with default parameters"
        )
    )
    assert interactive_t.key != ""

    direct_t.delete()
    inverse_t.delete()
    interactive_t.delete()


def test_simulation_template_factory(speos: Speos):
    """Test the simulation template factory."""
    assert speos.client.healthy is True
    # Get DB
    sim_t_db = speos.client.simulation_templates()  # Create simulation_templates stub from client channel

    # Direct simulation without precising ambiant material -> will be air.
    direct_t = sim_t_db.create(
        message=SimulationTemplateFactory.direct_mc(
            name="direct_1",
            description="Direct simulation template with default parameters",
            common_propagation_parameters=SimulationTemplateFactory.CommonPropagationParameters(
                geom_distance_tolerance=0.04,
                max_impact=80,
                colorimetric_standard=SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931,
                weight=SimulationTemplateFactory.CommonPropagationParameters.Weight(minimum_energy_percentage=0.6),
            ),
            dispersion=True,
            fast_transmission_gathering=True,
        )
    )
    assert direct_t.key != ""

    # Inverse
    inverse_t = sim_t_db.create(
        message=SimulationTemplateFactory.inverse_mc(
            name="inverse_1",
            description="Inverse simulation template with default parameters",
            common_propagation_parameters=SimulationTemplateFactory.CommonPropagationParameters(
                geom_distance_tolerance=0.04,
                max_impact=80,
                colorimetric_standard=SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931,
                weight=SimulationTemplateFactory.CommonPropagationParameters.Weight(minimum_energy_percentage=0.6),
            ),
            dispersion=False,
            splitting=False,
            number_of_gathering_rays_per_source=1,
            maximum_gathering_error=0,
            fast_transmission_gathering=True,
        )
    )
    assert inverse_t.key != ""

    # Interactive
    interactive_t = sim_t_db.create(
        message=SimulationTemplateFactory.interactive(
            name="interactive_1",
            description="Interactive simulation template with default parameters",
            common_propagation_parameters=SimulationTemplateFactory.CommonPropagationParameters(
                geom_distance_tolerance=0.04,
                max_impact=80,
                colorimetric_standard=SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931,
                weight=SimulationTemplateFactory.CommonPropagationParameters.Weight(minimum_energy_percentage=0.6),
            ),
        )
    )
    assert interactive_t.key != ""

    # Example of wrong simulation template : number_of_gathering_rays_per_source < 0
    with pytest.raises(ValueError) as exc:
        sim_t_db.create(
            message=SimulationTemplateFactory.inverse_mc(
                name="inverse_1",
                description="Inverse simulation template with default parameters",
                number_of_gathering_rays_per_source=-1,
            )
        )
    assert exc.value.args[0] == "Value out of range: -1"

    direct_t.delete()
    inverse_t.delete()
    interactive_t.delete()
