from elevenlabslib import *
from elevenlabslib.helpers import save_bytes_to_path

from configuration import ConfigFile, ConfigNode
from tts_provider import TTSProvider


class ElevenLabsTTS(TTSProvider):
    OUTPUT_FILE = "elevenlabs.wav"

    def __init__(self, config: ConfigFile):
        self.user = ElevenLabsUser(config.get(ConfigNode.API_KEY))

    def get_voices(self) -> list:
        """Return a list of voices"""
        return [voice.initialName for voice in self.user.get_available_voices()]

    def tts(self, text: str, voice: str) -> str:
        """Synthesize the text and return the path to the written audio file"""
        voice = self.user.get_voices_by_name(voice)[0]
        data = voice.generate_audio_bytes(text, 0.7, 0.7)
        save_bytes_to_path(self.OUTPUT_FILE, data)
        return self.OUTPUT_FILE
