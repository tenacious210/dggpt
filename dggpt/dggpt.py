import logging
from threading import Thread
from collections import deque
from random import choice
from datetime import datetime, timedelta
from time import sleep
from dggbot import DGGBot, DGGLive, Message, StreamInfo
from .config import (
    read_config,
    save_config,
)
from .gpt import generate_response
from .gpt.moderation import flag_check
from .dgg import format_dgg_message, will_trigger_bot_filter
from .dgg.moderation import SPAM_SEARCH_AMOUNT
from .request import (
    request_emotes,
    request_phrases,
)

logger = logging.getLogger(__name__)


class DGGPTBot(DGGBot):
    """Base form of the bot with no commands"""

    def __init__(self):
        # gpt_config keys: "dgg_key", "openai_key", "admins", "blacklist"
        self.gpt_config = read_config()
        super().__init__(self.gpt_config["dgg_key"])
        self._avoid_dupe = True
        self.stream_is_live: bool = False
        self.last_sent: datetime = datetime.now() - timedelta(seconds=60)
        self.convo: deque[dict] = deque(maxlen=150)
        self.message_history: deque[str] = deque(maxlen=SPAM_SEARCH_AMOUNT)
        self.cooldown = 60
        self.max_resp_tokens = 80
        Thread(target=self.update_live_status).start()
        logger.info(f"Bot initialized")

    def send(self, data: str):
        logger.debug(f"Sending message:\n{data}")
        super().send(data[:512])

    def _convert_to_int(self, value):
        try:
            return int(value)
        except ValueError as e:
            self.send("that's not an integer MMMM")
            raise e

    def check_cooldown(self) -> int:
        last_sent_delta = (datetime.now() - self.last_sent).seconds
        remaining = self.cooldown - last_sent_delta
        return 0 if remaining < 0 else remaining

    def is_admin(self, msg: Message) -> bool:
        return msg.nick in self.gpt_config["admins"]

    def delete_last_prompt(self):
        del self.convo[-1]
        del self.convo[-1]

    def process_privmsg(self, nick: str, data: str):
        logger.info(f"Got whispered: {nick}: {data}")
        if nick in self.gpt_config["admins"]:
            self.respond_to_mention(nick, data)
            sleep(3)
            self.send_privmsg(nick, "PepOk")

    def process_msg(self, nick: str, data: str):
        self.message_history.append(data)

    def respond_with_flags(self, nick: str, data: str):
        if flags := flag_check(data, raise_error=False):
            response = (
                f"{nick} Congrats, your prompt was flagged"
                + f" by openai for: {', '.join(flags)} GIGACHAD"
            )
            if "sexual/minors" in response:
                response = response.replace("GIGACHAD", "HUH")
            if will_trigger_bot_filter(response, self.message_history):
                self.send_filter_response(nick)
            else:
                self.send(response)
        self.last_sent = datetime.now()
        return flags

    def pre_response_check(self, nick: str, data: str) -> bool:
        if data.startswith(self.prefix):
            logger.debug("Check fail: Name and command used at the same time")
            return False
        if len(self.convo) > 0 and self.convo[-1]["role"] == "user":
            logger.warning("Check fail: Still waiting on the last completion")
            return False
        if "#kick/gpt71" in data:
            logger.debug(f"Check fail: Name used in Kick embed")
            return False
        if nick in self.gpt_config["admins"]:
            if nick == "tena" or nick == "Destiny":
                logger.debug("Check pass: Owner requested")
                return True
            if self.respond_with_flags(nick, data):
                logger.debug(f"Check fail: Admin prompt was flagged")
                return False
            logger.debug("Check pass: Admin requested")
            return True
        if self.stream_is_live:
            logger.debug("Check fail: Stream is live")
            return False
        if remaining := self.check_cooldown():
            logger.debug(f"Check fail: On cooldown for another {remaining}s")
            return False
        if nick in self.gpt_config["blacklist"]:
            logger.debug(f"Check fail: {nick} is blacklisted")
            return False
        if self.respond_with_flags(nick, data):
            logger.debug(f"Check fail: Prompt was flagged")
            return False
        logger.debug("Check pass")
        return True

    def send_filter_response(self, user: str):
        responses = (
            f"{user} nah, I don't feel like it MMMM",
            f"/me ignores {user}'s request TF",
            f"/me doesn't understand {user}'s request temmieDank",
            f"/me ignores {user} MMMM",
        )
        self.send(choice(responses))
        return

    def respond_to_mention(self, nick: str, data: str):
        logger.debug(f"Bot was mentioned:\n  {nick}: {data}")
        if not self.pre_response_check(nick, data):
            return
        self.last_sent = datetime.now()
        generate_response(nick, data, self.convo, self.max_resp_tokens)
        formatted = format_dgg_message(self.convo[-1]["content"])
        if will_trigger_bot_filter(formatted, self.message_history):
            logger.debug("Filter check failed")
            self.send_filter_response(nick)
            self.delete_last_prompt()
            return
        if formatted.isspace() or formatted == "":
            self.send_filter_response(nick)
            return
        self.send(formatted)

    def repeat(self, data: str):
        self.send(data.split(maxsplit=1)[1])
        self.last_sent = datetime.now()

    def clear_caches(self):
        logger.debug("!clearcache was called")
        request_phrases.cache_clear()
        request_emotes.cache_clear()
        self.send("PepOk cleared caches")

    def clear_convo(self):
        self.convo = []
        logger.debug(f"Convo wiped")

    def clear_last_prompt(self):
        logger.debug("!wipelast was called")
        self.delete_last_prompt()
        self.send(f"PepOk deleted the last prompt")

    def blacklist_add(self, name: str):
        logger.info(f"!bla was used on {name}")
        if name not in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].append(name)
        save_config(self.gpt_config)
        self.send(f"PepOk {name} blacklisted")

    def blacklist_remove(self, name: str):
        logger.info(f"!blr was used on {name}")
        if name in self.gpt_config["blacklist"]:
            self.gpt_config["blacklist"].remove(name)
        save_config(self.gpt_config)
        self.send(f"PepOk {name} unblacklisted")

    def change_cooldown(self, seconds: str):
        self.cooldown = self._convert_to_int(seconds)
        logger.info(f"cooldown set to {seconds}")
        self.send(f"PepOk changed the cooldown to {self.cooldown}s")

    def change_convo_limit(self, msg_limit: str):
        logger.debug("!context was used")
        msg_limit = abs(self._convert_to_int(msg_limit))
        if msg_limit < 15:
            msg_limit += 15
        self.convo.maxlen = msg_limit
        self.send(f"PepOk changed the context limit to {msg_limit}")

    def change_resp_token_limit(self, token_limit: str):
        logger.debug("!maxresp was used")
        token_limit = abs(self._convert_to_int(token_limit))
        self.max_resp_tokens = token_limit
        self.send(f"PepOk changed the max response length to {self.max_resp_tokens}")

    def update_live_status(self):
        """Runs as a thread, updates stream status"""
        live = DGGLive()

        @live.event()
        def on_streaminfo(streaminfo: StreamInfo):
            self.stream_is_live = streaminfo.is_live()
            logger.debug(f"Live status: {self.stream_is_live}")

        live.run_forever()
