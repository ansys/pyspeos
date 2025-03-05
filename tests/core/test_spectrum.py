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

"""Test basic using spectrums."""

import os
from pathlib import Path

from ansys.speos.core import Spectrum, Speos
from tests.conftest import test_path


def test_create_spectrum(speos: Speos):
    """Test creation of spectrum."""
    # Default value
    spectrum1 = Spectrum(speos_client=speos.client, name="Spectrum.1").commit()
    assert spectrum1.spectrum_link is not None
    assert spectrum1.spectrum_link.get().HasField("monochromatic")
    assert spectrum1.spectrum_link.get().monochromatic.wavelength == 555

    # monochromatic
    spectrum1.set_monochromatic(wavelength=777).commit()
    assert spectrum1.spectrum_link.get().HasField("monochromatic")
    assert spectrum1.spectrum_link.get().monochromatic.wavelength == 777

    # blackbody
    spectrum1.set_blackbody(temperature=3000).commit()
    assert spectrum1.spectrum_link.get().HasField("blackbody")
    assert spectrum1.spectrum_link.get().blackbody.temperature == 3000

    # sampled
    spectrum1.set_sampled(wavelengths=[300, 400, 500], values=[30, 20, 70]).commit()
    assert spectrum1.spectrum_link.get().HasField("sampled")
    assert spectrum1.spectrum_link.get().sampled.wavelengths == [300, 400, 500]
    assert spectrum1.spectrum_link.get().sampled.values == [30, 20, 70]

    # library
    spectrum1.set_library(
        file_uri=str(Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "Blue Spectrum.spectrum")
    ).commit()
    assert spectrum1.spectrum_link.get().HasField("library")

    # predefined
    spectrum1.set_incandescent().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("incandescent")

    spectrum1.set_warmwhitefluorescent().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("warmwhitefluorescent")

    spectrum1.set_daylightfluorescent().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("daylightfluorescent")

    spectrum1.set_whiteLED().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("whiteLED")

    spectrum1.set_halogen().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("halogen")

    spectrum1.set_metalhalide().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("metalhalide")

    spectrum1.set_highpressuresodium().commit()
    assert spectrum1.spectrum_link.get().HasField("predefined")
    assert spectrum1.spectrum_link.get().predefined.HasField("highpressuresodium")

    spectrum1.delete()


def test_commit_spectrum(speos: Speos):
    """Test commit of spectrum."""
    # Create
    spectrum1 = Spectrum(speos_client=speos.client, name="Spectrum.1")
    spectrum1.set_monochromatic(wavelength=777)
    assert spectrum1.spectrum_link is None

    # Commit
    spectrum1.commit()
    assert spectrum1.spectrum_link is not None
    assert spectrum1.spectrum_link.get().HasField("monochromatic")

    spectrum1.delete()


def test_reset_spectrum(speos: Speos):
    """Test reset of spectrum."""
    # Create + commit
    spectrum1 = Spectrum(speos_client=speos.client, name="Spectrum.1")
    spectrum1.set_monochromatic(wavelength=777).commit()
    assert spectrum1.spectrum_link.get().HasField("monochromatic")

    # Change local data
    spectrum1.set_blackbody()
    assert spectrum1.spectrum_link.get().HasField("monochromatic")
    assert spectrum1._spectrum.HasField("blackbody")

    # Ask for reset
    spectrum1.reset()
    assert spectrum1.spectrum_link.get().HasField("monochromatic")
    assert spectrum1._spectrum.HasField("monochromatic")

    spectrum1.delete()


def test_delete_spectrum(speos: Speos):
    """Test delete of spectrum."""
    # Create + commit
    spectrum1 = Spectrum(speos_client=speos.client, name="Spectrum.1")
    spectrum1.set_monochromatic(wavelength=777).commit()
    assert spectrum1.spectrum_link.get().HasField("monochromatic")
    assert spectrum1._spectrum.HasField("monochromatic")

    # Delete
    spectrum1.delete()
    assert spectrum1.spectrum_link is None
    assert spectrum1._spectrum.HasField("monochromatic")
