"""gRPC service that hosts MLModel classes."""
from model_service_pb2 import iris_model_input, iris_model_output, model, model_collection
from model_service_pb2_grpc import ModelgRPCServiceStub
from nameko_grpc.entrypoint import Grpc

from model_grpc_service.config import Config
from model_grpc_service.extensions import ModelManagerProvider, setup

grpc = Grpc.implementing(ModelgRPCServiceStub)


class GRPCService:
    name = "http_service"

    model_manager = ModelManagerProvider(configuration=Config.models)

    @grpc
    def get_models(self, request, context):
        model_data = self.model_manager.get_models()
        models = []
        for m in model_data:
            response_model = model(qualified_name=m["qualified_name"],
                                   display_name=m["display_name"],
                                   description=m["description"],
                                   major_version=m["major_version"],
                                   minor_version=m["minor_version"],
                                   input_type="{}_input".format(m["qualified_name"]),
                                   output_type="{}_output".format(m["qualified_name"]))
            models.append(response_model)

        response_models = model_collection()
        response_models.models.extend(models)
        return response_models

    @grpc
    def iris_model_predict(self, request, context):
        model = self.model_manager.get_model(qualified_name="iris_model")
        prediction = model.predict({"sepal_width": request.sepal_width,
                                    "sepal_length": request.sepal_length,
                                    "petal_length": request.petal_length,
                                    "petal_width": request.petal_width})
        return iris_model_output(species=prediction["species"])
