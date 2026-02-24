# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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
"""Provides a way to interact with Speos feature: ground plane."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import List, Optional

from ansys.speos.core.kernel.scene import ProtoScene
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils


class GroundPlane:
    """Speos feature: ground plane.

    Only usable when there is at least one Ambient Environment Source in the project.

    Parameters
    ----------
    project : project.Project
        Project that will own the feature.
    """

    def __init__(self, project: project.Project, ground: Optional[ProtoScene.GroundPlane] = None):
        self._project = project
        self._name = ""

        if ground is None:
            # Create local ground
            self._ground = ProtoScene.GroundPlane()
            self.ground_origin = [0.0, 0.0, 0.0]
            self.ground_zenith = [0.0, 0.0, 1.0]
            self.ground_height = 1000.0
            self._committed = False
        else:
            # Retrieve ground from input
            self._committed = True
            self._ground = ground

    @property
    def ground_origin(self) -> List[float]:
        """Ground origin.

        This property gets and sets the origin of the ground plane.
        Default as [0, 0, 0]

        Parameters
        ----------
        value : List[float]
            Ground origin.

        Returns
        -------
        List[float]
            Ground origin.
        """
        return self._ground.ground_origin

    @ground_origin.setter
    def ground_origin(self, value: List[float]) -> None:
        self._ground.ground_origin[:] = value

    @property
    def ground_zenith(self) -> List[float]:
        """Zenith direction.

        This property gets and sets the zenith direction of the ground plane.
        Default as [0, 0, 1]

        Parameters
        ----------
        value : List[float]
            Zenith direction.

        Returns
        -------
        List[float]
            Zenith direction.
        """
        return self._ground.zenith_direction

    @ground_zenith.setter
    def ground_zenith(self, value: List[float]) -> None:
        self._ground.zenith_direction[:] = value

    @property
    def ground_height(self) -> float:
        """Ground height.

        This property gets and sets the height of the ground plane.
        Default as 1000.0

        Parameters
        ----------
        value : float
            Ground height.

        Returns
        -------
        float
            Ground height.
        """
        return self._ground.ground_height

    @ground_height.setter
    def ground_height(self, value: float) -> None:
        self._ground.ground_height = value

    def _to_dict(self) -> dict:
        out_dict = {}

        if self._project.scene_link:
            scene_data = self._project.scene_link.get()

            if self._committed:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=scene_data.ground
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self._ground
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._ground
            )

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> str | dict:
        """Get dictionary corresponding to the ground plane - read only.

        Parameters
        ----------
        key : str

        Returns
        -------
        str | dict
        """
        if key == "":
            return self._to_dict()
        info = proto_message_utils._value_finder_key_startswith(dict_var=self._to_dict(), key=key)
        content = list(info)
        if len(content) != 0:
            content.sort(
                key=lambda x: SequenceMatcher(None, x[0], key).ratio(),
                reverse=True,
            )
            return content[0][1]
        info = proto_message_utils._flatten_dict(dict_var=self._to_dict())
        print("Used key: {} not found in key list: {}.".format(key, info.keys()))

    def __str__(self):
        """Return the string representation of the ground plane property."""
        out_str = ""

        if self._project.scene_link:
            if not self._committed:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def commit(self) -> GroundPlane:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.ground_plane.GroundPlane
            Ground plane feature.
        """
        # This boolean allows to keep track if the ground plane is committed
        self._committed = True

        # Update the scene with the ground plane
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # In case the ground is different from what is stored on server -> update
            if scene_data.ground != self._ground:
                scene_data.ground.CopyFrom(self._ground)
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> GroundPlane:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.ground_plane.GroundPlane
            Ground plane feature.
        """
        # Reset ground plane
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            self._ground = scene_data.ground  # store locally the ground from server data

        return self

    def delete(self) -> GroundPlane:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.ground_plane.GroundPlane
            Ground plane feature.
        """
        # Remove the ground from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data

        if scene_data.HasField("ground"):
            scene_data.ClearField("ground")
            self._project.scene_link.set(data=scene_data)  # update scene data

        # _committed to false -> this feature is no longer committed
        self._committed = False

        return self
