"""gRPC service that hosts MLModel classes."""
from concurrent import futures
import logging
import grpc

from model_service_pb2 import model, model_collection
import model_service_pb2_grpc

from model_grpc_service.config import Config
from model_grpc_service.model_manager import ModelManager
from model_grpc_service.ml_model_grpc_endpoint import MLModelgRPCEndpoint


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
            response_model = model(qualified_name=m["qualified_name"],
                                   display_name=m["display_name"],
                                   description=m["description"],
                                   major_version=m["major_version"],
                                   minor_version=m["minor_version"],
                                   input_type="{}_input".format(m["qualified_name"]),
                                   output_type="{}_output".format(m["qualified_name"]),
                                   predict_operation="{}_predict".format(m["qualified_name"]))
            models.append(response_model)

        # creating the response protobuf
        response_models = model_collection()
        response_models.models.extend(models)
        return response_models


def serve():
    """Start the model service."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_service_pb2_grpc.add_ModelgRPCServiceServicer_to_server(ModelgRPCServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
