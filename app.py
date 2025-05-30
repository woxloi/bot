import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_DIR = "data/history"
os.makedirs(DATA_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2"  # 事前に `ollama pull llama2` を実行しておく

def get_session_path(session_id):
    safe_session_id = session_id.replace("/", "_")
    return os.path.join(DATA_DIR, f"{safe_session_id}.json")

def ollama_chat(messages):
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    path = get_session_path(session_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    history.append({"role": "user", "content": message})

    reply_text = ollama_chat(history)
    history.append({"role": "assistant", "content": reply_text})

    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return jsonify({"reply": reply_text})

@app.route("/api/sessions")
def sessions():
    files = os.listdir(DATA_DIR)
    sessions = [f[:-5] for f in files if f.endswith(".json")]
    return jsonify(sessions)

@app.route("/api/history/<session_id>", methods=["GET", "POST"])
def history(session_id):
    path = get_session_path(session_id)
    if request.method == "POST":
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
        return jsonify({"status": "created"})

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    simple = []
    for msg in history:
        if msg["role"] == "user":
            simple.append({"user": msg["content"], "bot": ""})
        elif msg["role"] == "assistant":
            if simple:
                simple[-1]["bot"] = msg["content"]

    return jsonify(simple)

@app.route("/api/explain_url", methods=["POST"])
def explain_url():
    data = request.json
    url = data.get("url", "")
    summary = f"URL {url} の内容を解析・要約しました（ダミー）"
    return jsonify({"summary": summary})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.json
    text = data.get("text", "")
    audio_url = "/static/zundamon_dummy.wav"  # 音声合成未実装
    return jsonify({"url": audio_url})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
