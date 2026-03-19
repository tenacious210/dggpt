# Handles moderation for prompts to openai
import logging
from .responses import moderation_completion

logger = logging.getLogger(__name__)


def flag_check(message: str, raise_error: bool = True) -> list:
    """Get all flags triggered by a prompt and raise an error"""
    if (flags := moderation_completion(message)) and raise_error:
        raise Exception(f"Prompt was flagged")
    return flags
