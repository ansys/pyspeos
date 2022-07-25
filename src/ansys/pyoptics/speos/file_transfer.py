"""Module to handle file transfer to SpeosRPC Server.

This module allows to upload files to the server

Examples
--------
>>> from ansys.pyoptics.speos import file_transfer
>>> file_transfer.upload_files_to_server(
        server_port=50051,
        repo_test_path="path/to/files/directory/")
"""
import pathlib
import os.path
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
import ansys.api.speos.file.v1.file_transfer_pb2 as file_transfer__v1__pb2
from ansys.pyoptics.speos import grpc_stub


def list_files(folder_path, regex='*'):
    """List files matching the regex in the folder_path.

    Parameters
    ----------
    folder_path : Path
    regex : str - default to "*"

    Returns
    -------
    list of Path
        list of file's path matching the regex in the folder_path.

    Examples
    --------
    List all lpf files in path/to/folder/
    >>> from ansys.pyoptics.speos import file_transfer
    >>> file_transfer.list_files(
            folder_path="path/to/folder/",
            regex="*.lpf")
    """
    return pathlib.Path(folder_path).rglob(regex)

def file_to_chunks(file, chunk_size=4000000):
    """Cut a file into chunks of specified chunk_size.

    Parameters
    ----------
    file : file object
    chunk_size : size
        number of bytes max in the chunk - default to 4000000

    Examples
    --------
    >>> from ansys.pyoptics.speos import file_transfer
    >>> with open(file_path, 'rb') as file:
    >>>     chunk_iterator = file_transfer.file_to_chunks(file)
    >>>     # do something with chunk iterator
    """
    while buffer := file.read(chunk_size):
        chunk = file_transfer__v1__pb2.Chunk(binary=buffer, size=len(buffer))
        yield chunk

def upload_file_to_server(stub, file_path):
    """Upload a single file to a server.

    Parameters
    ----------
    stub : gRPC stub

    file_path : Path
        file's path to be uploaded

    Returns
    -------
    FileUpload_Response - object created from file_transfer.proto file, response of FileUpload procedure
    contains for example file_size, upload_duration

    Examples
    --------
    >>> from ansys.pyoptics.speos import file_transfer
    >>> from ansys.pyoptics.speos import grpc_stub
    >>> import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
    >>> file_transfer_stub = grpc_stub.get_stub_insecure_channel(
        port=50051, stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub
    )
    >>> file_transfer.upload_file_to_server(
            stub=file_transfer_stub,
            file_path="path/to/file")
    """
    with open(file_path, 'rb') as file:
        chunk_iterator = file_to_chunks(file)

        metadata = [(b'file_name', os.path.basename(file_path))]
        file_upload_response = stub.FileUpload(chunk_iterator, metadata=metadata)

        if(os.path.getsize(file_path) != file_upload_response.file_size):
            raise ValueError('issue during upload : file size is different from file uploaded size')

        return file_upload_response

def upload_files_to_server(server_port, repo_test_path, regex='*'):
    """Upload several files to a server.

    Parameters
    ----------
    server_port : port of the server

    repo_test_path : Path
        repository's path containing files to be uploaded

    regex : str - default to "*"

    Returns
    -------
    list of FileUpload_Response - object created from file_transfer.proto file, response of FileUpload procedure
    contains for example file_size, upload_duration

    Examples
    --------
    Upload all lpf files in path/to/repository to the server connected on port 50051
    >>> from ansys.pyoptics.speos import file_transfer
    >>> file_transfer.upload_files_to_server(
            server_port="50051",
            repo_test_path="path/to/repository",
            regex="*.lpf")
    """
    if not os.path.isdir(repo_test_path):
        raise ValueError('repo_test_path does not exist')

    stub = grpc_stub.get_stub_insecure_channel(
        port=server_port, stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub
    )

    file_upload_result = []
    for file_path in list_files(repo_test_path, regex):
        file_upload_response = upload_file_to_server(stub, file_path)
        file_upload_result.append(file_upload_response)

    return file_upload_result

def get_server_tmp_directory(server_port):
    """Retrieve the path of the directory on the server where the files are uploaded.

        Parameters
        ----------
        server_port : port of the server

        Returns
        -------
        Path - Path of the server tmp directory

        Examples
        --------
        >>> from ansys.pyoptics.speos import file_transfer
        >>> file_transfer.get_server_tmp_directory(server_port="50051")
    """
    stub = grpc_stub.get_stub_insecure_channel(
        port=server_port, stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub
    )

    res = stub.GetServerTmpDirectory(file_transfer__v1__pb2.GetServerTmpDirectory_Request())
    return res.directory_path