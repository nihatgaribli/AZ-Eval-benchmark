"""Uçurumu benchmark sızması izah edə bilərmi?

    python -m src.contamination

ETİRAZ. Faktual benchmarkların hamısına verilən sual budur: suallar modelin
təlim datasına düşübsə, model onları bilmir, XATIRLAYIR. Bu halda ingilis
balının yüksək olması biliyi yox, sızmanı göstərərdi.

BURADA ONA CAVAB VERMƏK ASANDIR, çünki datasetin bir hissəsi sızma üçün
əlçatmazdır. `computed-template` mənşəli 120 sual `src/generate_math.py`
tərəfindən istehsal olunub və ölçülən modellərin heç birindən sonra yaradılıb.
Həmin sətirlər HEÇ BİR təlim korpusunda ola bilməz, çünki mövcud deyildilər.

DƏQİQ İDDİA. "Bu suallar sızmayıb" demək olar; "bu faktlar sızmayıb" demək
olmaz və lazım da deyil. Üçbucağın bucaqları toplamının 180 olması hər
korpusdadır və olmalıdır: ölçdüyümüz şey elə həmin biliyin azərbaycanca
işlədilə bilməsidir. Sızma dedikdə BENCHMARK SƏTRİNİN özünün əzbərlənməsi
nəzərdə tutulur, faktın bilinməsi yox.

MƏNŞƏ MÜQAYİSƏSİ AYRICA VERİLİR VƏ SÜBUT DEYİL. Wikidata mənşəli suallar əl
ilə yazılanlardan asandır, amma bu, sızmanın dəlili sayıla bilməz: harvester
`sitelinks >= 8` filtri ilə MƏŞHUR obyektləri seçir, əl ilə yazılanlar isə
Azərbaycana xas və qaranlıqdır. Fərq çətinlikdən də gələ bilər və ayırd
etmək üçün əlimizdə vasitə yoxdur. Cədvəl kontekst üçün verilir.

DÖŞƏMƏ MODELLƏRİ. Hər iki dildə sıfıra yaxın bal alan modellər (`mGPT`,
`bloomz`, `EuroLLM`) cədvəldə qalır, amma onların 0.0 bəndlik "uçurumu"
məlumat daşımır: itirməyə balı yoxdur. Ayrıca işarələnir ki, sıfır fərq
"uçurum yoxdur" kimi oxunmasın.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from src.analyze import _column, load_runs, score_run
from src.build_dataset import load_jsonl
from src.metrics import STRICT, compare_paired

#: Sızma üçün əlçatmaz mənşə: sətirlər ölçülən modellərdən sonra yaradılıb.
LEAK_PROOF = "computed-template"

#: Bu həddən aşağı ingilis balı olan model tapşırığı ümumiyyətlə bacarmır;
#: onun AZ/EN fərqi sıfıra yaxın olur, çünki itirəcək balı yoxdur.
FLOOR_EN = 0.05

#: Eşiyin İKİ TƏRƏFİ VAR və bu, dürüstlük məsələsidir. `Trendyol` ingiliscə
#: 6.7% alır: eşiyin cəmi 1.7 bənd üstündə, yəni onun da itirəcək balı demək
#: olar yoxdur, amma `*` almır. Eşiyi nəticəni GÖRDÜKDƏN SONRA aşağı-yuxarı
#: etmək post-hoc tənzimləmə olardı, ona görə eşik toxunulmaz qalır və
#: əvəzində SƏRHƏDƏ YAXIN modellər ayrıca göstərilir. Oxucu qaydanı da,
#: sərhəd hallarını da görür və özü qərar verir.
NEAR_FLOOR_EN = 0.10


def gap_table(
    dataset: dict[str, dict[str, Any]],
    runs: dict[tuple[str, str], Any],
    ids: Sequence[str],
    seed: int = 0,
) -> str:
    """Verilmiş sual dəsti üzərində hər modelin AZ/EN fərqi."""
    models = sorted({m for m, _ in runs if (m, "az") in runs and (m, "en") in runs})
    lines = [
        "| Model | EN | AZ | Fərq | 95% CI | p |",
        "|---|---|---|---|---|---|",
    ]
    floor = []
    near_floor: list[tuple[str, float]] = []
    for model in models:
        az, en = runs[(model, "az")], runs[(model, "en")]
        common = [i for i in ids if i in az.ids and i in en.ids]
        if not common:
            continue
        a = _column(score_run(en, dataset, STRICT, common), "em", common)
        b = _column(score_run(az, dataset, STRICT, common), "em", common)
        result = compare_paired(a, b, seed=seed)
        mark = ""
        if result.mean_a < FLOOR_EN:
            floor.append(model)
            mark = " *"
        elif result.mean_a < NEAR_FLOOR_EN:
            near_floor.append((model, result.mean_a))
            mark = " †"
        lines.append(
            f"| `{model}`{mark} | {100 * result.mean_a:.1f}% | "
            f"{100 * result.mean_b:.1f}% | {100 * result.diff:.1f}pp | "
            f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}] | "
            f"{result.p_value:.4f} |"
        )
    if floor:
        names = ", ".join(f"`{m}`" for m in floor)
        lines += [
            "",
            f"\\* İngilis balı {100 * FLOOR_EN:.0f}%-dən aşağı: {names} "
            "tapşırığı ingiliscə də bacarmır. Onların sıfıra yaxın fərqi "
            "'uçurum yoxdur' demək DEYİL: itirəcək balları yoxdur.",
        ]
    if near_floor:
        names = ", ".join(f"`{m}` ({100 * v:.1f}%)" for m, v in near_floor)
        lines += [
            "",
            f"† EŞİYƏ YAXIN ({100 * FLOOR_EN:.0f}%-"
            f"{100 * NEAR_FLOOR_EN:.0f}% arası): {names}. Bunlar `*` almır, "
            "çünki eşik əvvəlcədən elan edilib və nəticə göründükdən sonra "
            "dəyişdirilmir. Amma onların da itirəcək balı azdır, ona görə "
            "kiçik fərqləri yuxarıdakılar kimi ehtiyatla oxunmalıdır.",
        ]
    return "\n".join(lines)


def provenance_table(
    dataset: dict[str, dict[str, Any]],
    runs: dict[tuple[str, str], Any],
    seed: int = 0,
) -> str:
    """Mənşəyə görə bal. Kontekst üçündür, sızma dəlili deyil."""
    kinds = sorted({r.get("provenance", "?") for r in dataset.values()})
    models = sorted({m for m, _ in runs if (m, "en") in runs})
    lines = [
        "| Model | Dil | " + " | ".join(f"`{k}`" for k in kinds) + " |",
        "|---" * (len(kinds) + 2) + "|",
    ]
    for model in models:
        for language in ("en", "az"):
            if (model, language) not in runs:
                continue
            run = runs[(model, language)]
            cells = []
            for kind in kinds:
                ids = [
                    i
                    for i, r in dataset.items()
                    if r.get("provenance") == kind and i in run.ids
                ]
                if not ids:
                    cells.append("n/a")
                    continue
                scores = score_run(run, dataset, STRICT, ids)
                cells.append(
                    f"{100 * sum(s['em'] for s in scores.values()) / len(ids):.1f}%"
                )
            lines.append(
                f"| `{model}` | {language.upper()} | " + " | ".join(cells) + " |"
            )
    return "\n".join(lines)


def build_report(
    dataset: dict[str, dict[str, Any]],
    runs: dict[tuple[str, str], Any],
    seed: int = 0,
) -> str:
    leak_proof = [i for i, r in dataset.items() if r.get("provenance") == LEAK_PROOF]
    counts = Counter(r.get("provenance", "?") for r in dataset.values())

    return "\n".join(
        [
            "# Sızma uçurumu izah edə bilərmi?",
            "",
            f"Dataset {len(dataset)} sual: "
            + ", ".join(f"`{k}` {v}" for k, v in sorted(counts.items()))
            + ".",
            "",
            "## Sızma üçün əlçatmaz altdəst",
            "",
            f"`{LEAK_PROOF}` mənşəli **{len(leak_proof)} sual** "
            "`src/generate_math.py` tərəfindən istehsal olunub və ölçülən "
            "modellərin hamısından sonra yaradılıb. Onlar heç bir təlim "
            "korpusunda ola bilməz, çünki mövcud deyildilər.",
            "",
            gap_table(dataset, runs, leak_proof, seed),
            "",
            "Uçurum bu altdəstdə də qalır. Deməli **benchmark sızması onu izah "
            "edə bilmir.**",
            "",
            "İddia dəqiqdir: bu SƏTİRLƏR sızmayıb. Bu FAKTLARIN korpusda olması "
            "isə həm gözləniləndir, həm də lazımdır, çünki ölçdüyümüz şey elə "
            "həmin biliyin azərbaycanca işlədilə bilməsidir.",
            "",
            "## Mənşəyə görə bal (kontekst, dəlil deyil)",
            "",
            provenance_table(dataset, runs, seed),
            "",
            "Wikidata mənşəli suallar əl ilə yazılanlardan asandır. Bu, sızma "
            "dəlili SAYILA BİLMƏZ: harvester `sitelinks >= 8` filtri ilə məşhur "
            "obyektləri seçir, əl ilə yazılanlar isə Azərbaycana xas və "
            "qaranlıqdır. Fərq çətinlikdən də gələ bilər və iki izahı ayırd "
            "etmək üçün əlimizdə vasitə yoxdur.",
            "",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="contamination")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument(
        "--out", type=Path, default=Path("results/tables/contamination.md")
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs = {
        (r.key.model, r.key.language): r
        for r in load_runs(args.raw_dir)
        if r.key.prompt_style == "default"
    }
    if not runs:
        print(f"Qaçış tapılmadı: {args.raw_dir}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(dataset, runs, args.seed)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
