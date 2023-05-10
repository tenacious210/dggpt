# Handles moderation for messages going out to DGG

import re
from collections import deque
import Levenshtein
from gpt71.request import request_phrases

SPAM_SEARCH_AMOUNT = 75


def bot_filter(message: str, message_history: deque[str]) -> bool:
    def unique(message: str) -> bool:
        words_list = re.findall(r"[^, ]+", message.lower())
        if len(words_list) >= 8:
            total_words = len(words_list)
            unique_words = len(set(words_list))
            if total_words == 0:
                return False
            return unique_words / total_words <= 0.45
        return False

    def repeated(message: str) -> bool:
        if len(message) < 90 and len(message.split()) > 4:
            return False
        words = message.split()
        return not all(len(mess) < 90 / 1.5 or len(set(mess)) >= 9 for mess in words)

    def ascii(message: str) -> bool:
        non_ascii_count = len(re.findall(r"[^\x20-\x7F]", message))
        ascii_punct_count = len(re.findall(r"[\x21-\x2F\x3A-\x40]", message))
        return non_ascii_count > 20 or ascii_punct_count > 40

    def bad_word(message: str) -> bool:
        phrases, regex_phrases = request_phrases()
        return any(p.lower() in message.lower() for p in phrases) or any(
            regex.search(message) for regex in regex_phrases
        )

    def too_similar(message: str, message_history: deque[str]) -> bool:
        def similarity(old_message: str, new_message: str) -> float:
            longer_message = max(old_message, new_message, key=len)
            shorter_message = min(old_message, new_message, key=len)
            longer_length = len(longer_message)
            if longer_length == 0:
                return 1.0
            dist = Levenshtein.distance(longer_message, shorter_message)
            return (longer_length - dist) / float(longer_length)

        if len(message) < 100:
            return False
        match_percents = [
            similarity(msg.lower().strip(), msg.lower().strip())
            for msg in message_history
        ]
        return any(match_percent > 0.9 for match_percent in match_percents)

    if too_similar(message, message_history):
        return True

    return any(check(message) for check in (unique, repeated, ascii, bad_word))
