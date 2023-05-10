# Handles moderation for messages going out to DGG

import re
from gpt71.request import request_phrases


def bot_filter(message: str) -> bool:
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

    return any(check(message) for check in (unique, repeated, ascii, bad_word))
