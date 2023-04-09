import sys
import threading

from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QLabel, QApplication, QLineEdit, QComboBox, \
    QPushButton, QCheckBox, QStatusBar

import record
import whisper
from elevenlabs_tts import ElevenLabsTTS
import qdarktheme

import elevenlabs_tts
from configuration import ConfigFile, ConfigNode
from record import Recorder


# Subclass QMainWindow to customize your application's main window
class ElevensLabS4TS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recFile = None
        self.config = ConfigFile('config')

        self.recorder = Recorder(channels=1, rate=16000, frames_per_buffer=1024)

        self.setWindowTitle("ElevenLabsS4TS")

        self.layout = QGridLayout()

        # Create widgets
        api_key_label = QLabel("API Key")
        self._setup_player()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self._set_up_key():
            self._setup_voice()
        else:
            self.api_key_input.setPlaceholderText("Enter your API key")
            self.api_key_input.returnPressed.connect(self.on_api_key_input)

        device_label = QLabel("Input")
        self.device_combo = QComboBox()
        self.input_devices = record.get_audio_devices()
        self._fix_input_names()
        self.device_combo.addItems(self.input_devices)

        self.output_label = QLabel("Output")
        self.output_combo = QComboBox()
        self.audio_output_devices = QMediaDevices.audioOutputs()
        self.output_combo.addItems([device.description() for device in self.audio_output_devices])
        self.output_combo.currentIndexChanged.connect(self.on_output_combo_index_changed)

        self.transcript_mode_label = QLabel("Transcript Mode")
        self.transcript_mode_checkbox = QCheckBox()
        self.transcript_mode_checkbox.stateChanged.connect(self.on_use_transcript_mode_checkbox)

        self.use_medium_model_label = QLabel("Use Medium Model")
        self.use_medium_model_checkbox = QCheckBox()
        self.use_medium_model_checkbox.stateChanged.connect(self.on_use_medium_model_checkbox)

        self.record_button = QPushButton("Record")
        self.record_button.pressed.connect(self.on_record_button)
        self.record_button.released.connect(self.on_stop_button)

        self.transcript = QLabel("Transcription")
        self.transcription_preview = QLineEdit()
        self.transcription_preview.setReadOnly(True)

        self.status_bar = QStatusBar()

        # Set layout
        self.layout.addWidget(api_key_label, 0, 0)
        self.layout.addWidget(self.api_key_input, 0, 1)

        self.layout.addWidget(device_label, 1, 0)
        self.layout.addWidget(self.device_combo, 1, 1)

        self.layout.addWidget(self.output_label, 2, 0)
        self.layout.addWidget(self.output_combo, 2, 1)

        toggle_layout = QGridLayout()
        toggle_layout.addWidget(self.transcript_mode_label, 0, 0)
        toggle_layout.addWidget(self.transcript_mode_checkbox, 0, 1)
        toggle_layout.addWidget(self.use_medium_model_label, 0, 2)
        toggle_layout.addWidget(self.use_medium_model_checkbox, 0, 3)

        self.layout.addLayout(toggle_layout, 4, 0, 1, 2)

        self.layout.addWidget(self.record_button, 5, 0, 1, 2)

        self.layout.addWidget(self.transcript, 6, 0)
        self.layout.addWidget(self.transcription_preview, 7, 0, 1, 2)

        # Set layout for central widget
        self.widget = QWidget()
        self.layout.setAlignment(Qt.AlignTop)
        self.widget.setLayout(self.layout)

        self.setFixedSize(380, self.sizeHint().height())

        self.setCentralWidget(self.widget)
        self.setStatusBar(self.status_bar)

    def _setup_player(self):
        self.media_player = QMediaPlayer()
        self.output = QAudioOutput()
        self.output.setVolume(1.0)
        self.media_player.setAudioOutput(self.output)

    def _set_up_key(self) -> bool:
        key = self.config.get(ConfigNode.API_KEY)
        if key != ConfigNode.API_KEY.get_value():
            self.api_key_input.setText(key)
            self.api_key_input.setDisabled(True)
            return True
        return False

    def _fix_input_names(self):
        named_devices = [device.description() for device in QMediaDevices.audioInputs()]
        for i in self.input_devices:
            for j in named_devices:
                if j.startswith(i):
                    self.input_devices[self.input_devices.index(i)] = j

    def _setup_voice(self):
        self.tts = ElevenLabsTTS(self.config)
        self.voice_label = QLabel("Voice")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.tts.get_voices())
        self.layout.addWidget(self.voice_label, 3, 0)
        self.layout.addWidget(self.voice_combo, 3, 1)

    def on_output_combo_index_changed(self):
        self.output.setDevice(self.audio_output_devices[self.output_combo.currentIndex()])

    def on_record_button(self):
        self.recFile = self.recorder.open('recorded.wav', 'wb')
        self.recFile.start_recording(self.device_combo.currentIndex())

    def on_stop_button(self):
        if self.recFile is None:
            return
        self.recFile.stop_recording()
        self.status_bar.showMessage('Transcribing...')
        thread = threading.Thread(target=self.thread_target, args=('recorded.wav',))
        thread.start()

    def thread_target(self, file: str):
        text = whisper.transcribe(file)
        self.transcription_preview.setText(text)
        self.status_bar.showMessage('Transcription done')
        self.tts.tts(text, self.voice_combo.currentText())
        if not self.transcript_mode_checkbox.isChecked():
            self.status_bar.showMessage('Playing audio')
            self.media_player.setSource('elevenlabs.wav')
            self.media_player.play()

    def on_use_transcript_mode_checkbox(self):
        checked = self.transcript_mode_checkbox.isChecked()
        if checked:
            self.status_bar.showMessage('Now using transcription mode')
        else:
            self.status_bar.showMessage('Now using S4TS mode')

    def on_use_medium_model_checkbox(self):
        checked = self.use_medium_model_checkbox.isChecked()
        self.status_bar.showMessage('Changing model, this may take a while...')
        thread = threading.Thread(target=self.model_changed_thread, args=(checked,))
        thread.start()

    def model_changed_thread(self, checked: bool):
        def thread_target():
            param = 'medium' if checked else 'base'
            whisper.set_param_size(param)
            self.status_bar.showMessage(f'Model changed to {param}')

        thread = threading.Thread(target=thread_target)
        thread.start()

    def on_api_key_input(self):
        self.api_key_input.setDisabled(True)
        self.config.set(ConfigNode.API_KEY, self.api_key_input.text())
        self._setup_voice()


if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    application = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    window = ElevensLabS4TS()
    window.show()

    application.exec()
