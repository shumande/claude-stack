#!/usr/bin/env python3
"""
Speaker diarization pipeline: pyannote.audio (who spoke when) + Spokenly (what was said).
Usage: HF_TOKEN=hf_xxx python3 diarize.py /path/to/audio.m4a
Writes: <audio>.segments.json — merged speaker turns with start/end (seconds).
Next step (separate script) cuts audio per segment and sends each to Spokenly.
"""
import sys
import os
import json
import subprocess

from hf_token import load_hf_token, KEY_FILE

def main():
    audio_path = sys.argv[1]
    hf_token = load_hf_token()
    if not hf_token:
        print(f"Нет токена HuggingFace: положи его в {KEY_FILE} (chmod 600) "
              "или задай HF_TOKEN=hf_xxx в окружении. Токен — huggingface.co/settings/tokens, "
              "после accept на pyannote/speaker-diarization-community-1.", file=sys.stderr)
        sys.exit(1)

    # Convert to 16kHz mono wav — avoids torchcodec/m4a decoding issues, standard for diarization.
    wav_path = os.path.splitext(audio_path)[0] + ".diarize16k.wav"
    if not os.path.exists(wav_path):
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-ac", "1", "-ar", "16000", wav_path],
            check=True, capture_output=True,
        )

    from pyannote.audio import Pipeline
    import torch
    import soundfile as sf

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1", token=hf_token
    )
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    pipeline.to(torch.device(device))

    # Bypass torchcodec (broken native dylib on this machine) by loading the waveform
    # ourselves and handing pyannote an in-memory tensor instead of a file path.
    data, sample_rate = sf.read(wav_path, dtype="float32", always_2d=True)
    waveform = torch.from_numpy(data.T)  # (channel, time)

    output = pipeline({"waveform": waveform, "sample_rate": sample_rate})

    raw = []
    for turn, _, speaker in output.speaker_diarization.itertracks(yield_label=True):
        raw.append({"start": turn.start, "end": turn.end, "speaker": speaker})

    # Merge same-speaker turns separated by < 1.2s gap, to avoid hundreds of tiny clips.
    merged = []
    for seg in raw:
        if merged and merged[-1]["speaker"] == seg["speaker"] and seg["start"] - merged[-1]["end"] < 1.2:
            merged[-1]["end"] = seg["end"]
        else:
            merged.append(dict(seg))

    # Drop sub-0.3s slivers (usually diarization noise, not real turns).
    merged = [s for s in merged if s["end"] - s["start"] >= 0.3]

    out_path = os.path.splitext(audio_path)[0] + ".segments.json"
    with open(out_path, "w") as f:
        json.dump({"wav": wav_path, "segments": merged}, f, ensure_ascii=False, indent=2)

    speakers = sorted(set(s["speaker"] for s in merged))
    print(f"{len(raw)} raw turns -> {len(merged)} merged segments, {len(speakers)} speakers: {speakers}")
    print(f"Written: {out_path}")

if __name__ == "__main__":
    main()
