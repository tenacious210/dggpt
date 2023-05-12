# Handles all requests to openai
import logging
import openai
from gpt71.config import OPENAI_KEY, add_monthly_tokens

logger = logging.getLogger(__name__)

CHAT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 100

openai.api_key = OPENAI_KEY


def moderation_completion(message: str) -> list[str]:
    """
    Gets a moderation completion from openai.
    Returns the flags that the prompt triggered.
    """
    flags = []
    logger.debug("Sending moderation request...")
    mod = openai.Moderation.create(input=message)
    for category in mod["results"][0]["categories"]:
        if mod["results"][0]["categories"][category]:
            flags.append(category)
    if flags:
        logger.info(
            f"Moderation flags triggered:"
            + f'\n  Input: "{message}"'
            + f'\n  Flags: {", ".join(flags)}'
        )
    return flags


def chat_completion(convo: list[dict]) -> list[dict]:
    """
    Gets a chat completion from openai.
    Takes in an openai convo, returns the updated convo.
    """
    logger.info(f"Sending chat request\n  Input: {convo[-1]}")
    rsp = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        max_tokens=MAX_TOKENS,
        messages=convo,
    )
    convo.append(rsp["choices"][0]["message"])
    logger.info(f"Chat completion recieved\n  Output: {convo[-1]}")
    add_monthly_tokens(rsp["usage"]["total_tokens"])
    return convo
