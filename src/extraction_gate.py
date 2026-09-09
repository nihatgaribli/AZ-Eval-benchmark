"""Çıxarıcı cavabı İTİRİRSƏ, o qaçış ölçmə deyil.

    python -m src.extraction_gate

NƏYİ ÖLÇÜR. Səhv sayılan sətirlərin neçə faizində QIZIL CAVAB xam mətndə
onsuz da var. Yüksək pay o deməkdir ki, model sualı bilirdi, çıxarıcı isə
cavabı tapa bilmədi. Belə qaçışın balı modelin biliyini yox, çıxış formatını
ölçür.

NİYƏ ÜÇÜNCÜ QAPI. `MAX_EMPTY` modelin heç nə yazmadığını tutur, `echo_gate`
promptun geri qaytarıldığını. Bu qapı isə hər ikisinin NƏTİCƏSİNİ tutur və
onlardan ümumidir: hansı səbəbdən olursa olsun, cavab mətndədir və bala
çevrilmir.

HƏDD PAYLANMADAN SEÇİLİR, GÖZDƏN YOX. 106 qaçış üzrə ölçüldü:

    ən yüksək                    42.4%   (`Kolkha-Mini-Georgian`, ingiliscə)
    BOŞLUQ                       26.1 bənd
    növbəti dəstə                16.4%, 16.0%, 15.5%, 15.1%, 14.8%, ...

Yeganə həqiqi boşluq 42.4% ilə 16.4% arasındadır, ona görə hədd onun
ortasına, 30%-ə qoyulur. İlk yazdığım 15% SƏHV İDİ: o, boşluqda deyil,
sıx dəstənin ORTASINDAN keçirdi və beş qaçışı sərhəd halına salırdı.
Hədd məlumatdakı boşluğa qoyulmalıdır, gözəl görünən rəqəmə yox.

DİQQƏT: uzun cavab ÖZÜ pozuntu deyil. `Mistral-7B-v0.1` cavabların 100%-ni
cümlə ilə verir və yenə ingiliscədə 52.6% alır, çünki çıxarıcı işini görür.
Ona görə uzunluq deyil, İTİRİLMİŞ CAVAB ölçülür.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from src.analyze import load_runs, run_label, score_run
from src.build_dataset import load_jsonl
from src.metrics import STRICT

#: Bu paydan çox səhvi bərpa oluna bilən qaçış müqayisəyə girmir.
MAX_RECOVERABLE = 0.30

#: Hansı sahə hansı dilin qızıl cavabıdır.
GOLD_FIELD = {"az": "answer", "en": "answer_en"}

_KEEP = re.compile(r"[^0-9a-zəğışçöüA-ZƏĞIŞÇÖÜİ]")


def _fold(value: Any) -> str:
    """Müqayisə üçün sadələşdirmə: yalnız hərf və rəqəm, kiçik hərflə."""
    return _KEEP.sub("", str(value)).lower()


def answer_present(raw: str, gold: Any) -> bool:
    """Qızıl cavab xam mətnin içindədirmi?"""
    needle = _fold(gold)
    return bool(needle) and needle in _fold(raw)


def recoverable_rate(run: Any, dataset: dict[str, dict[str, Any]]) -> tuple[float, int]:
    """Səhvlərin neçə payında cavab xam mətndədir, və səhv sayı."""
    field = GOLD_FIELD.get(run.key.language)
    ids = sorted(set(run.ids) & set(dataset))
    if not field or not ids:
        return 0.0, 0
    scored = score_run(run, dataset, STRICT, ids)
    wrong = [i for i in ids if not scored[i]["em"]]
    if not wrong:
        return 0.0, 0
    hits = sum(
        1 for i in wrong if answer_present(run.raw.get(i, "") or "", dataset[i].get(field))
    )
    return hits / len(wrong), len(wrong)


def degenerate(run: Any, dataset: dict[str, dict[str, Any]]) -> float | None:
    """Qapıdan keçmirsə payı qaytarır, keçirsə `None`."""
    share, _ = recoverable_rate(run, dataset)
    return share if share > MAX_RECOVERABLE else None


def build_report(runs: Sequence[Any], dataset: dict[str, dict[str, Any]]) -> str:
    rows = []
    for run in runs:
        share, wrong = recoverable_rate(run, dataset)
        if wrong:
            rows.append((run_label(run.key), run.key.language, share, wrong))
    rows.sort(key=lambda row: -row[2])
    broken = [row for row in rows if row[2] > MAX_RECOVERABLE]

    lines = [
        "# Çıxarış qapısı",
        "",
        "Səhv sayılan sətirlərin neçə faizində qızıl cavab XAM mətndə onsuz da",
        "var. Yüksək pay modelin bilmədiyini yox, çıxarıcının tapmadığını",
        "göstərir; belə qaçışın balı çıxış formatını ölçür.",
        "",
        f"Hədd: **{100 * MAX_RECOVERABLE:.0f}%**.",
        "",
    ]
    if broken:
        lines += [
            f"**{len(broken)} qaçış qapıdan keçmir:**",
            "",
            "| Qaçış | Dil | Bərpa oluna bilən səhv | Səhv sayı |",
            "|---|---|---|---|",
        ]
        for label, lang, share, wrong in broken:
            lines.append(f"| `{label}` | {lang} | **{100 * share:.1f}%** | {wrong} |")
        lines.append("")
    else:
        lines += ["Bütün qaçışlar qapıdan keçir.", ""]

    lines += [
        "## Ən yüksək on qaçış",
        "",
        "| Qaçış | Dil | Bərpa oluna bilən səhv | Səhv sayı |",
        "|---|---|---|---|",
    ]
    for label, lang, share, wrong in rows[:10]:
        lines.append(f"| `{label}` | {lang} | {100 * share:.1f}% | {wrong} |")
    lines += [
        "",
        "Hədd 106 qaçışın paylanmasından seçilib: 42.4%-dən sonra 26 bəndlik",
        "boşluq, sonra 16.4%-dən aşağı sıx dəstə. Hədd boşluğun ortasındadır.",
        "",
        "Uzun cavab özü pozuntu deyil: `Mistral-7B-v0.1` cavabların 100%-ni",
        "cümlə ilə verir və yenə ingiliscədə 52.6% alır, çünki çıxarıcı işini",
        "görür. Ona görə uzunluq deyil, itirilmiş cavab ölçülür.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="extraction_gate")
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument(
        "--out", type=Path, default=Path("results/tables/extraction_gate.md")
    )
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs = load_runs(args.raw_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(runs, dataset)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
