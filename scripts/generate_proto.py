""""""
import argparse
import jinja2

from model_grpc_service.config import Config
from model_grpc_service.model_manager import ModelManager

# instantiating the ModelManager singleton
model_manager = ModelManager()
model_manager.load_models(Config.models)

# this dict maps the field types of the model schema to proto buffer types
type_mappings = {
    "string": "string",
    "number": "float",
    "integer": "int64",
    "boolean": "bool",
    "null": "NullValue"
}


def main(output_file):
    template_loader = jinja2.FileSystemLoader(searchpath="./scripts")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("template.proto")

    # building a data structure to feed to the template from the models in ModelManager
    models = []
    for model in model_manager.get_models():
        model_details = model_manager.get_model_metadata(qualified_name=model["qualified_name"])
        models.append(
            {
                "qualified_name": model_details["qualified_name"],
                "input_schema": [
                    {
                        "index": str(index + 1),
                        "name": field_name,
                        "type": type_mappings[model_details["input_schema"]["properties"][field_name]["type"]]
                    } for index, field_name in enumerate(model_details["input_schema"]["properties"])],
                "output_schema": [
                    {
                        "index": str(index + 1),
                        "name": field_name,
                        "type": type_mappings[model_details["output_schema"]["properties"][field_name]["type"]]
                    } for index, field_name in enumerate(model_details["output_schema"]["properties"])]
            }
        )

    # rendering the template with the data structure
    output_text = template.render(models=models)

    with open(output_file, "w") as f:
        f.write(output_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build a protocol buffer definition from MLModel classes.')
    parser.add_argument('--output_file', type=str, help='Location of output .proto file.')

    args = parser.parse_args()

    main(output_file=args.output_file)
