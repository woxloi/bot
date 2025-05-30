# app.py
from flask import Flask, request, jsonify, send_from_directory
from bs4 import BeautifulSoup
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# 会話履歴保存パス
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data["message"]
    session_id = data.get("session_id", "default")

    response = requests.post("http://localhost:11434/api/chat", json={
        "model": "llama3",
        "messages": [{"role": "user", "content": user_message}]
    }).json()

    reply = response["message"]["content"]

    save_history(session_id, user_message, reply)

    return jsonify({"reply": reply})

def save_history(session_id, user_message, reply):
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "bot": reply
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route("/api/history/<session_id>")
def get_history(session_id):
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
        return jsonify(history)
    else:
        return jsonify([])

@app.route("/api/sessions")
def list_sessions():
    sessions = [f.replace(".json", "") for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
    return jsonify(sessions)

@app.route("/api/explain_url", methods=["POST"])
def explain_url():
    url = request.json["url"]
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    texts = [p.get_text() for p in soup.find_all("p")]
    content = "\n".join(texts)[:3000]

    prompt = f"次のウェブページの内容をわかりやすく解説してください：\n\n{content}"

    llm_response = requests.post("http://localhost:11434/api/chat", json={
        "model": "llama3",
        "messages": [{"role": "user", "content": prompt}]
    }).json()["message"]["content"]

    return jsonify({"summary": llm_response})

@app.route("/api/speak", methods=["POST"])
def speak():
    text = request.json["text"]
    speaker_id = 1  # ずんだもんのID（VOICEVOX）

    qres = requests.post("http://localhost:50021/audio_query", params={"text": text, "speaker": speaker_id})
    query = qres.json()

    wav = requests.post("http://localhost:50021/synthesis", params={"speaker": speaker_id}, json=query)

    path = "static/audio/zundamon.wav"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(wav.content)

    return jsonify({"url": "/" + path})

@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("static/audio", filename)

if __name__ == "__main__":
    app.run(debug=True)
