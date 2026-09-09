"""İkinci annotator və annotatorlararası razılıq.

    python -m src.agreement sample          # ikinci annotator üçün nümunə hazırla
    python -m src.agreement score           # razılığı hesabla

NİYƏ LAZIMDIR. Bu, resurs məqaləsində hakimin BİRİNCİ verdiyi sualdır:
"dataseti kim yoxlayıb və başqa biri eyni qərarı verərdimi?" Hazırda bütün
sətirlər bir nəfər tərəfindən, özü də datasetin MÜƏLLİFİ tərəfindən
təsdiqlənib. Meyl müəllifin xeyrinədir və bunu ölçmədən iddia edilə bilməz.

NƏ ÖLÇÜLÜR. İkinci annotator sətri görür və bir sual cavablandırır: bu sətir
datasetdə qalmalıdırmı? Üç cavab var:

    düzgün      sual aydındır, cavab doğrudur
    səhv        cavab yanlışdır və ya sual qüsurludur
    qeyri-səlis qərar vermək mümkün deyil

Sonra Cohen kappa hesablanır: iki annotatorun TƏSADÜFDƏN ARTIQ nə qədər
razılaşdığı. Xam faiz kifayət etmir, çünki hər iki annotator demək olar hər
şeyə "düzgün" desə, faiz 95% çıxar və heç nə demiş olmaz.

ƏSAS QAYDA: İKİNCİ ANNOTATOR BİRİNCİNİN QƏRARINI GÖRMƏMƏLİDİR.
Görsəydi, razılıq süni şəkildə yuxarı çıxardı və ölçü mənasını itirərdi.
`sample` əmri məhz buna görə yalnız sualı və qızıl cavabı yazır; birinci
annotatorun qərarı (`verified_by`) çıxarılır.

NÜMUNƏ TƏBƏQƏLƏNDİRİLİR. Mənşəyə görə, çünki risk mənşəyə görə fərqlidir:
`computed-template` sətirlərində cavab alqoritmdən gəlir və səhv ehtimalı
demək olar sıfırdır; `wikidata-template` sətirlərində məlumat xarici bazadan
gəlir; `manual` sətirlərini müəllif özü yazıb və ən çox risk oradadır.
Təsadüfi seçim `manual` payını azaldıb ölçünü yumşaldardı.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

from src.build_dataset import load_jsonl

#: İkinci annotatorun verə biləcəyi cavablar.
LABELS = ("düzgün", "səhv", "qeyri-səlis")


def stratified_sample(
    dataset: dict[str, dict[str, Any]], size: int, seed: int = 0
) -> list[str]:
    """Mənşəyə görə təbəqələndirilmiş nümunə.

    Kvota mənşənin datasetdəki payına uyğundur, amma hər mənşədən ən azı bir
    sətir götürülür: kiçik mənşə tamamilə düşsəydi, onun barədə heç nə
    deyilə bilməzdi.
    """
    rng = random.Random(seed)
    by_origin: dict[str, list[str]] = defaultdict(list)
    for record_id, record in dataset.items():
        by_origin[str(record.get("provenance", "?"))].append(record_id)

    total = len(dataset) or 1
    chosen: list[str] = []
    for origin, ids in sorted(by_origin.items()):
        ids = sorted(ids)
        rng.shuffle(ids)
        quota = max(1, round(size * len(ids) / total))
        chosen.extend(ids[:quota])

    rng.shuffle(chosen)
    return chosen[:size]


def write_sample(
    dataset: dict[str, dict[str, Any]], ids: Sequence[str], path: Path
) -> int:
    """İkinci annotator üçün fayl: BİRİNCİNİN QƏRARI OLMADAN.

    `verified_by`, `notes` və `source` sahələri QƏSDƏN çıxarılır. `notes`
    şablon adını, `source` isə mənbə linkini saxlayır; hər ikisi ikinci
    annotatora ipucu verə bilər.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record_id in ids:
            record = dataset[record_id]
            handle.write(
                json.dumps(
                    {
                        "id": record_id,
                        "question_az": record.get("question_az", ""),
                        "answer": record.get("answer", ""),
                        "answer_en": record.get("answer_en", ""),
                        "category": record.get("category", ""),
                        "label": "",
                        "comment": "",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return len(ids)


def cohen_kappa(first: Sequence[str], second: Sequence[str]) -> float:
    """Cohen kappa: təsadüfdən ARTIQ razılıq.

    NİYƏ XAM FAİZ KİFAYƏT ETMİR. Datasetin demək olar hamısı düzgündür, ona
    görə hər iki annotator kor-koranə "düzgün" desə, razılıq 95%+ çıxar və
    heç nə göstərməz. Kappa gözlənilən təsadüfi razılığı çıxarır.

        kappa = (müşahidə - gözlənilən) / (1 - gözlənilən)

    Sıfır: təsadüfdən yaxşı deyil. Bir: tam razılıq. Mənfi: təsadüfdən pis.
    """
    if len(first) != len(second):
        raise ValueError("iki siyahının uzunluğu fərqlidir")
    n = len(first)
    if n == 0:
        raise ValueError("boş siyahı")

    observed = sum(1 for a, b in zip(first, second, strict=True) if a == b) / n

    count_first = Counter(first)
    count_second = Counter(second)
    expected = sum(
        (count_first[label] / n) * (count_second[label] / n)
        for label in set(count_first) | set(count_second)
    )
    if expected == 1.0:
        # Hər iki annotator TƏK bir etiket işlədib. Kappa təyin olunmur:
        # məxrəc sıfırdır. Bu, razılığın mükəmməl olduğunu göstərmir, ölçünün
        # qurula bilmədiyini göstərir.
        return float("nan")
    return (observed - expected) / (1 - expected)


def interpret(kappa: float) -> str:
    """Kappa üçün standart oxunuş (Landis & Koch şkalası).

    Şkala KOBUDDUR və bunu yazmaq lazımdır: sərhədlər konvensiyadır, təbiət
    qanunu deyil. Rəqəmin özü həmişə yanında verilir.
    """
    if kappa != kappa:  # NaN
        return "təyin olunmur (bir annotator tək etiket işlədib)"
    if kappa < 0.0:
        return "təsadüfdən PİS"
    if kappa < 0.20:
        return "cüzi"
    if kappa < 0.40:
        return "zəif"
    if kappa < 0.60:
        return "orta"
    if kappa < 0.80:
        return "əhəmiyyətli"
    return "demək olar tam"


def build_report(
    dataset: dict[str, dict[str, Any]],
    answers: dict[str, dict[str, str]],
    seed: int = 0,
) -> str:
    """Razılıq hesabatı.

    BİRİNCİ ANNOTATORUN ETİKETİ NƏDİR. Datasetdə olan hər sətir birinci
    annotator tərəfindən qəbul edilib, yəni onun etiketi həmişə `düzgün`-dür.
    Bu, ölçünün ZƏİF nöqtəsidir və gizlədilmir: kappa yalnız ikinci
    annotatorun nə qədər `səhv` dediyindən asılı olur.

    Buna baxmayaraq ölçü mənalıdır, çünki əsl sual budur: müstəqil adam eyni
    sətirlərə baxıb nə qədərini rədd edir? Yüksək rədd nisbəti datasetin
    keyfiyyət iddiasını birbaşa zəiflədir.
    """
    labelled = {
        record_id: row["label"]
        for record_id, row in answers.items()
        if row.get("label") in LABELS
    }
    if not labelled:
        return "_İkinci annotator hələ heç nə etiketləməyib._\n"

    ids = sorted(labelled)
    second = [labelled[i] for i in ids]
    first = ["düzgün"] * len(ids)  # datasetdə olan sətir qəbul edilmiş sətirdir

    counts = Counter(second)
    kappa = cohen_kappa(first, second)
    agreement = 100 * counts["düzgün"] / len(ids)

    lines = [
        "# Annotatorlararası razılıq",
        "",
        f"Nümunə: {len(ids)} sətir, mənşəyə görə təbəqələndirilib (seed={seed}).",
        "",
        "| İkinci annotatorun qərarı | n | pay |",
        "|---|---|---|",
    ]
    for label in LABELS:
        n = counts.get(label, 0)
        lines.append(f"| {label} | {n} | {100 * n / len(ids):.1f}% |")

    lines += [
        "",
        f"**Razılıq: {agreement:.1f}%.** Cohen kappa: "
        f"{'təyin olunmur' if kappa != kappa else f'{kappa:.3f}'} "
        f"({interpret(kappa)}).",
        "",
        "## Bu rəqəmi necə oxumaq lazımdır",
        "",
        "Birinci annotatorun etiketi HƏMİŞƏ `düzgün`-dür, çünki datasetdə olan",
        "sətir onun tərəfindən artıq qəbul edilib. Bu, ölçünün zəif nöqtəsidir",
        "və gizlədilmir: kappa yalnız ikinci annotatorun nə qədər `səhv`",
        "dediyindən asılı olur, iki müstəqil qərar paylanmasından yox.",
        "",
        "Buna baxmayaraq rəqəm mənalıdır, çünki əsl sual budur: **müstəqil adam",
        "eyni sətirlərə baxıb nə qədərini rədd edir?** Yüksək rədd nisbəti",
        "datasetin keyfiyyət iddiasını birbaşa zəiflədir; aşağı rədd nisbəti isə",
        "onu müstəqil şəkildə dəstəkləyir.",
        "",
        "TAM SİMMETRİK ÖLÇÜ üçün hər iki annotator eyni sətirləri SIFIRDAN,",
        "bir-birindən xəbərsiz yoxlamalı idi. Bu, gələcək iş üçün qeyd edilir.",
        "",
    ]

    rejected = [i for i in ids if labelled[i] != "düzgün"]
    if rejected:
        lines += ["## Rədd edilən və ya şübhəli sətirlər", ""]
        for record_id in rejected[:40]:
            record = dataset.get(record_id, {})
            comment = answers[record_id].get("comment", "").strip()
            lines.append(
                f"- `{record_id}` [{labelled[record_id]}] "
                f"{record.get('question_az', '')[:70]} -> "
                f"{record.get('answer', '')}"
                + (f" — _{comment}_" if comment else "")
            )
        lines.append("")
        lines += [
            "Bu sətirlər AVTOMATİK silinmir. Hər biri əl ilə baxılmalı və",
            "ya düzəldilməli, ya da `verified_by: rejected` edilməlidir.",
            "",
        ]

    by_origin: dict[str, list[str]] = defaultdict(list)
    for record_id in ids:
        by_origin[str(dataset.get(record_id, {}).get("provenance", "?"))].append(
            labelled[record_id]
        )
    lines += ["## Mənşəyə görə", "", "| Mənşə | n | düzgün |", "|---|---|---|"]
    for origin, values in sorted(by_origin.items()):
        ok = sum(1 for v in values if v == "düzgün")
        lines.append(f"| `{origin}` | {len(values)} | {100 * ok / len(values):.1f}% |")
    lines.append("")

    return "\n".join(lines)


def write_csv(
    dataset: dict[str, dict[str, Any]], ids: Sequence[str], path: Path
) -> int:
    """Eyni nümunə, amma CSV — ikinci annotator Excel-də doldura bilsin.

    NİYƏ CSV. JSONL faylını əl ilə redaktə etmək texniki adam tələb edir,
    ikinci annotator isə sadəcə azərbaycanca bilən adamdır. Windows konsolu
    da azərbaycan hərflərində problem çıxarır, yəni terminal aləti də uyğun
    deyil. Excel hər ikisini həll edir.

    `utf-8-sig` kodlaşdırması QƏSDƏNDİR: BOM olmadan Excel azərbaycan
    hərflərini pozur.

    DÜSTUR İNYEKSİYASINDAN QORUMA. Excel `=`, `-`, `+`, `@` ilə başlayan
    xanani DÜSTUR sanır. Azərbaycan dilində şəkilçi cavabları məhz tire ilə
    başlayır (`-ki`, `-y`, `-acaq`), yəni bu, nadir hal deyil, DÜZ MƏRKƏZƏ
    dəyir.

    ÖLÇÜLDÜ: birinci ixracda `az-631` (`-y`) və `az-647` (`-ki`) Excel-də
    `#NAME?` kimi göründü və ikinci annotator onları haqlı olaraq səhv saydı.
    Yəni qüsur datasetdə deyil, ixracda idi və ölçünü korlayırdı.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["id", "sual", "cavab", "kateqoriya", "qərar", "qeyd"]
        )
        for record_id in ids:
            record = dataset[record_id]
            writer.writerow(
                [
                    record_id,
                    excel_safe(record.get("question_az", "")),
                    excel_safe(record.get("answer", "")),
                    record.get("category", ""),
                    "",
                    "",
                ]
            )
    return len(ids)


#: Excel bu simvollarla başlayan xanani düstur sanır.
_FORMULA_START = ("=", "-", "+", "@")


def excel_safe(value: str) -> str:
    """Excel-in düstur sandığı dəyəri mətn kimi qorumaq.

    Qabaqda tək dırnaq Excel-ə "bu, mətndir" deyir və xanada GÖRÜNMÜR.
    Faylı geri oxuyanda da problem olmur, çünki biz yalnız `qərar` və `qeyd`
    sütunlarını oxuyuruq.

    Alternativ (dəyəri dırnağa almaq) İŞLƏMİR: Excel dırnağı CSV sintaksisi
    sayır və içəridəki tireni yenə düstur kimi oxuyur.
    """
    text = str(value)
    return "	" + text if text.startswith(_FORMULA_START) else text


def load_answers(path: Path) -> dict[str, dict[str, str]]:
    """Etiketləri oxuyur; həm JSONL, həm CSV qəbul edilir."""
    if not path.exists():
        return {}
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return {
                row["id"]: {
                    "id": row["id"],
                    "label": (row.get("qərar") or "").strip(),
                    "comment": (row.get("qeyd") or "").strip(),
                }
                for row in csv.DictReader(handle)
                if (row.get("id") or "").strip()
            }
    return {
        row["id"]: row
        for _, row in load_jsonl(path)
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="agreement")
    parser.add_argument("command", choices=("sample", "score"))
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument(
        "--out", type=Path, default=Path("results/agreement/second_annotator.jsonl")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("results/agreement/agreement.md")
    )
    parser.add_argument("--size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    if not dataset:
        print(f"Dataset boşdur: {args.dataset}", file=sys.stderr)
        return 1

    if args.command == "sample":
        if args.out.exists():
            print(
                f"{args.out} artıq var. Üstündən yazmaq etiketləri itirər; "
                "başqa ad ver və ya faylı özün sil.",
                file=sys.stderr,
            )
            return 1
        ids = stratified_sample(dataset, args.size, args.seed)
        if args.out.suffix.lower() == ".csv":
            count = write_csv(dataset, ids, args.out)
        else:
            count = write_sample(dataset, ids, args.out)
        print(f"{count} sətir -> {args.out}")
        print()
        print("İKİNCİ ANNOTATOR ÜÇÜN TƏLİMAT:")
        print("  Hər sətirdə `label` sahəsini doldur:")
        for label in LABELS:
            print(f"    {label}")
        print("  Şübhən varsa `comment` sahəsinə qeyd yaz.")
        print()
        print("  MÜHÜMDÜR: bu faylda birinci annotatorun qərarı YOXDUR.")
        print("  Datasetə baxma, internetdə axtarma qadağan deyil, amma")
        print("  qərarı ÖZÜN ver.")
        print()
        print(f"Doldurduqdan sonra: python -m src.agreement score")
        return 0

    answers = load_answers(args.out)
    if not answers:
        print(f"Etiket faylı yoxdur və ya boşdur: {args.out}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(dataset, answers, args.seed)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
