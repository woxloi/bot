import os
import json
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

DATA_DIR = "data/history"
os.makedirs(DATA_DIR, exist_ok=True)

def get_session_path(session_id):
    safe_session_id = session_id.replace("/", "_")  # 簡易サニタイズ
    return os.path.join(DATA_DIR, f"{safe_session_id}.json")

# Ollama呼び出し（例）
def ollama_chat(messages):
    # messagesは[{role: "user"/"assistant", content: "..."}]
    # 実際のコマンドに合わせて修正してください
    prompt = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    # ここは例示なので適宜実装してください
    result = subprocess.run(
        ["ollama", "chat", "modelname"], input=prompt.encode(), capture_output=True
    )
    return result.stdout.decode()

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    # 履歴読み込み
    path = get_session_path(session_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            history = json.load(f)
    else:
        history = []

    # 履歴にユーザーメッセージ追加
    history.append({"role": "user", "content": message})

    # Ollamaに投げる形式で整理
    reply_text = ollama_chat(history)

    # 履歴にAI返答追加
    history.append({"role": "assistant", "content": reply_text})

    # 履歴保存
    with open(path, "w") as f:
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
        # 新規セッション用に空ファイル作成
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
        return jsonify({"status": "created"})

    # GET時は履歴返す
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    # クライアント用に簡易整形
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
    url = data.get("url")
    # URL解析・要約処理の例（ここはダミー）
    summary = f"URL {url} の内容を解析・要約しました（ダミー）"
    return jsonify({"summary": summary})

@app.route("/api/speak", methods=["POST"])
def speak():
    data = request.json
    text = data.get("text", "")
    # ずんだもんの音声生成処理（例）
    # 生成したwav/mp3をstatic以下に保存しURLを返す想定
    audio_url = "/static/zundamon_dummy.wav"
    return jsonify({"url": audio_url})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
