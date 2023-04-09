# ElevenLabs S4TS

_Speech to text, text to Speech - STTTTS - S4TS_

ElevenLabs S4TS is a PySide6 (Qt) application that does speech to text and then text to speech using eleven labs. The automatic speech recognition (ASR) model used for this application is OpenAI’s [Whisper](https://openai.com/research/whisper). 

At startup, the application will use the `whisper-base` model for faster audio transcription. However, if your hardware supports `cuda`, you can change it to `whisper-medium` by checking `Use Medium Model`. ElevenLabs S4TS will automatically use `cuda` if your hardware supports `cuda` and your PyTorch is installed to support it.

<img src="https://raw.githubusercontent.com/CyR1en/ElevenLabsS4TS/master/docs/image-mac-latest.png" width="50%">

### How to Run ElevenLabs S4TS
#### Install Dependencies

- Make sure Python 3.9  > is installed

- Make your `conda` or `pip` env

- Activate the virtual environment

- Install `PyTorch` by following the instructions [here](https://pytorch.org/get-started/locally/)

- Install ElevenLabs S4TS dependencies

  ```
  # Pip
  pip install -U -r requirements.txt
  
  # Conda
  conda install pip
  pip install -U -r requirements.txt
  ```

#### Run the application

Once you have all of the dependencies installed. We simply need to run `ui.py` by doing the following (assuming the virtual environment is activated):

```
python3 ui.py
```

#### How to use ElevenLabs S4TS

- First of all, you need to have a plan for ElevenLabs. It does not matter what plan tier you have as long as you have one.  Go [here](https://beta.elevenlabs.io/pricing) to check out plans that they offer.
- When you’re signed up, go to your profile icon on the top left and click profile and copy your API Key. 
- Paste your API key on the input field labeled `API Key` on the window
- Select your desired input and output device
- Select desired ElevenLabs voice
- Hold the Record button and speak
- Once released, the audio will be processed using `whisper` for transcription
- After transcription, the text will be sent to ElevenLabs using their API
- The request returns an audio data that ElevenLabsS4TS plays through the set output device

#### Future plans
- Package application
- Add ability to voice clone using mic

