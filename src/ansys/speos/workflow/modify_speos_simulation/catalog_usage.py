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
import time
from typing import List, Optional, Union

from ansys.api.speos.job.v2 import job_pb2

import ansys.speos.core as core


class Catalog:
    def __init__(self, speos: core.Speos):
        self._speos = speos

    def fill(self, catalog_name: str = "CatalogDefault", sensor_templates: List[core.SensorTemplate] = []):
        for ssr_t in sensor_templates:
            ssr_t.metadata.update({catalog_name: ssr_t.name})
            self._speos.client.sensor_templates().create(message=ssr_t)

    def find_sensor_template(self, name: str) -> core.SensorTemplate:
        for ssr_t in self._speos.client.sensor_templates().list():
            if ssr_t.get().name == name:
                return ssr_t

    def find_source_template(self, name: str) -> core.SourceTemplate:
        for src_t in self._speos.client.source_templates().list():
            if src_t.get().name == name:
                return src_t


class SpeosSimulationMod:
    """
    Class to load ".speos" simulation file in order to update it using a catalog usage.

    Parameters
    ----------
    speos : core.Speos
        Speos session (connected to gRPC server).
    file_name : str
        ".speos" simulation file name.
    """

    def __init__(self, speos: core.Speos, file_name: str):
        self._speos = speos

        self._scene = self._speos.client.scenes().create()

        # Create empty scene and load file
        self._scene.load_file(file_uri=file_name)

    @property
    def scene(self) -> core.SceneLink:
        """The scene."""
        return self._scene

    def modify_template(self, instance_index: int, template: Union[core.SensorTemplateLink, core.SourceTemplateLink]):
        scene_data = self._scene.get()

        if type(template) == core.SensorTemplateLink:
            scene_data.sensors[instance_index].sensor_guid = template.key
        elif type(template) == core.SourceTemplateLink:
            scene_data.sources[instance_index].source_guid = template.key

        self._scene.set(scene_data)

    def compute(self, job_name="new_job", stop_condition_duration: Optional[int] = None) -> core.JobLink:
        """Compute first simulation.

        Parameters
        ----------
        job_name : str
            Name of the job.
            By default, ``"new_job"``.
        stop_condition_duration : int, optional
            Duration in s to be used as stop condition.
            By default, ``None``.

        Returns
        -------
        core.JobLink
            Job who launched the simulation.
        """

        scene_data = self._scene.get()
        if len(scene_data.simulations) == 0:
            raise ValueError("At least one simulation is needed in the scene.")

        simu_t_link = self._speos.client.get_item(scene_data.simulations[0].simulation_guid)
        props = None
        if isinstance(simu_t_link, core.SimulationTemplateLink):
            simu_t_data = simu_t_link.get()
            if simu_t_data.HasField("direct_mc_simulation_template"):
                props = core.JobFactory.direct_mc_props(stop_condition_duration=stop_condition_duration)
            elif simu_t_data.HasField("inverse_mc_simulation_template"):
                props = core.JobFactory.inverse_mc_props(stop_condition_duration=stop_condition_duration)
            elif simu_t_data.HasField("interactive_simulation_template"):
                props = core.JobFactory.interactive_props()

        if props is None:
            raise KeyError(core.SimulationTemplateLink)

        new_job = self._speos.client.jobs().create(
            message=core.JobFactory.new(
                name=job_name,
                scene=self._scene,
                simulation_path=scene_data.simulations[0].name,
                properties=props,
            )
        )

        new_job.start()

        job_state_res = new_job.get_state()
        while (
            job_state_res.state != job_pb2.Job.State.FINISHED
            and job_state_res.state != job_pb2.Job.State.STOPPED
            and job_state_res.state != job_pb2.Job.State.IN_ERROR
        ):
            time.sleep(3)

            job_state_res = new_job.get_state()
            if job_state_res.state == job_pb2.Job.State.IN_ERROR:
                core.LOG.error(core.protobuf_message_to_str(new_job.get_error()))

        return new_job

    def close(self):
        """Clean SpeosSimulationUpdate before closing"""

        self._scene.delete()
