import torch
from transformers import pipeline

dev_id = 0 if torch.cuda.is_available() else -1
print(f'Using device: {dev_id}')
whisper = pipeline('automatic-speech-recognition', model='openai/whisper-medium', device=dev_id)


def whisper_transcribe(file_name: str) -> str:
    text = whisper(file_name)
    return text['text']
