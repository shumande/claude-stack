#!/usr/bin/env python3
"""agent-council — гетерогенный совет ИИ как конвейер + мини-совет.

Веерит один артефакт по 5 мозгам (Claude/GPT/Gemini/Kimi/GLM), каждый отдаёт
КОМПАКТНЫЙ verdict-JSON (не прозу), затем Claude сводит финал. Наружу — только финал.
Адаптеры едут на подписках где можно (Claude/GPT/Gemini = $0), Kimi/GLM = центы.

Запуск:
    OPENROUTER_API_KEY=sk-or-... python3 council.py --task @rubric.txt --file scenario.txt
    cat scenario.txt | OPENROUTER_API_KEY=sk-or-... python3 council.py --task "оцени хук рилса"
Опции: --voices claude,gemini,gpt  (подмножество), --out <dir>

Дизайн: docs/superpowers/specs/2026-07-11-multi-ai-agent-conveyor-design.md
Механику шимов см. reference_kors_triada_models (Kimi temp=1/detached, agy Pro High, codex read-only).
"""
from __future__ import annotations
import os, sys, re, json, argparse, subprocess, concurrent.futures, time, pathlib

PROTOCOL = ('{"from":"<id>","verdict":"pass|weak|fail","severity":0,'
            '"cuts":[{"at":"хук|середина|финал","why":"кратко"}],'
            '"root":"корневая причина одной фразой","graft":["конкретная замена"]}')


def grader_prompt(task: str, artifact: str, who: str) -> str:
    schema = PROTOCOL.replace("<id>", who)
    return (
        f"Ты грейдер '{who}' в совете из нескольких моделей. Оцени артефакт остро и "
        f"конкретно, без лести, с указанием конкретных резов.\n\n"
        f"ЗАДАЧА/РУБРИКА:\n{task}\n\n"
        f"АРТЕФАКТ:\n{artifact}\n\n"
        f"Верни РОВНО один компактный JSON-объект, ASCII-ключи, без прозы вокруг, "
        f"без markdown-забора. Схема: {schema}"
    )


def extract_json(text: str):
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text)
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _run(cmd, inp=None, timeout=180, env=None):
    try:
        p = subprocess.run(cmd, input=inp, capture_output=True, text=True,
                           timeout=timeout, env=env)
        return p.stdout or "", p.stderr or "", p.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 124
    except Exception as e:  # noqa
        return "", f"EXC:{e}", 1


# --- адаптеры: (task, artifact, who) -> raw text ---
def ad_claude(task, artifact, who):
    out, _, _ = _run(["claude", "-p", grader_prompt(task, artifact, who)], timeout=240)
    return out


def ad_gpt(task, artifact, who):
    # codex-grade: инструкция в arg1, артефакт на stdin, модель gpt-5.5
    instr = grader_prompt(task, "<артефакт на stdin>", who)
    env = dict(os.environ, CODEX_GRADE_MODEL=os.environ.get("CODEX_GRADE_MODEL", "gpt-5.5"))
    shim = os.path.expanduser("~/.local/bin/codex-grade")
    out, _, _ = _run([shim, instr], inp=artifact, timeout=300, env=env)
    return out


def _openrouter(prompt, model, timeout=300):
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return "ERROR: OPENROUTER_API_KEY не задан"
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]})
    out, _, _ = _run(["curl", "-sS", "--max-time", str(timeout),
                      "https://openrouter.ai/api/v1/chat/completions",
                      "-H", "Content-Type: application/json",
                      "-H", f"Authorization: Bearer {key}",
                      "-d", body], timeout=timeout + 20)
    try:
        return json.loads(out)["choices"][0]["message"]["content"]
    except Exception:
        return out


def ad_gemini(task, artifact, who):
    prompt = grader_prompt(task, artifact, who)
    # agy виснет на промпте >13k → сразу фолбэк OpenRouter
    if len(prompt) <= 12000:
        out, err, rc = _run(["agy", "--model", "Gemini 3.1 Pro (High)", "-p", prompt], timeout=150)
        if rc == 0 and out.strip():
            return out
    return _openrouter(prompt, os.environ.get("GEMINI_OR_MODEL", "google/gemini-2.5-pro"))


