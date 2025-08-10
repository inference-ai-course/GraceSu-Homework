import whisper

print("[INFO] Loading Whisper ASR model...")
asr_model = whisper.load_model("small")
print("[INFO] Whisper ASR model loaded.")

def transcribe_audio(audio_bytes):
    result = asr_model.transcribe("recording.webm")
    print("[INFO] Transcription result:", result["text"])
    return result["text"]
