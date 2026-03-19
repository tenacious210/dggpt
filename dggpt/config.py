# Handles reading/writing files in the config folder
import json
import logging
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


with open("config/config.json", "r") as config_json:
    config = json.load(config_json)
    OPENAI_KEY = config["openai_key"]

with open("config/system.txt", "r") as sys_txt:
    SYSTEM = sys_txt.read()

with open("config/base_convo.json", "r") as base_json:
    BASE_CONVO = tuple(json.load(base_json))

with open("config/schema.config.json", "r") as schema_json:
    _schema = json.load(schema_json)

logger.debug("Loaded constants from config files")


def read_config() -> dict[str, str | list]:
    """Reads the config.json file, returns it as a dict"""
    logger.debug("Reading config file")
    with open("config/config.json", "r") as config_json:
        config = json.load(config_json)
    return config


def save_config(config: dict) -> None:
    """Validates and writes a dict to the config.json file"""
    logger.debug("Saving config file")
    try:
        validate(instance=config, schema=_schema)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration data: {e.message}")

    with open("config/config.json", "w") as config_json:
        json.dump(config, config_json, indent=1)
