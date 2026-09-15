"""Загрузка токена HuggingFace для pyannote.

Порядок поиска (тот же принцип, что у ~/.claude/scripts/openrouter-key.sh):
1. ~/.secrets/huggingface.key — свой файл ключа, chmod 600, только сам токен внутри.
2. $HF_TOKEN — если задан в окружении на момент запуска.
Токен нигде не коммитится и не пишется в код/конфиги.
"""
import os

KEY_FILE = os.path.expanduser("~/.secrets/huggingface.key")


def load_hf_token():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            token = f.read().strip()
        if token:
            return token
    return os.environ.get("HF_TOKEN", "").strip() or None
