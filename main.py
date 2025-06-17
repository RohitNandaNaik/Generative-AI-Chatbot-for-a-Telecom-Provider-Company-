# You are a friendly and helpful telecom infrastructure customer support chatbot. Keep your replies short, clear, and easy to understand. Avoid technical jargon unless necessary:



from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from io import StringIO
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

#test 
# =================== Read DATA ===================
hardware_data = pd.read_excel("data/Hardware_Product_Data.xlsx")
infra_faq_data = pd.read_excel("data/Infra_FAQ_Data.xlsx")

# =================== LOAD DATA ===================
def load_data():
    hardware_df = pd.read_csv(StringIO(hardware_data))
    faq_df = pd.read_csv(StringIO(infra_faq_data))
    return hardware_df, faq_df

hardware_df, faq_df = load_data()
faq_dict = dict(zip(faq_df['question'], faq_df['answer']))
hardware_context = "\n".join([
    f"Product: {row['Name']} | Type: {row['Type']} | Model: {row['Model']} | Support: {row['SupportContact']} | Warranty: {row['Warranty']}"
    for _, row in hardware_df.iterrows()
])

# =================== GLOBAL MEMORY & FEEDBACK ===================
session_memory = {}  # Holds history for dialogue management
feedback_log = []    # Stores feedback entries

# =================== GPT FUNCTION ===================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def generate_response(user_query, session_id="default"):
    memory = session_memory.get(session_id, [])

    # Build context prompt
    context = f"""
You are a friendly and helpful telecom infrastructure customer support chatbot. Keep your replies short, clear, and easy to understand. Avoid technical jargon unless necessary:


=== Hardware Products ===
{hardware_context}

=== FAQs ===
{str(faq_dict)}

Recent Conversation:
{format_chat_memory(memory)}

User: {user_query}
Assistant:"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You assist telecom customers with simple, helpful answers using the product and FAQ context provided."},
            {"role": "user", "content": context}
        ]
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content']
        
        # Update memory
        memory.append({"user": user_query, "bot": answer})
        session_memory[session_id] = memory[-5:]  # Keep only last 5 exchanges
        return answer
    except Exception as e:
        return f"Sorry, an error occurred: {e}"

def format_chat_memory(memory):
    return "\n".join([f"User: {m['user']}\nAssistant: {m['bot']}" for m in memory])

# =================== ROUTES ===================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    session_id = request.json.get("session_id", "default")
    bot_reply = generate_response(user_message, session_id)
    return jsonify({"response": bot_reply})

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    feedback_log.append({
        "message": data.get("message"),
        "response": data.get("response"),
        "thumbs": data.get("thumbs"),
        "comment": data.get("comment")
    })
    return jsonify({"status": "feedback received"})

# =================== RUN ===================
if __name__ == "__main__":
    app.run(debug=True)
