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

"""Provides a way to interact with feature: Part."""
from __future__ import annotations

from typing import List, Mapping, Optional, Union

import ansys.speos.core as core
import ansys.speos.script.body as body
import ansys.speos.script.project as project


class Part:
    class SubPart:
        def __init__(self, speos_client: core.SpeosClient, name: str, description: str = "") -> None:
            self._speos_client = speos_client
            self._name = name
            self.part_link = None
            """Link object for the part in database."""
            self._part_instance = core.Part.PartInstance(name=name, description=description)

            # Create local Part
            self._part = core.Part(name=name, description=description)

            self._geom_features = []

        def create_body(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> body.Body:
            body_feat = body.Body(speos_client=self._speos_client, name=name, description=description, metadata=metadata)
            self._geom_features.append(body_feat)
            return body_feat

        def set_axis_system(self, axis_system: List[float]) -> Part.SubPart:
            self._part_instance.axis_system[:] = axis_system
            return self

        def _to_str(self, light_print: bool = False) -> str:
            out_str = ""

            if light_print == False:
                out_str += f"local: " + core.protobuf_message_to_str(self._part_instance)  # how to know non local

            if self.part_link is None:
                out_str += f"\nlocal: " + core.protobuf_message_to_str(self._part)
            else:
                out_str += "\n" + str(self.part_link)

            for g in self._geom_features:
                if type(g) == body.Body:
                    out_str += "\n" + str(g)

            return out_str

        def __str__(self) -> str:
            """Return the string representation of the sub part."""
            out_str = self._to_str()
            return out_str

        def commit(self) -> Part.SubPart:
            """Save feature: send the local data to the speos server database.

            Returns
            -------
            ansys.speos.script.part.Part.SubPart
                SubPart feature.
            """

            self._part.ClearField("body_guids")
            for g in self._geom_features:
                g.commit()
                if type(g) == body.Body:
                    self._part.body_guids.append(g.body_link.key)

            # Save or Update the part (depending on if it was already saved before)
            if self.part_link is None:
                self.part_link = self._speos_client.parts().create(message=self._part)
            else:
                self.part_link.set(data=self._part)

            self._part_instance.part_guid = self.part_link.key

            # Instance unique id in description?

            return self

        def reset(self) -> Part.SubPart:
            """Reset feature: override local data by the one from the speos server database.

            Returns
            -------
            ansys.speos.script.part.Part.SubPart
                SubPart feature.
            """
            # Reset part
            if self.part_link is not None:
                self._part = self.part_link.get()

            return self

        def delete(self) -> Part.SubPart:
            """Delete feature: delete data from the speos server database.
            The local data are still available

            Returns
            -------
            ansys.speos.script.part.Part.SubPart
                SubPart feature.
            """
            # Delete the part
            if self.part_link is not None:
                self.part_link.delete()
                self.part_link = None

            # Delete features
            for g in self._geom_features:
                if type(g) == body.Body:
                    self._part.body_guids.remove(g.body_link.key)
                    g.delete()

            return self

        def find(self, name: str) -> Optional[body.Body]:
            orig_name = name
            idx = name.find("/")
            if idx != -1:
                name = name[0:idx]

            found_feature = next((x for x in self._geom_features if x._name == name), None)

            if found_feature is not None:
                if idx != -1:
                    found_feature = found_feature.find(orig_name[idx + 1 :])
                return found_feature
            return None

    """Feature : Part.

    Parameters
    ----------
    project : ansys.speos.script.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.

    Attributes
    ----------
    part_link : ansys.speos.core.part.PartLink
        Link object for the part in database.
    """

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self.part_link = None
        """Link object for the part in database."""

        self._geom_features = []

        # Create local Part
        self._part = core.Part(name=name, description=description, metadata=metadata)

    def create_body(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> body.Body:
        body_feat = body.Body(speos_client=self._project.client, name=name, description=description, metadata=metadata)
        self._geom_features.append(body_feat)
        return body_feat

    def create_sub_part(self, name: str, description: str = "") -> Part.SubPart:
        sub_part_feat = Part.SubPart(speos_client=self._project.client, name=name, description=description)
        self._geom_features.append(sub_part_feat)
        return sub_part_feat

    def __str__(self) -> str:
        """Return the string representation of the part."""
        out_str = ""

        if self.part_link is None:
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._part)
        else:
            out_str += "\n" + str(self.part_link)

        for g in self._geom_features:
            if type(g) == body.Body:
                out_str += "\n" + str(g)

        for g in self._geom_features:
            if type(g) == Part.SubPart:
                out_str += g._to_str(light_print=True)

        return out_str

    def commit(self) -> Part:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.part.Part
            Part feature.
        """
        # Retrieve all features to commit them
        self._part.ClearField("body_guids")
        self._part.ClearField("parts")
        for g in self._geom_features:
            g.commit()
            if type(g) == body.Body:
                self._part.body_guids.append(g.body_link.key)
            elif type(g) == Part.SubPart:
                self._part.parts.append(g._part_instance)

        # Save or Update the part (depending on if it was already saved before)
        if self.part_link is None:
            self.part_link = self._project.client.parts().create(message=self._part)
        else:
            self.part_link.set(data=self._part)

        # Update the scene with the part
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            scene_data.part_guid = self.part_link.key
            self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> Part:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.part.Part
            Part feature.
        """
        # Reset part
        if self.part_link is not None:
            self._part = self.part_link.get()

        return self

    def delete(self) -> Part:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.part.Part
            Part feature.
        """
        # Delete the part
        if self.part_link is not None:
            self.part_link.delete()
            self.part_link = None

        # Retrieve all features to delete them
        for g in self._geom_features:
            if type(g) == body.Body:
                self._part.body_guids.remove(g.body_link.key)
            elif type(g) == Part.SubPart:
                for p in self._part.parts:
                    if p.part_guid == g._part_instance.part_guid:
                        p.part_guid = ""
            g.delete()

        # Remove the part guid from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        scene_data.part_guid = ""
        self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def find(self, name: str) -> Optional[Union[body.Body, Part.SubPart]]:
        orig_name = name
        idx = name.find("/")
        if idx != -1:
            name = name[0:idx]

        found_feature = next((x for x in self._geom_features if x._name == name), None)

        if found_feature is not None:
            if idx != -1:
                found_feature = found_feature.find(orig_name[idx + 1 :])
            return found_feature
        return None
