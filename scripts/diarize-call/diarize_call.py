#!/usr/bin/env python3
"""diarize_call.py — диаризация + транскрипция звонка ОДНИМ вызовом.

Оборачивает проверенный пайплайн diarize.py -> extract_clips.py ->
transcribe_all_segments.py (см. README.md — грабли и почему именно так) и добавляет
последний шаг: склейку соседних реплик одного спикера и сборку читаемого .md
с именами и таймкодами.

Usage:
  python3 diarize_call.py /path/to/call.m4a
  python3 diarize_call.py /path/to/call.m4a --speakers "SPEAKER_00=Алексей,SPEAKER_01=Клара"
  python3 diarize_call.py /path/to/call.m4a --out /path/to/result.md --keep-work

HF_TOKEN — см. hf_token.py (~/.secrets/huggingface.key или $HF_TOKEN).
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile

from hf_token import load_hf_token, KEY_FILE

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPOKENLY_PORT = 51089
MAX_MERGE_GAP = 6.0  # секунд — дольше этого не считаем "тот же спикер продолжил", даже если следующий отрезок с той же меткой


class StepError(Exception):
    def __init__(self, step_name, returncode):
        super().__init__(f"{step_name}: код {returncode}")
        self.step_name = step_name
        self.returncode = returncode


def run_step(cmd, step_name):
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise StepError(step_name, result.returncode)


def spokenly_reachable(timeout=1.5):
    try:
        with socket.create_connection(("127.0.0.1", SPOKENLY_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def parse_speakers(raw):
    mapping = {}
    if not raw:
        return mapping
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        key, sep, value = pair.partition("=")
        if not sep or not value.strip():
            print(f"[diarize_call] пропускаю «{pair}» — нужен формат SPEAKER_00=Имя", file=sys.stderr)
            continue
        mapping[key.strip()] = value.strip()
    return mapping


def fmt_ts(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def merge_adjacent(transcribed, max_gap=MAX_MERGE_GAP):
    """Склеивает подряд идущие отрезки одного спикера в один блок — pyannote уже
    мержит повороты внутри diarize.py по паузе <1.2с, но соседние отрезки в
    итоговом списке всё равно остаются отдельными записями (см. README).

    Отрезок без текста (Spokenly не распознала слов — короткий вдох/шум/бэкчаннел)
    в финальный .md не попадает — на реальном звонке таких десятки, и рендерить
    каждый отдельной строкой «нет текста» — шум, которого не было в одобренном
    варианте. Но если этот пустой отрезок принадлежит ДРУГОМУ спикеру, чем текущий
    блок, — это реальное (пусть и нераспознанное) чужое вклинивание, и его нельзя
    просто игнорировать: тогда два отрезка первого спикера до и после вклинивания
    склеятся в один, как будто второй спикер вообще не говорил. Поэтому такое
    вклинивание не рендерится, но помнится как разрыв — следующий отрезок первого
    спикера начинает новый блок, а не продолжает старый.

    Склейка одного и того же спикера без вклинивания дополнительно ограничена
    max_gap: пауза больше этого порога — уже не продолжение той же реплики, а
    отдельный заход после долгой паузы, сшивать который исказило бы, когда что
    было сказано."""
    blocks = []
    interrupted = False  # с последнего блока успел (пусть и без текста) вклиниться другой спикер
    for item in transcribed:
        text = item["text"].strip()
        speaker = item["speaker"]

        if blocks and blocks[-1]["speaker"] != speaker:
            interrupted = True

        if not text:
            if blocks and blocks[-1]["speaker"] == speaker and not interrupted:
                blocks[-1]["end"] = item["end"]
            continue

        gap = item["start"] - blocks[-1]["end"] if blocks else None
        can_merge = (
            blocks and blocks[-1]["speaker"] == speaker and not interrupted
            and gap is not None and gap < max_gap
        )
        if can_merge:
            blocks[-1]["end"] = item["end"]
            blocks[-1]["text"] = (blocks[-1]["text"] + " " + text).strip()
        else:
            blocks.append({**item, "text": text})
            interrupted = False
    return blocks


def render_markdown(audio_path, blocks, speaker_names):
    title = os.path.basename(audio_path)
    speakers = sorted(set(b["speaker"] for b in blocks))
    names_line = ", ".join(f"{s} = {speaker_names[s]}" if s in speaker_names else s for s in speakers)
    lines = [
        f"# Транскрипт звонка: {title}",
        "",
        f"> Диаризация pyannote (speaker-diarization-community-1) + распознавание Spokenly "
        f"по отрезкам отдельно. Спикеры: {names_line}. Первые 1-2 реплики звонка — зона "
        f"риска, доверяй диаризации там чуть меньше, чем в середине разговора.",
        "",
    ]
    for b in blocks:
        name = speaker_names.get(b["speaker"], b["speaker"])
        lines.append(f"**{name}** [{fmt_ts(b['start'])}]: {b['text']}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Диаризация + транскрипция звонка одним вызовом")
    parser.add_argument("audio", help="Путь к аудио звонка (m4a/wav/...)")
    parser.add_argument("--speakers", default="", help='Имена: "SPEAKER_00=Алексей,SPEAKER_01=Клара"')
    parser.add_argument("--out", default=None, help="Куда писать итоговый .md (по умолчанию рядом с аудио)")
    parser.add_argument("--work-dir", default=None, help="Папка для клипов (по умолчанию временная)")
    parser.add_argument("--keep-work", action="store_true", help="Не удалять клипы после сборки")
    args = parser.parse_args()

    audio_path = os.path.abspath(args.audio)
    if not os.path.exists(audio_path):
        print(f"[diarize_call] файл не найден: {audio_path}", file=sys.stderr)
        sys.exit(1)

    if not load_hf_token():
        print(f"[diarize_call] нет токена HuggingFace: положи его в {KEY_FILE} (chmod 600) "
              "или задай HF_TOKEN=hf_xxx в окружении. См. README.md.", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("[diarize_call] не найден ffmpeg (нужен diarize.py и extract_clips.py) — "
              "brew install ffmpeg", file=sys.stderr)
        sys.exit(1)

    if not spokenly_reachable():
        print(f"[diarize_call] Spokenly не отвечает на localhost:{SPOKENLY_PORT} — "
              "запусти приложение Spokenly и повтори.", file=sys.stderr)
        sys.exit(1)

    speaker_names = parse_speakers(args.speakers)

    # Свою временную папку удаляем после работы (если не просили оставить).
    # Папку, которую дал пользователь через --work-dir, НИКОГДА не трогаем —
    # там может быть не только наш мусор, и мало ли что там уже лежало.
    own_work_dir = args.work_dir is None
    work_dir = os.path.abspath(args.work_dir) if args.work_dir else tempfile.mkdtemp(prefix="diarize_call_")
    os.makedirs(work_dir, exist_ok=True)

    try:
        print("[diarize_call] шаг 1/3: диаризация (pyannote)...", file=sys.stderr)
        run_step([sys.executable, os.path.join(SCRIPT_DIR, "diarize.py"), audio_path], "diarize")
        segments_json = os.path.splitext(audio_path)[0] + ".segments.json"

        print("[diarize_call] шаг 2/3: нарезка клипов...", file=sys.stderr)
        run_step([sys.executable, os.path.join(SCRIPT_DIR, "extract_clips.py"), segments_json, work_dir],
                  "extract_clips")
        manifest_json = os.path.join(work_dir, "manifest.json")

        print("[diarize_call] шаг 3/3: распознавание клипов через Spokenly...", file=sys.stderr)
        transcribed_json = os.path.join(work_dir, "transcribed.json")
        run_step([sys.executable, os.path.join(SCRIPT_DIR, "transcribe_all_segments.py"),
                  manifest_json, transcribed_json], "transcribe")

        with open(transcribed_json) as f:
            transcribed = json.load(f)
        blocks = merge_adjacent(transcribed)

        actual_speakers = set(b["speaker"] for b in blocks)
        for key in speaker_names:
            if key not in actual_speakers:
                print(f"[diarize_call] предупреждение: «{key}» из --speakers не встретился среди "
                      f"распознанных спикеров {sorted(actual_speakers)} — проверь написание", file=sys.stderr)

        markdown = render_markdown(audio_path, blocks, speaker_names)

        out_path = os.path.abspath(args.out) if args.out else os.path.splitext(audio_path)[0] + ".diarized.md"
        with open(out_path, "w") as f:
            f.write(markdown)

        print(f"[diarize_call] готово: {out_path}", file=sys.stderr)
    except StepError as e:
        print(f"[diarize_call] шаг «{e.step_name}» упал (код {e.returncode})", file=sys.stderr)
        sys.exit(e.returncode)
    finally:
        if own_work_dir and not args.keep_work:
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(f"[diarize_call] клипы и промежуточные файлы оставлены: {work_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
