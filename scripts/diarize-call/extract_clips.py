#!/usr/bin/env python3
"""Extract each diarized segment into its own small wav file (no concatenation)."""
import sys, json, subprocess, os

SEG_JSON = sys.argv[1]
OUT_DIR = sys.argv[2]
os.makedirs(OUT_DIR, exist_ok=True)

d = json.load(open(SEG_JSON))
wav = d["wav"]
segs = d["segments"]

manifest = []
for i, s in enumerate(segs):
    clip_path = os.path.join(OUT_DIR, f"seg_{i:03d}_{s['speaker']}.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav, "-ss", str(s["start"]), "-to", str(s["end"]),
         "-ac", "1", "-ar", "16000", clip_path],
        check=True, capture_output=True,
    )
    manifest.append({"index": i, "start": s["start"], "end": s["end"],
                      "speaker": s["speaker"], "clip": clip_path})

with open(os.path.join(OUT_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"{len(manifest)} clips written to {OUT_DIR}")
