#!/usr/bin/env python3
"""Transcribe every diarized clip by hitting Spokenly's local JSON-RPC endpoint directly
(same endpoint its own MCP bridge posts to), looping locally instead of one tool-call per clip."""
import json
import subprocess
import sys

MANIFEST = sys.argv[1]
OUT = sys.argv[2]
PORT = 51089

manifest = json.load(open(MANIFEST))
results = []
for i, item in enumerate(manifest):
    req = {
        "jsonrpc": "2.0", "id": i, "method": "tools/call",
        "params": {"name": "transcribe_file",
                    "arguments": {"file_path": item["clip"], "format": "text"}},
    }
    r = subprocess.run(
        ["curl", "-s", "--max-time", "60", "-X", "POST", f"http://localhost:{PORT}",
         "-H", "Content-Type: application/json", "-d", json.dumps(req)],
        capture_output=True, text=True,
    )
    text = ""
    try:
        resp = json.loads(r.stdout)
        content = resp.get("result", {}).get("content", [])
        text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
    except Exception as e:
        text = f"[ERROR: {e}; raw: {r.stdout[:200]}]"
    results.append({
        "index": item["index"], "start": item["start"], "end": item["end"],
        "speaker": item["speaker"], "text": text.strip(),
    })
    if i % 20 == 0:
        print(f"{i}/{len(manifest)}...", file=sys.stderr)

with open(OUT, "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Done: {len(results)} clips -> {OUT}")
