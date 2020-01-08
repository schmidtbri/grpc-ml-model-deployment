from model_service_pb2 import iris_model_input
from model_service_pb2_grpc import ModelgRPCServiceStub

from nameko_grpc.client import Client


with Client("//127.0.0.1", ModelgRPCServiceStub) as client:

    response = client.iris_model_predict(iris_model_input(sepal_length=1.1, sepal_width=1.2, petal_length=1.3, petal_width=1.4))
    # response = client.get_models(request=empty())
    print(response)
