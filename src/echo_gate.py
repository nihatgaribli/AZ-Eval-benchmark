"""Model few-shot NÜMUNƏLƏRİNİ təkrarlayırsa, o qaçış ölçmə deyil.

    python -m src.echo_gate

NİYƏ VAR. `MAX_EMPTY` qapısı modelin HEÇ NƏ yazmadığı halı tutur. Bu qapı
başqa bir pozuntunu tutur: model nümunələrin cavablarını təkrarlayır, sonra
əsl cavabı yazır. Çıxarıcı birinci sətri götürdüyü üçün model DÜZGÜN
cavabladığı sualda səhv sayılır.

NECƏ ÜZƏ ÇIXDI. `MamayLM-Gemma-3-4B-IT` azərbaycanca cavabların 67.8%-ini
belə verirdi, ingiliscə cavabların isə 0%-ini. Bazası hər iki dildə 0%.
Yəni ölçmə İKİTƏRƏFLİ müqayisənin BİR tərəfində sınmışdı və artıq zərəri
+7.0 bənd göstərirdi. Doğru rəqəm +0.1-dir.

BU, ƏN TƏHLÜKƏLİ SƏHV NÖVÜDÜR, çünki hipotezi TƏSDİQLƏYİRDİ. Hipotezə zidd
rəqəm həmişə araşdırılır; təsdiqləyən rəqəm çox vaxt araşdırılmır.

SƏBƏB NÜMUNƏ SAYIDIR, məzmunu deyil: iki nümunə ilə 67.8-100%, bir nümunə
ilə 0.3%, nümunəsiz 0%.

QAYDA ŞABLONDAN ÇIXARILIR, kodda təkrar yazılmır. Nümunə cavablarını buraya
əl ilə köçürsək, şablon dəyişəndə qapı səssizcə yalan danışardı.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from src.analyze import load_runs, run_label
from src.build_dataset import load_jsonl
from src.run_eval import PROMPT_STYLES, QUESTION_FIELD

#: Bu paydan çox sətri nümunəni təkrarlayan qaçış müqayisəyə girmir.
#: Ölçülmüş dəyərlər: sağlam qaçışlarda 0-0.3%, sınıq qaçışda 67.8-100%.
#: Sərhəd halı yoxdur, ona görə hədd geniş qoyulur.
MAX_ECHO = 0.20

#: Bu paydan çox sətri SUALI təkrarlayan qaçış da müqayisəyə girmir.
#: Ayrı pozuntudur: model cavab vermir, promptu geri qaytarır. Nümunə
#: təkrarından fərqli olaraq cavab TƏK sətirlidir, ona görə həmin qayda
#: bunu tutmurdu. `Kolkha-Mini-Georgian` üzərində üzə çıxdı.
MAX_QUESTION_ECHO = 0.20

#: Şablonda sualın yerini tutan işarə.
_SENTINEL = "\u0001QUESTION\u0001"


def prompt_prefix(style: str, language: str) -> str:
    """Şablonun sualdan ƏVVƏLKİ hissəsi: təlimat və nümunələr.

    İstehsal şablonundan alınır (`run_eval.PROMPT_STYLES`), yenidən yazılmır.
    """
    template = PROMPT_STYLES[style][language]
    rendered = template.replace("{question}", _SENTINEL)
    return rendered.split(_SENTINEL)[0]


def echoes_examples(text: str, prefix: str) -> bool:
    """Cavab nümunənin cavabını təkrarlayıb sonra davam edirmi?

    İki şərt birlikdə: cavab ÇOXSƏTİRLİDİR və birinci sətir promptun
    nümunə hissəsində keçir. Tək sətirli cavab, hətta prompta oxşasa da,
    pozuntu deyil.
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    return lines[0] in prefix


