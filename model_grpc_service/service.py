"""gRPC service that hosts MLModel classes."""
import os
import logging
from nameko_grpc.entrypoint import Grpc
from model_service_pb2 import iris_model_input, iris_model_output
from model_service_pb2_grpc import ModelgRPCServiceStub

from model_grpc_service.config import Config
from model_grpc_service.model_manager import ModelManager

logging.basicConfig(level=logging.INFO)

grpc = Grpc.implementing(ModelServiceStub)


class ExampleService:
    name = "Model gRPC Service"

    @grpc
    def unary_unary(self, request, context):
        message = request.value * (request.multiplier or 1)
        return iris_model_output(message=message)
