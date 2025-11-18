#!/usr/bin/env python
# サーバーを起動するスクリプト

import sys
import os

# カレントディレクトリをserverに変更
os.chdir(os.path.join(os.path.dirname(__file__), 'server'))

# server.pyを実行
from server import *