def echoes_question(text: str, question: str) -> bool:
    """Model cavab vermək əvəzinə SUALI geri yazıbmı?

    `Kolkha-Mini-Georgian` bunu edirdi: azərbaycanca sualı olduğu kimi
    təkrarlayıb dayanırdı. Nümunə təkrarından fərqli rejimdir, çünki cavab
    TƏK sətirlidir və nümunə hissəsində yox, sualın özündə üst-üstə düşür.

    Cavablar orta hesabla 1.34 sözdür, sual isə tam cümlədir, ona görə
    yanlış müsbət ehtimalı praktiki olaraq yoxdur.
    """
    body = text.strip()
    needle = question.strip()
    if not body or len(needle) < 12:
        return False
    first_line = body.splitlines()[0] if body.splitlines() else ""
    return body.startswith(needle) or needle in first_line


def question_echo_rate(run: Any, dataset: dict[str, dict[str, Any]]) -> float:
    """Qaçışda sualı təkrarlayan cavabların payı."""
    field = QUESTION_FIELD.get(run.key.language)
    if not field or not run.raw:
        return 0.0
    hits = 0
    counted = 0
    for row_id, value in run.raw.items():
        question = (dataset.get(row_id) or {}).get(field)
        if not isinstance(question, str):
            continue
        counted += 1
        if echoes_question(value or "", question):
            hits += 1
    return hits / counted if counted else 0.0


def echo_rate(run: Any) -> float:
    """Qaçışda nümunəni təkrarlayan cavabların payı."""
    if not run.raw:
        return 0.0
    prefix = prompt_prefix(run.key.prompt_style, run.key.language)
    hits = sum(1 for value in run.raw.values() if echoes_examples(value or "", prefix))
    return hits / len(run.raw)


def degenerate(run: Any) -> float | None:
    """Qaçış bu qapıdan keçmirsə payı qaytarır, keçirsə `None`."""
    share = echo_rate(run)
    return share if share > MAX_ECHO else None


def build_report(
    runs: Sequence[Any], dataset: dict[str, dict[str, Any]] | None = None
) -> str:
    rows = sorted(
        (
            (
                run_label(r.key),
                r.key.language,
                echo_rate(r),
                question_echo_rate(r, dataset) if dataset else 0.0,
                len(r.raw),
            )
            for r in runs
        ),
        key=lambda row: -max(row[2], row[3]),
    )
    broken = [
        row for row in rows if row[2] > MAX_ECHO or row[3] > MAX_QUESTION_ECHO
    ]

    lines = [
        "# Nümunə təkrarı qapısı",
        "",
        "Model few-shot nümunələrinin cavablarını təkrarlayıb sonra əsl cavabı",
        "yazırsa, çıxarıcı birinci sətri götürür və model düzgün cavabladığı",
        "sualda səhv sayılır. Belə qaçış ölçmə deyil.",
        "",
        f"Hədd: nümunə təkrarı **{100 * MAX_ECHO:.0f}%**, "
        f"sual təkrarı **{100 * MAX_QUESTION_ECHO:.0f}%**.",
        "",
    ]
    if broken:
        lines += [
            f"**{len(broken)} qaçış qapıdan keçmir:**",
            "",
            "| Qaçış | Dil | Nümunə təkrarı | Sual təkrarı | n |",
            "|---|---|---|---|---|",
        ]
        for label, lang, share, qshare, n in broken:
            lines.append(
                f"| `{label}` | {lang} | **{100 * share:.1f}%** | "
                f"**{100 * qshare:.1f}%** | {n} |"
            )
        lines.append("")
    else:
        lines += ["Bütün qaçışlar qapıdan keçir.", ""]

    lines += [
        "## Ən yüksək on qaçış",
        "",
        "| Qaçış | Dil | Nümunə təkrarı | Sual təkrarı | n |",
        "|---|---|---|---|---|",
    ]
    for label, lang, share, qshare, n in rows[:10]:
        lines.append(
            f"| `{label}` | {lang} | {100 * share:.1f}% | {100 * qshare:.1f}% | {n} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="echo_gate")
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out", type=Path, default=Path("results/tables/echo_gate.md"))
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    args = parser.parse_args(argv)

    runs = load_runs(args.raw_dir)
    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(runs, dataset)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
