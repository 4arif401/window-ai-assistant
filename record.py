import sounddevice as sd
from scipy.io.wavfile import write
import os

os.makedirs("wake_samples", exist_ok=True)

for i in range(5):
    print(f"Recording sample {i+1}... say 'Airi'")
    recording = sd.rec(int(1.5 * 16000), samplerate=16000, channels=1)
    sd.wait()
    write(f"wake_samples/airi_{i+1}.wav", 16000, recording)
print("✅ All samples recorded.")