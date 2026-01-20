# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# (c) 2025 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited.
"""Module to handle file transfer to a server.

This module allows to transfer files to and from a server.
"""

import datetime
from pathlib import Path

import ansys.api.speos.file.v1.file_transfer_pb2 as file_transfer__v1__pb2
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
import grpc

from ansys.speos.core.generic.general_methods import check_version_gte
from ansys.speos.core.kernel.client import SpeosClient


def _raise_incompatibility():
    raise NotImplementedError(
        "Incompatibility between SpeosRPC_Server version (>= 2026.1.0)"
        + " and ansys-api-speos version (<0.16.0)."
    )


def _check_server_gte_2026r1(client: SpeosClient) -> bool:
    if client._server_version is not None:
        return check_version_gte(client._server_version, 2026, 1, 0)
    return False


def _file_to_chunks(file, file_name, gte_2026_1_0, chunk_size=4000000):
    first_chunk = True
    while buffer := file.read(chunk_size):
        chunk = file_transfer__v1__pb2.Chunk(binary=buffer, size=len(buffer))

        if first_chunk:
            if gte_2026_1_0:
                chunk.file_name = file_name
            first_chunk = False

        yield chunk


def upload_file(
    speos_client: SpeosClient,
    file_path: Path,
    reserved_file_uri: str = "",
) -> file_transfer__v1__pb2.Upload_Response:
    """Upload a file to a server.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    file_path: Path
        File's path to be uploaded
    reserved_file_uri: str, optional
        Optional - In case an uri was already reserved in server for the file.

    Returns
    -------
    ansys.api.speos.file.v1.file_transfer_pb2.Upload_Response
        Object created from file_transfer.proto file, response of Upload procedure.
        Contains for example file uri and upload duration.
    """
    if not file_path.exists() or not file_path.is_file():
        raise ValueError("Incorrect file_path : " + file_path)

    file_transfer_service_stub = file_transfer__v1__pb2_grpc.FileTransferServiceStub(
        channel=speos_client.channel
    )

    gte_2026_1_0 = _check_server_gte_2026r1(client=speos_client)

    with file_path.open("rb") as file:
        chunk_iterator = _file_to_chunks(file, file_path.name, gte_2026_1_0)

        metadata = [("file-size", str(file_path.stat().st_size))]
        if not gte_2026_1_0:
            metadata.append(("file-name", file_path.name))

        if reserved_file_uri:
            metadata.append(("reserved-file-uri", reserved_file_uri))

        try:
            return file_transfer_service_stub.Upload(chunk_iterator, metadata=metadata)
        except grpc._channel._InactiveRpcError as e:
            err = (
                '"file_name" field in Chunk is missing or "reserved-file-uri"'
                + " key/value not provided in ClientContext's metadata"
            )
            if e.args[0].details == err:
                _raise_incompatibility()

        return file_transfer__v1__pb2.Upload_Response()


