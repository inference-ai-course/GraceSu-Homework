import whisper

print("[INFO] Loading Whisper ASR model...")
asr_model = whisper.load_model("small")
print("[INFO] Whisper ASR model loaded.")

def transcribe_audio(audio_bytes, filename="temp.wav"):
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    result = asr_model.transcribe(filename)
    print("[INFO] Transcription result:", result["text"])
    return result["text"]
