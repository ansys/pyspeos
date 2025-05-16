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

"""Provides a way to interact with feature: Face."""

from __future__ import annotations

from typing import List, Mapping, Optional

from ansys.speos.core import proto_message_utils
import ansys.speos.core.body as body
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.face import ProtoFace


class Face:
    """Feature : Face.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    parent_body : ansys.speos.core.body.Body, optional
        Feature containing this face.
        By default, ``None``.

    Attributes
    ----------
    face_link : ansys.speos.core.kernel.face.FaceLink
        Link object for the face in database.
    """

    def __init__(
        self,
        speos_client: SpeosClient,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        parent_body: Optional[body.Body] = None,
    ) -> None:
        self._speos_client = speos_client
        self._parent_body = parent_body
        self._name = name
        self.face_link = None
        """Link object for the face in database."""
        if metadata is None:
            metadata = {}

        # Create local Face
        self._face = ProtoFace(name=name, description=description, metadata=metadata)

    @property
    def geo_path(self) -> GeoRef:
        """Geometry path to be used within other speos objects."""
        geo_paths = [self._name]
        parent = self._parent_body
        if isinstance(parent, body.Body):
            geo_paths.insert(0, parent.geo_path.metadata["GeoPath"])
        return GeoRef.from_native_link("/".join(geo_paths))

    def set_vertices(self, values: List[float]) -> Face:
        """Set the face vertices.

        Parameters
        ----------
        values : List[float]
            Coordinates of all points [p1x p1y p1z p2x p2y p2z ...].

        Returns
        -------
        ansys.speos.core.face.Face
            Face feature.
        """
        self._face.vertices[:] = values
        return self

    def set_facets(self, values: List[int]) -> Face:
        """Set the facets.

        Parameters
        ----------
        values : List[int]
            Indexes of points for all triangles (t1_1 t1_2 t1_3 t2_1 t2_2 t2_3 ...)

        Returns
        -------
        ansys.speos.core.face.Face
            Face feature.
        """
        self._face.facets[:] = values
        return self

    def set_normals(self, values: List[float]) -> Face:
        """Set the face normals.

        Parameters
        ----------
        values : List[float]
            Normal vectors for all points [n1x n1y n1z n2x n2y n2z ...]

        Returns
        -------
        ansys.speos.core.face.Face
            Face feature.
        """
        self._face.normals[:] = values
        return self

    def _to_dict(self) -> dict:
        out_dict = ""

        if self.face_link is None:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._speos_client, message=self._face
            )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._speos_client, message=self.face_link.get()
            )

        return out_dict

    def __str__(self) -> str:
        """Return the string representation of the face."""
        out_str = ""

        if self.face_link is None:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def commit(self) -> Face:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.face.Face
            Face feature.
        """
        # Save or Update the face (depending on if it was already saved before)
        if self.face_link is None:
            self.face_link = self._speos_client.faces().create(message=self._face)
        elif self.face_link.get() != self._face:
            self.face_link.set(data=self._face)  # Only Update if data has changed

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
        ansys.speos.core.face.Face
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
        ansys.speos.core.face.Face
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
