import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import os
from vosk import Model, KaldiRecognizer
import queue
import json

# Load model
model = Model("models/vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Load wake samples
def load_reference_embeddings():
    from scipy.fftpack import dct
    refs = []
    for filename in os.listdir("wake_samples"):
        sr, data = wavfile.read(f"wake_samples/{filename}")
        data = data.flatten().astype(np.float32)
        mfcc = dct(data, norm='ortho')[:100]  # simple MFCC-like representation
        refs.append(mfcc)
    return refs

reference_vectors = load_reference_embeddings()

# Compare new audio to reference
def match_input(audio, threshold=0.8):
    from scipy.spatial.distance import cosine
    from scipy.fftpack import dct
    mfcc = dct(audio.flatten().astype(np.float32), norm='ortho')[:100]
    scores = [1 - cosine(mfcc, ref) for ref in reference_vectors]
    return max(scores) >= threshold

# Stream and check
def listen_for_wake_word():
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(indata.copy())

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎧 Say 'Airi' to wake me up...")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text:
                    print(f"[heard]: {text}")
            audio_np = np.frombuffer(data, dtype=np.int16)
            if match_input(audio_np):
                print("✅ Wake word detected!")
                return True
