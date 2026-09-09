"""Xəta taksonomiyasının İNSAN yarısı.

    python -m src.error_labels sample     # etiketlənəcək CSV hazırla
    python -m src.error_labels score      # nəticəni hesabla

NİYƏ LAZIMDIR. `analyze.py` xətaların bir hissəsini maşınla etiketləyir:
normalizasiya zəncirinin hansı həlqəsi xətanı düzəldirsə, səbəb odur. Amma
zəncir kömək etmirsə, maşın SUSUR və sətir insana qalır. Bacarıq tipli
modellərdə həmin qalıq 82-97%-dir, yəni taksonomiyanın əsl hissəsi hələ
yoxdur.

MİQYAS QƏSDƏN KİÇİKDİR. Bütün 2909 sətri etiketləmək lazım deyil və zərərli
olardı: iş saatlarla çəkərdi və yarımçıq qalardı. İki model, hər birindən
100 sətir kifayətdir, çünki məqsəd payları müqayisə etməkdir, dəqiq say yox.

MODELLƏR NİYƏ MƏHZ BELƏ SEÇİLİR. Biri orfoqrafik uğursuzluq tipindən, biri
bacarıq tipindən götürülür. Yalnız birini etiketləsək, "iki rejim fərqlidir"
iddiası müqayisəsiz qalardı.

YALNIZ MAŞININ SUSDUĞU SƏTİRLƏR seçilir. Maşın artıq etiket veribsə, insanın
onu təkrarlaması vaxt itkisidir; insanın əlavə dəyəri məhz qalıqdadır.

`qızıl səhv` ETİKETİ İKİ İŞ GÖRÜR. O, xəta taksonomiyasına aid deyil, amma
etiketləyən adam qızıl cavabın özünün yanlış olduğunu görürsə, bunu qeyd
etməlidir. Belə sətirlər datasetin auditinə qayıdır.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

#: İnsanın verə biləcəyi etiketlər.
LABELS = {
    "faktual": "cavab yanlış faktdır",
    "format": "məzmun düz, forma yanlış (artıq söz, cümlə)",
    "başqa dil": "cavab başqa dildədir (türkcə, rusca, ingiliscə)",
    "mənasız": "cavab sualla əlaqəsizdir və ya mənasızdır",
    "qızıl səhv": "QIZIL cavabın özü yanlışdır",
}

#: Etiketlənəcək modellər: biri orfoqrafik, biri bacarıq tipindən.
#: `analyze.py` ölçüsünə görə Qolda 94% orfoqrafik, Turkish-Llama 0%-dir.
DEFAULT_MODELS = (
    "issai__Qwen3.5-4B-Base-Kazakh",
    "ytu-ce-cosmos__Turkish-Llama-8b-v0.1",
)


def load_error_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pick_unlabelled(
    rows: Sequence[dict[str, str]], size: int, seed: int = 0
) -> list[dict[str, str]]:
    """Maşının SUSDUĞU sətirlərdən təsadüfi nümunə.

    Maşın etiket veribsə, sətir buraxılır: insanın əlavə dəyəri yalnız
    qalıqdadır. Seçim kateqoriyaya görə təbəqələndirilir, yoxsa nümunə ən
    böyük kateqoriyaya sürüşər.
    """
    residue = [r for r in rows if not (r.get("error_type_auto") or "").strip()]
    if not residue:
        return []

    by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in residue:
        by_category[row.get("category", "?")].append(row)

    rng = random.Random(seed)
    quota = max(1, size // max(1, len(by_category)))
    chosen: list[dict[str, str]] = []
    for group in by_category.values():
        pool = sorted(group, key=lambda r: r.get("id", ""))
        rng.shuffle(pool)
        chosen.extend(pool[:quota])

    if len(chosen) < min(size, len(residue)):
        picked = {r.get("id") for r in chosen}
        rest = sorted(
            (r for r in residue if r.get("id") not in picked),
            key=lambda r: r.get("id", ""),
        )
        rng.shuffle(rest)
        chosen.extend(rest[: size - len(chosen)])

    return sorted(chosen, key=lambda r: r.get("id", ""))[:size]


def write_sample(
    models: Sequence[str], tables: Path, out: Path, size: int, seed: int = 0
) -> int:
    """Etiketlənəcək CSV: bir fayl, bütün modellər birlikdə.

    Model adı sütunda qalır ki, hesabat onları ayıra bilsin, amma sətirlər
    QARIŞDIRILMIR: annotator bir modeli bitirib digərinə keçir. Qarışdırsaydıq,
    kontekst dəyişməsi işi yavaşladardı.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["model", "id", "sual", "qızıl cavab", "modelin cavabı", "etiket", "qeyd"]
        )
        for model in models:
            rows = load_error_rows(tables / f"errors__{model}.csv")
            for row in pick_unlabelled(rows, size, seed):
                writer.writerow(
                    [
                        model,
                        row.get("id", ""),
                        row.get("question", ""),
                        row.get("gold", ""),
                        row.get("prediction", ""),
                        "",
                        "",
                    ]
                )
                written += 1
    return written


