#!/usr/bin/env python
# サーバーを起動するスクリプト

import sys
import os
import subprocess

# プロジェクトルートとサーバーディレクトリのパスを取得
project_root = os.path.dirname(__file__)
server_dir = os.path.join(project_root, 'server')

# server.pyを実行（カレントディレクトリはプロジェクトルート）
if __name__ == "__main__":
    subprocess.run([sys.executable, os.path.join(server_dir, 'server.py')], cwd=project_root)
