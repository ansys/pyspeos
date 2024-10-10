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

"""Provides a way to interact with feature: Face."""
from __future__ import annotations

from typing import List, Mapping, Optional

import ansys.speos.core as core
import ansys.speos.script.body as body


class Face:
    """Feature : Face.

    Parameters
    ----------
    speos_client : ansys.speos.core.client.SpeosClient
        The Speos instance client.
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
    face_link : ansys.speos.core.face.FaceLink
        Link object for the face in database.
    """

    def __init__(
        self,
        speos_client: core.SpeosClient,
        name: str,
        description: str = "",
        metadata: Mapping[str, str] = {},
        parent_body: Optional[body.Body] = None,
    ) -> None:
        self._speos_client = speos_client
        self._parent_body = parent_body
        self._name = name
        self.face_link = None
        """Link object for the face in database."""

        # Create local Face
        self._face = core.Face(name=name, description=description, metadata=metadata)

    def set_vertices(self, values: List[float]) -> Face:
        self._face.vertices[:] = values
        return self

    def set_facets(self, values: List[int]) -> Face:
        self._face.facets[:] = values
        return self

    def set_normals(self, values: List[float]) -> Face:
        self._face.normals[:] = values
        return self

    def __str__(self) -> str:
        """Return the string representation of the face."""
        out_str = ""

        if self.face_link is None:
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._face)
        else:
            out_str += "\n" + str(self.face_link)

        return out_str

    def commit(self) -> Face:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.face.Face
            Face feature.
        """
        # Save or Update the face (depending on if it was already saved before)
        if self.face_link is None:
            self.face_link = self._speos_client.faces().create(message=self._face)
        else:
            self.face_link.set(data=self._face)

        # Update the parent body
        if self._parent_body is not None:
            if self.face_link.key not in self._parent_body._body.face_guids:
                self._parent_body._body.face_guids.append(self.face_link.key)
                if self._parent_body.body_link is not None:
                    self._parent_body.body_link.set(data=self._parent_body._body)

        return self

    def reset(self) -> Face:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.face.Face
            Face feature.
        """
        # Reset face
        if self.face_link is not None:
            self._face = self.face_link.get()

        return self

    def delete(self) -> Face:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.face.Face
            Face feature.
        """
        if self.face_link is not None:
            # Update the parent body
            if self._parent_body is not None:
                if self.face_link.key in self._parent_body._body.face_guids:
                    self._parent_body._body.face_guids.remove(self.face_link.key)
                    if self._parent_body.body_link is not None:
                        self._parent_body.body_link.set(data=self._parent_body._body)

            # Delete the face
            self.face_link.delete()
            self.face_link = None

            if self in self._parent_body._geom_features:
                self._parent_body._geom_features.remove(self)

        return self
