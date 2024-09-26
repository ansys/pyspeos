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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import List, Mapping, Optional

from ansys.api.speos.source.v1 import source_pb2 as messages
from ansys.api.speos.source.v1 import source_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.intensity_template import IntensityTemplateLink
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.spectrum import SpectrumLink

SourceTemplate = messages.SourceTemplate
"""SourceTemplate protobuf class : ansys.api.speos.source.v1.source_pb2.SourceTemplate"""
SourceTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SourceTemplateLink(CrudItem):
    """Link object for a source template in database.

    Parameters
    ----------
    db : ansys.speos.core.source_template.SourceTemplateStub
        Database to link to.
    key : str
        Key of the source template in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the source template."""
        return str(self.get())

    def get(self) -> SourceTemplate:
        """Get the datamodel from database.

        Returns
        -------
        source_template.SourceTemplate
            Source template datamodel.
        """
        return self._stub.read(self)

    def set(self, data: SourceTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : source_template.SourceTemplate
            New source template datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SourceTemplateStub(CrudStub):
    """
    Database interactions for source templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SourceTemplateStub is to retrieve it from SpeosClient via source_templates() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> src_t_db = speos.client.source_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SourceTemplatesManagerStub(channel=channel))

    def create(self, message: SourceTemplate) -> SourceTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : source_template.SourceTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.source_template.SourceTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(source_template=message))
        return SourceTemplateLink(self, resp.guid)

    def read(self, ref: SourceTemplateLink) -> SourceTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.source_template.SourceTemplateLink
            Link object to read.

        Returns
        -------
        source_template.SourceTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.source_template

    def update(self, ref: SourceTemplateLink, data: SourceTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.source_template.SourceTemplateLink
            Link object to update.
        data : source_template.SourceTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, source_template=data))

    def delete(self, ref: SourceTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.source_template.SourceTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SourceTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.source_template.SourceTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SourceTemplateLink(self, x), guids))


class SourceTemplateFactory:
    """Class to help creating SourceTemplate message"""

    class Flux:
        """
        Class to help creating SourceTemplate.Flux message. It represents the source flux.

        Parameters
            ----------
            unit : ansys.speos.core.source_template.SourceTemplateFactory.Flux.Unit, optional
                Flux unit.
                By default, ``Unit.Lumen``.
            value : float, optional
                Flux value.
                By default, ``683``.
        """

        class Unit(Enum):
            """Enum representing the unit of the flux."""

            Lumen = 1
            Watt = 2
            Candela = 3

        def __init__(self, unit: Optional[Unit] = Unit.Lumen, value: Optional[float] = 683) -> None:
            self.unit = unit
            self.value = value

    @staticmethod
    def luminaire(
        name: str,
        intensity_file_uri: str,
        spectrum: SpectrumLink,
        flux: Optional[Flux] = None,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SourceTemplate:
        """
        Create a SourceTemplate message, with luminaire type.

        Parameters
        ----------
        name : str
            Name of the source template.
        intensity_file_uri : str
            IES or EULUMDAT format file uri
        spectrum : ansys.speos.core.spectrum.SpectrumLink
            Spectrum.
        flux : ansys.speos.core.source_template.SourceTemplateFactory.Flux, optional
            Can be filled not to take the flux from intensity file.
            Flux units allowed are Lumen or Watt.
            By default, ``None``, ie flux taken from intensity_file_uri.
        description : str, optional
            Description of the source template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the source template.
            By default, ``None``.

        Returns
        -------
        source_template.SourceTemplate
            SourceTemplate message created.
        """
        src = SourceTemplate(name=name, description=description)
        if metadata is not None:
            src.metadata.update(metadata)

        if flux is None:
            src.luminaire.flux_from_intensity_file.SetInParent()
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Lumen:
            src.luminaire.luminous_flux.luminous_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Watt:
            src.luminaire.radiant_flux.radiant_value = flux.value
        else:
            src.luminaire.flux_from_intensity_file.SetInParent()

        src.luminaire.intensity_file_uri = intensity_file_uri
        src.luminaire.spectrum_guid = spectrum.key
        return src

    @staticmethod
    def surface(
        name: str,
        intensity_template: IntensityTemplateLink,
        flux: Optional[Flux] = Flux(),
        exitance_xmp_file_uri: Optional[str] = "",
        spectrum: Optional[SpectrumLink] = None,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SourceTemplate:
        """
        Create a SourceTemplate message, with surface type.

        Parameters
        ----------
        name : str
            Name of the source template.
        intensity_template : ansys.speos.core.intensity_template.IntensityTemplateLink
            Intensity template.
        flux : ansys.speos.core.source_template.SourceTemplateFactory.Flux, optional
            If set to None, take the flux from intensity file. Ok if intensity_template.get().HasField("library").
            By default, ``Flux()``
        exitance_xmp_file_uri : str, optional
            If defined, surface source template has exitance variable.
            XMP file describing exitance.
            By default, ``""``, ie exitance constant
        spectrum : ansys.speos.core.spectrum.SpectrumLink, optional
            Spectrum.
            No need to fill if exitance_xmp_file_uri is spectral
            By default, ``None``, ie spectrum from xmp file.
        description : str, optional
            Description of the source template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the source template.
            By default, ``None``.

        Returns
        -------
        source_template.SourceTemplate
            SourceTemplate message created.
        """
        src = SourceTemplate(name=name, description=description)
        if metadata is not None:
            src.metadata.update(metadata)

        if flux is None:
            src.surface.flux_from_intensity_file.SetInParent()
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Lumen:
            src.surface.luminous_flux.luminous_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Watt:
            src.surface.radiant_flux.radiant_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Candela:
            src.surface.luminous_intensity_flux.luminous_intensity_value = flux.value
        else:
            src.surface.flux_from_intensity_file.SetInParent()

        src.surface.intensity_guid = intensity_template.key

        if exitance_xmp_file_uri == "":
            src.surface.exitance_constant.SetInParent()
        else:
            src.surface.exitance_variable.exitance_xmp_file_uri = exitance_xmp_file_uri

        if spectrum is not None:
            src.surface.spectrum_guid = spectrum.key
        else:
            src.surface.spectrum_from_xmp_file.SetInParent()

        return src
