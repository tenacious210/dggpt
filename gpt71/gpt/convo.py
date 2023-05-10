# Various tools for manipulating openai convos

from gpt71.config import BASE_LENGTH
from .tokens import count_tokens


def trim_tokens(convo: list[dict], max_tokens: int) -> list[dict]:
    """Trims old messages from a convo"""
    while count_tokens(convo) > max_tokens:
        del convo[BASE_LENGTH : BASE_LENGTH + 2]
    return convo


def delete_last_prompt(convo: list[dict]) -> list[dict]:
    del convo[-2:]
    return convo
