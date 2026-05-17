#!/usr/bin/env python3
"""Validate JSON files in the repo (mod.json and any others)."""
import json
import pathlib
import sys


def check(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
        dupes = []

        def check_pairs(pairs):
            keys = [k for k, _ in pairs]
            seen = set()
            for k in keys:
                if k in seen:
                    dupes.append(k)
                seen.add(k)
            return dict(pairs)

        json.loads(text, object_pairs_hook=check_pairs)
        if dupes:
            return f"duplicate keys: {set(dupes)}"
    except json.JSONDecodeError as e:
        return str(e)
    return None


root = pathlib.Path(__file__).parent.parent.parent
files = [p for p in root.rglob("*.json") if not any(part.startswith(".") for part in p.parts)]
failures = []
for p in files:
    err = check(p)
    if err:
        failures.append(f"{p.relative_to(root)}: {err}")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    sys.exit(1)

print(f"OK — {len(files)} JSON files passed")
