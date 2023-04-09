import pyaudio
import wave


# Attribution: https://github.com/dv66/audio-recorder-pyqt/blob/master/record.py
# Repo: https://github.com/dv66/audio-recorder-pyqt


def get_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            devices.append(p.get_device_info_by_host_api_device_index(0, i).get("name"))
    return devices


class Recorder(object):
    """A recorder class for recording audio to a WAV file.
    Records in mono by default.
    """

    def __init__(self, channels=1, rate=44100, frames_per_buffer=1024, update_func=None):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.update_func = update_func

    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.channels, self.rate,
                             self.frames_per_buffer, self.update_func)


class RecordingFile(object):
    def __init__(self, fname, mode, channels,
                 rate, frames_per_buffer, update_func=None):
        self.fname = fname
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._pa = pyaudio.PyAudio()
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self.update_func = update_func
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record(self, duration):
        # Use a stream with no callback function in blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self, device_index: int):
        # Use a stream with a callback in non-blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.frames_per_buffer,
                                     stream_callback=self.get_callback(),
                                     input_device_index=device_index)
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            data = [int.from_bytes(in_data[i:i + 2], byteorder='little', signed=True) for i in
                    range(0, len(in_data), 2)]
            if self.update_func is not None:
                self.update_func(data, frame_count)
            return in_data, pyaudio.paContinue

        return callback

    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile
