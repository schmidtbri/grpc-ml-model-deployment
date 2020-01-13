"""gRPC service that hosts MLModel classes."""
import os
import logging
import time
from concurrent import futures
import grpc

from model_service_pb2 import model, model_collection
import model_service_pb2_grpc

from model_grpc_service.config import Config
from model_grpc_service.model_manager import ModelManager
from model_grpc_service.ml_model_grpc_endpoint import MLModelgRPCEndpoint

logging.basicConfig(level=logging.INFO)

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class ModelgRPCServiceServicer(model_service_pb2_grpc.ModelgRPCServiceServicer):
    """Provides methods that implement functionality of Model gRPC Service."""

    def __init__(self):
        """Initialize an instance of the service."""
        self.model_manager = ModelManager()
        self.model_manager.load_models(configuration=Config.models)

        for model in self.model_manager.get_models():
            endpoint = MLModelgRPCEndpoint(model_qualified_name=model["qualified_name"])
            operation_name = "{}_predict".format(model["qualified_name"])
            setattr(self, operation_name, endpoint)

    def get_models(self, request, context):
        """Return list of models hosted in this service."""
        model_data = self.model_manager.get_models()
        models = []
        for m in model_data:
            # creating a list of model protobufs from the model information returned by the model manager
            response_model = model(qualified_name=m["qualified_name"],
                                   display_name=m["display_name"],
                                   description=m["description"],
                                   major_version=m["major_version"],
                                   minor_version=m["minor_version"],
                                   input_type="{}_input".format(m["qualified_name"]),
                                   output_type="{}_output".format(m["qualified_name"]),
                                   predict_operation="{}_predict".format(m["qualified_name"]))
            models.append(response_model)

        # creating the response protobuf from the list created above
        response_models = model_collection()
        response_models.models.extend(models)
        return response_models


def serve():
    """Start the model service."""
    # importing the right configuration
    configuration = __import__("model_grpc_service"). \
        __getattribute__("config"). \
        __getattribute__(os.environ["APP_SETTINGS"])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_service_pb2_grpc.add_ModelgRPCServiceServicer_to_server(ModelgRPCServiceServicer(), server)
    server.add_insecure_port(configuration.service_port)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
