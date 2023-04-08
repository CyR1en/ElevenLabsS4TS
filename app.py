import sys

from pvrecorder import PvRecorder

import struct
import threading
import wave
import os

import elevenlabs_tts
import text_proc
import whisper
from configuration import ConfigFile, ConfigNode


def get_device_list() -> list:
    """Return a list of audio devices"""
    return PvRecorder.get_audio_devices()


def make_file(audio_list: list) -> None:
    """Create a file from the audio data"""
    if os.path.exists('recorded.wav'):
        os.remove('recorded.wav')

    f = wave.open('recorded.wav', 'w')
    f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
    f.writeframes(struct.pack("h" * len(audio_list), *audio_list))
    f.close()


def speech_to_text(audio_list: list):
    """Return the text from the audio data"""
    print('Transforming...')
    make_file(audio_list)
    text = whisper.whisper_transcribe('recorded.wav')
    print(f'Raw: {text}')
    if text == '':
        return
    elevenlabs_tts.tts(text, 'Gekko')
    text = text_proc.enhance_text(text)
    print(f'Enhanced: {text}')
    print(f'Playing audio...', end='\n========================================\n')


class Recorder:
    def __init__(self, device_index: int, frame_length: int = 512) -> None:
        self.device_index = device_index
        self.frame_length = frame_length
        self.is_recording = False

    def start(self) -> None:
        self.is_recording = True
        recorder = PvRecorder(device_index=self.device_index, frame_length=self.frame_length)
        audio = []

        recorder.start()
        counter = 0

        while self.is_recording:
            frame = recorder.read()
            audio.extend(frame)
            counter += 1
            if counter % 20 != 0:
                continue

            frame_average = sum([abs(val) for val in frame]) / len(frame)
            audio_average = sum([abs(val) for val in audio]) / len(audio)
            if frame_average == 0.0 and audio_average > 1.0:
                thread = threading.Thread(target=speech_to_text, args=(audio,))
                thread.start()
                audio = []
            if audio_average < 0.005:
                audio = []
        recorder.stop()
        recorder.delete()
        self.is_recording = False



if __name__ == '__main__':
    print('Available devices:')
    for index, device in enumerate(get_device_list()):
        print(f"[{index}]: {device}")

    index = int(input("Enter the index of the device you want to use: "))

    recorder = Recorder(index)
    recorder.start()
