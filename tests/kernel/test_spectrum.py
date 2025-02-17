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
Test basic spectrum database connection.
"""

import os

from tests.conftest import test_path

from ansys.speos.core.kernel.spectrum import ProtoSpectrum
from ansys.speos.core.speos import Speos


def test_client_spectrum_init(speos: Speos):
    """Test the abstraction layer for spectrums. How to use SpectrumLink objects"""
    assert speos.client.healthy is True
    # Get DB
    spec_db = speos.client.spectrums()  # Create spectrum stub from client channel

    # Create SpectrumLink:
    s_ph_data = ProtoSpectrum()
    s_ph_data.name = "predefined_halogen_0"
    s_ph_data.description = "Predefined spectrum"
    s_ph_data.predefined.halogen.SetInParent()
    s_ph = spec_db.create(message=s_ph_data)  # at this step the spectrum is stored in DB
    assert s_ph.key != ""
    assert s_ph.stub is not None

    # Create SpectrumLink
    s_bb_5321 = spec_db.create(
        message=ProtoSpectrum(
            name="blackbody_0",
            description="Blackbody spectrum",
            blackbody=ProtoSpectrum.BlackBody(temperature=5321.0),
        )
    )  # the spectrum created is stored in DB
    # Get data
    s_bb_5321_data = s_bb_5321.get()
    assert s_bb_5321_data.blackbody.temperature == 5321
    # Update data
    s_bb_5321_data.blackbody.temperature = 5326  # data modified only locally, not in DB
    s_bb_5321.set(s_bb_5321_data)  # data modified in DB thanks to set method
    s_bb_5321_data = (
        s_bb_5321.get()
    )  # retrieve value from DB to verify that it is correctly updated
    assert s_bb_5321_data.blackbody.temperature == 5326
    # Delete
    s_bb_5321.delete()  # Delete from DB

    # Create SpectrumLink
    s_m_659 = spec_db.create(
        ProtoSpectrum(
            name="monochr_0",
            description="Monochromatic spectrum",
            monochromatic=ProtoSpectrum.Monochromatic(wavelength=659.0),
        )
    )
    # Duplicate = same data but different keys
    s_m_659_bis = spec_db.create(s_m_659.get())
    assert s_m_659_bis.stub == s_m_659.stub
    assert s_m_659_bis.key != s_m_659.key
    assert s_m_659_bis.get() == s_m_659.get()

    # Delete all spectrums from DB
    for spec in spec_db.list():
        spec.delete()


def test_spectrum(speos: Speos):
    """Test spectrum."""
    assert speos.client.healthy is True
    # Get DB
    spec_db = speos.client.spectrums()  # Create spectrum stub from client channel

    # Monochromatic
    spec_mono = spec_db.create(
        ProtoSpectrum(
            name="monochr_1",
            description="Monochromatic spectrum",
            monochromatic=ProtoSpectrum.Monochromatic(wavelength=659.0),
        )
    )
    assert spec_mono.key != ""

    # Blackbody
    spec_blackbody = spec_db.create(
        message=ProtoSpectrum(
            name="blackbody_1",
            description="Blackbody spectrum",
            blackbody=ProtoSpectrum.BlackBody(temperature=5321.0),
        )
    )
    assert spec_blackbody.key != ""

    # Sampled
    s_sampled = spec_db.create(
        message=ProtoSpectrum(
            name="sampled_1",
            description="Sampled spectrum",
            sampled=ProtoSpectrum.Sampled(
                wavelengths=[500.0, 550.0, 600.0], values=[20.5, 100.0, 15.6]
            ),
        )
    )
    assert s_sampled.key != ""

    # Library
    spectrum_path = os.path.join(
        test_path, os.path.join("CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    s_lib = spec_db.create(
        message=ProtoSpectrum(
            name="library_1",
            description="Library spectrum",
            library=ProtoSpectrum.Library(file_uri=spectrum_path),
        )
    )
    assert s_lib.key != ""

    # Predefined
    s_predefined_incandescent = spec_db.create(
        ProtoSpectrum(
            name="predefined_1",
            description="Predefined incandescent spectrum",
            predefined=ProtoSpectrum.Predefined(incandescent=ProtoSpectrum.Incandescent()),
        )
    )
    assert s_predefined_incandescent.key != ""

    # Delete all spectrums from DB
    for spec in spec_db.list():
        spec.delete()
