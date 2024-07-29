# Handles moderation for messages going out to DGG
import re
import logging
from collections import deque
import Levenshtein
from dggpt.request import request_phrases

logger = logging.getLogger(__name__)

SIMILARITY_MINIMUM_LEN = 85
SPAM_SEARCH_AMOUNT = 75
DESTINY_LINK_REGEX = re.compile(
    "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


def will_trigger_bot_filter(message: str, message_history: deque[str]) -> bool:
    def unique(message: str) -> bool:
        words_list = re.findall(r"[^, ]+", message.lower())
        if len(words_list) >= 8:
            total_words = len(words_list)
            unique_words = len(set(words_list))
            if total_words == 0:
                return False
            if unique_words / total_words <= 0.45:
                logger.debug(f'Failed uniqueness test:\n  "{message}"')
                return True
        return False

    def repeated(message: str) -> bool:
        if len(message) < 90 and len(message.split()) > 4:
            return False
        words = message.split()
        if not all(len(mess) < 90 / 1.5 or len(set(mess)) >= 9 for mess in words):
            logger.debug(f'Failed repetition test:\n  "{message}"')
            return True
        return False

    def ascii(message: str) -> bool:
        non_ascii_count = len(re.findall(r"[^\x20-\x7F]", message))
        ascii_punct_count = len(re.findall(r"[\x21-\x2F\x3A-\x40]", message))
        if non_ascii_count > 20 or ascii_punct_count > 40:
            logger.debug(f'Failed ascii test:\n  "{message}"')
            return True
        return False

    def bad_word(message: str) -> bool:
        phrases, regex_phrases = request_phrases()
        banned_phrase = any(p.lower() in message.lower() for p in phrases)
        banned_regex = any(r.search(message) for r in regex_phrases)
        if banned_phrase or banned_regex:
            logger.debug(f'Failed bad word test:\n  "{message}"')
            return True
        return False

    def too_similar(message: str, message_history: deque[str]) -> bool:
        def similarity(old_message: str, new_message: str) -> float:
            longer_message = max(old_message, new_message, key=len)
            shorter_message = min(old_message, new_message, key=len)
            longer_length = len(longer_message)
            if longer_length == 0:
                return 1.0
            dist = Levenshtein.distance(longer_message, shorter_message)
            return (longer_length - dist) / float(longer_length)

        if len(message) < SIMILARITY_MINIMUM_LEN:
            return False
        for old_message in message_history:
            if similarity(message.lower().strip(), old_message.lower().strip()) > 0.9:
                logger.debug(
                    "Failed similarity test:"
                    + f'\n  Input message: "{message}"'
                    + f'\n  Other message: "{old_message}"'
                )
                return True
        return False

    if too_similar(message, message_history):
        return True

    def tags_destiny_with_link(message: str):
        return "https" in message.lower() and "destiny" in message.lower()

    return any(
        check(message)
        for check in (unique, repeated, ascii, bad_word, tags_destiny_with_link)
    )
