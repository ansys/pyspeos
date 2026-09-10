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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs for sensor.v2."""

from typing import List

from ansys.api.speos.sensor.v2 import (
    sensor_pb2 as messages,
    sensor_pb2_grpc as service,
)

from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoSensorTemplateV2 = messages.SensorTemplate
"""SensorTemplate protobuf class : ansys.api.speos.sensor.v2.sensor_pb2.SensorTemplate"""
ProtoSensorTemplateV2.__str__ = lambda self: protobuf_message_to_str(self)


class SensorTemplateLinkV2(CrudItem):
    """
    Link object for sensor template v2 in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.sensor_template_v2.SensorTemplateStubV2
        Database to link to.
    key : str
        Key of the sensor template in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.kernel.sensor_template_v2 import ProtoSensorTemplateV2
    >>> speos = Speos()
    >>> ssr_t_db = speos.client.sensor_templates_v2()
    >>> ssr_t_message = ProtoSensorTemplateV2(name="Irradiance")
    >>> ssr_t_message.irradiance.mode_photometric.SetInParent()
    >>> ssr_t_message.irradiance.integration_type = 1  # PLANAR
    >>> ssr_t_message.irradiance.dimensions.x_start = -50
    >>> ssr_t_message.irradiance.dimensions.x_end = 50
    >>> ssr_t_message.irradiance.dimensions.x_sampling = 100
    >>> ssr_t_message.irradiance.dimensions.y_start = -50
    >>> ssr_t_message.irradiance.dimensions.y_end = 50
    >>> ssr_t_message.irradiance.dimensions.y_sampling = 100
    >>> ssr_t_link = ssr_t_db.create(message=ssr_t_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the sensor template."""
        return str(self.get())

    def get(self) -> ProtoSensorTemplateV2:
        """Get the datamodel from database.

        Returns
        -------
        sensor_template_v2.SensorTemplate
            Sensor template datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoSensorTemplateV2) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : sensor_template_v2.SensorTemplate
            New sensor template datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SensorTemplateStubV2(CrudStub):
    """
    Database interactions for sensor templates v2.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SensorTemplateStubV2 is to retrieve it from SpeosClient via
    sensor_templates_v2() method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos()
    >>> ssr_t_db = speos.client.sensor_templates_v2()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SensorTemplatesManagerStub(channel=channel))

    def create(self, message: ProtoSensorTemplateV2) -> SensorTemplateLinkV2:
        """Create a new entry.

        Parameters
        ----------
        message : sensor_template_v2.SensorTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.sensor_template_v2.SensorTemplateLinkV2
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(sensor_template=message))
        return SensorTemplateLinkV2(self, resp.guid)

    def read(self, ref: SensorTemplateLinkV2) -> ProtoSensorTemplateV2:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sensor_template_v2.SensorTemplateLinkV2
            Link object to read.

        Returns
        -------
        sensor_template_v2.SensorTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SensorTemplateLinkV2 is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.sensor_template

    def update(self, ref: SensorTemplateLinkV2, data: ProtoSensorTemplateV2):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sensor_template_v2.SensorTemplateLinkV2
            Link object to update.

        data : sensor_template_v2.SensorTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SensorTemplateLinkV2 is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, sensor_template=data))

    def delete(self, ref: SensorTemplateLinkV2) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sensor_template_v2.SensorTemplateLinkV2
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SensorTemplateLinkV2 is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SensorTemplateLinkV2]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.sensor_template_v2.SensorTemplateLinkV2]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SensorTemplateLinkV2(self, x), guids))
