#!/usr/bin/env python
# ゲームを起動するメインスクリプト

import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# カレントディレクトリをsrcに変更（相対パスが正しく動作するように）
os.chdir(os.path.join(os.path.dirname(__file__), 'src'))

# main.pyを実行
from main import *
