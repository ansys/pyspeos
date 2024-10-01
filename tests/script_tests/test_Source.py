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
Test basic using source from script layer.
"""

import os

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_create_luminaire_source(speos: Speos):
    """Test creation of luminaire source."""
    p = script.Project(speos=speos)

    # Default value
    source1 = p.create_source(name="Luminaire.1")
    source1.set_luminaire()
    source1.set_luminaire_properties()
    assert source1._source_template.HasField("luminaire")
    assert source1._source_template.luminaire.intensity_file_uri == ""
    assert source1._source_template.luminaire.HasField("flux_from_intensity_file")
    assert source1._type._spectrum._spectrum.HasField("predefined")
    assert source1._type._spectrum._spectrum.predefined.HasField("incandescent")
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # intensity_file_uri
    source1.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().luminaire.intensity_file_uri != ""

    # spectrum
    source1.set_luminaire().set_spectrum().set_halogen()
    source1.commit()
    spectrum = speos.client.get_item(key=source1.source_template_link.get().luminaire.spectrum_guid)
    assert spectrum.get().HasField("predefined")
    assert spectrum.get().predefined.HasField("halogen")

    # flux luminous_flux
    source1.set_luminaire().set_flux_luminous(value=650)
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("luminous_flux")
    assert source1.source_template_link.get().luminaire.luminous_flux.luminous_value == 650

    # flux radiant_flux
    source1.set_luminaire().set_flux_radiant(value=1.2)
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("radiant_flux")
    assert source1.source_template_link.get().luminaire.radiant_flux.radiant_value == 1.2

    # flux_from_intensity_file
    source1.set_luminaire().set_flux_from_intensity_file()
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("flux_from_intensity_file")

    # Properties
    source1.set_luminaire_properties(axis_system=[10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    source1.commit()
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].luminaire_properties.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    source1.delete()
    assert len(p.scene_link.get().sources) == 0
