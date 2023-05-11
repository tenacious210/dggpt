# Handles reading/writing files in the config folder
import os
import json
import logging
from typing import Union
from datetime import datetime
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

os.chdir("config")

with open("config.json", "r") as config_json:
    OPENAI_KEY = json.load(config_json)["openai_key"]

with open("system.txt", "r") as sys_txt:
    SYSTEM = sys_txt.read()

with open("base_convo.json", "r") as base_json:
    _base_list = [{"role": "system", "content": SYSTEM}] + json.load(base_json)
    BASE_CONVO = tuple(_base_list)
    BASE_LENGTH = len(BASE_CONVO)

with open("base_summary.json", "r") as summarize_json:
    BASE_SUMMARY = tuple(json.load(summarize_json))

with open("bad_words.csv", "r") as bad_words_csv:
    BAD_WORDS = tuple(bad_words_csv.read().split())

with open("config_schema.json", "r") as schema_json:
    _schema = json.load(schema_json)

logger.debug("Loaded constants from config files")


def read_config() -> dict[str, Union[str, list]]:
    """Reads the config.json file, returns it as a dict"""
    logger.debug("Reading config file")
    with open("config.json", "r") as config_json:
        config = json.load(config_json)
    return config


def save_config(config: dict) -> None:
    """Validates and writes a dict to the config.json file"""
    logger.debug("Saving config file")
    try:
        validate(instance=config, schema=_schema)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration data: {e.message}")

    with open("config.json", "w") as config_json:
        json.dump(config, config_json, indent=1)


def add_monthly_tokens(amount: int) -> None:
    """Adds tokens to this month's tally"""
    this_month = datetime.utcnow().strftime("%Y-%m")

    with open("monthly_tokens.json", "r") as monthly_tokens_json:
        monthly_tokens: dict = json.load(monthly_tokens_json)

    if this_month not in monthly_tokens.keys():
        monthly_tokens[this_month] = 0
    monthly_tokens[this_month] += amount

    with open("monthly_tokens.json", "w") as monthly_tokens_json:
        json.dump(monthly_tokens, monthly_tokens_json)

    logger.debug(f"Added {amount} to {this_month} in monthly_tokens")


def read_monthly_tokens() -> int:
    """Reads this month's token tally"""
    this_month = datetime.utcnow().strftime("%Y-%m")
    with open("monthly_tokens.json", "r") as monthly_tokens_json:
        monthly_tokens: dict = json.load(monthly_tokens_json)
    if this_month not in monthly_tokens.keys():
        add_monthly_tokens(0)
        return 0
    current_tokens = monthly_tokens[this_month]
    logger.debug(f"Read {current_tokens} tokens for {this_month} from monthly_tokens")
    return current_tokens
