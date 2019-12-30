"""Application that holds MLModel stream processors."""
import os
import logging

from model_grpc_service.config import Config
from model_grpc_service.model_manager import ModelManager


logging.basicConfig(level=logging.INFO)
