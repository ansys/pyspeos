"""This module allows pytest to perform unit testing.

Usage:
.. code::
   $ pytest
   $ pytest -vx

With coverage.
.. code::
   $ pytest --cov ansys.pyoptics.speos

"""
# import math
import os

from conftest import config
from conftest import test_path
from google.protobuf.empty_pb2 import Empty

import ansys.api.speos.xmp.v1.xmp_file_pb2 as xmp__file__v1__pb2
import ansys.api.speos.xmp.v1.xmp_file_pb2_grpc as xmp__file__v1__pb2_grpc
from ansys.pyoptics import speos

# import helper


def test_XmpFileInfo_Mono_Basic():
    stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=xmp__file__v1__pb2_grpc.XmpFileService_MonoStub
    )

    # CreateXMPFileInfo
    path = os.path.join(test_path, "Colorimetric.xmp")
    stub.CreateXMPFileInfo(xmp__file__v1__pb2.FileName(file_name=path))

    # BuildMapRelativeStandardError
    stub.BuildMapRelativeStandardError(Empty())

    # GetNbPixelXRelativeStandardError
    px = stub.GetNbPixelXRelativeStandardError(Empty())
    assert px.nb_pixel == 180

    # GetNbPixelYRelativeStandardError
    py = stub.GetNbPixelYRelativeStandardError(Empty())
    assert py.nb_pixel == 120
