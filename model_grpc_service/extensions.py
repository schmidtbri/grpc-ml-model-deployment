"""Nameko extensions to support the model service."""
from nameko.extensions import DependencyProvider, Entrypoint
from nameko.exceptions import ContainerBeingKilled

from model_grpc_service.model_manager import ModelManager


class ModelManagerProvider(DependencyProvider):
    """Instantiates and injects a ModelManager instance into every worker."""

    def __init__(self, configuration, **kwargs):
        """Initialize dependency provider."""
        self.configuration = configuration
        super(ModelManagerProvider, self).__init__(**kwargs)

    def setup(self):
        """Instantiate and load models into ModelManager once at startup time."""
        self.model_manager = ModelManager()
        self.model_manager.load_models(configuration=self.configuration)

    def get_dependency(self, worker_ctx):
        """Return the instance of ModelManager created at setup."""
        return self.model_manager


class StartupEntryPoint(Entrypoint):
    """Entrypoint that executes method at container startup."""

    def __init__(self):
        """Initialize entrypoint object."""
        super(StartupEntryPoint).__init__()

    def start(self):
        """Execute method at startup."""
        try:
            self.container.spawn_worker(self, (), {})
        except ContainerBeingKilled:
            pass


startup = StartupEntryPoint.decorator
