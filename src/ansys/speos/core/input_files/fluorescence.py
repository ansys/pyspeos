# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Models Speos fluorescent pigment files and pigment data in material files."""

from __future__ import annotations

from typing import ClassVar, List, Sequence

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _finite_number,
    _property_name,
    _single_line,
    _ValueComparable,
    format_number,
)
from ansys.speos.core.input_files.spectrum_file import SpectrumFile

_DEFAULT_SPECTRUM_DESCRIPTION = "Default spectrum : edit or load -->"
_DEFAULT_ABSORPTION_WAVELENGTHS = (350.0, 360.0, 370.0)
_DEFAULT_ABSORPTION_VALUES = (0.0, 0.1, 0.0)
_DEFAULT_EFFICIENCY_WAVELENGTHS = (350.0, 360.0, 370.0)
_DEFAULT_EFFICIENCY_VALUES = (95.0, 95.0, 95.0)
_DEFAULT_EXCITANCE_WAVELENGTHS = (350.0, 360.0, 370.0)
_DEFAULT_EXCITANCE_VALUES = (0.0, 0.095, 0.0)
_DEFAULT_EMISSION_WAVELENGTHS = (400.0, 500.0, 600.0)
_DEFAULT_EMISSION_VALUES = (0.0, 100.0, 0.0)


def _pigment_spectrum(value: SpectrumFile, *, percent: bool) -> SpectrumFile:
    if not isinstance(value, SpectrumFile):
        raise TypeError("Pigment spectra must be SpectrumFile instances.")
    value.percent = percent
    return value


def _default_spectrum(wavelengths: Sequence[float], values: Sequence[float]) -> SpectrumFile:
    return SpectrumFile(
        wavelengths=wavelengths, values=values, description=_DEFAULT_SPECTRUM_DESCRIPTION
    )


def _spectrum_to_lines(spectrum: SpectrumFile, *, standalone_dye: bool) -> List[str]:
    # Standalone .dye files insert a "0" record after each spectrum header.
    return [SpectrumFile.HEADER, *(["0"] if standalone_dye else []), *spectrum._to_lines()]


def _spectrum_from_lines(
    reader: LineReader, *, standalone_dye: bool, percent: bool = True
) -> SpectrumFile:
    header = reader.next_data_line()
    if header.lower() != SpectrumFile.HEADER.lower():
        raise reader.error(f"expected a spectrum header, got {header!r}.")
    if standalone_dye and reader.next_int() != 0:
        raise reader.error("unsupported standalone dye spectrum option.")
    return SpectrumFile._from_lines(reader, percent=percent)


# Absorption and excitance spectra are in mm-1; efficiency and emission are percentages.
_SPECTRUM_PERCENT = (False, True, False, True)


