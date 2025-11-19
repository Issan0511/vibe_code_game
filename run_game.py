#!/usr/bin/env python
# ゲームを起動するメインスクリプト

import sys
import os

# プロジェクトルートをカレントディレクトリに設定
project_root = os.path.dirname(__file__)
os.chdir(project_root)

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(project_root, 'src'))

# main.pyを実行
from main import *
