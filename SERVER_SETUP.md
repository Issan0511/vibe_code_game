# サーバーセットアップガイド

## 概要

`server.py` は、ゲーム PC で常駐させるサーバーです。外部からのHTTPリクエストを受け取り、OpenAI APIを使ってゲームスクリプトを生成・更新します。

## 動作の流れ

1. クライアントから `/update_script` エンドポイントにプロンプトを送信
2. `server.py` が `AI_PROMPT.md` の内容と組み合わせて OpenAI API に送信
3. OpenAI API から生成されたコードを `script_user.py` に保存
4. `reload.flag` ファイルを作成してゲーム本体にリロードを通知
5. `main.py` が定期的に `reload.flag` をチェックし、存在すれば `custom_runner.py` を再起動
6. 新しい `script_user.py` が読み込まれてゲームの挙動が変更される

## インストール

### 1. 必要なパッケージのインストール

```powershell
pip install -r requirements_server.txt
```

または個別にインストール:

```powershell
pip install fastapi uvicorn openai pydantic
```

### 2. OpenAI API キーの設定

環境変数 `OPENAI_API_KEY` を設定してください:

```powershell
# PowerShell の場合
$env:OPENAI_API_KEY = "your-api-key-here"

# 永続的に設定する場合
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your-api-key-here', 'User')
```

または、`server.py` の以下の部分を直接編集:

```python
# 環境変数から API キーを取得（必要に応じて設定）
openai.api_key = os.getenv("OPENAI_API_KEY")
```

↓

```python
# 直接設定する場合
openai.api_key = "your-api-key-here"
```

## 起動方法

### サーバーの起動

```powershell
python server.py
```

サーバーが起動すると、`http://0.0.0.0:8000` でリクエストを待ち受けます。

### ゲームの起動

別のターミナルで:

```powershell
python main.py
```

## API の使い方

### スクリプト更新エンドポイント

**POST** `/update_script`

リクエストボディ (JSON):
```json
{
  "prompt": "敵をたくさん出して欲しい"
}
```

レスポンス:
```json
{
  "status": "ok",
  "comment": "0.5秒ごとに100%の確率で敵を出現させるようにしました。",
  "code_length": 234
}
```

### 動作確認エンドポイント

**GET** `/`
```json
{
  "message": "ゲームスクリプト更新サーバー稼働中"
}
```

**GET** `/health`
```json
{
  "status": "healthy"
}
```

## テスト方法

### cURL でテスト

```powershell
curl -X POST http://localhost:8000/update_script `
  -H "Content-Type: application/json" `
  -d '{"prompt": "敵をたくさん出して欲しい"}'
```

### PowerShell でテスト

```powershell
$body = @{
    prompt = "敵をたくさん出して欲しい"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/update_script" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Python でテスト

```python
import requests

response = requests.post(
    "http://localhost:8000/update_script",
    json={"prompt": "敵をたくさん出して欲しい"}
)
print(response.json())
```

## 既存の実装との整合性

### main.py との連携

- `main.py` は 0.5 秒ごとに `reload.flag` の存在をチェック
- フラグが見つかると、`custom_runner.py` を再起動
- 再起動により新しい `script_user.py` が読み込まれる

### custom_runner.py との連携

- `custom_runner.py` は `script_user.py` をインポート
- TCP 通信でゲーム本体とやり取り
- 再起動時に `script_user.py` がリロードされる

### AI_PROMPT.md の利用

- `server.py` は `AI_PROMPT.md` をシステムプロンプトとして使用
- ユーザーのプロンプトを適切な位置に挿入
- OpenAI API に送信して JSON 形式のコードを生成

## トラブルシューティング

### エラー: OPENAI_API_KEY が設定されていません

環境変数を設定するか、コード内で直接 API キーを設定してください。

### エラー: AI_PROMPT.md が読み込めませんでした

`server.py` と同じディレクトリに `AI_PROMPT.md` があることを確認してください。

### エラー: script_user.py への書き込みに失敗

ファイルの書き込み権限を確認してください。

### ゲームにスクリプトが反映されない

1. `reload.flag` が作成されているか確認
2. `main.py` が起動中か確認
3. `custom_runner.py` が正常に再起動されているか確認

## セキュリティ上の注意

- API キーを公開リポジトリにコミットしないこと
- 本番環境では適切な認証・認可を実装すること
- 外部からアクセスする場合はファイアウォール設定を確認すること