class FluorescentPigmentFile(SpeosTextFileFormat):
    """Speos ``*.dye`` pigment, with sampled absorption and emission spectra.

    The default spectra and settings match the default entry in the Speos dye editor.
    The model supports the editor's default unscattering pigment with isotropic emission.
    Other scattering and emission-distribution models are not yet represented. Changing
    a spectrum does not recalculate the other spectra; keep derived data consistent.

    Each spectrum is a :class:`ansys.speos.core.input_files.spectrum_file.SpectrumFile`,
    so an existing ``*.spectrum`` file can be loaded and assigned directly. Assigning a
    spectrum sets its :attr:`SpectrumFile.percent` attribute to match its role: ``False``
    for the absorption and excitance spectra, in mm-1, whose values may exceed 100, and
    ``True`` for the efficiency and emission spectra, in percent.

    Parameters
    ----------
    description : str, optional
        Pigment description. Defaults to ``"Fluorescent pigment"``.
    absorption_spectrum : SpectrumFile, optional
        Absorption spectrum, in mm-1. Values may exceed 100.
    efficiency_spectrum : SpectrumFile, optional
        Quantum-efficiency spectrum, in percent.
    excitance_spectrum : SpectrumFile, optional
        Excitance spectrum, in mm-1. Values may exceed 100.
    emission_spectrum : SpectrumFile, optional
        Emission spectrum, in percent.
    measured_concentration : float, optional
        Concentration at which the dye was measured. Defaults to ``1.0``.
    spectrum_selection_code : int, optional
        Spectrum selection code stored by the dye editor: ``0``, ``1``, or ``2``.
        Defaults to ``0``.
    """

    def __init__(
        self,
        description: str = "Fluorescent pigment",
        absorption_spectrum: SpectrumFile | None = None,
        efficiency_spectrum: SpectrumFile | None = None,
        excitance_spectrum: SpectrumFile | None = None,
        emission_spectrum: SpectrumFile | None = None,
        measured_concentration: float = 1.0,
        spectrum_selection_code: int = 0,
    ) -> None:
        self.description = description
        self.measured_concentration = measured_concentration
        self.spectrum_selection_code = spectrum_selection_code
        self.absorption_spectrum = (
            absorption_spectrum
            if absorption_spectrum is not None
            else _default_spectrum(_DEFAULT_ABSORPTION_WAVELENGTHS, _DEFAULT_ABSORPTION_VALUES)
        )
        self.efficiency_spectrum = (
            efficiency_spectrum
            if efficiency_spectrum is not None
            else _default_spectrum(_DEFAULT_EFFICIENCY_WAVELENGTHS, _DEFAULT_EFFICIENCY_VALUES)
        )
        self.excitance_spectrum = (
            excitance_spectrum
            if excitance_spectrum is not None
            else _default_spectrum(_DEFAULT_EXCITANCE_WAVELENGTHS, _DEFAULT_EXCITANCE_VALUES)
        )
        self.emission_spectrum = (
            emission_spectrum
            if emission_spectrum is not None
            else _default_spectrum(_DEFAULT_EMISSION_WAVELENGTHS, _DEFAULT_EMISSION_VALUES)
        )

    @property
    def description(self) -> str:
        """Single-line pigment description.

        Parameters
        ----------
        value : str
            New description.

        Returns
        -------
        str
            Pigment description.
        """
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = _single_line(value)

    @property
    def measured_concentration(self) -> float:
        """Concentration at which the dye was measured.

        Parameters
        ----------
        value : float
            New measured concentration.

        Returns
        -------
        float
            Measured concentration.
        """
        return self._measured_concentration

    @measured_concentration.setter
    def measured_concentration(self, value: float) -> None:
        self._measured_concentration = _finite_number(
            _property_name(FluorescentPigmentFile.measured_concentration), value
        )

    @property
    def spectrum_selection_code(self) -> int:
        """Spectrum selection code stored by the Speos dye editor.

        Parameters
        ----------
        value : int
            Spectrum selection code ``0``, ``1``, or ``2``.

        Returns
        -------
        int
            Spectrum selection code.
        """
        return self._spectrum_selection_code

    @spectrum_selection_code.setter
    def spectrum_selection_code(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("spectrum_selection_code must be an integer.")
        if value not in (0, 1, 2):
            raise ValueError("Only spectrum selection codes 0, 1, and 2 are supported.")
        self._spectrum_selection_code = value

    @property
    def absorption_spectrum(self) -> SpectrumFile:
        """Shared absorption spectrum, in mm-1.

        Parameters
        ----------
        value : SpectrumFile
            New absorption spectrum.

        Returns
        -------
        SpectrumFile
            Absorption spectrum.
        """
        return self._absorption_spectrum

    @absorption_spectrum.setter
    def absorption_spectrum(self, value: SpectrumFile) -> None:
        self._absorption_spectrum = _pigment_spectrum(value, percent=False)

    @property
    def efficiency_spectrum(self) -> SpectrumFile:
        """Shared quantum-efficiency spectrum, in percent.

        Parameters
        ----------
        value : SpectrumFile
            New efficiency spectrum.

        Returns
        -------
        SpectrumFile
            Efficiency spectrum.
        """
        return self._efficiency_spectrum

    @efficiency_spectrum.setter
    def efficiency_spectrum(self, value: SpectrumFile) -> None:
        self._efficiency_spectrum = _pigment_spectrum(value, percent=True)

    @property
    def excitance_spectrum(self) -> SpectrumFile:
        """Shared excitance spectrum, in mm-1.

        Parameters
        ----------
        value : SpectrumFile
            New excitance spectrum.

        Returns
        -------
        SpectrumFile
            Excitance spectrum.
        """
        return self._excitance_spectrum

    @excitance_spectrum.setter
    def excitance_spectrum(self, value: SpectrumFile) -> None:
        self._excitance_spectrum = _pigment_spectrum(value, percent=False)

    @property
    def emission_spectrum(self) -> SpectrumFile:
        """Shared emission spectrum, in percent.

        Parameters
        ----------
        value : SpectrumFile
            New emission spectrum.

        Returns
        -------
        SpectrumFile
            Emission spectrum.
        """
        return self._emission_spectrum

    @emission_spectrum.setter
    def emission_spectrum(self, value: SpectrumFile) -> None:
        self._emission_spectrum = _pigment_spectrum(value, percent=True)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        "description",
        "measured_concentration",
        "spectrum_selection_code",
        "absorption_spectrum",
        "efficiency_spectrum",
        "excitance_spectrum",
        "emission_spectrum",
    )

    EXTENSION = ".dye"
    HEADER = "OPTIS - Fluorescent pigment file v3.000000"
    HEADER_PREFIX = HEADER
    EMBEDDED_HEADER = "OPTIS - Fluorescent pigment file v3.0"

    def validate(self) -> None:
        """Check that all four pigment spectra are complete."""
        for spectrum in (
            self.absorption_spectrum,
            self.efficiency_spectrum,
            self.excitance_spectrum,
            self.emission_spectrum,
        ):
            spectrum.validate()

    def _to_lines(self, *, embedded: bool = False) -> List[str]:
        lines = [
            self.description,
            "ISOTROPIC",
            format_number(self.measured_concentration),
            str(self.spectrum_selection_code),
        ]
        for spectrum in (
            self.absorption_spectrum,
            self.efficiency_spectrum,
            self.excitance_spectrum,
            self.emission_spectrum,
        ):
            lines.extend(_spectrum_to_lines(spectrum, standalone_dye=not embedded))
        lines.extend(("0", "0"))
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader, *, embedded: bool = False) -> FluorescentPigmentFile:
        description = reader.next_line()
        particle_type = reader.next_data_line()
        if particle_type != "ISOTROPIC":
            raise reader.error(f"unsupported pigment particle type {particle_type!r}.")
        measured_concentration = reader.next_floats(count=1)[0]
        spectrum_selection_code = reader.next_int(minimum=0)
        spectra = [
            _spectrum_from_lines(reader, standalone_dye=not embedded, percent=percent)
            for percent in _SPECTRUM_PERCENT
        ]
        if reader.next_int() != 0 or reader.next_int() != 0:
            raise reader.error("unsupported fluorescent pigment scattering or emission settings.")
        return cls(
            description=description,
            absorption_spectrum=spectra[0],
            efficiency_spectrum=spectra[1],
            excitance_spectrum=spectra[2],
            emission_spectrum=spectra[3],
            measured_concentration=measured_concentration,
            spectrum_selection_code=spectrum_selection_code,
        )


