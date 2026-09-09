"""Şablon möhkəmliyi üçün qalan qaçışlar: `zeroshot` tamamlanması və `plain`.

    python run_prompt_styles.py

İKİ AYRI PROBLEM VAR.

1. `zeroshot` qaçışları 604 sətirdədir, dataset isə 729. Nisbət 82.8%-dir,
   yəni örtük qapısından (90%) KEÇMİR və müqayisə cədvəllərinə düşmür.
   `run_eval` susmaya görə davam edir, ona görə bu qaçışlar yalnız çatmayan
   125 sətri yazacaq, hamısını yenidən yox.

2. `plain` qaçışı ÜMUMİYYƏTLƏ yoxdur. Köhnə variant qüsurlu idi: şablon
   qısalıq göstərişini DƏ, etiketləri DƏ atırdı, ona görə modellər düzgün
   cavab verə-verə ~0% alırdı (`"Fransanın paytaxtı **Paris**dir."`).
   Göstəriş bərpa olundu, köhnə sətirlər `superseded_plain_v1/`-ə köçürüldü.

NİYƏ ÜÇ ŞABLON LAZIMDIR. `prompt_robustness.verdict` bir şablonla möhkəmlik
iddiası qurmur və qurmamalıdır: uçurumun promptdan gəlmədiyini göstərmək
üçün ən azı üç fərqli şablonda qalması lazımdır. Hazırda iki şablon var,
yəni iddia HƏLƏ QURULA BİLMİR.

MODEL SEÇİMİ. `prompt_robustness.PAIR` cütü məcburidir. `Instruct` variantı
da əlavə olunur, çünki əsas cədvəldə ən yüksək bal onundur və şablon
həssaslığı ən çox orada gözlənilir.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MODELS = (
    "Qwen/Qwen3-VL-4B-Thinking",
    "issai/Qolda-AVL-5B",
    "Qwen/Qwen3-VL-4B-Instruct",
)

FLAGS = {
    "issai/Qolda-AVL-5B": ["--load-in-4bit", "--trust-remote-code"],
}

#: `zeroshot` əvvəl gəlir, çünki ucuzdur: hər qaçışda cəmi 125 sətir qalıb.
STYLES = ("zeroshot", "plain")

RUNS = [
    (model, language, style)
    for style in STYLES
    for model in MODELS
    for language in ("az", "en")
]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    results = []
    for index, (model, language, style) in enumerate(RUNS, start=1):
        label = f"{model} [{language}/{style}]"
        print(f"\n{'=' * 72}\n[{index}/{len(RUNS)}] {label}\n{'=' * 72}", flush=True)
        started = time.time()
        completed = subprocess.run(
            [
                sys.executable, "-m", "src.run_eval",
                "--model", model,
                "--language", language,
                "--prompt-style", style,
                "--max-new-tokens", "32",
                "--batch-size", "8",
                "--seed", "0",
                *FLAGS.get(model, ["--load-in-4bit"]),
            ],
            cwd=ROOT,
        )
        results.append((label, completed.returncode, time.time() - started))

    print(f"\n{'=' * 72}\nXÜLASƏ\n{'=' * 72}")
    for label, code, elapsed in results:
        print(f"  {'OK ' if code == 0 else 'XTA'} {label:52} {elapsed / 60:5.1f} deq")
    return 0 if all(c == 0 for _, c, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
