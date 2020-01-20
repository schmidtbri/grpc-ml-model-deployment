Title: A gRPC Service ML Model Deployment
Date: 2020-01-20 09:27
Category: Blog
Slug: grpc-ml-model-deployment
Authors: Brian Schmidt
Summary: With the rise of service oriented architectures and microservice architectures, the gRPC](https://grpc.io/) system has become a popular choice for building services. gRPC is a fairly new system for doing inter-service communication through Remote Procedure Calls (RPC) that started in Google in 2015. A remote procedure call is an abstraction that allows a developer to make a call to a function that runs in a separate process, but that looks like it executes locally. gRPC is a standard for defining the data exchanged in an RPC call and the API of the function through [protocol buffers](https://developers.google.com/protocol-buffers). gRPC also supports many other features, such as simple and streaming RPC invocations, authentication, and load balancing.

This blog post builds on the ideas started in
[three]({filename}/articles/a-simple-ml-model-base-class/post.md)
[previous]({filename}/articles/improving-the-mlmodel-base-class/post.md)
[blog posts]({filename}/articles/using-ml-model-abc/post.md).

In this blog post I'll show how to deploy the same ML model that l
deployed as a batch job in this [blog
post]({filename}/articles/etl-job-ml-model-deployment/post.md),
as a task queue in this [blog post]({filename}/articles/task-queue-ml-model-deployment/post.md),
inside an AWS Lambda in this [blog post]({filename}/articles/lambda-ml-model-deployment/post.md),
and a Kafka streaming application in this [blog post]({filename}/articles/streaming-ml-model-deployment/post.md).

The code in this blog post can be found in this [github repo](https://github.com/schmidtbri/grpc-ml-model-deployment).

# Introduction

With the rise of service oriented architectures and microservice
architectures, the [gRPC](https://grpc.io/) system has
become a popular choice for building services. gRPC is a fairly new
system for doing inter-service communication through Remote Procedure
Calls (RPC) that started in Google in 2015. A remote procedure call is
an abstraction that allows a developer to make a call to a function that
runs in a separate process, but that looks like it executes locally.
gRPC is a standard for defining the data exchanged in an RPC call and
the API of the function through [protocol
buffers](https://developers.google.com/protocol-buffers).
gRPC also supports many other features, such as simple and streaming RPC
invocations, authentication, and load balancing.

Protocol buffers are defined through an interface definition language,
and the code that actually does the serialization/deserialization is
then generated from the definition. Once a protocol buffer definition
file is created, the protocol buffer definition can be compiled into
many different programming languages through a compiler. This allows
gRPC to be a cross-language standard for a common exchange format
between services.

gRPC services are coded in much the same way as a regular web service
but have several differences that will affect the service we'll build in
this blog post. First, protocol buffers are statically typed, which
makes the serialized data packages smaller but allows for less
flexibility in the code of the service. Second, protocol buffers must be
compiled to source code, which makes it harder to evolve services that
use them. Lastly, a protocol buffer is a binary data structure that is
optimized for size and processing speed, whereas a JSON data structure
is a string-based data structure optimized for simplicity and
readability. In [performance
comparisons](https://dev.to/plutov/benchmarking-grpc-and-rest-in-go-565),
protocol buffers have been found to be many times faster than JSON.

In previous blog posts, we've used JSON exclusively, to keep things
simple. JSON allowed the services and applications to deserialize the
data structure and send it directly to the model without having to worry
about the contents of the data structure. This is not possible with gRPC
since the service requires explicit knowledge of the schema of the
models incoming and outgoing data.

# Package Structure

```
-   model_grpc_service (python package for service)
    -   __init__.py
    -   config.py configuration for the application)
    -   ml_model_grpc_endpoint.py (MLModel gRPC endpoint class)
    -   model_manager.py (model manager singleton class)
    -   service.py (service code)
-   scripts
    -   client.py (single prediction test)
    -   generate_proto.py
-   tests (unit tests)
-   Dockerfile
-   Makefle
-   model_service.proto (protocol buffer definition of gRPC service)
-   model_service_pb2.py (python protocol buffer code)
-   model_service_pb2_grpc.py (python gRPC service bindings)
-   model_service_template.proto (protocol buffer template file)
-   README.md
-   requirements.txt
-   setup.py
-   test_requirements.txt
```

This structure can be seen in the [github
repository](https://github.com/schmidtbri/grpc-ml-model-deployment).

# Installing the Model

In order to create a gRPC service for ML models we'll first install a
model package into the environment. We'll use the iris\_model package,
which has been used in
[several]({filename}/articles/lambda-ml-model-deployment/post.md)
[previous]({filename}/articles/streaming-ml-model-deployment/post.md)
[blog
posts]({filename}/articles/using-ml-model-abc/post.md).
The model package itself was created in [this blog
post]({filename}/articles/improving-the-mlmodel-base-class/post.md).
The model package can be installed from its git repository with this
command:

```bash
pip install git+https://github.com/schmidtbri/ml-model-abc-improvements
```

Now that we have the model package in the environment, we can add it to
the config.py module:

```python
class Config(dict):
models = [{
    "module_name": "iris_model.iris_predict",
    "class_name": "IrisModel"
}]
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/config.py#L4-L12).

This configuration class is used by the service in all environments. The
module\_name and class\_name fields allow the application to find the
MLModel class that implements the prediction functionality of the
iris\_model package. The list can hold information for many models, so
there's no limitation to how many models can be hosted by the service.

The reason that we need to install the model package before we can write
any other code is because the model's input and output schemas are
needed to be able to define the gRPC service's API.

# Generating a Protocol Buffer Definition

Since we can't code the gRPC service until we have a .proto file with
the definition of the API of the service, our first task is to generate
.proto file from the models that will be hosted by the service. In order
to automatically generate the file from the iris\_model's input and
output schemas we'll use the [Jinja2 templating
tool](https://jinja.palletsprojects.com/en/2.10.x/). Jinja2
is a templating tool that allows documents to be generated by combining
a template file and a data structure, it allows a developer to isolate
the unchanging parts of a document in the template, and keeps the parts
that change in the data structure. First we'll create a template, and
after that we'll add the schema information to it to generate a .proto
file for the service.

## The Template File

First we'll create the [template
file](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto)
from which we'll generate the .proto file:

```
syntax = "proto3";

package model_grpc_service;
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto#L1-L3).

At the top of the template, we declare that we'll use the proto3 format,
and the name of the package is "model\_grpc\_service". Next, we'll
declare some data structures:

```
message empty {}

message model {
    string qualified_name = 1;
    string display_name = 2;
    string description = 3;
    sint32 major_version = 4;
    sint32 minor_version = 5;
    string input_type = 6;
    string output_type = 7;
    string predict_operation = 8;
}

message model_collection {
    repeated model models = 1;
}
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto#L5-L20).

These data structures will be used by an operation that will be declared
further down in the template. The data structures hold information about
the models that are hosted by the service, including the names of the
input and output types and the name of the prediction operation for the
model. The model\_collection type holds a list of model objects.

Next, we'll generate an input type for the models hosted by the service:

```
{% for model in models %}
message {{ model.qualified_name }}_input { 
    {% for field in model.input_schema %}
        {{ field.type }} {{ field.name }} = {{ field.index }};
    {% endfor %}
}
{% endfor %}
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto#L22-L26).

This template code uses the qualified name of a model and the schema of
the input of the model to generate a protocol buffer type that matches
the model's input. The name of the input type for a model always follows
this pattern: "<model\_qualified\_name\>\_input". Each field in the
input schema of the model is translated to the equivalent field type in
a protocol buffer and is given the same name. Lastly, an index is
generated and assigned to the field.

Next, we'll do the same for the output schema of the model:

```
{% for model in models %}
message {{ model.qualified_name }}_output { 
    {% for field in model.output_schema %}
        {{ field.type }} {{ field.name }} = {{ field.index }};
    {% endfor %}
}
{% endfor %}
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto#L27-L31).

Now we can start to define the service's API:

```
service ModelgRPCService {
    rpc get_models (empty) returns (model_collection) {}
    {% for model in models %}
        rpc {{ model.qualified_name }}_predict ({{ model.qualified_name }}_input) returns ({{ model.qualified_name }}_output) {}
    {% endfor %}
}
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service_template.proto#L33-L38).

This code defines the operations that the service implements. The first
operation is called "get\_models" and it uses the first set of protobuf
data structures that we defined above. This operation is simple since it
does not change with the models that are being hosted by the gRPC
service. It accepts the "empty" type since it does not require any
inputs, and it returns the "model\_collection" type.

Next, we will generate a set of prediction operations, one for each
model hosted by the service. The name of the predict operation always
follows this pattern: "<model\_qualified\_name\>\_predict". The model's
input and output types are added to the operation by name.

## Using the Template File

This template file is now ready to be used, so we'll create a python
script that will take it and add information about the models that we
actually want to host in the service. The script to do this is in the
[generate\_proto.py
script](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/generate_proto.py).

This code will make use of the ModelManager class that has been used in
[several]({filename}/articles/lambda-ml-model-deployment/post.md)
[previous]({filename}/articles/streaming-ml-model-deployment/post.md)
[blog
posts]({filename}/articles/using-ml-model-abc/post.md).
The ModelManager class is responsible for loading models from
configuration, maintaining references to the model objects, and
returning information about the models. In this section we'll use the
get\_models() and get\_model\_metadata() operations to access the
information needed to generate the protocol buffer definition.

The script starts by instantiating the ModelManager and loading the
models from the configuration:

```python
model_manager = ModelManager()

model_manager.load_models(Config.models)

```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/generate_proto.py#L9-L10).

Then the script loads the Jinja2 template file:

```python
template_loader = jinja2.FileSystemLoader(searchpath="./")
template_env = jinja2.Environment(loader=template_loader)
template = template_env.get_template("model_service_template.proto")
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/generate_proto.py#L23-L25).

Now that the template is loaded, we can generate the data structure that
will be passed to the template:

```python
models = []
for model in model_manager.get_models():
    model_details = model_manager.get_model_metadata(qualified_name=model["qualified_name"])
    models.append({
            "qualified_name": model_details["qualified_name"],
            "input_schema": [{
                "index": str(index + 1),
                "name": field_name,
                "type": type_mappings[model_details["input_schema"]["properties"][field_name]["type"]]
        } for index, field_name in enumerate(model_details["input_schema"]["properties"])],
        "output_schema": [
        {
            "index": str(index + 1),
            "name": field_name,
            "type": type_mappings[model_details["output_schema"] ["properties"][field_name]["type"]]
        } for index, field_name in enumerate(model_details["output_schema"]["properties"])]
    })
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/generate_proto.py#L28-L47).

The code builds a dictionary for each model that contains the qualified
name, input schema, and output schema of each model in the ModelManager.
The python data types are converted to the equivalent protocol buffer
types as it goes along. The resulting dictionary is the data structure
that is used by the Jinja2 template defined above to generate a protocol
buffer definition.

Lastly, we'll render the template with the information we just extracted
from the models and then save the generated file to disk:

```python
output_text = template.render(models=models)
with open(output_file, "w") as f:
    f.write(output_text)
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/generate_proto.py#L50-L53).

Now that we have the template and the script that uses the template
completed, we can try to generate a protocol buffer definition for the
service. The command to do this goes like this:

```bash
export PYTHONPATH=./
python scripts generate_proto.py --output_file=model_service.proto
```

The file generated by the command above is called "model\_service.proto"
and it can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_service.proto).
The protocol buffer definition contains the types needed for the
get\_models operation as well as the operation itself. It also contains
the types and operations needed to interact with the iris\_model, which
were automatically extracted from the information provided by the model.

By using a template and script approach to generating a protocol buffer
definition we are able to host any number of models inside of the gRPC
service. This is possible because every model that will be hosted is
required to expose its input and output schema through the MLModel
interface.

# Defining the Service

Now that we have a protocol buffer definition for the gRPC service we
can actually start writing the code to implement the service itself. To
do this, we first need to compile the protocol buffer into its python
implementation. This is done with this command:

```bash
export PYTHONPATH=./
python -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. model_service.proto
```

This command generates two files: the model\_service\_pb2.py file and
the model\_service\_pb2\_grpc.py file. The model\_service\_pb2.py file
contains the python data structures that will serialize and deserialize
from native python types to the protocol buffer binary format. The
model\_service\_pb2\_grpc.py file contains the bindings that will allow
us to write a service that implements the operations defined in the
protocol buffer definition and also to write client code that can call
the implementations.

We'll start by creating a python file that contains the main service
codebase. We'll also implement the get\_models operation in this file
since it is not a dynamic endpoint which depends on the presence of a
model to execute.

The gRPC service is defined as a class that inherits from a "Servicer"
class that was generated by the protoc compiler:

```python
class ModelgRPCServiceServicer(model_service_pb2_grpc.ModelgRPCServiceServicer):
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/service.py#L20-L21).

Within the class, each operation is defined as a method with the same
name as the operation in the .proto file. The get\_models operation is
defined like this:

```python
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
            output_type="{}_output".format(m["qualified_name"]),
            predict_operation="{}_predict".format(m["qualified_name"]))
        models.append(response_model)
    response_models = model_collection()
    response_models.models.extend(models)
    return response_models
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/service.py#L33-L52).

The operation does not receive any data in the request and returns a
model\_collection data structure in the response. The model\_collection
data structure was defined in the .proto file and compiled into a python
class by the protoc compiler. In order to fill the model\_collection, we
iterate through the data returned by the ModelManager creating a list of
model objects as we go along. We then create the model\_collection from
the list and return it to the client.

# MLModelgRPCEndpoint Class

In order for the service to host any model that uses the MLModel base
class, we'll need to create a class that translates the protocol buffer
data structures into the native python data structures used by the
models. This class will be instantiated for every model that is hosted
by the service.

```python
class MLModelgRPCEndpoint(object):
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/ml_model_grpc_endpoint.py#L12-L13).

When the service is initiated, we'll create one instance of this class
for every model. The \_\_init\_\_ method is looks like this:

```python
def __init__(self, model_qualified_name):
    model_manager = ModelManager()
    self._model = model_manager.get_model(model_qualified_name)
    if self._model is None:
        raise ValueError("'{}' not found in ModelManager instance.".format(model_qualified_name))
    
    logger.info("Initializing endpoint for model: {}".format(self._model.qualified_name))
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/ml_model_grpc_endpoint.py#L15-L30).

The \_\_init\_\_ method has one argument called "model\_qualified\_name"
which tells the endpoint class which model it will be hosting. The
\_\_init\_\_ method gets a reference to the ModelManager object that is
managed by the service, then it gets a reference to the model object
from the ModelManager object using the model\_qualified\_name argument.
Lastly, before finishing we check that the model instance is actually
available in the ModelManager.

Now that we have an instance of the endpoint for the MLModel object, we
need to write a method that will make the predict method available as a
gRPC endpoint. We'll do this by defining the \_\_call\_\_ method on the
endpoint class. When a [\_\_call\_\_
method](https://www.journaldev.com/22761/python-callable-__call__)
is attached to a class, it turns all instances of the class into
callables, which allows instances of the class to be used like
functions. This will be useful later when we need to initialize a
dynamic number of endpoints in the gRPC service.

```python
def __call__(self, request, context):
    data = MessageToDict(request, preserving_proto_field_name=True)
    
    prediction = self._model.predict(data=data)
    
    output_protobuf_name = "{}_output".format(self._model.qualified_name)
    output_protobuf = MLModelgRPCEndpoint._get_protobuf(output_protobuf_name)
    
    response = output_protobuf(**prediction)
    
    return response
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/ml_model_grpc_endpoint.py#L32-L50).

The method uses the MessageToDict function from the protobuf package to
turn a protocol buffer data structure into a Python dictionary. The
dictionary is then passed into the model's predict method and a
prediction is returned.

Now that we have a prediction, we have to find the right protocol buffer
data structure to return the prediction result to the client. To do
this, a special method called
"[\_get\_protobuf](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/ml_model_grpc_endpoint.py#L52-L54)"
is used which goes into the model\_service\_pb2.py module where the
python protocol buffer definitions are stored, and dynamically import
the correct class for the output of the model. For example, the
iris\_model's output protocol buffer definition is called
"iris\_model\_output". This lookup is possible because the output
protocol buffer of a model is always named according to the same
pattern. In the last step, we hand over the model's prediction to the
protocol buffer class which initializes itself with the prediction data
and return the resulting object.

# Creating gRPC Endpoints Dynamically

Now that we have a class that can handle any model object, we need to
connect it to the service. To do this, we'll create an \_\_init\_\_
method in the service class that will execute when the service starts
up:

```python
def __init__(self):
    self.model_manager = ModelManager()
    self.model_manager.load_models(configuration=Config.models)
    
    for model in self.model_manager.get_models():
        endpoint = MLModelgRPCEndpoint(model_qualified_name=model["qualified_name"])
    
        operation_name = "{}_predict".format(model["qualified_name"])
        setattr(self, operation_name, endpoint)
```

The code above can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/model_grpc_service/service.py#L23-L31).

The \_\_init\_\_ method first instantiates the ModelManager class and
loads the models listed in the configuration. Once the models are in
memory, we create an endpoint object for each one in a loop. For each
model, we create an MLModelgRPCEndpoint object which is given the
model's qualified name. Then we generate the model's operation name
which matches the operation name for the model's predict operation
listed in the .proto file. For example, the iris\_model's predict
operation is named "iris\_model\_predict". Lastly, we use the operation
name and dynamically set an attribute on the service class that attaches
the newly created endpoint to the class. This last step allows the
service to find the right endpoint for the operation when a call for a
prediction from a certain model is received. The fact that each endpoint
object is callable allows the service to call the endpoint object as if
it was a method of the class even though the endpoint is actually
another class.

# Using the Service

We now have a complete service that we can test out. To do this we'll
execute these commands:

```bash
export PYTHONPATH=./
export APP_SETTINGS=ProdConfig
python model_grpc_service/service.py
```

In order to test out the service, I created a simple script that sends a
single gRPC request to the service. The script is found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/client.py).
To send a request to the get\_models operation, the code looks like
this:

```python
with grpc.insecure_channel("localhost:50051") as channel:
    stub = ModelgRPCServiceStub(channel)
    response = stub.get_models(empty())
    print(response)
```

This code can be found
[here](https://github.com/schmidtbri/grpc-ml-model-deployment/blob/master/scripts/client.py#L9-L15).

To send a test request to the iris\_model\_predict operation of the
service, execute this command:

```bash
export PYTHONPATH=./
python scripts/client.py --iris_model_predict
```

The script will contact the service running locally, make a prediction
with some sample data and print out the prediction result.

# Closing

In this blog post we've shown how to deploy an ML model inside a gRPC
service. As gRPC becomes more popular, the option of deploying ML models
as gRPC services is becoming more attractive. As in previous blog posts,
we've built the service so that it can support any number of ML models,
as long as they implement the ML Model interface. This is one more type
of deployment that we implemented without having to modify the
iris\_model package. The ability to deploy an ML model in different ways
without having to rewrite any part of the model code is very valuable
and ensures good software engineering practices.

By using gRPC to deploy an MLModel, we're able to take advantage of all
of the features of gRPC. These benefits include lightweight and fast
serialization of messages and built in support for streaming. The
ability to document a service API using protocol buffers also simplifies
the documentation and roll out of a new service. Lastly, the ability to
compile service and client codebases from the protocol buffer
definitions allows us to avoid many common errors.

In previous blog posts, deploying a new model was as simple as
installing the model package into the environment and adding it to the
configuration of the application. The schema of the model's inputs and
outputs did not affect the application code at all. In the code of this
blog post, we have to do more work because of the nature of protocol
buffers, since the generated code in the project is specific to a set of
models. Because of this, adding a new model to the gRPC service requires
us to generate a new .proto file from the model's input and output
schemas, generate python code from the .proto file, and finally add the
model to the configuration of the service. The extra steps make it more
complex to deploy the service.

In the future, the service could be improved by handling more complex
schemas, since currently the schema mapping between native python types
and protocol buffers only supports simple data structures. Another way
to improve the service is to add support for streaming endpoints for
each model. Lastly, protocol buffers have a mechanism for evolving
message schemas, the code could be improved by safely evolving the shema
of the service through this mechanism when the model schema changes. 
