# server.py (ゲームPCで常駐させる)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import openai

import os
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()

class PromptBody(BaseModel):
    prompt: str

# AI_PROMPT.mdの内容を読み込み
def load_system_prompt():
    try:
        with open("AI_PROMPT.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # script_user.pyの内容をリアルタイムで読み込み
        try:
            with open("script_user.py", "r", encoding="utf-8") as f:
                current_script = f.read()
            
            # AI_PROMPT.md内の既存script_user.py部分を現在の内容で置き換え
            import re
            pattern = r'## 既存の script_user\.py\n\n現在の `script_user\.py` の内容は以下の通りです：\n\n```python\n.*?\n```'
            replacement = f'## 既存の script_user.py\n\n現在の `script_user.py` の内容は以下の通りです：\n\n```python\n{current_script}\n```'
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
        except Exception as e:
            print(f"警告: script_user.py の読み込みに失敗しました: {e}")
        
        # AI_PROMPT.md の末尾に「ユーザーからの要望」セクションがあるので、そこまでを返す
        return content
    except Exception as e:
        return f"エラー: AI_PROMPT.md が読み込めませんでした - {e}"

@app.get("/", response_class=HTMLResponse)
async def index():
    # スマホ用の超シンプルUI
    return """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <title>ゲーム改変プロンプト</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, sans-serif; padding: 12px; }
    textarea { width: 100%; min-height: 140px; }
    button { padding: 8px 16px; margin-top: 8px; }
    .status { margin-top: 8px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>ゲーム改変プロンプト</h1>
  <p>例: 「敵が定期的に降って来るようにして」</p>
  <textarea id="prompt" placeholder="ここにやりたい改変内容を書いてください"></textarea><br>
  <button id="send">送信</button>
  <div class="status" id="status"></div>
  <script>
    const sendBtn = document.getElementById("send");
    const promptEl = document.getElementById("prompt");
    const statusEl = document.getElementById("status");

    sendBtn.onclick = async () => {
      const prompt = promptEl.value.trim();
      if (!prompt) {
        statusEl.textContent = "プロンプトを入力してください。";
        return;
      }
      statusEl.textContent = "送信中...";
      try {
        const res = await fetch("/update_script", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
        });
        if (!res.ok) {
          statusEl.textContent = "エラー: " + res.status + " " + res.statusText;
          return;
        }
        const json = await res.json();
        statusEl.textContent = json.comment || "スクリプトを更新しました。";
      } catch (e) {
        statusEl.textContent = "通信エラー: " + e;
      }
    };
  </script>
</body>
</html>
    """


@app.post("/update_script")
async def update_script(body: PromptBody):
    try:
        # 1. プロンプトを組み立て
        system_prompt = load_system_prompt()
        
        # AI_PROMPT.md の最後に「## ユーザーからの要望」セクションがあるので、
        # そこにユーザーのプロンプトを挿入する
        if "{ユーザーの自然言語プロンプトをここに挿入}" in system_prompt:
            system_prompt = system_prompt.replace(
                "{ユーザーの自然言語プロンプトをここに挿入}",
                body.prompt
            )
        else:
            # フォールバック: 末尾に追加
            system_prompt += f"\n\n## ユーザーからの要望\n\n{body.prompt}"

        # 2. OpenAI API呼び出し（ChatGPT からコード生成）
        # 環境変数から API キーを取得（必要に応じて設定）
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        resp = openai.chat.completions.create(
            model="gpt-5-mini",  # モデル名は正常
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body.prompt},
            ],
            #temperature使えないはず
        )
        print(resp)
        # レスポンスからJSONをパース
        import json

        response_content = resp.choices[0].message.content
        
        # JSON部分を抽出（```json ... ``` でラップされている場合に対応）
        if "```json" in response_content:
            json_start = response_content.find("```json") + 7
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        elif "```" in response_content:
            json_start = response_content.find("```") + 3
            json_end = response_content.find("```", json_start)
            json_str = response_content[json_start:json_end].strip()
        else:
            json_str = response_content.strip()
        
        result = json.loads(json_str)
        code = result.get("script_user", "")
        comment = result.get("comment", "")

        # 3. script_user.py を上書き保存
        with open("script_user.py", "w", encoding="utf-8") as f:
            f.write(code)

        # 4. 「リロードフラグ」を立てる
        with open("reload.flag", "w", encoding="utf-8") as f:
            f.write("")

        return {
            "status": "ok",
            "comment": comment,
            "code_length": len(code)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/")
async def root():
    return {"message": "ゲームスクリプト更新サーバー稼働中"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    # 環境変数チェック
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: OPENAI_API_KEY 環境変数が設定されていません")
        print("環境変数を設定するか、コード内で直接 openai.api_key を設定してください")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
