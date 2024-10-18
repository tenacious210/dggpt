from datetime import datetime
import logging

from elevenlabs.client import ElevenLabs
from elevenlabs import save
from pygame import mixer

from dggpt.config import ELEVENLABS_KEY

logger = logging.getLogger(__name__)
client = ElevenLabs(api_key=ELEVENLABS_KEY)

VOICE = "Jessica"
MODEL = "eleven_multilingual_v2"
# OUTPUT_DEVICE = "VB-Cable"
OUTPUT_DEVICE = "Speakers (VB-Audio Virtual Cable)"
# OUTPUT_DEVICE = "Speakers (Realtek(R) Audio)"

mixer.init(devicename=OUTPUT_DEVICE, buffer=4096)


def generate_tts(input: str = "Hello World"):
    """Takes in a string and outputs a TTS to the selected output device"""
    audio = client.generate(
        text=input,
        voice=VOICE,
        model=MODEL,
    )
    filename = "mp3files/" + datetime.now().strftime("%Y%m%d%H%M%S") + ".mp3"
    save(audio, filename)
    # filename = "mp3files/test.mp3"
    mixer.music.load(filename)
    logger.info(f"Playing audio for {input}")
    mixer.music.play()
