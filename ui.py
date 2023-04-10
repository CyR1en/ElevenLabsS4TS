import sys
import threading

import numpy as np
import qdarktheme
from PySide6 import QtCore
from PySide6.QtCore import QUrl, QObject, QRunnable, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QLabel, QApplication, QLineEdit, QComboBox, \
    QPushButton, QCheckBox, QStatusBar, QMessageBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import record
import util
import whisper
from configuration import ConfigFile, ConfigNode
from elevenlabs_tts import ElevenLabsTTS
from record import Recorder


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_alpha(0)
        self.axes = self.fig.add_subplot(111)
        self.axes.axis('off')
        self.axes.margins(0, 0, tight=True)
        self.fig.set_constrained_layout_pads(w_pad=0.05, h_pad=0.05, wspace=0.05, hspace=0.05)
        self.fig.tight_layout()
        self.fig.set_size_inches(self.fig.get_size_inches()[0], 0.5)
        super(MplCanvas, self).__init__(self.fig)


class S4TSWorkerSignals(QObject):
    transcription_finished = QtCore.Signal(str)
    tts_finished = QtCore.Signal()
    finished = QtCore.Signal()


class S4TSWorker(QRunnable):

    def __init__(self, stt_file: str, tts: ElevenLabsTTS, voice: str, *args, **kwargs):
        super(S4TSWorker, self).__init__()
        self.stt_file = stt_file
        self.tts = tts
        self.voice = voice
        # Add the callback to our kwargs
        self.args = args
        self.kwargs = kwargs
        self.signals = S4TSWorkerSignals()

    @Slot()
    def run(self):
        text = whisper.transcribe(self.stt_file)
        self.signals.transcription_finished.emit(text)
        self.tts.tts(text, self.voice)
        self.signals.tts_finished.emit()


