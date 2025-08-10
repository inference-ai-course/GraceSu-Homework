from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from asr import transcribe_audio
from llm import generate_response, conversation_history
from tts import synthesize_speech

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/chat/")
async def chat_endpoint(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    # ASR → LLM → TTS
    user_text = transcribe_audio(audio_bytes)
    bot_text = generate_response(user_text)
    audio_path = synthesize_speech(bot_text)
    return FileResponse(audio_path, media_type="audio/wav")

@app.get("/")
async def index():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/history/")
async def history():
    print("[INFO] Conversation History:", conversation_history)
    return conversation_history
