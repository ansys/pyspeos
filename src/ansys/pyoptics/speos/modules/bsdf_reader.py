import ansys.api.speos.bsdf.v1.bsdf_creation_pb2 as bsdf_creation__v1__pb2

class bsdf_analysis():

    @staticmethod
    def bsdf180(input_file_1, input_file_2, output_file):
        bsdf180_request = bsdf_creation__v1__pb2.Bsdf180InputData()
        bsdf180_request.input_front_bsdf_file_name = input_file_1
        bsdf180_request.input_opposite_bsdf_file_name = input_file_2
        bsdf180_request.output_file_name = output_file
        return bsdf180_request
    
    @staticmethod
    def spectral(input_file, output_file, wavelengths):
        spectral_request = bsdf_creation__v1__pb2.SpectralBsdfInputData()
        for wavelength in wavelengths:
            tmp = spectral_request.input_anisotropic_samples.add()
            tmp.wavelength = wavelength
            tmp.file_name = input_file
        spectral_request.output_file_name = output_file
        return spectral_request

    @staticmethod
    def Anisotropic(input_file, output_file, angles):
        anisotropic_request = bsdf_creation__v1__pb2.AnisotropicBsdfInputData()
        for angle in angles:
            temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
            temp.anisotropic_angle = angle
            temp.file_name = input_file
        anisotropic_request.fix_disparity = False
        anisotropic_request.output_file_name = output_file
        return anisotropic_request
