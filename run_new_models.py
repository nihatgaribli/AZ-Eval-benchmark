"""Yeni dörd modelin qaçışı: Gemma, Llama-3-8B baza, Türk-Llama, Aya.

NİYƏ AYRI FAYL. `run_all.py` bütün qaçışları yenidən başladır. Bu dörd model
sonradan əlavə olundu, qalan 18-i yenidən qaçırmağa ehtiyac yoxdur.

CHAT TEMPLATE. Dördüncü cüt `Meta-Llama-3-8B` -> `Turkish-Llama-8b-v0.1`
BAZA modellərindən ibarətdir; heç birində chat template yoxdur. Üçüncü cütdə
(`Mistral-7B-v0.1` -> `Trendyol`) məhz bu asimmetriya nəticəni sıfıra endirmişdi:
fine-tune olunmuş model şablonla, baza modeli şablonsuz soruşulmuşdu. Burada
`--no-chat-template` HƏR İKİSİNƏ AÇIQ verilir ki, asimmetriya təsadüfən də
qayıtmasın.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MODELS = [
    ("google/gemma-3-4b-it", ["--load-in-4bit"]),
    ("meta-llama/Meta-Llama-3-8B", ["--load-in-4bit", "--no-chat-template"]),
    ("ytu-ce-cosmos/Turkish-Llama-8b-v0.1", ["--load-in-4bit", "--no-chat-template"]),
    ("CohereLabs/aya-expanse-8b", ["--load-in-4bit"]),
]

RUNS = [(m, lang, flags) for m, flags in MODELS for lang in ("az", "en")]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    results = []
    for index, (model, language, flags) in enumerate(RUNS, start=1):
        label = f"{model} [{language}]"
        print(f"\n{'=' * 72}\n[{index}/{len(RUNS)}] {label}\n{'=' * 72}", flush=True)
        started = time.time()
        completed = subprocess.run(
            [
                sys.executable, "-m", "src.run_eval",
                "--model", model,
                "--language", language,
                "--prompt-style", "default",
                "--max-new-tokens", "32",
                "--batch-size", "8",
                "--seed", "0",
                *flags,
            ],
            cwd=ROOT,
        )
        results.append((label, completed.returncode, time.time() - started))

    print(f"\n{'=' * 72}\nXÜLASƏ\n{'=' * 72}")
    for label, code, elapsed in results:
        mark = "OK " if code == 0 else "XTA"
        print(f"  {mark} {label:56} {elapsed / 60:5.1f} deq")
    return 0 if all(c == 0 for _, c, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