def build_report(rows: Sequence[dict[str, str]]) -> str:
    """İnsan etiketlərinin payı, model-model."""
    labelled = [r for r in rows if (r.get("etiket") or "").strip() in LABELS]
    if not labelled:
        return "_Hələ heç nə etiketlənməyib._\n"

    by_model: dict[str, list[str]] = defaultdict(list)
    for row in labelled:
        by_model[row.get("model", "?")].append(row["etiket"].strip())

    lines = [
        "# Xəta taksonomiyası — insan hissəsi",
        "",
        "Yalnız maşının SUSDUĞU sətirlər etiketlənib: normalizasiya zənciri",
        "kömək etmirsə, səbəb insan tərəfindən təyin olunmalıdır.",
        "",
        f"Etiketlənən sətir: {len(labelled)}.",
        "",
        "| Etiket | " + " | ".join(f"`{m}`" for m in sorted(by_model)) + " |",
        "|---|" + "---|" * len(by_model),
    ]
    for label in LABELS:
        cells = []
        for model in sorted(by_model):
            values = by_model[model]
            n = sum(1 for v in values if v == label)
            cells.append(f"{n} ({100 * n / len(values):.0f}%)")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    relabelled = [r for r in labelled if "yenidən etiketləndi" in (r.get("qeyd") or "")]
    gold_errors = [r for r in labelled if r["etiket"].strip() == "qızıl səhv"]
    lines += [
        "",
        "## Necə oxunmalıdır",
        "",
        "Bu cədvəl MAŞININ ETİKETLƏDİYİ hissəni əvəz etmir, onu tamamlayır.",
        "Maşın orfoqrafik xətaları tutur (yazı sistemi, diakritika,",
        "morfologiya); burada isə onun tuta bilmədikləri var.",
        "",
        "`başqa dil` etiketi ayrıca vacibdir: model faktı bilir, amma səhv",
        "dildə yazır. Bu, kiril halının LATIN əlifbalı analoqudur və",
        "transliterasiya onu tuta bilmir, çünki əlifba onsuz da düzdür.",
        "",
    ]
    if relabelled:
        lines += [
            f"## AÇIQLAMA: {len(relabelled)} sətir SONRADAN yenidən etiketləndi",
            "",
            "Birinci keçiddə `başqa dil` etiketi heç işlədilmədi və türkcə",
            "yazılmış cavablar `format` sayıldı. Səbəb tərifin qeyri-dəqiq",
            "izahı idi.",
            "",
            "MEYAR: model EYNİ ANLAYIŞI başqa dildə yazıbsa, bu, dil",
            "səhvidir, forma səhvi deyil (`yapon dili` -> `Japonca`).",
            "Cavabın özü yanlışdırsa, türk yer adı içində olsa belə,",
            "etiket dəyişmir (`Şamaxı` -> `Bakü` faktual səhvdir).",
            "",
            "Yenidən etiketləmə SONRADAN aparılıb və bu, gizlədilmir:",
            "hər belə sətrin `qeyd` sahəsində köhnə etiket saxlanılır.",
            "Nəticəyə baxan adam dəyişikliyi izləyə bilər.",
            "",
        ]
    if gold_errors:
        lines += [
            f"## DATASET AUDİTİ: {len(gold_errors)} sətirdə qızıl cavab şübhəlidir",
            "",
            "Bunlar xəta taksonomiyasına aid deyil, datasetə aiddir və",
            "yoxlanılmalıdır.",
            "",
        ]
        for row in gold_errors[:30]:
            comment = (row.get("qeyd") or "").strip()
            lines.append(
                f"- `{row.get('id')}` {row.get('sual', '')[:60]} -> "
                f"qızıl: {row.get('qızıl cavab', '')}"
                + (f" — _{comment}_" if comment else "")
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="error_labels")
    parser.add_argument("command", choices=("sample", "score"))
    parser.add_argument("--tables", type=Path, default=Path("results/tables"))
    parser.add_argument(
        "--out", type=Path, default=Path("results/agreement/error_labels.csv")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/tables/errors_human.md")
    )
    parser.add_argument("--models", nargs="*", default=list(DEFAULT_MODELS))
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    if args.command == "sample":
        if args.out.exists():
            print(
                f"{args.out} artıq var. Üstündən yazmaq etiketləri itirər.",
                file=sys.stderr,
            )
            return 1
        count = write_sample(args.models, args.tables, args.out, args.size, args.seed)
        if not count:
            print("Etiketlənəcək sətir tapılmadı.", file=sys.stderr)
            return 1
        print(f"{count} sətir -> {args.out}")
        print()
        print("TƏLİMAT: `etiket` sütununu bu sözlərdən biri ilə doldur:")
        for label, description in LABELS.items():
            print(f"  {label:12} {description}")
        print()
        print("Şübhən varsa `qeyd` sütununa yaz.")
        print("Doldurduqdan sonra: python -m src.error_labels score")
        return 0

    rows = load_error_rows(args.out)
    if not rows:
        print(f"Etiket faylı yoxdur: {args.out}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(rows)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
