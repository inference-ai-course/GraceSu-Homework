# Homework 3 Responses

Name: Grace Su

## Voice Agent

Video demo:
https://github.com/inference-ai-course/GraceSu-Homework/blob/main/hw3/inference_ai_hw3_result.mp4

## Project Structure

This is a FastAPI-based voice agent that implements a complete ASR → LLM → TTS pipeline:

### Core Components
- **`main.py`** - FastAPI application with endpoints for chat, history, and static file serving
- **`asr.py`** - Audio transcription using Whisper ASR model
- **`llm.py`** - Text generation using Llama 3 8B Instruct model with conversation history
- **`tts.py`** - Speech synthesis using Piper TTS with Amy voice model
- **`config.py`** - Configuration for device selection and audio parameters

### API Endpoints
- `POST /chat/` - Main chat endpoint that processes audio input and returns audio response
- `GET /` - Serves the web interface
- `GET /history/` - Returns conversation history
- `GET /static/*` - Serves static files (HTML, JavaScript)

### Frontend
- **`static/index.html`** - Web interface for audio input/output
- **`static/app.js`** - Client-side JavaScript for handling audio recording and playback

### Models
- Whisper small model for speech recognition
- Meta Llama 3 8B Instruct for text generation
- Piper TTS with en_US-amy-medium voice for speech synthesis

