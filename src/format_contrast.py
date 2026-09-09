"""Eyni faktı iki formatda soruşur: seçmək ucuzdur, yazmaq bahadır.

    python -m src.format_contrast --model issai/Qolda-AVL-5B --load-in-4bit
    python -m src.format_contrast --score

SUAL. AZ-Eval-in əsas tapıntısı budur ki, qazax dilinə köklənmiş model
azərbaycan suallarına cavabların 91.7%-ini KİRİLLƏ yazır, ona görə STRICT
rejimdə 3.3% alır, transliterasiyadan sonra isə 10.5%. Amma bu, cavabı YAZMAQ
şərtilə görünür. Model `B` deyəndə heç nə yazmır və əlifba heç vaxt ortaya
çıxmır.

Dünyadakı bütün türk dili benchmarkları (KazMMLU, TUMLU, INCLUDE)
çoxvariantlıdır. Yəni onların heç biri bu effekti ölçə bilmir, ölçmədikləri
üçün də mövcud olmadığını düşünmək asandır.

Bu modul eyni sualı iki cür verir:

    mcq    dörd variant göstərilir, model hərf seçir
    short  variantlar gizlədilir, model cavabı YAZIR

Aradakı fərq cavabı Azərbaycan dilində istehsal etməyin qiymətidir. Model
faktı tanıyır, amma yaza bilmirsə, fərq böyük olacaq.

NƏZARƏTLƏR. Fərqi tək başına oxumaq olmaz, çünki çoxvariantlı test onsuz da
asandır: dörd variantdan təsadüfi seçim 25% verir, qısa cavabda isə təsadüf
sıfıra yaxındır. Ona görə İKİ model qaçırılır:

    Qolda-AVL-5B            kiril yazan model
    Qwen3-VL-4B-Instruct    latın yazan model, eyni ölçü sinfi

Format fərqi hər ikisində olacaq. Maraqlı olan onların FƏRQİDİR: Qoldada fərq
əhəmiyyətli dərəcədə böyükdürsə, səbəb formatın özü yox, əlifbadır.

DEKODLAMA HƏR İKİ ŞƏRAİTDƏ EYNİDİR (greedy, 32 token, sabit seed). Fərqli
olsaydı, ölçdüyümüz şey formatın təsiri yox, dekodlama parametrinin təsiri
olardı.

Qısa cavab promptu `run_eval.PROMPT_TEMPLATES["az"]` ilə HƏRFƏN eynidir, yoxsa
rəqəmlər AZ-Eval-in cədvəlləri ilə müqayisə edilə bilməz.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.analyze import extract_answer
from src.metrics import MODES, STRICT, bootstrap_ci, compare_paired, normalize
from src.run_eval import PROMPT_TEMPLATES, GenerationConfig

LETTERS = "ABCD"

#: Çoxvariantlı prompt. Nümunələr qısa cavab promptundakı ilə EYNİ faktlardır
#: (Misir, su), ona görə iki şərait arasında few-shot fərqi yoxdur. Həmin iki
#: cavab `build_dataset`-dəki çirklənmə qapısı ilə onsuz da datasetdən
#: kənardadır.
MCQ_PROMPT = (
    "Suala cavab ver. Yalnız düzgün variantın hərfini yaz.\n\n"
    "Sual: Misirin paytaxtı hansı şəhərdir?\n"
    "A) İsgəndəriyyə\nB) Qahirə\nC) Luksor\nD) Aswan\n"
    "Cavab: B\n\n"
    "Sual: Su molekulunun kimyəvi formulu nədir?\n"
    "A) CO2\nB) NaCl\nC) H2O\nD) O2\n"
    "Cavab: C\n\n"
    "Sual: {question}\n"
    "{options}\n"
    "Cavab:"
)

#: Cavabdan hərfi çıxarmaq. Model "B", "B)", "Cavab: B", "B) Qahirə" yaza
#: bilər; hamısı eyni seçimdir.
#:
#: "Cavab:" PREFİKSİ AYRICA SİLİNİR və bu, boş formallıq deyil. Prefiks
#: `C` hərfi ilə başlayır, yəni naxış onu variant kimi tutmağa çalışır və
#: sonrakı `a` söz sərhədini pozduğu üçün uyğunluq tamamilə itir. Nəticədə
#: "Cavab: B" CAVABSIZ sayılardı, halbuki model B seçib. Bu, MCQ balını
#: sistematik aşağı salar və format fərqini süni böyüdərdi.
_ANSWER_PREFIX = re.compile(r"^\s*(cavab|answer)\s*[:.]\s*", re.IGNORECASE)

#: Naxış sətrin ƏVVƏLİNƏ bağlanıb, yoxsa izahatın içindəki təsadüfi hərf
#: tutulardı ("Bu sualın cavabı..." -> B).
#: Bəzək simvolları da buraxılır. Qwen3-VL cavabı MARKDOWN ilə verir
#: (`Cavab: **B) 800 m**`), Qolda isə düz mətnlə (`B`). Bəzək qəbul
#: edilməsəydi, 521 cavabdan 92-si oxunmazdı VƏ YALNIZ BİR MODELDƏ:
#: nəzarətin MCQ balı süni aşağı düşər, onun format fərqi kiçilər,
#: Qoldanınkı isə nisbətən böyük görünərdi. Yəni səhv nəticəni gözlənilən
#: istiqamətə əyərdi, ona görə burada dəqiqlik xüsusilə vacibdir.
_LETTER = re.compile(r"^[\s:.\-*_`\"'([]*([ABCD])(?![A-Za-zƏəĞğİıÖöŞşÇçÜü])")

#: EHTİYAT YOL: cavab mətnin ORTASINDA. Qwen3-VL-Thinking few-shot naxışını
#: davam etdirir və sualı təkrar yazır, sonra cavabı verir:
#:
#:     "Sual: Təbiətdə neçə növ qarşılıqlı təsir var?\n\nCavab: C"
#:
#: Yalnız sətrin əvvəlinə baxılsaydı, həmin model 521 cavabın 521-ində
#: OXUNMAZ sayılardı və MCQ balı sıfır çıxardı. Bu, modelin uğursuzluğu
#: deyil, çıxarıcının qüsuru olardı; format fərqi isə həmin model üçün
#: tamamilə mənasız rəqəmə çevrilərdi.
#:
#: Naxış "Cavab:" nişanına bağlıdır, sərbəst hərf axtarmır: sərbəst axtarış
#: izahat mətnindəki təsadüfi böyük hərfi seçim sayardı.
_LETTER_AFTER_MARKER = re.compile(
    r"(?:cavab|answer)\s*[:.]\s*[*_`\"'([]*([ABCD])(?![A-Za-zƏəĞğİıÖöŞşÇçÜü])",
    re.IGNORECASE,
)


def load_items(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def build_prompts(item: dict[str, Any]) -> dict[str, str]:
    options = "\n".join(
        f"{letter}) {choice}" for letter, choice in zip(LETTERS, item["choices"])
    )
    return {
        "mcq": MCQ_PROMPT.format(question=item["question_az"], options=options),
        "short": PROMPT_TEMPLATES["az"].format(question=item["question_az"]),
    }


def letter_of(raw: str) -> str:
    """Modelin seçdiyi hərf, tapılmazsa boş sətir.

    Əvvəlcə sətrin BAŞINA baxılır, çünki cavab adətən oradadır və bu, ən az
    şərh tələb edən yoldur. Yalnız orada tapılmayanda "Cavab:" nişanından
    sonrakı hərf axtarılır.
    """
    text = _ANSWER_PREFIX.sub("", raw.strip())
    match = _LETTER.match(text)
    if match:
        return match.group(1)
    fallback = _LETTER_AFTER_MARKER.search(raw)
    return fallback.group(1) if fallback else ""


def score_short(raw: str, item: dict[str, Any], mode) -> float:
    """Qısa cavabın balı: normalizasiyadan sonra cavab və ya alternativlərdən biri."""
    prediction = normalize(extract_answer(raw), mode)
    gold = [item["answer"], *item.get("answer_aliases", [])]
    return float(any(prediction == normalize(g, mode) for g in gold))


@dataclass
class Condition:
    name: str
    rows: dict[str, str]


def run(
    items: Sequence[dict[str, Any]],
    backend,
    out_dir: Path,
    batch_size: int,
) -> None:
    """Hər iki şəraiti icra edir və xam mətni yazır.

    Bal BURADA hesablanmır. `run_eval`-dəki eyni ayrılıq: xam cavab bir dəfə
    alınır, qiymətləndirmə isə istənilən qədər təkrarlana bilər və heç bir GPU
    saatı yenidən xərclənmir.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for condition in ("mcq", "short"):
        path = out_dir / f"{backend.name.replace('/', '__')}__{condition}.jsonl"
        done = set()
        if path.exists():
            done = {
                json.loads(line)["id"]
                for line in path.open(encoding="utf-8")
                if line.strip()
            }
        pending = [i for i in items if i["id"] not in done]
        if not pending:
            print(f"  {condition}: hamısı hazırdır")
            continue

        with path.open("a", encoding="utf-8") as handle:
            for start in range(0, len(pending), batch_size):
                batch = pending[start : start + batch_size]
                prompts = [build_prompts(i)[condition] for i in batch]
                answers = backend.generate(prompts)
                for item, answer in zip(batch, answers):
                    handle.write(
                        json.dumps(
                            {
                                "id": item["id"],
                                "model": backend.name,
                                "condition": condition,
                                "subject": item["subject"],
                                # Büdcə hər sətrə yazılır. Format fərqi MODEL
                                # DAXİLİNDƏ ölçülür, ona görə şərt budur ki, bir
                                # modelin iki şəraiti eyni büdcə ilə qaçsın.
                                # Modellər arasında büdcə fərqlənə bilər və
                                # fərqlənəndə bu, sətirdən görünməlidir.
                                "max_new_tokens": backend.config.max_new_tokens,
                                "raw_response": answer,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                handle.flush()
                print(
                    f"  {condition}: {min(start + batch_size, len(pending))}"
                    f"/{len(pending)}",
                    flush=True,
                )


def score(items: Sequence[dict[str, Any]], raw_dir: Path, seed: int = 0) -> str:
    """İki şəraiti tutuşdurur və cədvəl qaytarır."""
    by_id = {i["id"]: i for i in items}
    runs: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for path in sorted(raw_dir.glob("*.jsonl")):
        for line in path.open(encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            runs[(row["model"], row["condition"])][row["id"]] = row["raw_response"]

    models = sorted({model for model, _ in runs})
    cyrillic = re.compile(r"[Ѐ-ӿ]")
    lines = [
        "# Format müqayisəsi: seçmək və yazmaq",
        "",
        f"Dəst: TUMLU-az, {len(items)} sual. Dekodlama hər iki şəraitdə eynidir.",
        "",
        "| Model | Zəncir | MCQ | Qısa cavab | Fərq | 95% CI | p |",
        "|---|---|---|---|---|---|---|",
    ]
    for model in models:
        mcq_raw = runs.get((model, "mcq"), {})
        short_raw = runs.get((model, "short"), {})
        ids = sorted(set(mcq_raw) & set(short_raw) & set(by_id))
        if not ids:
            continue
        mcq_scores = [
            float(letter_of(mcq_raw[i]) == by_id[i]["answer_letter"]) for i in ids
        ]
        for mode in MODES:
            short_scores = [score_short(short_raw[i], by_id[i], mode) for i in ids]
            result = compare_paired(mcq_scores, short_scores, seed=seed)
            lines.append(
                f"| {model} | {mode.name} | {100 * result.mean_a:.1f}% | "
                f"{100 * result.mean_b:.1f}% | {100 * result.diff:+.1f}pp | "
                f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}] | "
                f"{result.p_value:.4f} |"
            )

    lines += [
        "",
        "Təsadüfi seçim MCQ-də 25.0% verir, qısa cavabda isə sıfıra yaxındır.",
        "Ona görə fərqin ÖZÜ tək başına oxunmur; iki modelin fərqləri arasındakı",
        "məsafə oxunur.",
        "",
    ]

    # SAXLANMA: MCQ-də tanınan biliyin nə qədəri yazıya keçir.
    #
    # NİYƏ FƏRQ KİFAYƏT ETMİR. İki modelin format fərqi (37.4 və 38.8 bənd)
    # statistik olaraq eynidir, yəni "kiril yazan modelin fərqi daha böyükdür"
    # iddiası ÖLÇÜ İLƏ TƏSDİQLƏNMİR. Amma fərq bənd olaraq eyni olsa da,
    # modellərin ÇIXIŞ NÖQTƏSİ eyni deyil və fərq tavana dirənir: Qoldanın
    # qısa cavab balı 0.2%-dir, yəni sıfırdan aşağı düşə bilməz, ona görə onun
    # fərqi demək olar bütünlüklə MCQ balına bərabərdir.
    #
    # Saxlanma bu tavanı aradan qaldırır: yalnız MCQ-də DÜZGÜN seçilmiş
    # suallara baxılır və onların neçə faizinin yazıda da düz çıxdığı ölçülür.
    lines += [
        "",
        "## Saxlanma: tanınan biliyin yazıya keçən payı",
        "",
        "| Model | Zəncir | MCQ-də düz | Yazıda da düz | 95% CI |",
        "|---|---|---|---|---|",
    ]
    for model in models:
        mcq_raw = runs.get((model, "mcq"), {})
        short_raw = runs.get((model, "short"), {})
        correct = [
            i
            for i in sorted(set(mcq_raw) & set(short_raw) & set(by_id))
            if letter_of(mcq_raw[i]) == by_id[i]["answer_letter"]
        ]
        if not correct:
            continue
        for mode in (STRICT, MODES[-1]):
            kept = [score_short(short_raw[i], by_id[i], mode) for i in correct]
            ci = bootstrap_ci(kept, seed=seed)
            lines.append(
                f"| {model} | {mode.name} | {len(correct)} | "
                f"{100 * ci.mean:.1f}% | [{100 * ci.low:.1f}, {100 * ci.high:.1f}] |"
            )

    # UĞURSUZLUQ NÖVLƏRİ. "Model kirillə yazır" cümləsi baş verəni tam
    # izah etmir və izah etmədiyi hissə vacibdir:
    #
    #   dil dəyişməsi   "Təbiətdə neçə növ qarşılıqlı təsir var?" -> "Төрт."
    #                   Model cavabı BİLİR və düzgün deyir, sadəcə qazaxca.
    #                   Transliterasiya bunu XİLAS ETMİR: "Төрт" -> "Tört",
    #                   gözlənilən isə "4"-dür. Əlifba çevrilir, söz qalır.
    #   prompt əks-sədası  model sualı buraxıb promptdakı nümunəni təkrarlayır.
    #
    # Bu, AZ-Eval-in əsas datasetindən fərqin səbəbidir. Orada model doğru
    # cavabı kirillə YAZIRDI (Bakı -> Бакы) və transliterasiya onu qaytarırdı.
    # Burada söz başqa dildədir, ona görə qaytarmaq üçün heç nə yoxdur.
    echo = re.compile(r"H2O|Qahir|Каир|Мысыр", re.IGNORECASE)
    lines += [
        "",
        "| Model | Kirillə | Promptu təkrarlayan | MCQ hərfi çıxarılmayan |",
        "|---|---|---|---|",
    ]
    for model in models:
        short_raw = runs.get((model, "short"), {})
        mcq_raw = runs.get((model, "mcq"), {})
        if not short_raw:
            continue
        total = len(short_raw)
        lines.append(
            f"| {model} "
            f"| {sum(1 for t in short_raw.values() if cyrillic.search(t))}/{total} "
            f"| {sum(1 for t in short_raw.values() if echo.search(t))}/{total} "
            f"| {sum(1 for t in mcq_raw.values() if not letter_of(t))}/{len(mcq_raw)} |"
        )

    # Kiril payı: effektin mənbəyini göstərən sətir.
    lines += ["", "| Model | Şərait | Kirillə yazılmış cavab |", "|---|---|---|"]
    for model in models:
        for condition in ("mcq", "short"):
            raw = runs.get((model, condition), {})
            if not raw:
                continue
            hits = sum(1 for text in raw.values() if cyrillic.search(text))
            lines.append(
                f"| {model} | {condition} | {hits}/{len(raw)} "
                f"({100 * hits / len(raw):.1f}%) |"
            )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="format_contrast")
    parser.add_argument("--items", type=Path, default=Path("data/tumlu/tumlu_az_short.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/format_contrast"))
    parser.add_argument("--model")
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args(argv)

    items = load_items(args.items)
    if args.limit:
        items = items[: args.limit]

    if args.model:
        from src.run_eval import TransformersBackend

        backend = TransformersBackend(
            args.model,
            GenerationConfig(max_new_tokens=args.max_new_tokens, seed=args.seed),
            load_in_4bit=args.load_in_4bit,
            trust_remote_code=args.trust_remote_code,
        )
        print(f"{args.model}: {len(items)} sual, iki şərait")
        run(items, backend, args.raw_dir, args.batch_size)

    if args.score:
        table = score(items, args.raw_dir, args.seed)
        out = args.raw_dir / "tables.md"
        out.write_text(table, encoding="utf-8")
        print(table)
        print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
