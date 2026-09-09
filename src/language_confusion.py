"""Səhv dil xətasını ədəbiyyatdakı hazır metriklər tuturmu?

    python -m src.language_confusion

ETİRAZ. "Model azərbaycanca sual alıb türkcə cavab verir" yeni müşahidə
deyil. Ədəbiyyatda buna DİL QARIŞIQLIĞI deyilir və onun ölçüsü var:
Marchisio et al. (EMNLP 2024) LPR/WPR metriklərini təklif edir, Liu və
Niehues (MRL 2025) isə maşın tərcüməsində LangID dəqiqliyi verir. Deməli
"heç bir metrik bunu tutmur" cümləsi olduğu kimi YANLIŞDIR və məqalədə
yazıla bilməz.

BİZİM İDDİAMIZ DAHA DAR OLMALIDIR. Metrik var, amma bizim halda işə
düşmür. Marchisio-nun söz səviyyəli detektoru latın əlifbalı dillər üçün
belə təyin olunub: dilin Unicode diapazonundan KƏNAR simvol axtarılır.

NİYƏ İŞLƏMİR. Türk əlifbasının 29 hərfi azərbaycan əlifbasının 32 hərfinin
alt-çoxluğudur; azərbaycanca yalnız `ə`, `x`, `q` əlavə edir. Deməli türk
orfoqrafiyası ilə yazılmış söz azərbaycan diapazonundan kənara ÇIXA
BİLMƏZ. Detektor konstruksiyaya görə susur, məlumatın təsadüfünə görə yox.

NƏ ÖLÇÜLÜR. İnsan tərəfindən `başqa dil` etiketlənmiş sətirlərdə həmin
qayda tətbiq edilir və neçəsini tutduğu sayılır.

SƏTİR SƏVİYYƏLİ QAYDA ÖLÇÜLMÜR. O, fastText ilə sətir-sətir yoxlayır;
bizdə isə cavab orta hesabla 1.34 sözdür, sətir deyil. Mühitdə fastText
qurulmayıb, ona görə onun bu cütdə necə davranacağı barədə heç nə
İDDİA EDİLMİR: ölçülməyən şey yazılmır.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

#: Azərbaycan latın əlifbası (32 hərf).
AZ_ALPHABET: frozenset[str] = frozenset("abcçdeəfgğhxıijkqlmnoöprsştuüvyz")

#: Türk latın əlifbası (29 hərf).
TR_ALPHABET: frozenset[str] = frozenset("abcçdefgğhıijklmnoöprsştuüvyz")

#: İnsan etiketi: model cavabı başqa dildədir.
WRONG_LANGUAGE = "başqa dil"


def _fold(alphabet: frozenset[str]) -> frozenset[str]:
    """Böyük hərfləri də daxil et (`i`/`İ` cütü daxil olmaqla)."""
    return frozenset(alphabet | {c.upper() for c in alphabet} | {"İ", "I"})


def out_of_script(text: str, alphabet: frozenset[str] = AZ_ALPHABET) -> list[str]:
    """Marchisio et al.-in latın əlifbalı dillər üçün söz səviyyəli qaydası.

    Dilin diapazonundan kənar hərfləri qaytarır. Boş siyahı = detektor susur.
    """
    allowed = _fold(alphabet)
    return sorted({c for c in text if c.isalpha() and c not in allowed})


def word_level_detects(text: str, alphabet: frozenset[str] = AZ_ALPHABET) -> bool:
    """Detektor bu cavabda səhv dili tuturmu?"""
    return bool(out_of_script(text, alphabet))


def turkish_is_subset() -> bool:
    """Türk əlifbası azərbaycan əlifbasının alt-çoxluğudurmu?

    Bu, iddianın DAŞIYICI hissəsidir: doğru olmasa, detektorun susması
    təsadüf olardı.
    """
    return TR_ALPHABET <= AZ_ALPHABET


def load_labels(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_report(rows: Sequence[dict[str, str]]) -> str:
    wrong = [r for r in rows if (r.get("etiket") or "").strip() == WRONG_LANGUAGE]
    caught = [r for r in wrong if word_level_detects(r.get("modelin cavabı", ""))]
    missed = [r for r in wrong if r not in caught]

    extra = sorted(AZ_ALPHABET - TR_ALPHABET)
    lines = [
        "# Səhv dil: hazır metriklər onu tuturmu?",
        "",
        "Marchisio et al. (EMNLP 2024) latın əlifbalı dillər üçün söz",
        "səviyyəli dil qarışıqlığını dilin Unicode diapazonundan kənar",
        "simvolla təyin edir. Həmin qayda bizim insan etiketli sətirlərə",
        "tətbiq olunur.",
        "",
        f"Türk əlifbası azərbaycan əlifbasının alt-çoxluğudur: "
        f"**{'BƏLİ' if turkish_is_subset() else 'XEYR'}** "
        f"(azərbaycanca yalnız {', '.join('`' + c + '`' for c in extra)} əlavə edir).",
        "",
        "| | n |",
        "|---|---|",
        f"| İnsan etiketli xəta | {len(rows)} |",
        f"| Bunlardan `{WRONG_LANGUAGE}` | {len(wrong)} |",
        f"| Söz səviyyəli detektor tutur | {len(caught)} |",
        f"| Detektor buraxır | {len(missed)} |",
        "",
    ]
    if wrong:
        share = 100 * len(missed) / len(wrong)
        lines += [
            f"Detektor səhv dil xətalarının **{share:.0f}%-ni buraxır.**",
            "",
        ]
    if caught:
        lines += [
            "Tutulanlar qaydanı təsdiqləyir: hamısı azərbaycan əlifbasında",
            "olmayan hərf daşıyır.",
            "",
            "| id | cavab | kənar hərf |",
            "|---|---|---|",
        ]
        for r in caught:
            marks = ", ".join(f"`{c}`" for c in out_of_script(r.get("modelin cavabı", "")))
            lines.append(f"| {r.get('id', '?')} | {r.get('modelin cavabı', '')} | {marks} |")
        lines.append("")

    lines += [
        "## Buraxılanlar",
        "",
        "| id | qızıl | modelin cavabı |",
        "|---|---|---|",
    ]
    for r in missed:
        lines.append(
            f"| {r.get('id', '?')} | {r.get('qızıl cavab', '')} | {r.get('modelin cavabı', '')} |"
        )
    lines += [
        "",
        "Səbəb konstruksiyadadır, təsadüf deyil: türk orfoqrafiyası ilə",
        "yazılmış söz azərbaycan diapazonundan kənara çıxa bilmir.",
        "",
        "SƏTİR SƏVİYYƏLİ qayda burada ölçülmür: o, fastText ilə sətir-sətir",
        "işləyir, bizim cavab isə orta hesabla 1.34 sözdür. Mühitdə fastText",
        "yoxdur, ona görə onun bu cütdə davranışı barədə iddia edilmir.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="language_confusion")
    parser.add_argument(
        "--labels", type=Path, default=Path("results/agreement/error_labels.csv")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("results/tables/language_confusion.md")
    )
    args = parser.parse_args(argv)

    if not args.labels.exists():
        print(f"Etiket faylı yoxdur: {args.labels}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(load_labels(args.labels))
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
