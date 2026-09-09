"""Nəticələr promptdan asılıdırmı?

    python -m src.prompt_robustness

ETİRAZ. Bütün əsas rəqəmlər tək prompt şablonu ilə alınıb. Ən adi və ən haqlı
sual budur: "bəlkə sizin promptunuz pisdir və uçurum ondan gəlir".

ÜÇ ŞABLON MÜQAYİSƏ EDİLİR və fərq qəsdən struktur səviyyəsindədir, çünki
sadəcə söz dəyişikliyi yoxlamanı formal edərdi:

    default   iki nümunə, "Sual:/Cavab:" etiketləri
    zeroshot  nümunə YOXDUR
    plain     nümunə var, etiket yoxdur

İKİ İDDİA AYRICA YOXLANILIR, çünki onlar fərqli şeylərdir:

    AZ/EN uçurumu     eyni modelin iki dildəki fərqi
    cüt fərqi         baza ilə köklənmiş modelin azərbaycancadakı fərqi

Birincisi promptdan asılı ola bilər (prompt bir dildə yaxşı, digərində pis
işləyə bilər). İkincisi daha möhkəm olmalıdır, çünki hər iki model EYNİ
promptu alır.

NƏ AXTARIRIQ: rəqəmlərin eyni qalmasını yox, NƏTİCƏNİN eyni qalmasını.
Mütləq bal şablondan şablona dəyişəcək və bu, normaldır; dəyişməməli olan
uçurumun istiqaməti və mənalılığıdır.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from src.analyze import _column, load_runs, score_run
from src.build_dataset import load_jsonl
from src.metrics import STRICT, compare_paired

#: `oneshot` dördüncü nöqtədir və nümunə sayı oxunda yerləşir. Səbəb:
#: `zeroshot` bəzi modellərdə sınıq çıxır (boş cavab) və müqayisədən düşür,
#: nəticədə möhkəmlik iddiası üç yox, iki şablona söykənirdi.
STYLES = ("default", "zeroshot", "plain", "oneshot")

#: Cüt: baza modeli və ondan köklənmiş variant. Hər ikisi eyni promptu alır,
#: ona görə aralarındakı fərq prompt seçimindən daha az asılı olmalıdır.
PAIR = ("Qwen/Qwen3-VL-4B-Thinking", "issai/Qolda-AVL-5B")

#: Bu paydan çox sətri BOŞ qalan qaçış ölçmə sayılmır və müqayisəyə girmir.
#:
#: NİYƏ LAZIMDIR. `Qwen3-VL-4B-Thinking` şablonsuz `zeroshot` şəraitində
#: İNGİLİS sətirlərinin 42.7%-nə ümumiyyətlə cavab vermir (azərbaycanca isə
#: 0%-nə). Nəticədə ingilis balı 7.1%-ə düşür və AZ/EN uçurumu "itir". Bu,
#: iddianın uğursuzluğu DEYİL, ölçmənin uğursuzluğudur: müqayisənin bir tərəfi
#: yoxdur. İkisini qarışdırmaq hesabatı yanlış oxudardı.
#:
#: BU, NƏTİCƏYƏ GÖRƏ SEÇİLMİŞ HƏDD DEYİL. Qayda sadədir və məzmundan asılı
#: deyil: model heç nə yazmayıbsa, qiymətləndiriləcək şey yoxdur. Bütün
#: qaçışlara eyni tətbiq olunur. Ölçüldü: 56 qaçışın 53-ündə boş pay TAM
#: SIFIRDIR, `bloomz-1b7`-də 79-84% (o, tapşırığı ümumiyyətlə bacarmır) və
#: yuxarıdakı bir qaçışda 42.7%. Yəni qapı yalnız həqiqətən sınıq qaçışları
#: tutur, sərhəd halları yaratmır.
MAX_EMPTY = 0.20


def _degenerate(run) -> float | None:
    """Qaçış sınıqdırsa boş payını qaytarır, deyilsə `None`.

    Ölçü XAM cavab üzərindədir, çıxarışdan sonrakı üzərində yox: çıxarıcı boş
    qaytarsa, bu, onun qüsuru ola bilər; xam cavab boşdursa, model həqiqətən
    heç nə yazmayıb.
    """
    total = len(run.raw)
    if not total:
        return None
    empty = sum(1 for value in run.raw.values() if not value.strip())
    share = empty / total
    return share if share > MAX_EMPTY else None


def language_gap_table(dataset, runs, seed: int = 0) -> str:
    """Hər model və hər şablon üçün AZ/EN uçurumu."""
    models = sorted({m for m, _, _ in runs})
    lines = [
        "| Model | Şablon | AZ | EN | Uçurum | 95% CI | p |",
        "|---|---|---|---|---|---|---|",
    ]
    for model in models:
        for style in STYLES:
            if (model, "az", style) not in runs or (model, "en", style) not in runs:
                continue
            az, en = runs[(model, "az", style)], runs[(model, "en", style)]
            ids = sorted(az.ids & en.ids & set(dataset))
            a = _column(score_run(en, dataset, STRICT, ids), "em", ids)
            b = _column(score_run(az, dataset, STRICT, ids), "em", ids)
            result = compare_paired(a, b, seed=seed)
            lines.append(
                f"| `{model}` | {style} | {100 * result.mean_b:.1f}% | "
                f"{100 * result.mean_a:.1f}% | {100 * result.diff:.1f}pp | "
                f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}] | "
                f"{result.p_value:.4f} |"
            )
    return "\n".join(lines)


def pair_gap_table(dataset, runs, seed: int = 0) -> str:
    """Baza ilə köklənmiş modelin azərbaycancadakı fərqi, şablon-şablon."""
    base, tuned = PAIR
    lines = [
        "| Şablon | Baza | Köklənmiş | Fərq | 95% CI | p |",
        "|---|---|---|---|---|---|",
    ]
    for style in STYLES:
        if (base, "az", style) not in runs or (tuned, "az", style) not in runs:
            continue
        b, t = runs[(base, "az", style)], runs[(tuned, "az", style)]
        ids = sorted(b.ids & t.ids & set(dataset))
        a = _column(score_run(b, dataset, STRICT, ids), "em", ids)
        c = _column(score_run(t, dataset, STRICT, ids), "em", ids)
        result = compare_paired(a, c, seed=seed)
        lines.append(
            f"| {style} | {100 * result.mean_a:.1f}% | {100 * result.mean_b:.1f}% | "
            f"{100 * result.diff:+.1f}pp | "
            f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}] | "
            f"{result.p_value:.4f} |"
        )
    return "\n".join(lines)


def verdict(dataset, runs, seed: int = 0) -> str:
    """Nəticə şablondan şablona dəyişirmi?

    Mütləq balın dəyişməsi gözləniləndir. Dəyişməməli olan uçurumun İŞARƏSİ
    və MƏNALILIĞIDIR: bütün şablonlarda eyni istiqamətdə və sıfırdan fərqli
    qalırsa, iddia prompt seçiminə söykənmir.
    """
    checks: list[tuple[str, bool]] = []
    excluded: list[str] = []

    def usable(model: str, style: str) -> bool:
        """Şablon bu model üçün yararlı ölçmə şəraitidirmi?

        HƏR İKİ DİLƏ birdən baxılır və şərait yalnız bir dildə sınsa da,
        model üçün BÜTÜN müqayisələrdən çıxarılır.

        Niyə belə. `Qwen3-VL-4B-Thinking` şablonsuz `zeroshot`-da ingiliscə
        sətirlərin 42.7%-nə cavab vermir, azərbaycanca isə hamısına cavab
        verir. Yalnız ingilis qaçışını atsaydıq, cüt fərqi hesablanmağa davam
        edərdi, halbuki modelin həmin şəraitdə çökdüyü ingilis tərəfindən
        AŞKARDIR (bal 54.7%-dən 7.1%-ə düşür). Bir tərəfi sınıq şəraiti
        digər tərəfdə etibarlı saymaq olmaz.
        """
        keys = [(model, "az", style), (model, "en", style)]
        if any(key not in runs for key in keys):
            return False
        broken = False
        for key in keys:
            share = _degenerate(runs[key])
            if share is None:
                continue
            broken = True
            note = (
                f"`{key[0]}` [{key[1]}/{key[2]}]: "
                f"sətirlərin {100 * share:.1f}%-i boş"
            )
            if note not in excluded:
                excluded.append(note)
        return not broken

    for model in sorted({m for m, _, _ in runs}):
        signs = []
        for style in STYLES:
            if not usable(model, style):
                continue
            az, en = runs[(model, "az", style)], runs[(model, "en", style)]
            ids = sorted(az.ids & en.ids & set(dataset))
            a = _column(score_run(en, dataset, STRICT, ids), "em", ids)
            b = _column(score_run(az, dataset, STRICT, ids), "em", ids)
            r = compare_paired(a, b, seed=seed)
            signs.append(r.diff > 0 and r.diff_low > 0)
        if len(signs) > 1:
            checks.append((f"`{model}` AZ/EN uçurumu", all(signs)))

    base, tuned = PAIR
    signs = []
    for style in STYLES:
        if not usable(base, style) or not usable(tuned, style):
            continue
        b, t = runs[(base, "az", style)], runs[(tuned, "az", style)]
        ids = sorted(b.ids & t.ids & set(dataset))
        a = _column(score_run(b, dataset, STRICT, ids), "em", ids)
        c = _column(score_run(t, dataset, STRICT, ids), "em", ids)
        r = compare_paired(a, c, seed=seed)
        signs.append(r.diff > 0 and r.diff_low > 0)
    if len(signs) > 1:
        checks.append(("cüt fərqi (baza > köklənmiş)", all(signs)))

    lines = ["| Yoxlama | Yararlı şablonların hamısında qalır? |", "|---|---|"]
    for name, holds in checks:
        lines.append(f"| {name} | {'bəli' if holds else 'XEYR'} |")

    if excluded:
        lines += [
            "",
            "### Müqayisəyə girməyən şəraitlər",
            "",
            f"Sətirlərinin {100 * MAX_EMPTY:.0f}%-dən çoxu BOŞ qalan qaçış ölçmə",
            "sayılmır: model heç nə yazmayıbsa, qiymətləndiriləcək şey yoxdur.",
            "",
        ]
        lines += [f"- {note}" for note in excluded]
        lines += [
            "",
            "BU, İDDİANIN UĞURSUZLUĞU DEYİL, ÖLÇMƏNİN UĞURSUZLUĞUDUR və ikisini",
            "qarışdırmaq hesabatı yanlış oxudardı. Kənarda qalan şərait həmin",
            "iddia barədə nə lehinə, nə əleyhinə dəlil sayılır.",
            "",
            "MƏHDUDİYYƏT KİMİ QALIR: kənarlaşdırma möhkəmlik iddiasının",
            "söykəndiyi şablon sayını AZALDIR. Aşağıdakı nəticə həmin azalmış",
            "sayla oxunmalıdır.",
        ]

    if checks and all(holds for _, holds in checks):
        lines += [
            "",
            "Hər iki iddia yararlı şablonların hamısında eyni istiqamətdə və",
            "sıfırdan fərqli qalır. **Nəticələr prompt seçiminə söykənmir.**",
        ]
    elif checks:
        lines += [
            "",
            "ƏN AZI BİR İDDİA ŞABLONDAN ASILIDIR. Bu, ciddi tapıntıdır və",
            "hesabatda gizlədilə bilməz: həmin iddia prompt seçiminin nəticəsi",
            "ola bilər.",
        ]
    return "\n".join(lines)


def build_report(dataset, runs, seed: int = 0) -> str:
    return "\n".join(
        [
            "# Prompt robustluğu",
            "",
            "Üç şablon: `default` (iki nümunə, etiketli), `zeroshot` (nümunə yox),",
            "`plain` (nümunə var, etiket yox). Fərq struktur səviyyəsindədir.",
            "",
            "## AZ/EN uçurumu",
            "",
            language_gap_table(dataset, runs, seed),
            "",
            "## Cüt fərqi: baza ilə köklənmiş model",
            "",
            "Hər iki model EYNİ promptu alır, ona görə bu fərq prompt seçimindən",
            "daha az asılı olmalıdır.",
            "",
            pair_gap_table(dataset, runs, seed),
            "",
            "## Nəticə",
            "",
            "Mütləq balın şablonla dəyişməsi gözləniləndir. Dəyişməməli olan",
            "uçurumun işarəsi və mənalılığıdır.",
            "",
            verdict(dataset, runs, seed),
            "",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="prompt_robustness")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out", type=Path, default=Path("results/tables/prompts.md"))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset: dict[str, dict[str, Any]] = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs = {
        (r.key.model, r.key.language, r.key.prompt_style): r
        for r in load_runs(args.raw_dir)
    }
    report = build_report(dataset, runs, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
