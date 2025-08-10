from transformers import pipeline
from config import DEVICE

print("[INFO] Loading Llama LLM model...")
llm = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B-Instruct", device=DEVICE)
print("[INFO] Llama LLM model loaded.")
conversation_history = [
    {"role": "system", "content": "You are a helpful assistant that can answer questions concisely, in 3 sentences or less."},
]

def generate_response(user_text):
    conversation_history.append({"role": "user", "content": user_text})
    # Construct prompt from history
    print("[INFO] LLM generating response...")
    outputs = llm(conversation_history, max_new_tokens=256)
    print("[INFO] LLM response generated.")
    bot_response = outputs[0]["generated_text"][-1]['content']
    print("[INFO] LLM response:", bot_response)
    conversation_history.append({"role": "system", "content": bot_response})
    return bot_response
