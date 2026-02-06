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

"""Provides a way to interact with Speos feature: Intensity."""

from __future__ import annotations

from pathlib import Path
from typing import List, Mapping, Optional, Union

import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.intensity_template import ProtoIntensityTemplate
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_dict
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.proto_message_utils import dict_to_str


class Intensity:
    """Speos feature : Intensity.

    By default, a lambertian intensity is created (cos with N=1 and total_angle=180).

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
    intensity_props_to_complete : \
    ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties, optional
        Intensity properties to complete.
        By default, ``None``.
    key : str
        Creation from an IntensityTemplateLink key

    Attributes
    ----------
    intensity_template_link : ansys.speos.core.kernel.intensity_template.IntensityTemplateLink
        Link object for the intensity template in database.
    """

    class Library:
        """Intensity of type: Library.

        By default, orientation as axis system is chosen and no exit geometries.

        Parameters
        ----------
        library : ansys.api.speos.intensity.v1.IntensityTemplate.Library
            Library to complete.
        library_props : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties.LibraryProperties
            Library properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            library: ProtoIntensityTemplate.Library,
            library_props: ProtoScene.SourceInstance.IntensityProperties.LibraryProperties,
            default_values: bool = True,
        ) -> None:
            self._library = library
            self._library_props = library_props

            if default_values:
                # Default values
                self.set_orientation_axis_system()

        @property
        def intensity_file_uri(self) -> str:
            """Property of the intensity file uri.

            Parameters
            ----------
            uri : str
                uri of the intensity file IES (.ies), Eulumdat (.ldt), speos intensities (.xmp)

            Returns
            -------
            uri : str
                uri of the intensity file IES (.ies), Eulumdat (.ldt), speos intensities (.xmp)
            """
            return self._library.intensity_file_uri

        @intensity_file_uri.setter
        def intensity_file_uri(self, intensity_file_uri: Union[Path, str]) -> None:
            self._library.intensity_file_uri = str(intensity_file_uri)

        def set_orientation_axis_system(
            self, axis_system: Optional[List[float]] = None
        ) -> Intensity.Library:
            """Set the intensity orientation from an axis system.

            Parameters
            ----------
            axis_system : Optional[List[float]]
                Orientation of the intensity [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz]
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.core.intensity.Intensity.Library
                Library intensity.
            """
            if not axis_system:
                axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
            self._library_props.axis_system.values[:] = axis_system
            return self

        def set_orientation_normal_to_surface(self) -> Intensity.Library:
            """Set the intensity orientation as normal to surface.

            Returns
            -------
            ansys.speos.core.intensity.Intensity.Library
                Library intensity.
            """
            self._library_props.normal_to_surface.SetInParent()
            return self

        def set_orientation_normal_to_uv_map(self) -> Intensity.Library:
            """Set the intensity orientation as normal to uv map.

            Returns
            -------
            ansys.speos.core.intensity.Intensity.Library
                Library intensity.
            """
            self._library_props.normal_to_uv_map.SetInParent()
            return self

        @property
        def exit_geometries(self) -> List[GeoRef]:
            """Property of exit geometries.

            Parameters
            ----------
            exit_geometries : Optional[List[Union[GeoRef, body.Body, face.Face]]]
                Exit geometries list.
                By default, ``[]``.

            Returns
            -------
            List[ansys.speos.core.geo_ref.GeoRef]
                List of GeoRef of geometries.
            """
            if self._library_props.HasField("exit_geometries"):
                return self._library_props.exit_geometries.geo_paths

        @exit_geometries.setter
        def exit_geometries(
            self, exit_geometries: Optional[List[Union[GeoRef, body.Body, face.Face]]] = None
        ) -> None:
            if not exit_geometries:
                self._library_props.ClearField("exit_geometries")
            else:
                geo_paths = []
                for geometry in exit_geometries:
                    if isinstance(geometry, GeoRef):
                        geo_paths.append(geometry.to_native_link())
                    elif isinstance(geometry, (body.Body, face.Face)):
                        geo_paths.append(geometry.geo_path)
                    else:
                        raise ValueError("provided geometry is not of type supported")
                self._library_props.exit_geometries.geo_paths[:] = geo_paths

    class Gaussian:
        """Intensity of type: Gaussian.

        By default, full width at half maximum following x and y are set at 30 degrees, and total
        angle at 180 degrees.
        By default, no axis system is chosen, that means normal to surface map.

        Parameters
        ----------
        gaussian : ansys.api.speos.intensity.v1.IntensityTemplate.Gaussian
            Gaussian to complete.
        gaussian_props : \
        ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties.GaussianProperties
            Gaussian properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            gaussian: ProtoIntensityTemplate.Gaussian,
            gaussian_props: ProtoScene.SourceInstance.IntensityProperties.GaussianProperties,
            default_values: bool = True,
        ) -> None:
            self._gaussian = gaussian
            self._gaussian_props = gaussian_props

            if default_values:
                # Default values
                self.fwhm_angle_x = 30.0
                self.fwhm_angle_y = 30.0
                self.total_angle = 180.0
                self.axis_system = None

        @property
        def fwhm_angle_x(self) -> float:
            """Property of the full width following x at half maximum.

            Parameters
            ----------
            value : float
                Full Width in degrees following x at Half Maximum.
                By default, ``30.0``.

            Returns
            -------
            value : float
                Full Width in degrees following x at Half Maximum.
            """
            return self._gaussian.FWHM_angle_x

        @fwhm_angle_x.setter
        def fwhm_angle_x(self, fwhm_angle_x: float) -> None:
            self._gaussian.FWHM_angle_x = fwhm_angle_x

        @property
        def fwhm_angle_y(self) -> float:
            """Property of the full width following y at half maximum.

            Parameters
            ----------
            value : float
                Full Width in degrees following y at Half Maximum.
                By default, ``30.0``.

            Returns
            -------
            value : float
                Full Width in degrees following y at Half Maximum.
            """
            return self._gaussian.FWHM_angle_y

        @fwhm_angle_y.setter
        def fwhm_angle_y(self, fwhm_angle_y: float) -> None:
            self._gaussian.FWHM_angle_y = fwhm_angle_y

        @property
        def total_angle(self) -> float:
            """Property of total angle of the emission of the light source.

            Parameters
            ----------
            value : float
                Total angle in degrees of the emission of the light source.
                By default, ``180.0``.

            Returns
            -------
            value : float
                Total angle in degrees of the emission of the light source.
            """
            return self._gaussian.total_angle

        @total_angle.setter
        def total_angle(self, total_angle: float) -> None:
            self._gaussian.total_angle = total_angle

        @property
        def axis_system(self) -> float:
            """Property the intensity distribution axis system orientation.

            Parameters
            ----------
            axis_system : List[float], optional
                Orientation of the intensity distribution [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``None`` : normal to surface map.

            Returns
            -------
            axis_system : List[float]
                Orientation of the intensity distribution [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            """
            return self._gaussian.total_angle

        @axis_system.setter
        def axis_system(self, axis_system: Optional[List[float]] = None) -> None:
            self._gaussian_props.Clear()
            if axis_system is None:
                self._gaussian_props.SetInParent()
            else:
                self._gaussian_props.axis_system[:] = axis_system

    class Cos:
        """Intensity of type: Cos.

        By default, Order of cos law 3, total angle in degrees of the source emission 180.0.

        Parameters
        ----------
        cos : ansys.api.speos.intensity.v1.IntensityTemplate.Cos
            Cos to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            cos: ProtoIntensityTemplate.Cos,
            default_values: bool = True,
        ) -> None:
            self._cos = cos

            if default_values:
                # Default values
                self.n = 3
                self.total_angle = 180.0

        @property
        def n(self) -> float:
            """Property of order of cos law.

            Parameters
            ----------
            value : float
                order of cos law.
                By default, ``3``.

            Returns
            -------
            value : float
                order of cos law.
            """
            return self._cos.N

        @n.setter
        def n(self, n: float) -> None:
            self._cos.N = n

        @property
        def total_angle(self) -> float:
            """Property of total angle of the emission of the light source.

            Parameters
            ----------
            value : float
                Total angle in degrees of the emission of the light source.
                By default, ``180.0``.

            Returns
            -------
            value : float
                Total angle in degrees of the emission of the light source.
            """
            return self._cos.total_angle

        @total_angle.setter
        def total_angle(self, total_angle: float) -> None:
            self._cos.total_angle = total_angle

    def __init__(
        self,
        speos_client: SpeosClient,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        intensity_props_to_complete: Optional[ProtoScene.SourceInstance.IntensityProperties] = None,
        key: str = "",
    ) -> None:
        self._client = speos_client
        self.intensity_template_link = None
        """Link object for the intensity template in database."""

        if metadata is None:
            metadata = {}

        # Attribute representing the more complex intensity.
        self._type = None

        # Create IntensityProperties
        self._intensity_properties = ProtoScene.SourceInstance.IntensityProperties()
        self._light_print = False
        if intensity_props_to_complete is not None:
            self._intensity_properties = intensity_props_to_complete
            self._light_print = True

        if key == "":
            # Create IntensityTemplate
            self._intensity_template = ProtoIntensityTemplate(
                name=name, description=description, metadata=metadata
            )

            # Default values
            self.set_cos().n = 1  # By default will be lambertian (cos with N =1)
        else:
            # Retrieve IntensityTemplate
            self.intensity_template_link = speos_client[key]
            self._intensity_template = self.intensity_template_link.get()

    def set_library(self) -> Intensity.Library:
        """Set the intensity as library.

        Returns
        -------
        ansys.speos.core.intensity.Intensity.Library
            Library intensity.
        """
        if self._type is None and self._intensity_template.HasField("library"):
            # Happens in case of project created via load of speos file
            self._type = Intensity.Library(
                library=self._intensity_template.library,
                library_props=self._intensity_properties.library_properties,
                default_values=False,
            )
        elif not isinstance(self._type, Intensity.Library):
            # if the _type is not Library then we create a new type.
            self._type = Intensity.Library(
                library=self._intensity_template.library,
                library_props=self._intensity_properties.library_properties,
            )
        elif (
            self._type._library is not self._intensity_template.library
            or self._type._library_props is not self._intensity_properties.library_properties
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._library = self._intensity_template.library
            self._type._library_props = self._intensity_properties.library_properties
        return self._type

    def set_cos(self):
        """Set the intensity as cos.

        Returns
        -------
        ansys.speos.core.intensity.Intensity.Cos
            intensity Cos feature type to complete.
        """
        if self._type is None and self._intensity_template.HasField("cos"):
            # Happens in case of project created via load of speos file
            self._type = Intensity.Cos(
                cos=self._intensity_template.cos,
                default_values=False,
            )
        elif not isinstance(self._type, Intensity.Cos):
            # if the _type is not Gaussian then we create a new type.
            self._type = Intensity.Cos(
                cos=self._intensity_template.cos,
            )
        elif self._type._cos is not self._intensity_template.cos:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._cos = self._intensity_template.cos
        self._intensity_properties.Clear()
        return self._type

    def set_gaussian(self) -> Intensity.Gaussian:
        """Set the intensity as gaussian.

        Returns
        -------
        ansys.speos.core.intensity.Intensity.Gaussian
            Gaussian intensity.
        """
        if self._type is None and self._intensity_template.HasField("gaussian"):
            # Happens in case of project created via load of speos file
            self._type = Intensity.Gaussian(
                gaussian=self._intensity_template.gaussian,
                gaussian_props=self._intensity_properties.gaussian_properties,
                default_values=False,
            )
        elif not isinstance(self._type, Intensity.Gaussian):
            # if the _type is not Gaussian then we create a new type.
            self._type = Intensity.Gaussian(
                gaussian=self._intensity_template.gaussian,
                gaussian_props=self._intensity_properties.gaussian_properties,
            )
        elif (
            self._type._gaussian is not self._intensity_template.gaussian
            or self._type._gaussian_props is not self._intensity_properties.gaussian_properties
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._gaussian = self._intensity_template.gaussian
            self._type._gaussian_props = self._intensity_properties.gaussian_properties
        return self._type

    @property
    def type(self) -> type:
        """Return type of sensor.

        Returns
        -------
        Example: None for lambertian or ansys.speos.core.intensity.Intensity.Library

        """
        return type(self._type)

    def _to_dict(self) -> dict:
        out_dict = {}
        if self.intensity_template_link is None:
            out_dict = protobuf_message_to_dict(self._intensity_template)
        else:
            out_dict = protobuf_message_to_dict(message=self.intensity_template_link.get())

        if self._light_print is False:
            out_dict["intensity_properties"] = protobuf_message_to_dict(
                message=self._intensity_properties
            )

        return out_dict

    def __str__(self) -> str:
        """Return the string representation of the intensity."""
        out_str = ""
        if self.intensity_template_link is None:
            out_str += "local: "
        out_str += dict_to_str(self._to_dict())
        return out_str

    def commit(self) -> Intensity:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.intensity.Intensity
            Intensity feature.
        """
        if self.intensity_template_link is None:
            self.intensity_template_link = self._client.intensity_templates().create(
                message=self._intensity_template
            )
        elif self.intensity_template_link.get() != self._intensity_template:
            self.intensity_template_link.set(
                data=self._intensity_template
            )  # Only update if template has changed

        return self

    def reset(self) -> Intensity:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.intensity.Intensity
            Intensity feature.
        """
        if self.intensity_template_link is not None:
            self._intensity_template = self.intensity_template_link.get()
        return self

    def delete(self) -> Intensity:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.intensity.Intensity
            Intensity feature.
        """
        if self.intensity_template_link is not None:
            self.intensity_template_link.delete()
            self.intensity_template_link = None
        return self
