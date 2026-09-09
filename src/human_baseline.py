"""İnsan bazası: eyni suallara adam nə qədər düz cavab verir.

    python -m src.human_baseline            # cavablamağa başla
    python -m src.human_baseline --score    # nəticəni hesabla

NİYƏ LAZIMDIR. Cədvəldə `Qwen3-VL-4B riyaziyyatda azərbaycanca 39.8%` yazılıb.
Bu, pisdir? Yaxşıdır? Rəqəmin ANKERİ yoxdur. İnsanın həmin suallarda nə aldığı
ölçülməsə, model balı yalnız başqa modellə müqayisə edilə bilir, halbuki
benchmarkın məqsədi real bacarığı ölçməkdir. Hakimlərin resurs məqaləsində
verdiyi ilk sual budur.

QAYDALAR, POZULARSA ÖLÇÜ MƏNASINI İTİRİR:

  1. AXTARIŞ YOXDUR. Google, kitab, telefon yox. Ölçdüyümüz şey "insan tapa
     bilərmi" deyil, "insan bilirmi"dir. Model də axtarış etmir.
  2. Bilmirsənsə BOŞ burax. Təxmin etmə. Boş cavab "bilmirəm" deməkdir və
     ayrıca hesablanır; təxmin edilmiş səhv cavab isə statistikanı korlayır.
  3. Cavabı qısa yaz, model kimi. Cümlə qurma.

EYNİ QİYMƏTLƏNDİRMƏ YOLU. Cavab modellərinki ilə eyni funksiyalardan keçir:
`extract_answer`, sonra normalizasiya zənciri, sonra alias müqayisəsi. Fərqli
yol seçilsəydi, insan və model balları müqayisə edilə bilməzdi.

NÜMUNƏ TƏBƏQƏLƏNDİRİLİB. Kateqoriyalar datasetdəki nisbətə uyğun seçilir,
sabit seed ilə. Təsadüfi seçim kiçik kateqoriyaları (`world` 45 sual)
tamamilə kənarda qoya bilərdi.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

from src.analyze import extract_answer, gold_answers
from src.build_dataset import load_jsonl
from src.metrics import MODES, STRICT, TRANSLIT, bootstrap_ci, normalize, score_example


def stratified_sample(
    dataset: dict[str, dict[str, Any]], size: int, seed: int = 0
) -> list[str]:
    """Kateqoriya nisbətini qoruyan nümunə.

    Sadə təsadüfi seçim `world` (45 sual) və ya `mathematics`-in universal
    yarısı kimi kiçik təbəqələri tamamilə buraxa bilər, halbuki tapıntıların
    çoxu məhz onlardadır.
    """
    rng = random.Random(seed)
    by_category: dict[str, list[str]] = defaultdict(list)
    for record_id, record in dataset.items():
        by_category[record.get("category", "?")].append(record_id)

    total = len(dataset)
    chosen: list[str] = []
    for category, ids in sorted(by_category.items()):
        ids = sorted(ids)
        rng.shuffle(ids)
        quota = max(1, round(size * len(ids) / total))
        chosen.extend(ids[:quota])

    rng.shuffle(chosen)
    return chosen[:size]


def load_answers(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        row["id"]: row["answer"]
        for _, row in load_jsonl(path)
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def ask(
    dataset: dict[str, dict[str, Any]], ids: Sequence[str], path: Path
) -> None:
    """Sualları bir-bir soruşur və cavabı dərhal fayla yazır.

    Hər cavabdan sonra fayl bağlanır: sessiya yarımçıq kəsilsə də iş itmir və
    `--resume` davam etdirir.
    """
    done = load_answers(path)
    pending = [i for i in ids if i not in done]
    if not pending:
        print(f"Hamısı cavablanıb: {len(done)} sual.")
        return

    print(f"\n{len(pending)} sual qalıb ({len(done)}/{len(ids)} hazırdır).")
    print("Qaydalar: axtarış yoxdur, bilmirsənsə ENTER (boş burax), qısa yaz.")
    print("Çıxmaq üçün: q + ENTER\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    for index, record_id in enumerate(pending, start=1):
        record = dataset[record_id]
        print(f"[{index}/{len(pending)}]  ({record.get('category', '?')})")
        print(f"  {record['question_az']}")
        try:
            reply = input("  cavab: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nDayandırıldı, cavablar saxlanıldı.")
            return
        if reply.lower() == "q":
            print("Dayandırıldı, cavablar saxlanıldı.")
            return
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps({"id": record_id, "answer": reply}, ensure_ascii=False) + "\n"
            )
        print()

    print("Bitdi. Nəticə üçün: python -m src.human_baseline --score")


def model_comparison(
    dataset: dict[str, dict[str, Any]],
    ids: Sequence[str],
    human: float,
    raw_dir: Path,
    seed: int = 0,
) -> str:
    """İnsanı və modelləri EYNİ suallar üzərində sıralayır.

    Ayrı dəstlər üzərində müqayisə mənasızdır: model 604 sualın hamısını
    görür, insan isə 49-nu. Sıralama yalnız ortaq sətirlər üzərində qurulur.
    """
    from src.analyze import load_runs, score_run

    rows = [("**İNSAN**", 100 * human)]
    for run in load_runs(raw_dir):
        if run.key.language != "az" or run.key.prompt_style != "default":
            continue
        common = [i for i in ids if i in run.ids]
        if len(common) < 0.9 * len(ids):
            continue
        scores = score_run(run, dataset, TRANSLIT, common)
        rows.append(
            (
                f"`{run.key.model}`",
                100 * sum(s["em"] for s in scores.values()) / len(common),
            )
        )

    lines = [
        "## İnsan və modellər, eyni suallar (TRANSLIT)",
        "",
        "| | AZ |",
        "|---|---|",
    ]
    for name, value in sorted(rows, key=lambda r: -r[1]):
        lines.append(f"| {name} | {value:.1f}% |")
    return "\n".join(lines)


def _best_model_score(dataset, ids, raw_dir) -> float:
    """Eyni suallarda ən yaxşı modelin balı (TRANSLIT)."""
    from src.analyze import load_runs, score_run

    best = 0.0
    for run in load_runs(raw_dir):
        if run.key.language != "az" or run.key.prompt_style != "default":
            continue
        common = [i for i in ids if i in run.ids]
        if len(common) < 0.9 * len(ids):
            continue
        scores = score_run(run, dataset, TRANSLIT, common)
        best = max(best, sum(s["em"] for s in scores.values()) / len(common))
    return best


def reading_guide(
    human: float, best_model: float, total: int, blank: int
) -> list[str]:
    """Oxunuş RƏQƏMDƏN çıxarılır, sabit mətn deyil.

    NİYƏ DƏYİŞDİ. Əvvəl burada sabit abzas vardı: "insan bazası TAVAN DEYİL,
    ən yaxşı model insanı üstələyir". O, BİR ölçmə üçün yazılmışdı: datasetin
    müəllifi 49 sualı cavablamış, 59%-ni boş buraxmış və 26.5% almışdı.

    Dataseti görməmiş ikinci adam ölçüləndə rəqəm çevrildi (64.0%, ən yaxşı
    model 36.0%), sabit mətn isə əksini yazmağa davam edirdi. Sabit nəticə
    mətni yalnız onu doğuran ölçmə üçün doğrudur.
    """
    beats = human > best_model
    lines = [
        "## Bu cədvəli necə oxumaq lazımdır",
        "",
    ]
    if beats:
        lines += [
            f"İnsan modellərin hamısından yuxarıdır: {100 * human:.1f}% "
            f"qarşı {100 * best_model:.1f}%. Deməli dataset həll EDİLƏ",
            "biləndir və modellərin aşağı balı tapşırığın mümkünsüzlüyündən",
            "deyil.",
            "",
            "Bu, mühüm fərqdir: həll edilə bilməyən dəst modelləri ölçmür,",
            "yalnız hamısını sıfıra yaxın saxlayır.",
        ]
    else:
        lines += [
            f"İnsan bazası TAVAN QURMUR: {100 * human:.1f}%, ən yaxşı model",
            f"{100 * best_model:.1f}%. Dataset insan üçün də çətindir.",
        ]
    lines += [
        "",
        "MƏHDUDİYYƏTLƏR:",
        "",
        f"1. **Azsaylı sual ({total}).** İntervallar genişdir.",
        f"2. **Boş cavab SƏHV sayılır** ({blank} sual, "
        f"{100 * blank / max(1, total):.0f}%). Model həmişə nəsə yazır, insan",
        "   isə bilmədiyini boş buraxa bilər. İnsan təxmin etsəydi, balı",
        "   bir qədər yuxarı olardı.",
        "3. **Cavablayanın dəstlə əlaqəsi nəticəni əyir.** Datasetin müəllifi",
        "   sualları görüb, yəni meyl onun xeyrinədir; dəsti görməmiş adamın",
        "   balı isə təmiz ölçüdür. Hansı halda olduğu ayrıca yazılmalıdır.",
        "",
    ]
    return lines


def score(
    dataset: dict[str, dict[str, Any]],
    answers: dict[str, str],
    seed: int = 0,
    raw_dir: Path | None = None,
) -> str:
    """İnsan balını modellərlə EYNİ yoldan keçirir."""
    ids = sorted(set(answers) & set(dataset))
    if not ids:
        return "_Cavab yoxdur._\n"

    blank = [i for i in ids if not answers[i].strip()]
    lines = [
        "# İnsan bazası",
        "",
        f"Cavablanan sual: {len(ids)}. Boş buraxılan (bilmirəm): {len(blank)} "
        f"({100 * len(blank) / len(ids):.1f}%).",
        "",
        "| Zəncir | EM | 95% CI |",
        "|---|---|---|",
    ]
    for mode in MODES:
        scores = [
            score_example(
                extract_answer(answers[i]), gold_answers(dataset[i], "az"), mode
            )["em"]
            for i in ids
        ]
        ci = bootstrap_ci(scores, seed=seed)
        lines.append(
            f"| {mode.name} | {100 * ci.mean:.1f}% | "
            f"[{100 * ci.low:.1f}, {100 * ci.high:.1f}] |"
        )

    lines += ["", "## Kateqoriya üzrə (STRICT)", "", "| Kateqoriya | n | EM |", "|---|---|---|"]
    by_category: dict[str, list[float]] = defaultdict(list)
    for i in ids:
        value = score_example(
            extract_answer(answers[i]), gold_answers(dataset[i], "az"), STRICT
        )["em"]
        by_category[dataset[i].get("category", "?")].append(value)
    for category, values in sorted(by_category.items()):
        lines.append(
            f"| {category} | {len(values)} | {100 * sum(values) / len(values):.1f}% |"
        )

    lines += [
        "",
        "Boş cavablar SƏHV sayılır, çünki model də cavabsız sətirdə bal almır.",
        "Onların payı ayrıca verilir: insanın bilmədiyi sual modelin də",
        "bilmədiyi sual ola bilər və bu, uçurumun bir hissəsini izah edir.",
        "",
    ]

    if raw_dir is not None:
        best_model = _best_model_score(dataset, ids, raw_dir)
        human = sum(
            score_example(
                extract_answer(answers[i]), gold_answers(dataset[i], "az"), TRANSLIT
            )["em"]
            for i in ids
        ) / len(ids)
        lines += [
            model_comparison(dataset, ids, human, raw_dir, seed),
            "",
            *reading_guide(human, best_model, len(ids), len(blank)),
        ]

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="human_baseline")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument(
        "--annotator",
        default=None,
        help="cavablayanın adı; fayl adını təyin edir (first, second, ...)",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--score", action="store_true", help="yalnız hesabla")
    args = parser.parse_args(argv)

    # ANNOTATOR FAYL ADINA GİRİR. Girmədiyi müddətdə iki adamın cavabları
    # EYNİ fayla yazılırdı və faylda kimin cavabladığı qeyd olunmurdu.
    #
    # Bu, nəzəri risk deyil: 2026-09-08-də məhz belə oldu. Birinci
    # annotatorun 49 cavabı ilə ikinci annotatorun 19 cavabı bir faylda
    # qarışdı. Xoşbəxtlikdən ortaq sual yox idi və git tarixindən ayrıla
    # bildi, amma ayrıla bilməyə də bilərdi.
    #
    # İnsan bazasının bütün mənası MÜSTƏQİL ölçmədir; iki adamın cavabını
    # qarışdırmaq onu sıfırlayır.
    if args.annotator:
        args.out = args.out or Path(f"results/human/answers_{args.annotator}.jsonl")
        args.report = args.report or Path(
            f"results/human/baseline_{args.annotator}.md"
        )
    else:
        args.out = args.out or Path("results/human/answers_first.jsonl")
        args.report = args.report or Path("results/human/baseline_first.md")

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    ids = stratified_sample(dataset, args.size, args.seed)

    if not args.score:
        ask(dataset, ids, args.out)

    answers = load_answers(args.out)
    if not answers:
        print("Hələ cavab yoxdur.")
        return 0

    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = score(dataset, answers, args.seed, raw_dir=args.raw_dir)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
