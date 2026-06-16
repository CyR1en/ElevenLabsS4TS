import base64
import json
import wave
from urllib.parse import quote

from websocket import create_connection

from configuration import ConfigFile, ConfigNode
from tts_provider import TTSProvider


class SixtyDBTTS(TTSProvider):
    """
    60db (https://60db.ai) text-to-speech using the streaming WebSocket API.

    The app plays back a complete file, so we open a context, send the text,
    flush, accumulate every ``audio_chunk`` frame, then write a single WAV.
    We request ``LINEAR16`` (raw 16-bit signed little-endian mono PCM); those
    chunks concatenate directly and only need a WAV header wrapped around them.
    """

    WS_URL = "wss://api.60db.ai/ws/tts"
    OUTPUT_FILE = "sixtydb.wav"
    CONTEXT_ID = "s4ts"
    SAMPLE_RATE = 24000
    # Documented default voice; 60db exposes no list-voices endpoint.
    DEFAULT_VOICE_ID = "fbb75ed2-975a-40c7-9e06-38e30524a9a1"
    # Guards against a stalled socket never returning flush_completed.
    RECV_TIMEOUT_SECONDS = 60

    def __init__(self, config: ConfigFile):
        self.api_key = config.get(ConfigNode.SIXTYDB_API_KEY)
        self.voice_id = config.get(ConfigNode.SIXTYDB_VOICE_ID) or self.DEFAULT_VOICE_ID

    def get_voices(self) -> list:
        """60db has no list-voices endpoint, so expose the configured voice id."""
        return [self.voice_id]

    def tts(self, text: str, voice: str) -> str:
        """Synthesize the text and return the path to the written WAV file."""
        voice_id = voice or self.voice_id
        pcm = self._synthesize(text, voice_id)
        self._write_wav(pcm)
        return self.OUTPUT_FILE

    def _synthesize(self, text: str, voice_id: str) -> bytes:
        ws = create_connection(f"{self.WS_URL}?apiKey={quote(self.api_key)}",
                               timeout=self.RECV_TIMEOUT_SECONDS)
        try:
            self._await_connection(ws)
            ws.send(json.dumps({
                "create_context": {
                    "context_id": self.CONTEXT_ID,
                    "voice_id": voice_id,
                    "audio_config": {
                        "audio_encoding": "LINEAR16",
                        "sample_rate_hertz": self.SAMPLE_RATE,
                    },
                }
            }))
            ws.send(json.dumps({
                "send_text": {"context_id": self.CONTEXT_ID, "text": text}
            }))
            ws.send(json.dumps({"flush_context": {"context_id": self.CONTEXT_ID}}))

            pcm = bytearray()
            while True:
                msg = json.loads(ws.recv())
                if "audio_chunk" in msg:
                    pcm.extend(base64.b64decode(msg["audio_chunk"]["audioContent"]))
                elif "flush_completed" in msg:
                    break
                elif "error" in msg:
                    raise RuntimeError(f"60db TTS error: {msg['error'].get('message')}")

            ws.send(json.dumps({"close_context": {"context_id": self.CONTEXT_ID}}))
            return bytes(pcm)
        finally:
            ws.close()

    @staticmethod
    def _await_connection(ws) -> None:
        """Drain handshake frames until the connection is authenticated."""
        while True:
            msg = json.loads(ws.recv())
            if "connection_established" in msg:
                return
            if "error" in msg:
                raise RuntimeError(f"60db TTS error: {msg['error'].get('message')}")

    def _write_wav(self, pcm: bytes) -> None:
        with wave.open(self.OUTPUT_FILE, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.SAMPLE_RATE)
            wav.writeframes(pcm)
