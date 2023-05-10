# Handles all requests to openai

import openai
from gpt71.config import OPENAI_KEY, add_monthly_tokens

CHAT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 100

openai.api_key = OPENAI_KEY


def moderation_completion(message: str) -> list:
    """
    Gets a moderation completion from openai.
    Returns the flags that the prompt triggered.
    """
    flags = []
    mod = openai.Moderation.create(input=message)
    for category in mod["results"][0]["categories"]:
        if mod["results"][0]["categories"][category]:
            flags.append(category)
    return flags


def chat_completion(convo: list[dict]) -> list[dict]:
    """
    Gets a chat completion from openai.
    Takes in an openai convo, returns the updated convo.
    """
    rsp = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        max_tokens=MAX_TOKENS,
        messages=convo,
    )
    convo.append(rsp["choices"][0]["message"])
    add_monthly_tokens(rsp["usage"]["total_tokens"])
    return convo
