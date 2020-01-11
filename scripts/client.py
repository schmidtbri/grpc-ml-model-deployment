import grpc

from model_service_pb2 import iris_model_input, empty
from model_service_pb2_grpc import ModelgRPCServiceStub


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = ModelgRPCServiceStub(channel)
        response = stub.iris_model_predict(iris_model_input(sepal_length=1.1, sepal_width=1.2, petal_length=1.3, petal_width=1.4))
        # response = stub.get_models(empty())
        print(response)


if __name__ == '__main__':
    run()