def upload_folder(
    speos_client: SpeosClient,
    folder_path: Path,
    main_file_name: str,
    reserved_main_file_uri: str = "",
) -> list[file_transfer__v1__pb2.Upload_Response]:
    """Upload several files to a server.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    folder_path: Path
        Folder's path containing all files to upload
    main_file_name: str
        Name of the file that will be considered as main - other files will be dependencies of main.
    reserved_main_file_uri: str, optional
        Optional - In case an uri was already reserved in server for the main file.

    Returns
    -------
    List[ansys.api.speos.file.v1.file_transfer_pb2.Upload_Response]
        Object created from file_transfer.proto file, response of Upload procedure.
        Contains for example file uri and upload duration.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        raise ValueError("Incorrect folder_path : " + folder_path)

    main_file_path = folder_path / main_file_name
    if not main_file_path.exists() or not main_file_path.is_file():
        raise ValueError("Incorrect main_file_path : " + main_file_path)

    file_transfer_service_stub = file_transfer__v1__pb2_grpc.FileTransferServiceStub(
        channel=speos_client.channel
    )

    upload_responses = []
    add_dependencies_request = file_transfer__v1__pb2.AddDependencies_Request()
    # Upload all files, gather upload responses and use uri to fill request for dependencies call
    for file_to_upload in list(folder_path.glob("*")):
        if not file_to_upload.is_file():
            continue

        upload_response = file_transfer__v1__pb2.Upload_Response()
        if file_to_upload.name == main_file_path.name:
            upload_response = upload_file(speos_client, file_to_upload, reserved_main_file_uri)
            add_dependencies_request.uri = upload_response.info.uri
        else:
            upload_response = upload_file(speos_client, file_to_upload)
            add_dependencies_request.dependency_uris.append(upload_response.info.uri)
        upload_responses.append(upload_response)

    # Send dependencies to server
    if len(add_dependencies_request.dependency_uris) > 0:
        file_transfer_service_stub.AddDependencies(add_dependencies_request)

    return upload_responses


def _chunks_to_file(chunks, download_location: Path, gte_2026_1_0, metadata_file_name):
    first_chunk = True
    file_path = Path()
    file = None
    for chunk in chunks:
        if first_chunk:
            if gte_2026_1_0 and chunk.file_name != "":
                file_path = download_location / chunk.file_name
            elif not gte_2026_1_0 and metadata_file_name != "":
                file_path = download_location / metadata_file_name

            file = file_path.open("wb")
            first_chunk = False

        if file is not None:
            file.write(chunk.binary)

    if file is not None:
        file.close()

    return file_path


def download_file(
    speos_client: SpeosClient,
    file_uri: str,
    download_location: Path,
) -> file_transfer__v1__pb2.Download_Response:
    """Download a file from a server.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    file_uri: str
        File's uri on the server
    download_location: Path
        Path of download location

    Returns
    -------
    ansys.api.speos.file.v1.file_transfer_pb2.Download_Response
        Object created from file_transfer.proto file.
        Contains for example file uri, file name, file size and download duration
    """
    start_time = datetime.datetime.now()
    if not download_location.exists() or not download_location.is_dir():
        raise ValueError("Incorrect download_location : " + download_location)

    file_transfer_service_stub = file_transfer__v1__pb2_grpc.FileTransferServiceStub(
        channel=speos_client.channel
    )
    chunks = file_transfer_service_stub.Download(
        file_transfer__v1__pb2.Download_Request(uri=file_uri)
    )

    server_initial_metadata = dict(chunks.initial_metadata())

    if speos_client._server_version is None and "file-name" not in server_initial_metadata.keys():
        _raise_incompatibility()

    gte_2026r1 = _check_server_gte_2026r1(client=speos_client)
    file_path = _chunks_to_file(
        chunks,
        download_location,
        gte_2026r1,
        server_initial_metadata["file-name"]
        if "file-name" in server_initial_metadata.keys()
        else "",
    )

    if int(server_initial_metadata["file-size"]) != file_path.stat().st_size:
        raise ValueError("File download incomplete : " + file_path)

    # Compute download duration
    download_duration = datetime.datetime.now() - start_time

    # Fill response
    download_response = file_transfer__v1__pb2.Download_Response()
    download_response.info.uri = file_uri
    download_response.info.file_name = file_path.name
    download_response.info.file_size = int(server_initial_metadata["file-size"])
    s = int(download_duration.total_seconds())
    download_response.download_duration.seconds = s
    ns = int(
        1000
        * (download_duration - datetime.timedelta(seconds=s))
        / datetime.timedelta(microseconds=1)
    )
    download_response.download_duration.nanos = ns if ns != 0 else 1000
    return download_response


def download_folder(
    speos_client: SpeosClient,
    main_file_uri: str,
    download_location: Path,
) -> list[file_transfer__v1__pb2.Download_Response]:
    """Download several files from a server.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    main_file_uri : str
        Main file's uri on the server - this file and all its dependencies will be downloaded
    download_location : Path
        Path of download location

    Returns
    -------
    List[ansys.api.speos.file.v1.file_transfer_pb2.Download_Response]
        Object created from file_transfer.proto file.
        Contains for example file uri, file name, file size and download duration.
    """
    if not download_location.exists() or not download_location.is_dir():
        raise ValueError("Incorrect download_location : " + download_location)

    file_transfer_service_stub = file_transfer__v1__pb2_grpc.FileTransferServiceStub(
        channel=speos_client.channel
    )
    response = []

    # List all dependencies for the requested file
    list_deps_result = file_transfer_service_stub.ListDependencies(
        file_transfer__v1__pb2.ListDependencies_Request(uri=main_file_uri)
    )

    # Download first the main file
    response.append(download_file(speos_client, main_file_uri, download_location))

    # Then its dependencies
    for dep in list_deps_result.dependency_infos:
        response.append(download_file(speos_client, dep.uri, download_location))

    if not response:
        raise ValueError("No files downloaded for mainFileUri : " + main_file_uri)

    return response
