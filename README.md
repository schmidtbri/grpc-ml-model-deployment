# gRPC ML Model Deployment
Deploying an ML model in a gRPC service.

![](https://github.com/schmidtbri/grpc-ml-model-deployment/workflows/Build/badge.svg)

Deploying an ML model in a gRPC service.

This code is used in this [blog post]().

## Requirements
Docker

## Installation 
The makefile included with this project contains targets that help to automate several tasks.

To download the source code execute this command:

```bash
git clone https://github.com/schmidtbri/grpc-ml-model-deployment
```

Then create a virtual environment and activate it:

```bash
# go into the project directory
cd grpc-ml-model-deployment

make venv

source venv/bin/activate
```

Install the dependencies:

```bash
make dependencies
```

## Running the unit tests
To run the unit test suite execute these commands:
```bash

# first install the test dependencies
make test-dependencies

# run the test suite
make test
```

## Running the Service
To start the service execute these commands:
```bash
export PYTHONPATH=./
export APP_SETTINGS=ProdConfig 
python model_grpc_service/service.py
```

## Testing the Service
To test the service once it is running, execute these commands:
```bash
export PYTHONPATH=./
python scripts/client.py --get_models
python scripts/client.py --iris_model_predict
```
