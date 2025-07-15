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

"""Provides a way to interact with feature: Body."""

from __future__ import annotations

import re
from typing import List, Mapping, Optional, Union

from ansys.speos.core import proto_message_utils
import ansys.speos.core.face as face
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.visualization_methods import _VisualData
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.body import ProtoBody
from ansys.speos.core.kernel.client import SpeosClient
import ansys.speos.core.part as part


class Body:
    """Feature : Body.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.
    parent_part : Union[ansys.speos.core.part.Part, ansys.speos.core.part.Part.SubPart], optional
        Feature containing this sub part.
        By default, ``None``.

    Attributes
    ----------
    body_link : ansys.speos.core.kernel.body.BodyLink
        Link object for the body in database.
    """

    def __init__(
        self,
        speos_client: SpeosClient,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        parent_part: Optional[Union[part.Part, part.Part.SubPart]] = None,
    ) -> None:
        self._speos_client = speos_client
        self._parent_part = parent_part
        self._name = name
        self.body_link = None
        self._visual_data = _VisualData() if general_methods._GRAPHICS_AVAILABLE else None
        """Link object for the body in database."""

        if metadata is None:
            metadata = {}

        # Create local Body
        self._body = ProtoBody(name=name, description=description, metadata=metadata)

        self._geom_features = []

    @property
    def visual_data(self):
        """Property containing irradiance sensor visualization data.

        Returns
        -------
        VisualData
            Instance of VisualData Class for pyvista.PolyData of feature faces, coordinate_systems.

        """
        import numpy as np

        if self._visual_data.updated is True:
            return self._visual_data
        for feature_face in self._geom_features:
            vertices = np.array(feature_face._face.vertices).reshape(-1, 3)
            facets = np.array(feature_face._face.facets).reshape(-1, 3)
            temp = np.full(facets.shape[0], 3)
            temp = np.vstack(temp)
            facets = np.hstack((temp, facets))
            self._visual_data.add_data_mesh(vertices, facets)
        self._visual_data.updated = True
        return self._visual_data

    @property
    def geo_path(self) -> GeoRef:
        """Geometry path to be used within other speos objects."""
        geo_paths = [self._name]
        if isinstance(self._parent_part, part.Part.SubPart):
            geo_paths.insert(0, self._parent_part.geo_path.metadata["GeoPath"])
        return GeoRef.from_native_link("/".join(geo_paths))

    def create_face(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> face.Face:
        """Create a face in this element.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.core.face.Face
            Face feature.
        """
        if metadata is None:
            metadata = {}

        face_feat = face.Face(
            speos_client=self._speos_client,
            name=name,
            description=description,
            metadata=metadata,
            parent_body=self,
        )
        self._geom_features.append(face_feat)
        return face_feat

    def _to_dict(self) -> dict:
        out_dict = ""

        if self.body_link is None:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._speos_client, message=self._body
            )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._speos_client, message=self.body_link.get()
            )

        return out_dict

    def __str__(self) -> str:
        """Return the string representation of the body."""
        out_str = ""

        if self.body_link is None:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def commit(self) -> Body:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.body.Body
            Body feature.
        """
        if general_methods._GRAPHICS_AVAILABLE:
            self._visual_data.updated = False

        # Commit faces contained in this body
        for g in self._geom_features:
            g.commit()

        # Save or Update the body (depending on if it was already saved before)
        if self.body_link is None:
            self.body_link = self._speos_client.bodies().create(message=self._body)
        elif self.body_link.get() != self._body:
            self.body_link.set(data=self._body)  # Only Update if data has changed

        # Update the parent part
        if self._parent_part is not None:
            if self.body_link.key not in self._parent_part._part.body_guids:
                self._parent_part._part.body_guids.append(self.body_link.key)
                if self._parent_part.part_link is not None:
                    self._parent_part.part_link.set(data=self._parent_part._part)

        return self

    def reset(self) -> Body:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.body.Body
            Body feature.
        """
        # Reset body
        if self.body_link is not None:
            self._body = self.body_link.get()

        return self

    def delete(self) -> Body:
        """Delete feature: delete data from the speos server database.

        Returns
        -------
        ansys.speos.core.body.Body
            Body feature.
        """
        # Retrieve all features to delete them
        while len(self._geom_features) > 0:
            self._geom_features[0].delete()

        if self.body_link is not None:
            # Update the parent part
            if self._parent_part is not None:
                if self.body_link.key in self._parent_part._part.body_guids:
                    self._parent_part._part.body_guids.remove(self.body_link.key)
                    if self._parent_part.part_link is not None:
                        self._parent_part.part_link.set(data=self._parent_part._part)

            # Delete the body
            self.body_link.delete()
            self.body_link = None

        if self in self._parent_part._geom_features:
            self._parent_part._geom_features.remove(self)

        return self

    def find(
        self,
        name: str,
        name_regex: bool = False,
        feature_type: Optional[type] = None,
    ) -> List[face.Face]:
        """Find feature(s). In a body, only faces features can be found.

        Parameters
        ----------
        name : str
            Name of the feature.
            Example "FaceName"
        name_regex : bool
            Allows to use regex for name parameter.
            By default, ``False``, means that regex is not used for name parameter.
        feature_type : type
            Type of the wanted feature (example: ansys.speos.core.face.Face).
            By default, ``None``, means that all features will be considered.

        Returns
        -------
        List[ansys.speos.core.face.Face]
            Found features.
        """
        found_features = []
        if feature_type == face.Face or feature_type is None:
            if name_regex:
                p = re.compile(name)
                found_features.extend([x for x in self._geom_features if p.match(x._name)])
            else:
                found_features.extend([x for x in self._geom_features if x._name == name])

        return found_features
