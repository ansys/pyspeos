"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping, Optional

from ansys.api.speos.intensity.v1 import intensity_pb2 as messages
from ansys.api.speos.intensity.v1 import intensity_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

IntensityTemplate = messages.IntensityTemplate
IntensityTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class IntensityTemplateLink(CrudItem):
    """
    Link object for intensity template in database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.intensity_template import IntensityTemplateFactory
    >>> speos = Speos(host="localhost", port=50051)
    >>> int_t_db = speos.client.intensity_templates()
    >>> int_t_link = int_t_db.create(message=IntensityTemplateFactory.lambertian(name="Lambertian_170", total_angle=170))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return str(self.get())

    def get(self) -> IntensityTemplate:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: IntensityTemplate) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class IntensityTemplateStub(CrudStub):
    """
    Database interactions for intensity templates.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> int_t_db = speos.client.intensity_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.IntensityTemplatesManagerStub(channel=channel))

    def create(self, message: IntensityTemplate) -> IntensityTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(intensity_template=message))
        return IntensityTemplateLink(self, resp.guid)

    def read(self, ref: IntensityTemplateLink) -> IntensityTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.intensity_template

    def update(self, ref: IntensityTemplateLink, data: IntensityTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, intensity_template=data))

    def delete(self, ref: IntensityTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[IntensityTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: IntensityTemplateLink(self, x), guids))


class IntensityTemplateFactory:
    """Class to help creating IntensityTemplate message"""

    def library(
        name: str, file_uri: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> IntensityTemplate:
        """
        Create a IntensityTemplate message, with library type.

        Parameters
        ----------
        name : str
            Name of the intensity template.
        file_uri : str
            Uri of the intensity file IES (.ies), Eulumdat (.ldt), speos intensities (.xmp).
        description : str, optional
            Description of the intensity template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the intensity template.
            By default, ``None``.

        Returns
        -------
        IntensityTemplate
            IntensityTemplate message created.
        """
        intens = IntensityTemplate(name=name, description=description)
        if metadata is not None:
            intens.metadata.update(metadata)
        intens.library.intensity_file_uri = file_uri
        return intens

    def lambertian(
        name: str, total_angle: Optional[float] = 180, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> IntensityTemplate:
        """
        Create a IntensityTemplate message, with lambertian type.

        Parameters
        ----------
        name : str
            Name of the intensity template.
        total_angle : float, optional
            Total angle in degrees of the emission of the light source.
            By default, ``180``.
        description : str, optional
            Description of the intensity template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the intensity template.
            By default, ``None``.

        Returns
        -------
        IntensityTemplate
            IntensityTemplate message created.
        """
        intens = IntensityTemplate(name=name, description=description)
        if metadata is not None:
            intens.metadata.update(metadata)
        intens.lambertian.total_angle = total_angle
        return intens

    def cos(
        name: str,
        N: Optional[float] = 3,
        total_angle: Optional[float] = 180,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> IntensityTemplate:
        """
        Create a IntensityTemplate message, with cos type.

        Parameters
        ----------
        name : str
            Name of the intensity template.
        N : float, optional
            Order of cos law.
            By default, ``3``.
        total_angle : float, optional
            Total angle in degrees of the emission of the light source.
            By default, ``180``.
        description : str, optional
            Description of the intensity template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the intensity template.
            By default, ``None``.

        Returns
        -------
        IntensityTemplate
            IntensityTemplate message created.
        """
        intens = IntensityTemplate(name=name, description=description)
        if metadata is not None:
            intens.metadata.update(metadata)
        intens.cos.N = N
        intens.cos.total_angle = total_angle
        return intens

    def symmetric_gaussian(
        name: str,
        FWHM_angle: Optional[float] = 30,
        total_angle: Optional[float] = 180,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> IntensityTemplate:
        """
        Create a IntensityTemplate message, with symmetric gaussian type.

        Parameters
        ----------
        name : str
            Name of the intensity template.
        FWHM_angle : float, optional
            Full Width in degrees at Half Maximum.
            By default, ``30``.
        total_angle : float, optional
            Total angle in degrees of the emission of the light source.
            By default, ``180``.
        description : str, optional
            Description of the intensity template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the intensity template.
            By default, ``None``.

        Returns
        -------
        IntensityTemplate
            IntensityTemplate message created.
        """
        intens = IntensityTemplate(name=name, description=description)
        if metadata is not None:
            intens.metadata.update(metadata)
        intens.symmetric_gaussian.FWHM_angle = FWHM_angle
        intens.symmetric_gaussian.total_angle = total_angle
        return intens

    def asymmetric_gaussian(
        name: str,
        FWHM_angle_x: Optional[float] = 30,
        FWHM_angle_y: Optional[float] = 30,
        total_angle: Optional[float] = 180,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> IntensityTemplate:
        """
        Create a IntensityTemplate message, with asymmetric gaussian type.

        Parameters
        ----------
        name : str
            Name of the intensity template.
        FWHM_angle_x : float, optional
            Full Width in degrees following x at Half Maximum.
            By default, ``30``.
        FWHM_angle_y : float, optional
            Full Width in degrees following y at Half Maximum.
            By default, ``30``.
        total_angle : float, optional
            Total angle in degrees of the emission of the light source.
            By default, ``180``.
        description : str, optional
            Description of the intensity template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the intensity template.
            By default, ``None``.

        Returns
        -------
        IntensityTemplate
            IntensityTemplate message created.
        """
        intens = IntensityTemplate(name=name, description=description)
        if metadata is not None:
            intens.metadata.update(metadata)
        intens.asymmetric_gaussian.FWHM_angle_x = FWHM_angle_x
        intens.asymmetric_gaussian.FWHM_angle_y = FWHM_angle_y
        intens.asymmetric_gaussian.total_angle = total_angle
        return intens
