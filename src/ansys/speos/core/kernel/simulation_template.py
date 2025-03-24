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

from ansys.api.speos.simulation.v1 import (
    simulation_template_pb2 as messages,
    simulation_template_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoSimulationTemplate = messages.SimulationTemplate
"""SimulationTemplate protobuf class.

ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate
"""
ProtoSimulationTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SimulationTemplateLink(CrudItem):
    """
    Link object for simulation template in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.simulation_template.SimulationTemplateStub
        Database to link to.
    key : str
        Key of the simulation_template in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.api.speos.simulation.v1 import simulation_template_pb2
    >>> from ansys.speos.core.kernel.simulation_template import (
    ...     ProtoSimulationTemplate,
    ... )
    >>> speos = Speos(host="localhost", port=50098)
    >>> sim_t_db = speos.client.simulation_templates()
    >>> sim_t_message = ProtoSimulationTemplate(name="Direct")
    >>> sim_t_message.direct_mc_simulation_template.geom_distance_tolerance = 0.01
    >>> sim_t_message.direct_mc_simulation_template.max_impact = 100
    >>> sim_t_message.direct_mc_simulation_template.weight.minimum_energy_percentage = 0.005
    >>> sim_t_message.direct_mc_simulation_template.colorimetric_standard = (
    ...     simulation_template_pb2.CIE_1931
    ... )
    >>> sim_t_message.direct_mc_simulation_template.dispersion = True
    >>> sim_t_link = sim_t_db.create(message=sim_t_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the simulation_template."""
        return str(self.get())

    def get(self) -> ProtoSimulationTemplate:
        """Get the datamodel from database.

        Returns
        -------
        simulation_template.SimulationTemplate
            SimulationTemplate datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoSimulationTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : simulation_template.SimulationTemplate
            New simulation_template datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SimulationTemplateStub(CrudStub):
    """
    Database interactions for simulation templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SimulationTemplateStub is to retrieve it from SpeosClient via
    simulation_templates() method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> sim_t_db = speos.client.simulation_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SimulationTemplatesManagerStub(channel=channel))

    def create(self, message: ProtoSimulationTemplate) -> SimulationTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : simulation_template.SimulationTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.simulation_template.SimulationTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(simulation_template=message))
        return SimulationTemplateLink(self, resp.guid)

    def read(self, ref: SimulationTemplateLink) -> ProtoSimulationTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.simulation_template.SimulationTemplateLink
            Link object to read.

        Returns
        -------
        simulation_template.SimulationTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.simulation_template

    def update(self, ref: SimulationTemplateLink, data: ProtoSimulationTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.simulation_template.SimulationTemplateLink
            Link object to update.

        data : simulation_template.SimulationTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        CrudStub.update(
            self,
            messages.Update_Request(guid=ref.key, simulation_template=data),
        )

    def delete(self, ref: SimulationTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.simulation_template.SimulationTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SimulationTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.simulation_template.SimulationTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SimulationTemplateLink(self, x), guids))
