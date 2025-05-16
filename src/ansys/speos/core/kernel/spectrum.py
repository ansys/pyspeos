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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""

from typing import List

from ansys.api.speos.spectrum.v1 import (
    spectrum_pb2 as messages,
    spectrum_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoSpectrum = messages.Spectrum
"""Spectrum protobuf class : ansys.api.speos.spectrum.v1.spectrum_pb2.Spectrum"""
ProtoSpectrum.__str__ = lambda self: protobuf_message_to_str(self)


class SpectrumLink(CrudItem):
    """
    Link object for a spectrum in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.spectrum.SpectrumStub
        Database to link to.
    key : str
        Key of the spectrum in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.kernel.spectrum import ProtoSpectrum
    >>> speos = Speos(host="localhost", port=50098)
    >>> spe_db = speos.client.spectrums()
    >>> spe_message = ProtoSpectrum(name="Monochromatic_600")
    >>> spe_message.monochromatic.wavelength = 600
    >>> spe_link = spe_db.create(message=spe_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the spectrum."""
        return str(self.get())

    def get(self) -> ProtoSpectrum:
        """Get the datamodel from database.

        Returns
        -------
        spectrum.Spectrum
            Spectrum datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoSpectrum) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : spectrum.Spectrum
            New spectrum datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SpectrumStub(CrudStub):
    """
    Database interactions for spectrums.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SpectrumStub is to retrieve it from SpeosClient via spectrums() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> spe_db = speos.client.spectrums()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SpectrumsManagerStub(channel=channel))

    def create(self, message: ProtoSpectrum) -> SpectrumLink:
        """Create a new entry.

        Parameters
        ----------
        message : spectrum.Spectrum
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.spectrum.SpectrumLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(spectrum=message))
        return SpectrumLink(self, resp.guid)

    def read(self, ref: SpectrumLink) -> ProtoSpectrum:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.spectrum.SpectrumLink
            Link object to read.

        Returns
        -------
        spectrum.Spectrum
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.spectrum

    def update(self, ref: SpectrumLink, data: ProtoSpectrum):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.spectrum.SpectrumLink
            Link object to update.
        data : spectrum.Spectrum
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, spectrum=data))

    def delete(self, ref: SpectrumLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.spectrum.SpectrumLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SpectrumLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.spectrum.SpectrumLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SpectrumLink(self, x), guids))