class FluorescentPigment(_ValueComparable):
    """A dye entry in the fluorescence table of a material file.

    Parameters
    ----------
    dye : FluorescentPigmentFile, optional
        Pigment spectra and properties. A new default pigment is created when omitted.
    measured_concentration : float, optional
        Concentration at which the dye was measured. If omitted, uses the concentration
        already stored in ``dye`` (``1.0`` for a new default dye).
    user_concentration : float, optional
        Concentration used by the material. Defaults to ``1.0``.
    """

    def __init__(
        self,
        dye: FluorescentPigmentFile | None = None,
        measured_concentration: float | None = None,
        user_concentration: float = 1.0,
    ) -> None:
        self.dye = dye if dye is not None else FluorescentPigmentFile()
        if measured_concentration is not None:
            self.measured_concentration = measured_concentration
        self.user_concentration = user_concentration

    @property
    def measured_concentration(self) -> float:
        """Concentration at which the dye was measured.

        Parameters
        ----------
        value : float
            New measured concentration, also stored in the shared dye.

        Returns
        -------
        float
            Measured concentration.
        """
        return self.dye.measured_concentration

    @measured_concentration.setter
    def measured_concentration(self, value: float) -> None:
        self.dye.measured_concentration = value

    @property
    def user_concentration(self) -> float:
        """Concentration used by the material.

        Parameters
        ----------
        value : float
            New user concentration.

        Returns
        -------
        float
            User concentration.
        """
        return self._user_concentration

    @user_concentration.setter
    def user_concentration(self, value: float) -> None:
        self._user_concentration = _finite_number(
            _property_name(FluorescentPigment.user_concentration), value
        )

    @property
    def dye(self) -> FluorescentPigmentFile:
        """Shared pigment model.

        Parameters
        ----------
        value : FluorescentPigmentFile
            New pigment model.

        Returns
        -------
        FluorescentPigmentFile
            Pigment model.
        """
        return self._dye

    @dye.setter
    def dye(self, value: FluorescentPigmentFile) -> None:
        if not isinstance(value, FluorescentPigmentFile):
            raise TypeError("dye must be a FluorescentPigmentFile.")
        self._dye = value

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(dye),
        _property_name(measured_concentration),
        _property_name(user_concentration),
    )

    def validate(self) -> None:
        """Check the concentrations and pigment data."""
        _finite_number(
            _property_name(FluorescentPigment.measured_concentration),
            self.measured_concentration,
        )
        _finite_number(
            _property_name(FluorescentPigment.user_concentration), self.user_concentration
        )
        self.dye.validate()

    def _to_lines(self) -> List[str]:
        return [
            format_number(self.user_concentration),
            self.dye.EMBEDDED_HEADER,
            *self.dye._to_lines(embedded=True),
        ]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> FluorescentPigment:
        user_concentration = reader.next_floats(count=1)[0]
        header = reader.next_data_line()
        if header.lower() != FluorescentPigmentFile.EMBEDDED_HEADER.lower():
            raise reader.error(f"expected a fluorescent pigment header, got {header!r}.")
        dye = FluorescentPigmentFile._from_lines(reader, embedded=True)
        return cls(
            dye=dye,
            user_concentration=user_concentration,
        )
