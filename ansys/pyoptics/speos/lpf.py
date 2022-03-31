
import grpc
import ansys.api.speos.results.v1.lpf_file_reader_pb2_grpc as lpf__file__reader__v1__pb2_grpc
import ansys.api.speos.results.v1.lpf_file_reader_pb2 as lpf__file__reader__v1__pb2
#import ansys.data.speos.utils.v1.Point3_pb2 as Point3__v1__pb2

class lpfreader:
    def __init__(self):
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = lpf__file__reader__v1__pb2_grpc.LpfFileReader_MonoStub(channel)

    def InitLpfFileName(self, path):
        return self.stub.InitLpfFileName(
            lpf__file__reader__v1__pb2.InitLpfFileNameRequest_Mono(lpf_file_path=path)
            )