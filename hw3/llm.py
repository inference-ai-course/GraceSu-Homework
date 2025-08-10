from transformers import pipeline
from config import DEVICE

print("[INFO] Loading Llama LLM model...")
llm = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B-Instruct", device=DEVICE)
print("[INFO] Llama LLM model loaded.")
conversation_history = []

def generate_response(user_text):
    conversation_history.append({"role": "user", "content": user_text})
    # Construct prompt from history
    # prompt = ""
    # for turn in conversation_history[-5:]:
    #     prompt += f"{turn['role']}: {turn['text']}\n"
    outputs = llm(conversation_history, max_new_tokens=256)
    bot_response = outputs[0]["generated_text"][-1]['content']
    conversation_history.append({"role": "system", "content": bot_response})
    return bot_response
