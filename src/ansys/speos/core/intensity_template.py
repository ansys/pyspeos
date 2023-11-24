"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.intensity.v1 import intensity_pb2 as messages
from ansys.api.speos.intensity.v1 import intensity_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub

IntensityTemplate = messages.IntensityTemplate


class IntensityTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def get(self) -> IntensityTemplate:
        return self._stub.read(self)

    def set(self, data: IntensityTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class IntensityTemplateStub(CrudStub):
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

    def list(self) -> list[IntensityTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: IntensityTemplateLink(self, x), guids))


class IntensityTemplateHelper:
    def create_library(
        intensity_template_stub: IntensityTemplateStub, name: str, description: str, file_uri: str
    ) -> IntensityTemplateLink:
        intens = IntensityTemplate(name=name, description=description)
        intens.library.intensity_file_uri = file_uri
        return intensity_template_stub.create(message=intens)

    def create_lambertian(
        intensity_template_stub: IntensityTemplateStub, name: str, description: str, total_angle: float
    ) -> IntensityTemplateLink:
        intens = IntensityTemplate(name=name, description=description)
        intens.lambertian.total_angle = total_angle
        return intensity_template_stub.create(message=intens)

    def create_cos(
        intensity_template_stub: IntensityTemplateStub, name: str, description: str, N: float, total_angle: float
    ) -> IntensityTemplateLink:
        intens = IntensityTemplate(name=name, description=description)
        intens.cos.N = N
        intens.cos.total_angle = total_angle
        return intensity_template_stub.create(message=intens)

    def create_symmetric_gaussian(
        intensity_template_stub: IntensityTemplateStub,
        name: str,
        description: str,
        FWHM_angle: float,
        total_angle: float,
    ) -> IntensityTemplateLink:
        intens = IntensityTemplate(name=name, description=description)
        intens.symmetric_gaussian.FWHM_angle = FWHM_angle
        intens.symmetric_gaussian.total_angle = total_angle
        return intensity_template_stub.create(message=intens)

    def create_asymmetric_gaussian(
        intensity_template_stub: IntensityTemplateStub,
        name: str,
        description: str,
        FWHM_angle_x: float,
        FWHM_angle_y: float,
        total_angle: float,
    ) -> IntensityTemplateLink:
        intens = IntensityTemplate(name=name, description=description)
        intens.asymmetric_gaussian.FWHM_angle_x = FWHM_angle_x
        intens.asymmetric_gaussian.FWHM_angle_y = FWHM_angle_y
        intens.asymmetric_gaussian.total_angle = total_angle
        return intensity_template_stub.create(message=intens)
