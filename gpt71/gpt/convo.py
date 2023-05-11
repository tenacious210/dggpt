# Various tools for manipulating openai convos
import logging
from gpt71.config import BASE_LENGTH
from .tokens import count_tokens

logger = logging.getLogger(__name__)


def trim_tokens(convo: list[dict], max_tokens: int) -> list[dict]:
    """Trims old messages from a convo"""
    old_convo = convo[:]
    while count_tokens(convo) > max_tokens:
        logger.debug(f"Trimming from convo: {convo[BASE_LENGTH : BASE_LENGTH + 2]}")
        del convo[BASE_LENGTH : BASE_LENGTH + 2]
    if (new_tokens := count_tokens(convo)) != (old_tokens := count_tokens(old_convo)):
        logger.debug(f"Trimmed prompt from {old_tokens} to {new_tokens} tokens")
    return convo


def delete_last_prompt(convo: list[dict]) -> list[dict]:
    logger.debug(f"Deleting last prompt: {convo[-2:]}")
    del convo[-2:]
    return convo
