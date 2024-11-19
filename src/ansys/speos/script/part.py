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
import uuid

import ansys.speos.core as core
import ansys.speos.script.body as body
import ansys.speos.script.project as project


class Part:
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

    class SubPart:
        """Feature : SubPart.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        parent_part : ansys.speos.script.part.Part, optional
            Part containing this sub part.
            By default, ``None``.

        Attributes
        ----------
        part_link : ansys.speos.core.part.PartLink
            Link object for the part in database.
        """

        def __init__(self, speos_client: core.SpeosClient, name: str, description: str = "", parent_part: Optional[Part] = None) -> None:
            self._speos_client = speos_client
            self._parent_part = parent_part
            self._name = name
            self.part_link = None
            """Link object for the part in database."""
            self._unique_id = None
            self._part_instance = core.Part.PartInstance(name=name, description=description)

            # Create local Part
            self._part = core.Part(name=name, description=description)

            self._geom_features = []

        def create_body(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> body.Body:
            """Create a body in this element.

            Parameters
            ----------
            name : str
                Name of the feature.
            description : str
                Description of the feature.
                By default, ``""``.
            metadata : Mapping[str, str]
                Metadata of the feature.
                By default, ``{}``.

            Returns
            -------
            ansys.speos.script.body.Body
                Body feature.
            """
            body_feat = body.Body(speos_client=self._speos_client, name=name, description=description, metadata=metadata, parent_part=self)
            self._geom_features.append(body_feat)
            return body_feat

        def create_sub_part(self, name: str, description: str = "") -> Part.SubPart:
            """Create a sub part in this element.

            Parameters
            ----------
            name : str
                Name of the feature.
            description : str
                Description of the feature.
                By default, ``""``.

            Returns
            -------
            ansys.speos.script.part.Part.SubPart
                SubPart feature.
            """
            sub_part_feat = Part.SubPart(speos_client=self._speos_client, name=name, description=description, parent_part=self)
            self._geom_features.append(sub_part_feat)
            return sub_part_feat

        def set_axis_system(self, axis_system: List[float]) -> Part.SubPart:
            """Set the sub part orientation (relatively to parent element).

            Parameters
            ----------
            axis_system : List[float], optional
                Orientation of the sub part [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].

            Returns
            -------
            ansys.speos.script.part.Part.SubPart
                SubPart feature.
            """
            self._part_instance.axis_system[:] = axis_system
            return self

        def _to_str(self, light_print: bool = False) -> str:
            out_str = ""

            if light_print == False:
                out_str += f"local: " + core.protobuf_message_to_str(self._part_instance)

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
            # The _unique_id will help to find correct item in the scene.materials (the list of MaterialInstance)
            if self._unique_id is None:
                self._unique_id = str(uuid.uuid4())
                self._part_instance.description = "UniqueId_" + self._unique_id

            for g in self._geom_features:
                g.commit()

            # Save or Update the part (depending on if it was already saved before)
            if self.part_link is None:
                self.part_link = self._speos_client.parts().create(message=self._part)
            elif self.part_link.get() != self._part:
                self.part_link.set(data=self._part)  # Only update if data has changed

            self._part_instance.part_guid = self.part_link.key

            # Look if an element corresponds to the instance
            if self._parent_part is not None:
                update_part = True
                part_inst = next((x for x in self._parent_part._part.parts if x.description == "UniqueId_" + self._unique_id), None)
                if part_inst is not None:
                    if part_inst != self._part_instance:
                        part_inst.CopyFrom(self._part_instance)  # if yes, just replace
                    else:
                        update_part = False
                else:
                    self._parent_part._part.parts.append(self._part_instance)  # if no, just add it to the list of part instances

                if self._parent_part.part_link is not None and update_part:
                    self._parent_part.part_link.set(data=self._parent_part._part)  # update parent part

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

            # Reset part instance
            if self._parent_part.part_link is not None:
                parent_part_data = self._parent_part.part_link.get()  # retrieve server data
                # Look if an element corresponds to the _unique_id
                if self._unique_id is not None:
                    part_inst = next((x for x in parent_part_data.parts if x.description == "UniqueId_" + self._unique_id), None)
                    if part_inst is not None:
                        self._part_instance = part_inst

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
            # for g in self._geom_features:
            #    g.delete()

            # Remove the part instance from the parent part
            if self._parent_part is not None:
                part_inst = next((x for x in self._parent_part._part.parts if x.description == "UniqueId_" + self._unique_id), None)
                if part_inst is not None:
                    self._parent_part._part.parts.remove(part_inst)
                    if self._parent_part.part_link is not None:
                        self._parent_part.part_link.set(data=self._parent_part._part)  # update parent part

            # Reset the _unique_id
            self._unique_id = None
            self._part_instance.description = ""

            if self in self._parent_part._geom_features:
                self._parent_part._geom_features.remove(self)

            return self

        def find(self, name: str) -> Optional[Union[body.Body, Part.SubPart]]:
            """Find a feature.

            Parameters
            ----------
            name : str
                Name of the feature.
                Possibility to look also for bodies, faces, subpart.
                Example "BodyName/FaceName", "SubPartName/BodyName/FaceName"

            Returns
            -------
            Union[ansys.speos.script.body.Body, ansys.speos.script.part.Part.SubPart], optional
                Found feature, or None.
            """
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

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self.part_link = None
        """Link object for the part in database."""

        self._geom_features = []

        # Create local Part
        self._part = core.Part(name=name, description=description, metadata=metadata)

    def create_body(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> body.Body:
        """Create a body in this element.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.body.Body
            Body feature.
        """
        body_feat = body.Body(speos_client=self._project.client, name=name, description=description, metadata=metadata, parent_part=self)
        self._geom_features.append(body_feat)
        return body_feat

    def create_sub_part(self, name: str, description: str = "") -> Part.SubPart:
        """Create a sub part in this element.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.

        Returns
        -------
        ansys.speos.script.part.Part.SubPart
            SubPart feature.
        """
        sub_part_feat = Part.SubPart(speos_client=self._project.client, name=name, description=description, parent_part=self)
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
        for g in self._geom_features:
            g.commit()

        # Save or Update the part (depending on if it was already saved before)
        if self.part_link is None:
            self.part_link = self._project.client.parts().create(message=self._part)
        elif self.part_link.get() != self._part:
            self.part_link.set(data=self._part)  # Only update if data has changed

        # Update the scene with the part
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            if scene_data.part_guid != self.part_link.key:
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
        # for g in self._geom_features:
        #    g.delete()

        # Remove the part guid from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        scene_data.part_guid = ""
        self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def find(self, name: str) -> Optional[Union[body.Body, Part.SubPart]]:
        """Find a feature.

        Parameters
        ----------
        name : str
            Name of the feature.
            Possibility to look also for bodies, faces, subpart.
            Example "BodyName/FaceName", "SubPartName/BodyName/FaceName"

        Returns
        -------
        Union[ansys.speos.script.body.Body, ansys.speos.script.part.Part.SubPart], optional
            Found feature, or None.
        """
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
