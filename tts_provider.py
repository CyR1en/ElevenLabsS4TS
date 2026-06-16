from abc import ABC, abstractmethod

from configuration import ConfigFile, ConfigNode


class TTSProvider(ABC):
    """
    Common interface for all text-to-speech backends.

    Concrete providers (ElevenLabs, 60db, ...) implement these two methods so
    the rest of the application can synthesize speech without caring which
    service is actually used.
    """

    @abstractmethod
    def get_voices(self) -> list:
        """Return the list of selectable voice identifiers for this provider."""

    @abstractmethod
    def tts(self, text: str, voice: str) -> str:
        """
        Synthesize ``text`` with ``voice`` and write the audio to disk.

        :return: Path to the written audio file (so the caller can play it).
        """


def make_tts(config: ConfigFile) -> TTSProvider:
    """
    Build the TTS provider selected in the configuration.

    Defaults to ElevenLabs so existing setups keep working unchanged.
    Imports are local to avoid importing every provider's (heavy) dependencies
    when only one of them is used.
    """
    provider = config.get(ConfigNode.PROVIDER).strip().lower()
    if provider == "sixtydb":
        from sixtydb_tts import SixtyDBTTS
        return SixtyDBTTS(config)

    from elevenlabs_tts import ElevenLabsTTS
    return ElevenLabsTTS(config)