class ElevensLabS4TS(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ElevensLabS4TS, self).__init__(*args, **kwargs)
        self.threadpool = QtCore.QThreadPool()
        self.recFile = None
        self.config = ConfigFile('config')

        self.recorder = Recorder(channels=1, rate=16000, frames_per_buffer=1024, update_func=self.update_plot)

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
        self.change_if_config_set(self.config.get(ConfigNode.INPUT), self.device_combo)
        self.device_combo.currentTextChanged.connect(self.on_device_combo_name_changed)

        self.output_label = QLabel("Output")
        self.output_combo = QComboBox()
        self.audio_output_devices = QMediaDevices.audioOutputs()
        self.output_combo.addItems([device.description() for device in self.audio_output_devices])
        self.change_if_config_set(self.config.get(ConfigNode.OUTPUT), self.output_combo)
        self.output_combo.currentIndexChanged.connect(self.on_output_combo_index_changed)

        self.transcript_mode_label = QLabel("Transcript Mode")
        self.transcript_mode_checkbox = QCheckBox()
        self.change_if_config_set(self.config.get(ConfigNode.T_MODE), self.transcript_mode_checkbox)
        self.transcript_mode_checkbox.stateChanged.connect(self.on_use_transcript_mode_checkbox)

        self.use_medium_model_label = QLabel("Use Medium Model")
        self.use_medium_model_checkbox = QCheckBox()
        self.use_medium_model_checkbox.stateChanged.connect(self.on_use_medium_model_checkbox)

        self.record_button = QPushButton("Record")
        self.record_button.pressed.connect(self.on_record_button)
        self.record_button.released.connect(self.on_stop_button)

        self.plot = MplCanvas(self, width=5, height=1, dpi=100)
        x = [i for i in range(0, 1024)]
        y = [self.wave_func(x) for x in range(0, 1024)]
        y_max = max([max(y), 4000])
        self.plot.axes.set_ylim(-y_max, y_max)
        self.gradient = util.calculate_gradient_str('0xfe8c00', '0xf83600', 1024)
        self.plot.axes.scatter(x, y, c=self.gradient, s=2)

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

        self.layout.addWidget(self.plot, 6, 0, 1, 2)

        self.layout.addWidget(self.transcript, 7, 0)
        self.layout.addWidget(self.transcription_preview, 8, 0, 1, 2)

        # Set layout for central widget
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setStatusBar(self.status_bar)
        self.setFixedSize(420, 333)
        self.show()

    @staticmethod
    def wave_func(x):
        x = x / 200
        return (np.sin(8.8 * np.pi * x) + np.sin(11.0 * np.pi * x) + np.sin(13.2 * np.pi * x)) * 10 ** 3.1

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

    def update_plot(self, input_data, frame_count):
        self.plot.axes.cla()  # Clear the canvas.
        self.plot.axes.margins(0, 0, tight=True)
        self.plot.axes.axis('off')
        window_size = 30
        y_smooth = np.convolve(input_data, np.ones(window_size) / window_size, mode='same')
        y_max = max([max(y_smooth), 4000])
        self.plot.axes.set_ylim(-y_max, y_max)
        self.plot.axes.scatter(range(0, len(input_data)), y_smooth, c=self.gradient, s=2)
        # self.plot.axes.plot(range(0, len(input_data)), y_smooth, color=self.gradient[0])
        # Trigger the canvas to update and redraw.
        self.plot.draw()

    def _setup_voice(self):
        self.tts = ElevenLabsTTS(self.config)
        self.voice_label = QLabel("Voice")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.tts.get_voices())
        self.change_if_config_set(self.config.get(ConfigNode.VOICE), self.voice_combo)
        self.voice_combo.currentIndexChanged.connect(self.on_voice_combo_index_changed)
        self.layout.addWidget(self.voice_label, 3, 0)
        self.layout.addWidget(self.voice_combo, 3, 1)

    def on_device_combo_name_changed(self):
        curr_name = self.device_combo.currentText()
        self.config.set(ConfigNode.INPUT, curr_name)

    def on_output_combo_index_changed(self):
        device = self.audio_output_devices[self.output_combo.currentIndex()]
        self.output.setDevice(device)
        self.config.set(ConfigNode.OUTPUT, device.description())

    def on_voice_combo_index_changed(self):
        self.config.set(ConfigNode.VOICE, self.voice_combo.currentText())

    @staticmethod
    def change_if_config_set(config_val: str, widget: QComboBox | QCheckBox):
        if config_val == 'True' or config_val == 'False' or config_val == '0' or config_val == '1':
            widget.setChecked(config_val == 'True' or config_val == '1')
        elif config_val != '':
            widget_index = widget.findText(config_val)
            if widget != -1:
                widget.setCurrentIndex(widget_index)

    def on_record_button(self):
        self.recFile = self.recorder.open('recorded.wav', 'wb')
        self.recFile.start_recording(self.device_combo.currentIndex())

    def on_stop_button(self):
        if self.recFile is None:
            return
        self.recFile.stop_recording()
        self.status_bar.showMessage('Transcribing...')
        self.s4ts('recorded.wav')

    def s4ts(self, file: str):
        worker = S4TSWorker(file, self.tts, self.voice_combo.currentText())
        worker.signals.transcription_finished.connect(self.notify_transcription_done)
        worker.signals.tts_finished.connect(self.play_audio)
        self.threadpool.start(worker)

    def notify_transcription_done(self, text: str):
        self.transcription_preview.setText(text)
        self.status_bar.showMessage('Transcription done')

    def play_audio(self):
        if self.transcript_mode_checkbox.isChecked():
            return

        self.status_bar.showMessage('Playing audio')
        print(f'Media player status: {self.media_player.mediaStatus()}')
        self.media_player.setSource(QUrl.fromLocalFile('elevenlabs.wav'))
        self.media_player.setSource('elevenlabs.wav')
        self.media_player.setPosition(0)
        print(f'Media player status: {self.media_player.mediaStatus()}')
        self.media_player.play()

    def on_use_transcript_mode_checkbox(self):
        checked = self.transcript_mode_checkbox.isChecked()
        self.config.set(ConfigNode.T_MODE, checked)
        if checked:
            self.status_bar.showMessage('Now using transcription mode')
        else:
            self.status_bar.showMessage('Now using S4TS mode')

    def on_use_medium_model_checkbox(self):
        checked = self.use_medium_model_checkbox.isChecked()
        if not whisper.is_cuda() and checked:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle('Warning')
            message_box.setFixedHeight(10)
            message_box.setText('Device set to CPU, are you sure you want to use the medium model?')
            message_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if message_box.exec() == QMessageBox.StandardButton.No:
                self.use_medium_model_checkbox.setChecked(False)
                return
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

    application.exec()
