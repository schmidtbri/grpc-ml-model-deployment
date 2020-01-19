import unittest
from ml_model_abc import MLModel
from model_grpc_service.model_manager import ModelManager
from model_grpc_service.ml_model_grpc_endpoint import MLModelgRPCEndpoint


# creating an MLModel class to test with
class MLModelMock(MLModel):
    # accessing the package metadata
    display_name = "display name"
    qualified_name = "qualified_name"
    description = "description"
    major_version = 1
    minor_version = 1
    input_schema = None
    output_schema = None

    def __init__(self):
        pass

    def predict(self, data):
        return {"prediction": 123}


# creating a mockup class to test with
class SomeClass(object):
    pass


class MLModelgRPCEndpointTests(unittest.TestCase):

    def test1(self):
        """testing the __init__() method"""
        # arrange
        # instantiating the model manager class
        model_manager = ModelManager()
        # loading the MLModel objects from configuration
        model_manager.load_models(configuration=[{
            "module_name": "tests.model_manager_test",
            "class_name": "MLModelMock"
        }])

        # act
        endpoint = MLModelgRPCEndpoint(model_qualified_name="qualified_name")

        # assert
        self.assertTrue(str(type(endpoint._model)) == "<class 'tests.model_manager_test.MLModelMock'>")

    def test2(self):
        """testing the __init__() method with missing model"""
        # arrange
        # instantiating the model manager class
        model_manager = ModelManager()
        # loading the MLModel objects from configuration
        model_manager.load_models(configuration=[{
            "module_name": "tests.model_manager_test",
            "class_name": "MLModelMock"
        }])

        # act
        exception_raised = False
        exception_message = None
        try:
            endpoint = MLModelgRPCEndpoint(model_qualified_name="asdf")
        except Exception as e:
            exception_message = str(e)
            print(exception_message)
            exception_raised = True

        # assert
        self.assertTrue(exception_raised)
        self.assertTrue(exception_message == "'asdf' not found in ModelManager instance.")


if __name__ == '__main__':
    unittest.main()