def ad_kimi(task, artifact, who):
    prompt = grader_prompt(task, artifact, who)
    key = os.environ.get("MOONSHOT_API_KEY", "")
    if not key:
        return "ERROR: MOONSHOT_API_KEY не задан"
    body = json.dumps({"model": os.environ.get("KIMI_MODEL", "kimi-k2.6"),
                       "temperature": 1, "max_tokens": 16000,
                       "messages": [{"role": "user", "content": prompt}]})
    out, _, _ = _run(["curl", "-sS", "--max-time", "900",
                      "https://api.moonshot.ai/v1/chat/completions",
                      "-H", "Content-Type: application/json",
                      "-H", f"Authorization: Bearer {key}",
                      "-d", body], timeout=920)
    try:
        msg = json.loads(out)["choices"][0]["message"]
        return msg.get("content") or msg.get("reasoning_content", "")
    except Exception:
        return out


def ad_glm(task, artifact, who):
    return _openrouter(grader_prompt(task, artifact, who),
                       os.environ.get("GLM_MODEL", "z-ai/glm-5.2"))


ADAPTERS = {"claude": ad_claude, "gpt": ad_gpt, "gemini": ad_gemini,
            "kimi": ad_kimi, "glm": ad_glm}


def grade_one(who, task, artifact):
    t0 = time.time()
    raw = ADAPTERS[who](task, artifact, who)
    dt = round(time.time() - t0, 1)
    parsed = extract_json(raw)
    if parsed is None:
        return {"from": who, "parse_error": True, "raw": (raw or "")[:2000], "sec": dt}
    parsed.setdefault("from", who)
    parsed["sec"] = dt
    return parsed


def synthesize(task, verdicts):
    payload = json.dumps(verdicts, ensure_ascii=False, indent=None)
    prompt = (
        "Ты синтезатор совета моделей (хребет-голос). Вот вердикты совета как массив "
        f"JSON:\n{payload}\n\nЗАДАЧА была:\n{task}\n\n"
        "Сведи в ФИНАЛ по-русски: (1) общий вердикт pass/weak/fail с одной причиной, "
        "(2) 2-4 самых важных реза (консенсус + ценные одиночные сигналы), "
        "(3) отобранные графты — конкретные замены, лучшие из предложенных. "
        "Отбрасывай гарнир и повторы. Это единственный человеко-читаемый выход."
    )
    out, _, _ = _run(["claude", "-p", prompt], timeout=240)
    return out.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="Оцени артефакт: сильные/слабые места, что резать.")
    ap.add_argument("--file", help="артефакт из файла (иначе stdin)")
    ap.add_argument("--voices", default="claude,gpt,gemini,kimi,glm")
    ap.add_argument("--out", help="папка для сырых вердиктов/статов")
    args = ap.parse_args()

    task = args.task
    if task.startswith("@"):
        task = pathlib.Path(task[1:]).read_text(encoding="utf-8")
    artifact = pathlib.Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    if not artifact.strip():
        sys.exit("ПУСТОЙ артефакт (передай --file или на stdin)")

    voices = [v.strip() for v in args.voices.split(",") if v.strip() in ADAPTERS]
    sys.stderr.write(f"[совет] голоса: {', '.join(voices)}\n")

    verdicts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(voices)) as ex:
        futs = {ex.submit(grade_one, w, task, artifact): w for w in voices}
        for f in concurrent.futures.as_completed(futs):
            v = f.result()
            verdicts.append(v)
            tag = "raw" if v.get("parse_error") else v.get("verdict", "?")
            sys.stderr.write(f"[совет] {futs[f]:7s} -> {tag} ({v.get('sec')}s)\n")

    wire_bytes = sum(len(json.dumps(v, ensure_ascii=False)) for v in verdicts)
    ok = [v for v in verdicts if not v.get("parse_error")]
    sys.stderr.write(f"[совет] JSON-вердиктов: {len(ok)}/{len(verdicts)}, "
                     f"провод ~{wire_bytes} байт (~{wire_bytes // 4} ток.)\n")
    sys.stderr.write("[совет] синтез через claude -p ...\n")

    final = synthesize(task, verdicts)

    if args.out:
        d = pathlib.Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        (d / "verdicts.json").write_text(json.dumps(verdicts, ensure_ascii=False, indent=2), encoding="utf-8")
        (d / "final.md").write_text(final, encoding="utf-8")
        (d / "stats.json").write_text(json.dumps(
            {"voices": voices, "json_ok": len(ok), "wire_bytes": wire_bytes,
             "wire_tokens_est": wire_bytes // 4}, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.stderr.write(f"[совет] артефакты: {d}\n")

    print(final)


if __name__ == "__main__":
    main()
