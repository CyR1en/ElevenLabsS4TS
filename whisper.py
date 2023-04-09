import torch
import soundfile as sf
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperTokenizerFast

# load model and processor
tokenizer = WhisperTokenizerFast.from_pretrained('openai/whisper-base')
processor = WhisperProcessor.from_pretrained('openai/whisper-base', tokenizer=tokenizer)
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('Using device: ', device)
model.to(device)

model.config.forced_decoder_ids = None


def is_cuda():
    return device == 'cuda'


def transcribe(file_name: str) -> str:
    audio, sample_rate = sf.read(file_name)

    input_features = processor(audio, sampling_rate=sample_rate, return_tensors="pt").input_features
    predicted_ids = model.generate(input_features, max_length=1000)
    transcription: str = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription.strip()


def set_param_size(param_size: str = 'base'):
    global model, processor, tokenizer
    tokenizer = WhisperTokenizerFast.from_pretrained(f'openai/whisper-{param_size}')
    processor = WhisperProcessor.from_pretrained(f'openai/whisper-{param_size}', tokenizer=tokenizer)
    model = WhisperForConditionalGeneration.from_pretrained(f'openai/whisper-{param_size}')
