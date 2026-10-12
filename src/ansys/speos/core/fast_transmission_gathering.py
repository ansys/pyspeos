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

"""Provides a way to interact with Speos feature: fast transmission gathering."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import List, Optional, Union

import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.generic.general_methods import min_speos_version
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
import ansys.speos.core.part as part
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils


class FastTransmissionGathering:
    """Speos feature: fast transmission gathering (FTG).

    The fast transmission gathering accelerates the simulation by neglecting the light
    refraction that occurs when the light is being transmitted through the selected
    transparent geometries.

    Only one fast transmission gathering feature per project.

    Notes
    -----
    The geometries selected here are only taken into account if the fast transmission
    gathering is activated at simulation level, via the ``fast_transmission_gathering``
    property of :class:`ansys.speos.core.simulation.SimulationDirect` or
    :class:`ansys.speos.core.simulation.SimulationInverse`.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    fast_transmission_gathering : \
ansys.api.speos.scene.v2.scene_pb2.Scene.FastTransmissionGathering, optional
        Protobuf message to provide if the feature does not have to be created from scratch.
        By default, ``None``, means that the feature is created from scratch.
    """

    @min_speos_version(27, 1, 0)
    def __init__(
        self,
        project: project.Project,
        fast_transmission_gathering: Optional[ProtoScene.FastTransmissionGathering] = None,
    ) -> None:
        self._project = project
        self._name = ""

        if fast_transmission_gathering is None:
            # Create local fast transmission gathering
            self._fast_transmission_gathering = ProtoScene.FastTransmissionGathering()
            self._fast_transmission_gathering.geometries.geo_paths[:] = []
            self._committed = False
        else:
            # Retrieve fast transmission gathering from input
            self._committed = True
            self._fast_transmission_gathering = fast_transmission_gathering

    @property
    def geometries(self) -> List[str]:
        """Geometries with fast transmission gathering applied.

        This property gets and sets the geo paths on which the fast transmission gathering
        is applied.

        Parameters
        ----------
        geometries : Optional[List[Union[\
ansys.speos.core.geo_ref.GeoRef, \
ansys.speos.core.body.Body]]]
            Geometries on which the fast transmission gathering is applied.
            Pass ``None`` or an empty list to clear the geometries.

        Returns
        -------
        List[str]
            Geo paths with fast transmission gathering applied.
        """
        return list(self._fast_transmission_gathering.geometries.geo_paths)

    @geometries.setter
    def geometries(
        self,
        geometries: Optional[List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]],
    ) -> None:
        if not geometries:
            self._fast_transmission_gathering.ClearField("geometries")
            return

        geo_paths = []
        for geometry in geometries:
            if isinstance(geometry, GeoRef):
                geo_paths.append(geometry)
            elif isinstance(geometry, body.Body):
                geo_paths.append(geometry.geo_path)
            else:
                msg = (
                    f"Type {type(geometry)} is not supported as fast transmission "
                    "gathering geometry input."
                )
                raise TypeError(msg)
        self._fast_transmission_gathering.geometries.geo_paths[:] = [
            geo_path.to_native_link() for geo_path in geo_paths
        ]

    def _to_dict(self) -> dict:
        if self._project.scene_link and self._committed:
            scene_data = self._project.scene_link.get()
            message = scene_data.fast_transmission_gathering
        else:
            message = self._fast_transmission_gathering

        out_dict = proto_message_utils._replace_guids(
            speos_client=self._project.client, message=message
        )

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> Union[str, dict]:
        """Get dictionary corresponding to the fast transmission gathering - read only.

        Parameters
        ----------
        key : str, optional
            Key prefix used to look up a value.
            By default, ``""``, which returns the full dictionary.

        Returns
        -------
        str | dict
            Value found for the given key, or the full dictionary when *key* is empty.
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

    def __str__(self) -> str:
        """Return the string representation of the fast transmission gathering."""
        out_str = ""

        if self._project.scene_link:
            if not self._committed:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def _update_scene_data(self, scene_data: ProtoScene) -> bool:
        # In case the data is different from what is stored on server -> update
        if scene_data.fast_transmission_gathering != self._fast_transmission_gathering:
            scene_data.fast_transmission_gathering.CopyFrom(self._fast_transmission_gathering)
            return True
        return False

    def _prepare_commit(self) -> None:
        # This boolean allows to keep track if the feature is committed
        self._committed = True

    def commit(self) -> FastTransmissionGathering:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.fast_transmission_gathering.FastTransmissionGathering
            Fast transmission gathering feature.
        """
        self._prepare_commit()

        # Update the scene with the fast transmission gathering
        if self._project.scene_link:
            # Retrieve scene data
            scene_data = self._project.scene_link.get()

            # Update the scene data, and check if the scene needs to be updated
            if self._update_scene_data(scene_data):
                # Update if needed
                self._project.scene_link.set(data=scene_data)

        return self

    def reset(self) -> FastTransmissionGathering:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.fast_transmission_gathering.FastTransmissionGathering
            Fast transmission gathering feature.
        """
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # store locally the fast transmission gathering from server data
            self._fast_transmission_gathering = scene_data.fast_transmission_gathering

        return self

    def delete(self) -> FastTransmissionGathering:
        """Delete feature: delete data from the speos server database.

        The local data are still available.

        Returns
        -------
        ansys.speos.core.fast_transmission_gathering.FastTransmissionGathering
            Fast transmission gathering feature.
        """
        # Remove the fast transmission gathering from the scene
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data

            if scene_data.HasField("fast_transmission_gathering"):
                scene_data.ClearField("fast_transmission_gathering")
                self._project.scene_link.set(data=scene_data)  # update scene data

        # _committed to false -> this feature is no longer committed
        self._committed = False

        return self
