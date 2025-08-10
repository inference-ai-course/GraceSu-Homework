import wave
from piper import PiperVoice
from config import WAV_PARAMS

print("[INFO] Loading Piper TTS model...")
voice = PiperVoice.load("en_US-amy-medium.onnx")
print("[INFO] Piper TTS model loaded.")

def synthesize_speech(text, filename="response.wav"):
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(WAV_PARAMS["setnchannels"])
        wav_file.setframerate(WAV_PARAMS["setframerate"])
        wav_file.setsampwidth(WAV_PARAMS["setsamplewidth"])
        voice.synthesize_wav(text, wav_file)
    return filename
