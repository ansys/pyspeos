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

"""Provides a way to interact with Speos feature: Intensity."""
from __future__ import annotations

from typing import List, Mapping, Optional

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef


class Intensity:
    """Speos feature : Intensity.
    By default, a lambertian intensity is created (cos with N=1 and total_angle=180).

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
    intensity_props_to_complete : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties, optional
        Intensity properties to complete.
        By default, ``None``.
    key : str
        Creation from an IntensityTemplateLink key

    Attributes
    ----------
    intensity_template_link : ansys.speos.core.intensity_template.IntensityTemplateLink
        Link object for the intensity template in database.
    """

    class Library:
        """Intensity of type: Library.
        By default, orientation as axis system is chosen and no exit geometries.

        Parameters
        ----------
        library : ansys.api.speos.intensity.v1.IntensityTemplate.Library
            Library to complete.
        library_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties.LibraryProperties
            Library properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            library: core.IntensityTemplate.Library,
            library_props: core.Scene.SourceInstance.IntensityProperties.LibraryProperties,
            default_values: bool = True,
        ) -> None:
            self._library = library
            self._library_props = library_props

            if default_values:
                # Default values
                self.set_orientation_axis_system()

        def set_intensity_file_uri(self, uri: str) -> Intensity.Library:
            """Set the intensity file.

            Parameters
            ----------
            uri : str
                uri of the intensity file IES (.ies), Eulumdat (.ldt), speos intensities (.xmp)

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Library
                Intensity feature of type library.
            """
            self._library.intensity_file_uri = uri
            return self

        def set_orientation_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Intensity.Library:
            """Set the intensity orientation from an axis system.

            Parameters
            ----------
            axis_system : List[float]
                Orientation of the intensity [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz]
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Library
                Library intensity.
            """
            self._library_props.axis_system.values[:] = axis_system
            return self

        def set_orientation_normal_to_surface(self) -> Intensity.Library:
            """Set the intensity orientation as normal to surface.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Library
                Library intensity.
            """
            self._library_props.normal_to_surface.SetInParent()
            return self

        def set_orientation_normal_to_uv_map(self) -> Intensity.Library:
            """Set the intensity orientation as normal to uv map.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Library
                Library intensity.
            """
            self._library_props.normal_to_uv_map.SetInParent()
            return self

        def set_exit_geometries(self, exit_geometries: List[GeoRef] = []) -> Intensity.Library:
            """Set the exit geometries.

            Parameters
            ----------
            exit_geometries : List[ansys.speos.script.geo_ref.GeoRef]
                Exit geometries list.
                By default, ``[]``.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Library
                Library intensity.
            """

            if exit_geometries == []:
                self._library_props.ClearField("exit_geometries")
            else:
                self._library_props.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
            return self

    class Gaussian:
        """Intensity of type: Gaussian.
        By default, full width at half maximum following x and y are set at 30 degrees, and total angle at 180 degrees.
        By default, no axis system is chosen, that means normal to surface map.

        Parameters
        ----------
        gaussian : ansys.api.speos.intensity.v1.IntensityTemplate.Gaussian
            Gaussian to complete.
        gaussian_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties.GaussianProperties
            Gaussian properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            gaussian: core.IntensityTemplate.Gaussian,
            gaussian_props: core.Scene.SourceInstance.IntensityProperties.GaussianProperties,
            default_values: bool = True,
        ) -> None:
            self._gaussian = gaussian
            self._gaussian_props = gaussian_props

            if default_values:
                # Default values
                self.set_FWHM_angle_x().set_FWHM_angle_y().set_total_angle().set_axis_system()

        def set_FWHM_angle_x(self, value: float = 30) -> Intensity.Gaussian:
            """Set the full width following x at half maximum.

            Parameters
            ----------
            value : float
                Full Width in degrees following x at Half Maximum.
                By default, ``30.0``.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Gaussian
                Gaussian intensity.
            """
            self._gaussian.FWHM_angle_x = value
            return self

        def set_FWHM_angle_y(self, value: float = 30) -> Intensity.Gaussian:
            """Set the full width following y at half maximum.

            Parameters
            ----------
            value : float
                Full Width in degrees following y at Half Maximum.
                By default, ``30.0``.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Gaussian
                Gaussian intensity.
            """
            self._gaussian.FWHM_angle_y = value
            return self

        def set_total_angle(self, value: float = 180) -> Intensity.Gaussian:
            """Set the total angle of the emission of the light source.

            Parameters
            ----------
            value : float
                Total angle in degrees of the emission of the light source.
                By default, ``180.0``.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Gaussian
                Gaussian intensity.
            """
            self._gaussian.total_angle = value
            return self

        def set_axis_system(self, axis_system: Optional[List[float]] = None) -> Intensity.Gaussian:
            """Set the intensity distribution orientation.

            Parameters
            ----------
            axis_system : List[float], optional
                Orientation of the intensity distribution [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``None`` : normal to surface map.

            Returns
            -------
            ansys.speos.script.intensity.Intensity.Gaussian
                Gaussian intensity.
            """
            self._gaussian_props.Clear()
            if axis_system is None:
                self._gaussian_props.SetInParent()
            else:
                self._gaussian_props.axis_system[:] = axis_system
            return self

    def __init__(
        self,
        speos_client: core.SpeosClient,
        name: str,
        description: str = "",
        metadata: Mapping[str, str] = {},
        intensity_props_to_complete: Optional[core.Scene.SourceInstance.IntensityProperties] = None,
        key: str = "",
    ) -> None:
        self._client = speos_client
        self.intensity_template_link = None
        """Link object for the intensity template in database."""

        # Attribute representing the more complex intensity.
        self._type = None

        # Create IntensityProperties
        self._intensity_properties = core.Scene.SourceInstance.IntensityProperties()
        self._light_print = False
        if intensity_props_to_complete is not None:
            self._intensity_properties = intensity_props_to_complete
            self._light_print = True

        if key == "":
            # Create IntensityTemplate
            self._intensity_template = core.IntensityTemplate(name=name, description=description, metadata=metadata)

            # Default values
            self.set_cos(N=1)  # By default will be lambertian (cos with N =1)
        else:
            # Retrieve IntensityTemplate
            self.intensity_template_link = speos_client.get_item(key=key)
            self._intensity_template = self.intensity_template_link.get()

    def set_library(self) -> Intensity.Library:
        """Set the intensity as library.

        Returns
        -------
        ansys.speos.script.intensity.Intensity.Library
            Library intensity.
        """
        if self._type is None and self._intensity_template.HasField("library"):
            self._type = Intensity.Library(
                library=self._intensity_template.library, library_props=self._intensity_properties.library_properties, default_values=False
            )
        elif type(self._type) != Intensity.Library:
            self._type = Intensity.Library(
                library=self._intensity_template.library, library_props=self._intensity_properties.library_properties
            )
        return self._type

    def set_cos(self, N: float = 3, total_angle: float = 180) -> Intensity:
        """Set the intensity as cos.

        Parameters
        ----------
        N : float
            Order of cos law.
            By default, ``3``.
        total_angle : float
            Total angle in degrees of the emission of the light source.
            By default, ``180.0``.

        Returns
        -------
        ansys.speos.script.intensity.Intensity
            Intensity feature.
        """
        self._type = None
        self._intensity_template.cos.N = N
        self._intensity_template.cos.total_angle = total_angle
        self._intensity_properties.Clear()
        return self

    def set_gaussian(self) -> Intensity.Gaussian:
        """Set the intensity as gaussian.

        Returns
        -------
        ansys.speos.script.intensity.Intensity.Gaussian
            Gaussian intensity.
        """
        if self._type is None and self._intensity_template.HasField("gaussian"):
            self._type = Intensity.Gaussian(
                gaussian=self._intensity_template.gaussian,
                gaussian_props=self._intensity_properties.gaussian_properties,
                default_values=False,
            )
        elif type(self._type) != Intensity.Gaussian:
            self._type = Intensity.Gaussian(
                gaussian=self._intensity_template.gaussian, gaussian_props=self._intensity_properties.gaussian_properties
            )
        return self._type

    def __str__(self) -> str:
        """Return the string representation of the intensity."""
        out_str = ""
        if self.intensity_template_link is None:
            out_str += f"local: " + core.protobuf_message_to_str(self._intensity_template)
        else:
            out_str += str(self.intensity_template_link)

        if self._light_print is False:
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._intensity_properties)
        return out_str

    def commit(self) -> Intensity:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.intensity.Intensity
            Intensity feature.
        """
        if self.intensity_template_link is None:
            self.intensity_template_link = self._client.intensity_templates().create(message=self._intensity_template)
        else:
            self.intensity_template_link.set(data=self._intensity_template)

        return self

    def reset(self) -> Intensity:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.intensity.Intensity
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
        ansys.speos.script.intensity.Intensity
            Intensity feature.
        """
        if self.intensity_template_link is not None:
            self.intensity_template_link.delete()
            self.intensity_template_link = None
        return self
