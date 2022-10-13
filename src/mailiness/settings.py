import configparser
import os
from pathlib import Path
from typing import Optional


def get_default_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config["mail"] = {
        "vmail_directory": "/var/vmail",
    }
    config["db"] = {
        "connection_string": "/var/local/mailserver.db",
        "domains_table_name": "domains",
        "users_table_name": "users",
        "aliases_table_name": "aliases",
    }
    config["users"] = {
        "insert_password_hash_prefix": True,
        "password_hash_prefix": "{BLF-CRYPT}",
    }
    config["spam"] = {
        "dkim_private_key_directory": "/var/lib/rspamd/dkim",
        "dkim_maps_path": "/etc/rspamd/dkim_selectors.map",
    }
    return config


def write_default_config(path: Path) -> configparser.ConfigParser:
    config = get_default_config()
    with path.open("w", encoding="utf-8") as fp:
        config.write(fp)
    return config


def get_config(
    config_file_path: Optional[str] = os.getenv("CONFIG_FILE"),
) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if config_file_path is None:
        config_file_path = "/etc/mailiness.ini"

    config_file_path = Path(config_file_path)

    if not config_file_path.exists():
        config_file_path.touch()
        config = write_default_config(config_file_path)
    else:
        config.read(str(config_file_path))
    return config


# According to https://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
RSA_PUBLIC_EXPONENT = 65537

# Use 2048 for maximum compatibility as at year 2022.
DKIM_KEY_SIZE = 2048
