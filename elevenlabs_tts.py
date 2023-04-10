import os
import platform

from elevenlabslib import *
from elevenlabslib.helpers import save_bytes_to_path

from configuration import ConfigFile, ConfigNode


class ElevenLabsTTS:
    def __init__(self, config: ConfigFile):
        self.user = ElevenLabsUser(config.get(ConfigNode.API_KEY))

    def get_voices(self) -> list:
        """Return a list of voices"""
        return [voice.initialName for voice in self.user.get_available_voices()]

    def tts(self, text: str, voice: str) -> None:
        """Return the audio from the text"""
        voice = self.user.get_voices_by_name(voice)[0]
        data = voice.generate_audio_bytes(text, 0.7, 0.7)
        save_bytes_to_path("elevenlabs.wav", data)
