from transformers import pipeline

whisper = pipeline('automatic-speech-recognition', model='openai/whisper-medium', device=0)


def whisper_transcribe(file_name: str) -> str:
    text = whisper(file_name)
    return text['text']
