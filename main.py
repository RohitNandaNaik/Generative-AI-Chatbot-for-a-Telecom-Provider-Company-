from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from io import StringIO
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
app = Flask(__name__)

# =================== HARDWARE PRODUCT DATA ===================
hardware_data = """ProductID,Name,Type,Model,SupportContact,Warranty
H101,Home Wi-Fi Router,Router,RTR-AX3000,1800-555-1234,2 Years
H102,Gigabit Switch,Switch,GSW-800,1800-555-1235,3 Years
H103,Fiber Optic Modem,Modem,FOM-100,1800-555-1236,1 Year
H104,Wi-Fi Range Extender,Extender,EXT-500,1800-555-1237,2 Years
H105,Structured Cabling Kit,Cabling,SCK-100,1800-555-1238,Lifetime
"""

infra_faq_data = '''question,answer
"My internet connection is slow.","Try rebooting your router. If the issue persists, check for interference or call support."
"How do I install a Wi-Fi extender?","Plug it in near your router, connect using WPS or app, and move it to desired location."
"What's the warranty period?","Our hardware comes with 1 to 3 years warranty depending on the product."
"How to contact support?","You can call 1800-555-1234 or email support@commscope.com."
"How to check if my fiber modem is working?","Check the power LED and fiber signal light. Refer to the manual or call support."
"My router is overheating.","Ensure it's in a ventilated space. Unplug for 10 mins and restart."
'''

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

# =================== GPT FUNCTION ===================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OPENROUTER_API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
def generate_response(user_query):
    context = f"""
You are a friendly and helpful telecom infrastructure customer support chatbot. Keep your replies short, clear, and easy to understand. Avoid technical jargon unless necessary:


=== Hardware Products ==

{hardware_context}

=== FAQs ===
{str(faq_dict)}

User: {user_query}
Assistant:
"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful customer support assistant for telecom hardware and networking issues."},
            {"role": "user", "content": context}
        ]
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Sorry, an error occurred: {e}"

# =================== ROUTES ===================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    bot_reply = generate_response(user_message)
    return jsonify({"response": bot_reply})

# =================== RUN ===================
if __name__ == "__main__":  # ✅ FIXED: should be __main__ not _main_
    app.run(debug=True)
