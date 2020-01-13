"""Configuration for the application."""


class Config(dict):
    """Configuration for all environments."""

    models = [
        {
            "module_name": "iris_model.iris_predict",
            "class_name": "IrisModel"
        }
    ]


class ProdConfig(Config):
    """Configuration for the prod environment."""

    service_port = "[::]:50051"


class BetaConfig(Config):
    """Configuration for the beta environment."""

    service_port = "[::]:50051"


class TestConfig(Config):
    """Configuration for the test environment."""

    service_port = "[::]:50051"


class DevConfig(Config):
    """Configuration for the dev environment."""

    service_port = "[::]:50051"
