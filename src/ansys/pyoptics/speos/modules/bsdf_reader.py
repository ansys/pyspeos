import ansys.api.speos.bsdf.v1.bsdf_creation_pb2 as bsdf_creation__v1__pb2
import ansys.api.speos.bsdf.v1.bsdf_creation_pb2_grpc as bsdf_creation__v1__pb2_grpc
from ansys.pyoptics import speos

class bsdf_analysis():
    def __init__(self, port):
        self.port = port
        self.stub = speos.get_stub_insecure_channel(
            port=self.port, stub_type=bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub)

    def bsdf180(self, input_file_1, input_file_2, output_file):
        bsdf180_request = bsdf_creation__v1__pb2.Bsdf180InputData()
        bsdf180_request.input_front_bsdf_file_name = input_file_1
        bsdf180_request.input_opposite_bsdf_file_name = input_file_2
        bsdf180_request.output_file_name = output_file
        self.stub.BuildBsdf180(bsdf180_request)

    def spectral(self, input_file, output_file, wavelengths):
        spectral_request = bsdf_creation__v1__pb2.SpectralBsdfInputData()
        for wavelength in wavelengths:
            tmp = spectral_request.input_anisotropic_samples.add()
            tmp.wavelength = wavelength
            tmp.file_name = input_file
        spectral_request.output_file_name = output_file
        self.stub.BuildSpectralBsdf(spectral_request)

    def Anisotropic(self, input_file, output_file, angles):
        anisotropic_request = bsdf_creation__v1__pb2.AnisotropicBsdfInputData()
        for angle in angles:
            temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
            temp.anisotropic_angle = angle
            temp.file_name = input_file
        anisotropic_request.fix_disparity = False
        anisotropic_request.output_file_name = output_file
        self.stub.BuildAnisotropicBsdf(anisotropic_request)
