"""This module allows pytest to perform unit testing.

Usage:
.. code::
   $ pytest
   $ pytest -vx

With coverage.
.. code::
   $ pytest --cov ansys.pyoptics.speos

"""
import os

from ansys.api.speos import grpc_stub
import ansys.api.speos.job.v1.job_pb2 as job__v1__pb2
import ansys.api.speos.job.v1.job_pb2_grpc as job__v1__pb2_grpc
import ansys.api.speos.live_preview.v1.live_preview_pb2 as live_preview__v1__pb2
import ansys.api.speos.live_preview.v1.live_preview_pb2_grpc as live_preview__v1__pb2_grpc
import ansys.api.speos.simulation.v1.simulation_pb2 as simulation__v1__pb2
import ansys.api.speos.simulation.v1.simulation_pb2_grpc as simulation__v1__pb2_grpc

from conftest import test_path


def test_live_preview():
    # Stubs creations for Simulations
    simu_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationsManagerStub,
    )
    simu_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub,
    )
    # Stubs creations for Jobs
    job_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=job__v1__pb2_grpc.SpeosJobsManagerStub,
    )
    job_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=job__v1__pb2_grpc.SpeosJobStub,
    )
    # Stubs creations for LivePreviews
    live_preview_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=live_preview__v1__pb2_grpc.LivePreviewsManagerStub,
    )
    live_preview_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:50051",
        stub_type=live_preview__v1__pb2_grpc.LivePreviewStub,
        options=[
            ("grpc.max_receive_message_length", 1024 * 1024 * 1024),
        ],  # 1GB, need to increase max_receive_message_length for live preview
    )

    # Build sv5 path
    speos_simulation_name = "LG_50M_Colorimetric_short.sv5"
    folder_path = os.path.join(test_path, speos_simulation_name)
    speos_simulation_full_path = os.path.join(folder_path, speos_simulation_name)

    # Allocate simulation
    simu_create_res = simu_manager_stub.Create(simulation__v1__pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(
        simulation__v1__pb2.Load_Request(guid=simu_create_res.guid, input_file_path=speos_simulation_full_path)
    )

    # Allocate GPU job from simu
    job_create_res = job_manager_stub.Create(
        job__v1__pb2.Create_Request(simu_guid=simu_create_res.guid, job_type=job__v1__pb2.Job_Type.GPU)
    )

    # Allocate Live Preview from job
    live_preview_create_res = live_preview_manager_stub.Create(
        live_preview__v1__pb2.Create_Request(job_guid=job_create_res.guid)
    )

    # Let's init the preview on the first sensor - get in response nb of layers available and the preview dimensions
    live_preview_init_res = live_preview_stub.InitPreview(
        live_preview__v1__pb2.InitPreview_Request(guid=live_preview_create_res.guid, sensor_id=0)
    )
    assert live_preview_init_res.nb_of_layers == 2
    assert live_preview_init_res.image_dimensions == [500, 500]

    # Retrieve previews for all layers
    # ie layer_id is not precised in GetPreviews_Request, we could have ask layer_id = 0 or = 1 as nb_of_layers == 2
    preview_res = live_preview_stub.GetPreviews(
        live_preview__v1__pb2.GetPreviews_Request(guid=live_preview_create_res.guid)
    )
    i = 0
    preview_deserialized = live_preview__v1__pb2.Image_rgb32f()
    for preview in preview_res:  # for each preview
        # Deserialize the preview + check some data
        preview_deserialized.ParseFromString(preview.binary)
        assert preview_deserialized.image_dimensions == live_preview_init_res.image_dimensions
        assert (
            len(preview_deserialized.data)
            == live_preview_init_res.image_dimensions[0] * live_preview_init_res.image_dimensions[1]
        )

        # After few previews, stop the live preview
        if i == 5:
            live_preview_stub.Stop(live_preview__v1__pb2.Stop_Request(guid=live_preview_create_res.guid))

        i = i + 1

    # Delete Live Preview
    live_preview_manager_stub.Delete(live_preview__v1__pb2.Delete_Request(guid=live_preview_create_res.guid))

    # Delete job
    job_manager_stub.Delete(job__v1__pb2.Delete_Request(guid=job_create_res.guid))

    # Delete simu
    simu_manager_stub.Delete(simulation__v1__pb2.Delete_Request(guid=simu_create_res.guid))
