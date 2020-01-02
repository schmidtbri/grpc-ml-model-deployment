""""""
from nameko.extensions import DependencyProvider

from model_grpc_service.model_manager import ModelManager


class ModelManagerProvider(DependencyProvider):
    """Instantiates and injects a ModelManager instance into every worker."""

    def __init__(self, configuration, **kwargs):
        self.configuration = configuration
        super(ModelManagerProvider, self).__init__(**kwargs)

    def setup(self):
        self.model_manager = ModelManager()
        self.model_manager.load_models(configuration=self.configuration)

    def get_dependency(self, worker_ctx):
        return self.model_manager
