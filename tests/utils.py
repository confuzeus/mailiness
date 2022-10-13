import tempfile
from configparser import ConfigParser

from mailiness.settings import get_default_config


def get_test_config() -> ConfigParser:
    config = get_default_config()
    config["mail"]["vmail_directory"] = tempfile.mkdtemp()
    _, config["db"]["connection_string"] = tempfile.mkstemp()
    config["spam"]["dkim_private_key_directory"] = tempfile.mkdtemp()
    _, config["spam"]["dkim_maps_path"] = tempfile.mkstemp()

    return config
