from datetime import datetime
import logging

from elevenlabs.client import ElevenLabs
from elevenlabs import save

from dggpt.config import ELEVENLABS_KEY

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=ELEVENLABS_KEY)

VOICE = "Jessica"
MODEL = "eleven_flash_v2_5"


def generate_tts(input: str):
    """Takes in a string and outputs a TTS"""
    audio = client.generate(
        text=input,
        voice=VOICE,
        model=MODEL,
    )
    filename = "mp3files/" + datetime.now().strftime("%Y%m%d%H%M%S") + ".mp3"
    save(audio, filename)
