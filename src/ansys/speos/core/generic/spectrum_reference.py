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

"""Internal helpers for spectrum references stored as GUIDs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from ansys.speos.core.spectrum import Spectrum


class _SpectrumReference:
    """Internal helper for spectrum references.

    This helper centralizes the shared logic used by source and sensor features to keep a
    :class:`~ansys.speos.core.spectrum.Spectrum` instance synchronized with a protobuf GUID field.

    Parameters
    ----------
    name : str
        Name of the referenced spectrum.
    message_to_complete : Any
        Protobuf message containing the spectrum GUID field.
    field_name_to_complete : str, optional
        Name of the spectrum GUID field in ``message_to_complete``.
        The default is ``""``, which maps to ``"spectrum_guid"``.
    spectrum_guid : str, optional
        Existing spectrum GUID to bind to.
        The default is ``""``.
    project : Any, optional
        Project owning the feature. Required for helpers that expose the file URI API.
    speos_client : Any, optional
        Speos client used to create the underlying :class:`Spectrum` object.
    stable_ctr : bool, optional
        Guard flag for nested helper creation from class scope.

    Notes
    -----
    This is an internal helper. Do not instantiate it directly from user code.
    """

    def __init__(
        self,
        name: str,
        message_to_complete: Any,
        field_name_to_complete: str = "",
        spectrum_guid: str = "",
        project: Any = None,
        speos_client: Any = None,
        stable_ctr: bool = False,
    ) -> None:
        if project is not None and not stable_ctr:
            msg = "_SpectrumReference class instantiated outside of class scope"
            raise RuntimeError(msg)

        self._project = project
        self._speos_client = speos_client if speos_client is not None else project.client
        self._name = name
        self._message_to_complete = message_to_complete
        self._field_name_to_complete = field_name_to_complete or "spectrum_guid"
        self._file_uri = ""
        self._no_spectrum = None
        self._no_spectrum_local = False

        spectrum_name = name if project is not None else name + ".Spectrum"
        if spectrum_guid:
            self._spectrum = Spectrum(
                speos_client=self._speos_client,
                name=spectrum_name,
                key=spectrum_guid,
            )
        else:
            self._spectrum = Spectrum(speos_client=self._speos_client, name=spectrum_name)

        if project is not None:
            self.bind(message_to_complete)

    def __str__(self) -> str:
        if self._no_spectrum is None:
            if self._no_spectrum_local is False:
                return str(self._spectrum)
        else:
            if self._no_spectrum is False:
                return str(self._spectrum)
        return ""

    def _ensure_spectrum(self, key: str = "") -> Spectrum:
        """Get the current spectrum instance, rebinding it when needed."""
        current_key = ""
        if self._spectrum is not None and self._spectrum.spectrum_link is not None:
            current_key = self._spectrum.spectrum_link.key

        if self._spectrum is None or (key and current_key != key):
            spectrum_name = self._name if self._project is not None else self._name + ".Spectrum"
            if key:
                self._spectrum = Spectrum(
                    speos_client=self._speos_client,
                    name=spectrum_name,
                    key=key,
                )
            else:
                self._spectrum = Spectrum(speos_client=self._speos_client, name=spectrum_name)
        return self._spectrum

    def bind(self, message_to_complete: Any) -> _SpectrumReference:
        """Bind the helper to a protobuf message and refresh the cached file URI."""
        self._message_to_complete = message_to_complete
        spectrum_guid = getattr(self._message_to_complete, self._field_name_to_complete, "")
        if spectrum_guid:
            spectrum = self._ensure_spectrum(key=spectrum_guid)
            if spectrum._spectrum.HasField("library"):
                self._file_uri = spectrum._spectrum.library.file_uri
            else:
                self._file_uri = ""
        else:
            self._file_uri = ""
        return self

    @property
    def file_uri(self) -> str:
        """User-facing file path for a referenced library spectrum."""
        return self._file_uri

    @file_uri.setter
    def file_uri(self, file_uri: Union[str, Path]) -> None:
        self._file_uri = str(Path(file_uri)) if file_uri else ""
        if self._file_uri:
            spectrum = self._ensure_spectrum()
            spectrum.set_library().file_uri = self._file_uri

    def clear(self) -> _SpectrumReference:
        """Clear the cached file URI and referenced protobuf GUID field."""
        self._file_uri = ""
        self._message_to_complete.ClearField(self._field_name_to_complete)
        return self

    def commit(self) -> _SpectrumReference:
        """Commit the current library spectrum and write its GUID to the bound field."""
        if not self._file_uri:
            self._message_to_complete.ClearField(self._field_name_to_complete)
            return self

        spectrum = self._ensure_spectrum()
        spectrum.set_library().file_uri = self._file_uri
        spectrum.commit()
        setattr(
            self._message_to_complete,
            self._field_name_to_complete,
            spectrum.spectrum_link.key,
        )
        return self

    def _commit(self) -> _SpectrumReference:
        """Commit the current spectrum and write its GUID to the bound field."""
        if not self._no_spectrum_local:
            self._spectrum.commit()
            setattr(
                self._message_to_complete,
                self._field_name_to_complete,
                self._spectrum.spectrum_link.key,
            )
            self._no_spectrum = self._no_spectrum_local
        return self

    def _reset(self) -> _SpectrumReference:
        """Reset the referenced spectrum to its committed state."""
        self._spectrum.reset()
        if self._no_spectrum is not None:
            self._no_spectrum_local = self._no_spectrum
        return self

    def _delete(self) -> _SpectrumReference:
        """Mark the spectrum helper as deleted."""
        self._no_spectrum = None
        return self
