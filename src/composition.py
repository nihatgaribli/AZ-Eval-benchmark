"""Uçurum datasetin TƏRKİBİNDƏN gəlirmi?

    python -m src.composition

ETİRAZ. `mathematics` datasetin 26%-idir və uçurum məhz orada ən genişdir.
Deməli ümumi rəqəm modellərin azərbaycanca zəifliyini yox, datasetin
tərkibini əks etdirə bilər. Bu, tamamilə haqlı etirazdır və rəqəmlə
cavablandırılmalıdır, sözlə yox.

NECƏ YOXLANILIR. Ən böyük kateqoriya ÇIXARILIR və uçurum yenidən hesablanır.
Uçurum kompozisiyadan gəlirsə, çıxarışdan sonra ciddi KİÇİLMƏLİDİR.

NƏ TAPILDI. Əksi baş verir: riyaziyyat çıxarılanda uçurum BÖYÜYÜR. Yəni
riyaziyyat rəqəmi şişirtmir, seyrəldir. Səbəbi başa düşüləndir: riyaziyyat
sualının cavabı çox vaxt RƏQƏMDİR və rəqəmin əlifbası yoxdur, ona görə
orfoqrafik uğursuzluq orada işləmir və uçurum bir qədər azalır.

Bu, "hər ehtimala qarşı" yoxlama deyil. Datasetə 236 hesablanan riyaziyyat
sualı məhz sızmaya qarşı əlavə edilib və onların payı böyükdür; həmin
qərarın nəticəyə necə təsir etdiyi ölçülməlidir.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from src.analyze import _column, load_runs, score_run, universal_ids
from src.build_dataset import load_jsonl
from src.metrics import STRICT, compare_paired

#: Örtük: bu paydan az örtən qaçış müqayisəyə girmir (`analyze.py` ilə eyni).
COVERAGE = 0.9


def _gap(dataset, runs, model: str, ids: set[str], seed: int) -> tuple[float, int]:
    az, en = runs[(model, "az")], runs[(model, "en")]
    common = sorted(az.ids & en.ids & ids)
    if not common:
        return 0.0, 0
    a = _column(score_run(en, dataset, STRICT, common), "em", common)
    b = _column(score_run(az, dataset, STRICT, common), "em", common)
    return 100 * compare_paired(a, b, seed=seed).diff, len(common)


def build_report(dataset, runs, seed: int = 0) -> str:
    """Ən böyük kateqoriya çıxarılanda uçurum necə dəyişir."""
    models = sorted(
        {
            m
            for m, language in runs
            if language == "az"
            and (m, "en") in runs
            and len(runs[(m, "az")].ids & set(dataset)) >= COVERAGE * len(dataset)
        }
    )
    if not models:
        return "_Tam qaçış tapılmadı._\n"

    counts = Counter(r.get("category", "?") for r in dataset.values())
    biggest, biggest_n = counts.most_common(1)[0]

    universal = set(universal_ids(dataset))
    subsets = {
        "hamısı": set(dataset),
        f"{biggest}-sız": {i for i in dataset if dataset[i].get("category") != biggest},
        "universal": universal,
        f"universal, {biggest}-sız": {
            i for i in universal if dataset[i].get("category") != biggest
        },
    }

    lines = [
        "# Uçurum datasetin tərkibindən gəlirmi?",
        "",
        f"Ən böyük kateqoriya: `{biggest}` ({biggest_n} sual, "
        f"{100 * biggest_n / len(dataset):.0f}%). O çıxarılanda uçurum necə dəyişir?",
        "",
        "| Alt-dəst | n | orta uçurum |",
        "|---|---|---|",
    ]
    means: dict[str, float] = {}
    for name, ids in subsets.items():
        values = [_gap(dataset, runs, m, ids, seed)[0] for m in models]
        means[name] = statistics.mean(values)
        lines.append(f"| {name} | {len(ids)} | {means[name]:.1f}pp |")

    delta = means[f"{biggest}-sız"] - means["hamısı"]
    verdict = (
        "BÖYÜYÜR" if delta > 0.5 else "KİÇİLİR" if delta < -0.5 else "demək olar dəyişmir"
    )

    lines += [
        "",
        f"Ən böyük kateqoriya çıxarılanda uçurum **{verdict}** "
        f"({delta:+.1f} bənd).",
        "",
    ]
    if delta >= -0.5:
        lines += [
            "Deməli **uçurum kompozisiyadan gəlmir.** Etiraz haqlı idi, amma",
            "rəqəm onu dəstəkləmir: `" + biggest + "` payının böyüklüyü ümumi",
            "rəqəmi şişirtmir.",
            "",
            "Səbəb başa düşüləndir: riyaziyyat sualının cavabı çox vaxt",
            "RƏQƏMDİR və rəqəmin əlifbası yoxdur, ona görə orfoqrafik",
            "uğursuzluq orada işləmir və uçurum bir qədər azalır.",
            "",
        ]
    else:
        lines += [
            "DİQQƏT: uçurum kiçilir, yəni ümumi rəqəmin bir hissəsi",
            "kompozisiyadan gəlir. Bu, mətndə açıq yazılmalı və başlıq rəqəmi",
            "kateqoriya üzrə bölünmüş halda verilməlidir.",
            "",
        ]

    lines += ["## Model-model", "", "| Model | " + " | ".join(subsets) + " |",
              "|---|" + "---|" * len(subsets)]
    for model in models:
        cells = [f"{_gap(dataset, runs, model, ids, seed)[0]:.1f}" for ids in subsets.values()]
        lines.append(f"| `{model}` | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="composition")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out", type=Path, default=Path("results/tables/composition.md"))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset: dict[str, dict[str, Any]] = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs = {
        (r.key.model, r.key.language): r
        for r in load_runs(args.raw_dir)
        if r.key.prompt_style == "default"
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(dataset, runs, args.seed)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
