# Handles moderation for prompts to openai
import re
import logging
from gpt71.config import BAD_WORDS
from .completions import moderation_completion

logger = logging.getLogger(__name__)

bad_word_patterns = (
    re.compile(rf"\b{bad_word}\b", re.IGNORECASE) for bad_word in BAD_WORDS
)


def flag_check(message: str, raise_error: bool = True) -> list:
    """Get all flags triggered by a prompt and raise an error"""
    if (flags := moderation_completion(message)) and raise_error:
        raise Exception(f"Prompt was flagged")
    return flags


def remove_bad_words(message: str) -> str:
    """Removes all bad words (defined in bad_words.csv) from a string."""
    removed = []
    for bad_word_regex in bad_word_patterns:
        message = bad_word_regex.sub("_", message)
        removed.append(bad_word_regex)
    if removed:
        logger.debug(
            "Removed bad words:"
            + f'\n  Output: "{message}"'
            + f'\n  Removed words: {", ".join(removed)}'
        )
    return message
