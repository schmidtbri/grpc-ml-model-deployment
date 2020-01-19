"""Class to host an MlModel object in a gRPC endpoint."""
import logging
from google.protobuf.json_format import MessageToDict

import model_service_pb2
from model_grpc_service import __name__
from model_grpc_service.model_manager import ModelManager

logger = logging.getLogger(__name__)


class MLModelgRPCEndpoint(object):
    """Class for MLModel gRPC endpoints."""

    def __init__(self, model_qualified_name):
        """Create a gRPC endpoint for a model.

        :param model_qualified_name: The qualified name of the model that will be hosted in this endpoint.
        :type model_qualified_name: str
        :returns: An instance of MLModelStreamProcessor.
        :rtype: MLModelStreamProcessor

        """
        model_manager = ModelManager()
        self._model = model_manager.get_model(model_qualified_name)

        if self._model is None:
            raise ValueError("'{}' not found in ModelManager instance.".format(model_qualified_name))

        logger.info("Initializing endpoint for model: {}".format(self._model.qualified_name))

    def __call__(self, request, context):
        """Make predictions with protocol buffers."""
        # converting the protocol buffer into a dictionary
        # if the input protobuf is mapped to a type that the model cannot accept, this will cause a schema exception
        data = MessageToDict(request, preserving_proto_field_name=True)

        # making a prediction with the model
        prediction = self._model.predict(data=data)

        # getting the output protobuf for the model, this code relies on the fact that a model's output protobufs are
        # always named the same way
        output_protobuf_name = "{}_output".format(self._model.qualified_name)
        output_protobuf = MLModelgRPCEndpoint._get_protobuf(output_protobuf_name)

        # creating the response protocol buffer
        # if the model outputs a data structure that cannot be mapped to the protobuf, this code will fail
        response = output_protobuf(**prediction)

        return response

    @staticmethod
    def _get_protobuf(protobuf_name):
        return getattr(model_service_pb2, protobuf_name)
