"""Azərbaycan dili tokenizatorda ingiliscədən neçə dəfə baha başa gəlir.

    python -m src.tokenizer_fertility

NİYƏ ÖLÇÜLÜR. Bu layihə modellərin azərbaycanca zəif olduğunu göstərir və
səbəbləri bir-bir ayırır: yazı sistemi, morfologiya, diakritika, bilik boşluğu.
Bir səbəb daha var və o, modeldən ƏVVƏL, tokenizatorda başlayır.

Tokenizator sözü parçalara bölür. İngiliscə söz orta hesabla bir-iki parçaya
düşür, azərbaycanca söz isə üç-dörd parçaya. Yəni model eyni mənanı daha çox
və daha xırda fraqmentdə görür. Nəticələri:

  kontekst pəncərəsi eyni mətn üçün daha tez dolur
  eyni token büdcəsi daha az cavab yeri buraxır
  öyrənmə zamanı söz bütöv vahid kimi az görünür

Bu, BİLİKDƏN ASILI OLMAYAN struktur dezavantajdır. Model faktı bilsə belə,
onu daha çətin şəraitdə emal edir.

NƏ SÜBUT ETMİR. Yüksək məhsuldarlıq aşağı balın SƏBƏBİ olduğunu göstərmir,
yalnız onunla birlikdə mövcud olduğunu göstərir. Dörd modelin ikisi eyni
ailədəndir, ona görə buradakı rəqəmlərdən korrelyasiya çıxarmaq da olmaz.
Bu, izahedici kontekstdir, nəticə deyil.

ÖLÇÜ VAHİDİ: token / söz. Söz sadə boşluq bölgüsü ilə sayılır. Bu, kobud
tərifdir, amma HƏR İKİ dildə eyni tərifdir, ona görə nisbət mənalı qalır.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

DEFAULT_MODELS = (
    "Qwen/Qwen3-1.7B",
    "Qwen/Qwen3-VL-4B-Instruct",
    "Qwen/Qwen3-VL-4B-Thinking",
    "Qwen/Qwen3.5-4B-Base",
    "issai/Qolda-AVL-5B",
    "issai/Qwen3.5-4B-Base-Kazakh",
    "microsoft/Phi-3.5-mini-instruct",
    "tiiuae/Falcon3-3B-Instruct",
)


@dataclass(frozen=True)
class Fertility:
    """Bir modelin bir dildəki məhsuldarlığı."""

    model: str
    az_per_word: float
    en_per_word: float

    @property
    def ratio(self) -> float:
        return self.az_per_word / self.en_per_word


def measure(model: str, az: Sequence[str], en: Sequence[str]) -> Fertility:
    """Bir tokenizator üçün hər iki dildə token/söz.

    Xüsusi tokenlər ÇIXARILIR (`add_special_tokens=False`): onlar mətnin
    uzunluğundan asılı deyil və qısa sətirlərdə nisbəti süni sıxardı.
    """
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    counts = []
    for texts in (az, en):
        tokens = sum(len(tokenizer.encode(t, add_special_tokens=False)) for t in texts)
        words = sum(len(t.split()) for t in texts)
        counts.append(tokens / words if words else 0.0)
    return Fertility(model, counts[0], counts[1])


def build_table(results: Sequence[Fertility]) -> str:
    lines = [
        "# Tokenizator məhsuldarlığı",
        "",
        "Bir sözə düşən token sayı, datasetin sual mətnləri üzərində.",
        "",
        "| Model | AZ | EN | AZ / EN |",
        "|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: x.ratio):
        lines.append(
            f"| `{r.model}` | {r.az_per_word:.2f} | {r.en_per_word:.2f} | "
            f"**{r.ratio:.2f}x** |"
        )
    worst = max(results, key=lambda x: x.ratio)
    best = min(results, key=lambda x: x.ratio)
    lines += [
        "",
        f"Azərbaycan dili hər tokenizatorda ingiliscədən bahadır: ən yaxşı halda "
        f"{best.ratio:.2f}x (`{best.model}`), ən pisdə {worst.ratio:.2f}x "
        f"(`{worst.model}`).",
        "",
        "Bu, modelin bilikindən asılı olmayan struktur dezavantajdır: eyni mənanı",
        "daha çox və daha xırda fraqmentdə emal etmək lazım gəlir. Səbəb-nəticə",
        "iddiası DEYİL, izahedici kontekstdir.",
        "",
    ]
    lines += pair_vocabulary_section()
    return "\n".join(lines)


def _declared_pairs() -> tuple[tuple[str, str, str], ...]:
    """Elan edilmiş cütlər, KANONİK siyahıdan.

    ƏVVƏL BURADA ƏL İLƏ KÖÇÜRÜLMÜŞ NÜSXƏ VARDI və dairəvi importdan qaçmaq
    üçün saxlandığı yazılmışdı. Nüsxə səssizcə köhnəldi: kanonik siyahı 11
    cütə çatanda bu dördündə qaldı, cədvəl də dörd sətir verdi, halbuki
    məqalə doqquzunu iddia edirdi.

    Dairəvi asılılıq problemi funksiya daxilində importla həll olunur, elə
    `analyze.py` çıxarış qapısı üçün necə edirsə. Köçürmə yox.
    """
    from src.fine_tune_pairs import PAIRS

    return tuple((p.label, p.base, p.tuned) for p in PAIRS)


def _vocabulary(model: str) -> set[str] | None:
    """Modelin lüğəti (token sətirləri), yüklənməsə `None`."""
    from transformers import AutoTokenizer

    try:
        tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    except Exception:
        return None
    return set(tokenizer.get_vocab())


def added_tokens(base: str, tuned: str) -> tuple[int, int] | None:
    """(adi söz, xüsusi token) — köklənmiş modeldə əlavə olunanlar.

    AYRIM VACİBDİR VƏ HƏDD DEYİL. Xüsusi tokenlər (`<|audio_start|>` kimi)
    idarəetmə nişanlarıdır: mətnin necə parçalandığını DƏYİŞMİR, sadəcə
    modelə rejim siqnalı verir. Adi söz əlavə etmək isə tokenizasiyanın
    özünü dəyişir.

    `Qolda-AVL-5B` bazasına cəmi ÜÇ xüsusi token əlavə edib (audio rejimi
    üçün) və bir dənə də söz əlavə etməyib, yəni onun mətn tokenizasiyası
    bazası ilə eynidir. `Qwen3.5-4B-Base-Kazakh` isə 16 000 SÖZ əlavə edib
    (`Almaty`, `Kazakh`, `KZT`). İkisini eyni saymaq ölçünü korlayardı.
    """
    vb, vt = _vocabulary(base), _vocabulary(tuned)
    if vb is None or vt is None:
        return None
    extra = vt - vb
    special = sum(1 for token in extra if is_control_token(token))
    return len(extra) - special, special


def is_control_token(token: str) -> bool:
    """Token idarəetmə nişanıdırmı, yoxsa adi söz parçası?

    Qayda: bucaqlı və ya kvadrat mötərizə ilə ƏHATƏLƏNİB. `<|audio_start|>`
    və `[PAD]` nişandır; `<`, `-15`, ` Almaty` isə adi parçadır.

    Yalnız başlanğıca baxmaq YETƏRSİZDİR: `<` özü də lüğətdə ola bilər və
    o, mətn parçasıdır, nişan deyil.
    """
    return len(token) > 2 and (
        (token.startswith("<") and token.endswith(">"))
        or (token.startswith("[") and token.endswith("]"))
    )


def pair_vocabulary_section() -> list[str]:
    """Cüt daxilində tokenizator EYNİDİRMİ — iddia edilmir, ÖLÇÜLÜR.

    NİYƏ YENİDƏN YAZILDI. Əvvəl burada ümumi qayda yazılmışdı: "fine-tune
    tokenizatoru dəyişmir". Qayda YANLIŞDIR və yalnız iki qazax cütündə
    yoxlanılmışdı. `Trendyol` lüğəti 12 312 token genişləndirib.

    Bu, boş detal deyil. `cüt daxilindəki fərq tokenizasiya ilə izah edilə
    bilməz` iddiası məhz tokenizatorun eyni qalmasına söykənir; harada eyni
    deyilsə, orada iddia da qurula bilməz.
    """
    lines = [
        "## Cüt daxilində tokenizator eynidirmi (ÖLÇÜLÜR)",
        "",
        "Əlavə olunan tokenlər İKİ növə ayrılır. Xüsusi tokenlər",
        "(`<|audio_start|>` kimi) idarəetmə nişanlarıdır və mətnin necə",
        "parçalandığını dəyişmir. Adi SÖZ əlavə etmək isə tokenizasiyanın",
        "özünü dəyişir və nəzarəti pozur.",
        "",
        "| Cüt | Əlavə söz | Əlavə xüsusi token | Nəzarət qurulur? |",
        "|---|---|---|---|",
    ]
    broken: list[str] = []
    clean: list[str] = []
    for label, base, tuned in _declared_pairs():
        counts = added_tokens(base, tuned)
        if counts is None:
            lines.append(f"| {label} | ? | ? | ölçülmədi |")
            continue
        words, special = counts
        if words:
            broken.append(label)
        else:
            clean.append(label)
        lines.append(
            f"| {label} | {words} | {special} | "
            f"{'bəli' if not words else '**XEYR**'} |"
        )

    lines += [""]
    if clean:
        lines += [
            f"NƏZARƏT QURULAN CÜTLƏR: {', '.join(f'**{c}**' for c in clean)}.",
            "Burada hər iki model mətni eyni parçalara bölür, yəni **cüt",
            "daxilindəki fərq tokenizasiya ilə izah edilə bilməz**. Fərq",
            "çəkilərdədir, girişdə deyil.",
            "",
        ]
    if broken:
        lines += [
            f"NƏZARƏT QURULMAYAN CÜTLƏR: {', '.join(f'**{c}**' for c in broken)}.",
            "Burada lüğətə minlərlə söz əlavə edilib, yəni tokenizasiya",
            "alternativ izah olaraq QALIR və həmin cütlərdən çıxarılan nəticə",
            "bu şərtlə oxunmalıdır.",
            "",
            "Lüğətin genişlədilməsi adi fine-tune-dan qat-qat böyük",
            "müdaxilədir: model yeni tokenlər üçün embeddinq öyrənməli və",
            "köhnə paylanmanı yenidən qurmalıdır.",
            "",
            "ƏSAS NƏTİCƏYƏ TƏSİRİ. Xoşbəxtlikdən nəzarət qurulan cütlər hər",
            "İKİ tərəfdə var: biri kiril, biri latın. Deməli əsas müqayisə",
            "onların üzərində qurula bilir və genişlədilmiş lüğətli cütlər",
            "təsdiqləyici rol oynayır, daşıyıcı yox.",
            "",
        ]
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="tokenizer_fertility")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("results/tables/tokenizer.md"))
    parser.add_argument("--models", nargs="*", default=list(DEFAULT_MODELS))
    args = parser.parse_args(argv)

    rows: list[dict[str, Any]] = [
        json.loads(line) for line in args.dataset.open(encoding="utf-8") if line.strip()
    ]
    az = [r["question_az"] for r in rows]
    en = [r["question_en"] for r in rows]

    results = []
    for model in args.models:
        try:
            result = measure(model, az, en)
        except Exception as error:  # noqa: BLE001
            print(f"  ATLANDI  {model}: {str(error).splitlines()[0][:60]}")
            continue
        results.append(result)
        print(f"  {model:40} AZ {result.az_per_word:.2f}  EN {result.en_per_word:.2f}"
              f"  {result.ratio:.2f}x")

    if not results:
        print("heç bir tokenizator yüklənmədi", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_table(results), encoding="utf-8")
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
