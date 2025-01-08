# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
from typing import Iterator, List

from ansys.api.speos.job.v2 import job_pb2 as messages
from ansys.api.speos.job.v2 import job_pb2_grpc as service
from ansys.api.speos.results.v1.ray_path_pb2 import RayPath

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Job = messages.Job
"""Job protobuf class : ansys.api.speos.job.v2.job_pb2.Job"""
Job.__str__ = lambda self: protobuf_message_to_str(self)


class JobLink(CrudItem):
    """Link object for job in database.

    Parameters
    ----------
    db : ansys.speos.core.job.JobStub
        Database to link to.
    key : str
        Key of the job in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        """Return the string representation of the Job."""
        return str(self.get())

    def get(self) -> Job:
        """Get the datamodel from database.

        Returns
        -------
        job.Job
            Job datamodel.
        """
        return self._stub.read(self)

    def set(self, data: Job) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : job.Job
            New Job datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)

    # Actions
    def get_state(self) -> messages.GetState_Response:
        """
        Retrieve job state.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetState_Response
            State of the job.
        """
        return self._actions_stub.GetState(messages.GetState_Request(guid=self.key))

    def start(self) -> None:
        """Start the job."""
        self._actions_stub.Start(messages.Start_Request(guid=self.key))

    def stop(self) -> None:
        """Stop the job."""
        self._actions_stub.Stop(messages.Stop_Request(guid=self.key))

    def get_error(self) -> messages.GetError_Response:
        """
        Retrieve job error.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetError_Response
            Error of the job.
        """
        return self._actions_stub.GetError(messages.GetError_Request(guid=self.key))

    def get_results(self) -> messages.GetResults_Response:
        """
        Retrieve job results.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetResults_Response
            Results of the job.
        """
        return self._actions_stub.GetResults(messages.GetResults_Request(guid=self.key))

    def get_progress_status(self) -> messages.GetProgressStatus_Response:
        """
        Retrieve job progress.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetProgressStatus_Response
            Progress status of the job.
        """
        return self._actions_stub.GetProgressStatus(messages.GetProgressStatus_Request(guid=self.key))

    def get_ray_paths(self) -> Iterator[RayPath]:
        """
        Retrieve ray paths.
        Available for interactive simulation.

        Returns
        -------
        Iterator[ansys.api.speos.results.v1.ray_path_pb2.RayPath]
            Ray paths generated by the interactive simulation.
        """
        for rp in self._actions_stub.GetRayPaths(messages.GetRayPaths_Request(guid=self.key)):
            yield rp


class JobStub(CrudStub):
    """
    Database interactions for job.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a JobStub is to retrieve it from SpeosClient via jobs() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> job_db = speos.client.jobs()

    """

    def __init__(self, channel):
        super().__init__(stub=service.JobsManagerStub(channel=channel))
        self._actions_stub = service.JobActionsStub(channel=channel)

    def create(self, message: Job) -> JobLink:
        """Create a new entry.

        Parameters
        ----------
        message : job.Job
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.job.JobLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(job=message))
        return JobLink(self, resp.guid)

    def read(self, ref: JobLink) -> Job:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to read.

        Returns
        -------
        job.Job
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.job

    def update(self, ref: JobLink, data: Job):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to update.

        data : job.Job
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, job=data))

    def delete(self, ref: JobLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[JobLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.job.JobLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: JobLink(self, x), guids))
