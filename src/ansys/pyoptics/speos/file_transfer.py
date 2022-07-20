import pathlib
import os.path
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
import ansys.api.speos.file.v1.file_transfer_pb2 as file_transfer__v1__pb2
from ansys.pyoptics.speos import grpc_stub


def list_files(folder_path, regex='*'):
    return pathlib.Path(folder_path).rglob(regex)

def file_to_chunks(file, chunk_size=4000000):
    while buffer := file.read(chunk_size):
        chunk = file_transfer__v1__pb2.Chunk(binary=buffer, size=len(buffer))
        yield chunk

def upload_file_to_server(stub, file_path):
    with open(file_path, 'rb') as file:
        chunk_iterator = file_to_chunks(file)

        metadata = [(b'file_name', os.path.basename(file_path))]
        file_upload_response = stub.FileUpload(chunk_iterator, metadata=metadata)

        if(os.path.getsize(file_path) != file_upload_response.file_size):
            raise ValueError('issue during upload : file size is different from file uploaded size')

        return file_upload_response

def upload_files_to_server(server_port, repo_test_path, regex='*'):
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

def get_server_upload_directory(server_port):
    stub = grpc_stub.get_stub_insecure_channel(
        port=server_port, stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub
    )

    res = stub.GetServerTmpDirectory(file_transfer__v1__pb2.GetServerTmpDirectory_Request())
    return res.directory_path