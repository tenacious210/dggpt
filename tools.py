import tiktoken
import json
from typing import Union


def base_history() -> list[dict]:
    with open("system.txt", "r") as sys_txt:
        system = sys_txt.read()

    with open("base.json", "r") as base_json:
        base = json.loads(base_json.read())

    return [{"role": "system", "content": system}] + base


def read_cfg() -> dict[str, Union[str, list]]:
    with open("config.json", "r") as cfg_json:
        cfg = json.loads(cfg_json.read())
    return cfg


def save_cfg(cfg: dict):
    with open("config.json", "w") as cfg_json:
        cfg_json.write(json.dumps(cfg, indent=1))


def count_tokens(messages: dict):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens
