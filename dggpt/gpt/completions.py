# Handles all requests to openai
import logging
from openai import OpenAI
from openai import (
    OpenAI,
    RateLimitError,
    APIError,
    APIStatusError,
    BadRequestError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)

openai_errors = (
    RateLimitError,
    APIError,
    APIStatusError,
    BadRequestError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)
from dggpt.config import OPENAI_KEY, add_monthly_tokens

client = OpenAI(api_key=OPENAI_KEY, timeout=20, max_retries=0)

logger = logging.getLogger(__name__)

CHAT_MODEL = "gpt-4o-mini"
IMAGE_MODEL = "dall-e-3"


def moderation_completion(message: str) -> list[str]:
    """
    Gets a moderation completion from openai.
    Returns the flags that the prompt triggered.
    """
    flags = []
    logger.debug("Sending moderation request...")
    mod = client.moderations.create(input=message)
    for category in mod.results[0].categories:
        if category[1]:
            flags.append(category[0])
    if flags:
        logger.debug(
            f"Moderation flags triggered:"
            + f'\n  Input: "{message}"'
            + f'\n  Flags: {", ".join(flags)}'
        )
    if "harassment" in flags:
        flags.remove("harassment")
    return flags


def chat_completion(convo: list[dict], max_tokens: int = 65) -> list[dict]:
    """
    Gets a chat completion from openai.
    Takes in an openai convo, returns the updated convo.
    """

    logger.debug(f"Sending chat request...\n  Input: {convo[-1]}")
    try:
        rsp = client.chat.completions.create(
            model=CHAT_MODEL,
            max_tokens=max_tokens,
            messages=convo,
        )
    except openai_errors as openai_error:
        error_name = type(openai_error).__name__
        error_message = f"error: {error_name} temmieDank"
        logger.warning(f"Got an openai error: {openai_error}")
        convo.append({"role": "assistant", "content": error_message})
        return convo
    message = dict(rsp.choices[0].message)
    convo.append({"role": "assistant", "content": message["content"]})
    logger.debug(f"Chat completion recieved\n  Output: {message}")
    add_monthly_tokens(rsp.usage.total_tokens)
    return convo


def image_completion(prompt: str) -> str:
    """
    Gets an image from openai.
    Takes in a prompt convo, returns the link to the image.
    """

    logger.debug(f"Sending image request...\n  Input: {prompt}")
    rsp = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return rsp.data[0].url
