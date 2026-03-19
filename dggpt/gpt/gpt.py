# Ties together all of the gpt tools
import logging
from collections import deque
from .responses import chat_completion

logger = logging.getLogger(__name__)

user_message: dict = lambda name, data: {"role": "user", "content": f"{name}: {data}"}


def generate_response(
    nick: str,
    data: str,
    convo: deque[dict],
    max_tokens: int,
) -> deque[dict]:
    """
    Gets a chat completion from openai for a DGG message
    Takes in an openai convo, returns the new openai convo
    Warning: Does not moderate the input or response!
    """
    logger.debug("Getting chat response...")
    convo.append(user_message(nick, data))
    return chat_completion(convo, max_tokens)
