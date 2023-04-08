import os
import platform
import sys

from elevenlabslib import *
from elevenlabslib.helpers import save_bytes_to_path

from configuration import ConfigFile, ConfigNode

configuration = ConfigFile('config')

api_key = configuration.get(ConfigNode.API_KEY)
if api_key == ConfigNode.API_KEY.get_value():
    print('You need to replace the API key in the configuration file with your own API key')
    print('Please enter your API key:')
    try:
        api_key = input()
        configuration.set(ConfigNode.API_KEY, api_key)
    except KeyboardInterrupt:
        print("Interrupted token input")
        sys.exit()

voices = {'Jinxy': '9qhXbLC9ho8bE9Qhwqvi', 'Max': 'ayCXsBoe6zBT9GixXYh8', 'Gekko': 'chGe1zWSFl1gYsFRVW7U'}

user = ElevenLabsUser(api_key)


def tts(text: str, voice: str) -> None:
    """Return the audio from the text"""
    voice = user.get_voices_by_name(voice)[0]
    data = voice.generate_audio_bytes(text, 0.7, 0.7)
    save_bytes_to_path("elevenlabs.wav", data)
    os.system('elevenlabs.wav')


def play_sound_os(sound: str) -> None:
    """Play a sound"""
    sys = platform.system()
    if sys == 'Windows':
        os.system(sound)
    if sys == 'Mac':
        os.system(f'afplay {sound}')
    if sys == 'Linux':
        os.system(f'mpg123{sound}')
