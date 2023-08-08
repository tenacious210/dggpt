# Ties together all of the gpt tools
import logging
from dggbot import Message
from .completions import chat_completion
from .moderation import flag_check, remove_bad_words

logger = logging.getLogger(__name__)

user_message: dict = lambda name, data: {"name": name, "role": "user", "content": data}
summary_message: dict = lambda data: {"role": "user", "content": data}


def generate_response(
    nick: str,
    data: str,
    convo: list[dict],
    max_tokens: int,
) -> list[dict]:
    """
    Gets a chat completion from openai for a DGG message
    Takes in an openai convo, returns the new openai convo
    Warning: Does not moderate the input or response!
    """
    logger.info("Getting chat response...")
    convo.append(user_message(nick, data))
    return chat_completion(convo, max_tokens)


def generate_summary(debate: str, convo: list[dict]) -> list[dict]:
    """
    Moderates a DGG debate and then gets a summary completion from openai
    Takes in an openai convo, returns the new openai convo
    Warning: Does not moderate the response!
    """
    logger.info("Getting summary...")
    debate = remove_bad_words(debate)
    flag_check(debate)
    convo.append(summary_message(debate))
    return chat_completion(convo)


def generate_solution(convo: list[dict]) -> list[dict]:
    """Generates a solution to a summary convo"""
    logger.info("Getting solution...")
    PROMPT = "Is anyone being unreasonable? Be concise. Do not give a neutral answer."
    convo.append(summary_message(PROMPT))
    return chat_completion(convo)
