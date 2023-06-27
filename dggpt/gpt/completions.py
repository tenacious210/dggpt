# Handles all requests to openai
import logging
import openai
from openai.error import RateLimitError, APIError, ServiceUnavailableError
from dggpt.config import OPENAI_KEY, add_monthly_tokens

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

    logger.info(f"Sending chat request...\n  Input: {convo[-1]}")
    try:
        rsp = openai.ChatCompletion.create(
            model=CHAT_MODEL,
            max_tokens=MAX_TOKENS,
            messages=convo,
        )
    except (RateLimitError, APIError, ServiceUnavailableError) as openai_error:
        error_name = type(openai_error).__name__
        error_message = (
            f"sorry, I got a {error_name} from openai FeelsDankMan try again later"
        )
        logger.info("Got an openai error.")
        convo.append({"role": "assistant", "content": error_message})
        return convo
    message = dict(rsp["choices"][0]["message"])
    convo.append(message)
    logger.info(f"Chat completion recieved\n  Output: {message}")
    add_monthly_tokens(rsp["usage"]["total_tokens"])
    return convo
