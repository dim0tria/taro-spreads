#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Удаляет истёкшие публикации (TTL) из дерева репо и из _ledger.json.

Запускается двумя путями:
  - GitHub Actions ежечасно (cleanup.yml) — работает даже при выключенном ПК;
  - локально: taro_publish.py --cleanup.

Только файловые операции: git-коммит делает вызывающий. Stdlib.
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone

LEDGER = "_ledger.json"


def parse_ts(s):
    """ISO '2026-10-28 20:17:19 +0300' -> aware datetime."""
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")


def cleanup(root):
    lp = os.path.join(root, LEDGER)
    data = {}
    if os.path.isfile(lp):
        with open(lp, encoding="utf-8") as f:
            data = json.load(f)
    now = datetime.now(timezone.utc)
    removed = []
    for slug, meta in sorted(list(data.items())):
        try:
            expired = parse_ts(meta["expires_at"]) <= now
        except Exception:
            continue  # битая запись — не трогаем
        if not expired:
            continue
        d = os.path.join(root, slug)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        data.pop(slug, None)
        removed.append(slug)
    tmp = lp + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, lp)
    return removed


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    removed = cleanup(root)
    print("removed: " + (",".join(removed) if removed else "(none)"))
    sys.exit(0)
