"""gRPC service that hosts MLModel classes."""
from model_service_pb2 import model, model_collection, iris_model_output
from model_service_pb2_grpc import ModelgRPCServiceStub
from nameko_grpc.entrypoint import Grpc
from google.protobuf.json_format import MessageToDict

from model_grpc_service.config import Config
from model_grpc_service.extensions import ModelManagerProvider
from model_grpc_service.extensions import startup

grpc = Grpc.implementing(ModelgRPCServiceStub)


class GRPCService:
    name = "Model gRPC Service"

    model_manager = ModelManagerProvider(configuration=Config.models)

    @startup
    def register_endpoints(self):
        print("test")
        return

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
        """Predict with the iris_model package."""
        # getting a reference to the model from the ModelManager singleton
        model = self.model_manager.get_model(qualified_name="iris_model")

        # converting the protocol buffer into a dictionary
        data = MessageToDict(request, preserving_proto_field_name=True)

        # making a prediction with the model
        prediction = model.predict(data=data)

        # creating the response protocol buffer
        response = iris_model_output(**prediction)
        return response
