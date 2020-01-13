import argparse
import grpc

from model_service_pb2 import iris_model_input, empty
from model_service_pb2_grpc import ModelgRPCServiceStub


def run(get_models=False, iris_model_predict=False):
    with grpc.insecure_channel("localhost:50051") as channel:

        stub = ModelgRPCServiceStub(channel)

        if get_models:
            response = stub.get_models(empty())
            print(response)
        elif iris_model_predict:
            response = stub.iris_model_predict(
                iris_model_input(sepal_length=1.1, sepal_width=1.2, petal_length=1.3, petal_width=1.4))
            print(response)
        else:
            print("No action selected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Interact with gRPC service.')
    parser.add_argument('--get_models', help='Get a list of models', action='store_true')
    parser.add_argument('--iris_model_predict', help='Make a prediction with the iris_model.',
                        action='store_true')

    args = parser.parse_args()

    run(args.get_models, args.iris_model_predict)
