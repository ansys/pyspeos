"""This module allows pytest to perform unit testing.
Usage:
.. code::
   $ pytest
   $ pytest -vx
With coverage.
.. code::
   $ pytest --cov ansys.pyoptics.speos
"""
import logging
import os

from ansys.api.speos.intensity_distributions.v1 import ies_pb2, ies_pb2_grpc
import grpc

from conftest import config, test_path
import helper


def createIesIntensity():
    ies = ies_pb2.IesIntensityDistribution()

    ies.norme_version = 1
    ies.key_words.append("IESNA:LM-63-95")
    ies.key_words.append("[TEST]  \t  \tTest report number and laboratory")
    ies.key_words.append("[MANUFAC]   \tManufacturer of luminaire")
    ies.key_words.append("[LUMCAT]    \tLuminaire catalog number")
    ies.key_words.append("[LUMINAIRE] \tLuminaire description")
    ies.key_words.append("[LAMPCAT]   \tLamp catalogue number")
    ies.key_words.append("[LAMP]      \tLamp description")
    ies.unit = 1
    ies.nb_vertical_angle = 2
    ies.nb_horizontal_angle = 2
    ies.tilt_type = 1
    ies.tilt_geometry = 1
    ies.tilt_nb_pair_angle = 2
    ies.nb_lamp = 1
    ies.photo_type = 1
    ies.lumen_lamp = 4000
    ies.multiplier = 1
    ies.width = 0
    ies.length = 0
    ies.height = 0
    ies.ballast = 1
    ies.future_use = 1
    ies.input_watt = 500
    for i in range(int(ies.nb_vertical_angle)):
        ies.vertical_angle.append(0 + i * 180 / (ies.nb_vertical_angle - 1))
    for i in range(int(ies.nb_horizontal_angle)):
        ies.horizontal_angle.append(0 + i * 360 / (ies.nb_horizontal_angle - 1))
        for j in range(int(ies.nb_vertical_angle)):
            ies.candela_value.append(1000)
    for i in range(int(ies.tilt_nb_pair_angle)):
        ies.tilt_angle.append(0 + i * 90 / (ies.tilt_nb_pair_angle - 1))
        ies.tilt_mult_factor.append(1)
    ies.local_vert = 0

    return ies


def compareIesIntensities(ies1, ies2):
    if ies1.norme_version != ies2.norme_version:
        return False
    if len(ies1.key_words) != len(ies2.key_words):
        return False
    for i in range(len(ies1.key_words)):
        if ies1.key_words[i] != ies2.key_words[i]:
            return False
    if ies1.unit != ies2.unit:
        return False
    if ies1.nb_vertical_angle != ies2.nb_vertical_angle:
        return False
    if ies1.nb_horizontal_angle != ies2.nb_horizontal_angle:
        return False
    if ies1.tilt_type != ies2.tilt_type:
        return False
    if ies1.tilt_geometry != ies2.tilt_geometry:
        return False
    if ies1.tilt_nb_pair_angle != ies2.tilt_nb_pair_angle:
        return False
    if ies1.nb_lamp != ies2.nb_lamp:
        return False
    if ies1.photo_type != ies2.photo_type:
        return False
    if ies1.lumen_lamp != ies2.lumen_lamp:
        return False
    if ies1.multiplier != ies2.multiplier:
        return False
    if ies1.width != ies2.width:
        return False
    if ies1.length != ies2.length:
        return False
    if ies1.height != ies2.height:
        return False
    if ies1.ballast != ies2.ballast:
        return False
    if ies1.future_use != ies2.future_use:
        return False
    if ies1.input_watt != ies2.input_watt:
        return False
    for i in range(int(ies1.nb_vertical_angle)):
        if ies1.vertical_angle[i] != ies2.vertical_angle[i]:
            return False
    for i in range(int(ies1.nb_horizontal_angle)):
        if ies1.horizontal_angle[i] != ies2.horizontal_angle[i]:
            return False
        for j in range(int(ies1.nb_vertical_angle)):
            if ies1.candela_value[i * ies1.nb_vertical_angle + j] != ies2.candela_value[i * ies1.nb_vertical_angle + j]:
                return False
    for i in range(int(ies1.tilt_nb_pair_angle)):
        if ies1.tilt_angle[i] != ies2.tilt_angle[i]:
            return False
        if ies1.tilt_mult_factor[i] != ies2.tilt_mult_factor[i]:
            return False
    if ies1.local_vert != ies2.local_vert:
        return False
    return True


def test_grpc_ies_intensity():
    with grpc.insecure_channel(f"localhost:" + str(config.get("SpeosServerPort"))) as channel:
        stub = ies_pb2_grpc.IesIntensityServiceStub(channel)
        save_request = ies_pb2.Save_Request()
        save_request.file_uri = os.path.join(test_path, "tmp2_file.ies")
        load_request = ies_pb2.Load_Request()
        load_request.file_uri = os.path.join(test_path, "tmp2_file.ies")

        logging.debug("Creating ies intensity protocol buffer")
        ies = createIesIntensity()

        logging.debug("Sending protocol buffer to server")
        import_response = ies_pb2.Import_Response()
        import_response = stub.Import(ies)

        logging.debug("Writing as {save_request.file_uri}")
        save_response = ies_pb2.Save_Response()
        save_response = stub.Save(save_request)
        assert helper.does_file_exist(save_request.file_uri)

        logging.debug("Reading {load_response.file_uri}")
        load_response = ies_pb2.Load_Response()
        load_response = stub.Load(load_request)
        helper.remove_file(load_request.file_uri)

        logging.debug("Exporting ies intensity protocol buffer")
        export_request = ies_pb2.Export_Request()
        ies2 = ies_pb2.IesIntensityDistribution()
        ies2 = stub.Export(export_request)

        logging.debug("Comparing ies intensity distributions")
        assert compareIesIntensities(ies, ies2)
