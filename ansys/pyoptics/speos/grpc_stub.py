"""Module to handle gRPC stub.

This module allows to get gRPC stub

Examples
--------
>>> from ansys.pyoptics import speos
>>> import ansys.api.speos.results.v1.lpf_file_reader_pb2_grpc as lpf_file_reader__v1__pb2_grpc
>>> speos.get_stub_insecure_channel(
        port=50051,
        stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MonoStub)
"""

import grpc

def get_stub_insecure_channel(port, stub_type):
    """Get gRPC stub with insecure channel.

    Parameters
    ----------
    port : int
        port on which the insecure channel will be created.
    stub_type : type
        type of the stub which will be returned.

    Returns
    -------
    stub_type
        gRPC stub.

    Examples
    --------
    >>> from ansys.pyoptics import speos
    >>> import ansys.api.speos.results.v1.lpf_file_reader_pb2_grpc as lpf_file_reader__v1__pb2_grpc
    >>> speos.get_stub_insecure_channel(
            port=50051,
            stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MonoStub)
    """
    channel = grpc.insecure_channel('localhost:' + str(port))
    return stub_type(channel)