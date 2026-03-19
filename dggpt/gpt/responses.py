# Handles all requests to openai
import logging
from collections import deque
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
from dggpt.config import OPENAI_KEY, SYSTEM, BASE_CONVO

client = OpenAI(api_key=OPENAI_KEY, timeout=20, max_retries=0)

logger = logging.getLogger(__name__)

CHAT_MODEL = "gpt-5.4-nano"


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
    if "harassment" in flags:
        flags.remove("harassment")
    return flags


def chat_completion(convo: deque[dict], max_tokens: int) -> list[dict]:
    """
    Gets a chat completion from openai.
    Takes in an openai convo, returns the updated convo.
    """

    logger.debug(f"Sending chat request...\n  Input: {convo[-1]}")

    rsp = client.responses.create(
        model=CHAT_MODEL,
        reasoning={"effort": "none"},
        instructions=SYSTEM,
        input=BASE_CONVO + tuple(convo),
    )
    if err := rsp.error:
        error_message = f"error: {err.message} temmieDank"
        logger.warning(f"Got an openai error: {err.message}")
        convo.append({"role": "assistant", "content": error_message})
        return convo

    convo.append({"role": "assistant", "content": rsp.output_text})
    logger.debug(f"Chat completion recieved\n  Output: {rsp}")
    return convo
