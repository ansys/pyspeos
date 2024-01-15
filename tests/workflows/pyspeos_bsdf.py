import math

import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2 as spectral_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2_grpc as spectral_bsdf__v1__pb2_grpc

import ansys.speos.core as core

speos = core.Speos(host="localhost", port=50051)
stub = spectral_bsdf__v1__pb2_grpc.SpectralBsdfServiceStub(speos.client.channel)
bsdf = spectral_bsdf__v1__pb2.SpectralBsdfData(description="test description")
nbw = 7
nbi = 10
for i in range(nbi):
    bsdf.incidence_samples.append(i * math.pi * 0.5 / (nbi - 1))
for w in range(nbw):
    bsdf.wavelength_samples.append(360.0 + w * (780.0 - 360.0) / (nbw - 1))
    for i in range(nbi):
        IW = bsdf.wavelength_incidence_samples.add()

        # IW.reflection
        nb_theta = 10
        nb_phi = 37
        IW.reflection.integral = 0.5
        for p in range(nb_phi):
            IW.reflection.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
        for t in range(nb_theta):
            IW.reflection.theta_samples.append(t * math.pi * 0.5 / (nb_theta - 1))
            for p in range(nb_phi):
                IW.reflection.bsdf_cos_theta.append(0.5 * math.cos(IW.reflection.theta_samples[t]) / math.pi)

        # IW.transmission
        nb_theta = 10
        nb_phi = 37
        IW.transmission.integral = 0.5
        for p in range(nb_phi):
            IW.transmission.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
        for t in range(nb_theta):
            IW.transmission.theta_samples.append(math.pi * 0.5 * (1 + t / (nb_theta - 1)))
            for p in range(nb_phi):
                IW.transmission.bsdf_cos_theta.append(0.5 * abs(math.cos(IW.transmission.theta_samples[t])) / math.pi)

file_name = spectral_bsdf__v1__pb2.FileName()
stub.Import(bsdf)
file_name.file_name = r"D:\Temp\test.anisotropicbsdf"

# Exporting to {file_name.file_name}
stub.ExportFile(file_name)
