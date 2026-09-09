"""Şübhəli cavab açarlarını modellərin razılığı ilə tapır.

    python -m src.audit_keys

FİKİR. Müstəqil modellər eyni SƏHVİ etməzlər. Səhvin yolu çoxdur, doğrunun
yolu birdir. Ona görə bir neçə model eyni variantda birləşir, amma açar başqa
variantı göstərirsə, ehtimal ki səhv modellərdə deyil, AÇARDADIR.

Bu, TUMLU-nun məlum problemidir. Məqalənin özü icma mənbəli dillərdə, o
cümlədən azərbaycancada, sualların təxminən 10%-inin yararsız və ya səhv
açarlı olduğunu etiraf edir. Əl ilə yoxlanmış 14 riyaziyyat sualından birində
belə səhv tapıldı: "6 sm və 8 sm tərəfli düzbucaqlının diaqonalı" üçün açar 5
göstərir, doğru cavab isə 10-dur və variantlar arasındadır.

Əl ilə 521 sualı yoxlamaq baha başa gəlir. Bu modul həmin yükü daraldır:
şübhəli sətirləri ayırır ki, insan yalnız onlara baxsın.

MÜSTƏQİLLİK MƏHDUDİYYƏTİ, ƏN VACİB QEYD. Metod modellərin müstəqilliyinə
söykənir, bizim modellər isə tam müstəqil DEYİL:

    Qolda-AVL-5B            Qwen3-VL-4B-Thinking-dən köklənib
    Qwen3-VL-4B-Instruct    eyni ailə
    Qwen3-1.7B              eyni ailə, kiçik

Hamısı bir ailədəndir və eyni ön-təlim datasını böyük ölçüdə paylaşır. Yəni
onlar eyni səhvi ETMƏYƏ MEYLLİDİR və razılıq açarın səhv olduğunu SÜBUT
ETMİR. Nəticə şübhə siyahısıdır, hökm deyil; hər sətir insan tərəfindən
yoxlanmalıdır. Fərqli ailədən model əlavə olunsa, metod xeyli güclənər.

TƏSADÜFİ RAZILIQ DA HESABLANIR. Dörd variantda iki model təsadüfən eyni səhv
variantı seçə bilər. Hesabatda gözlənilən təsadüfi razılıq sayı verilir ki,
tapılan rəqəm ona qarşı oxunsun.

ÖLÇÜLMÜŞ NƏTİCƏ: DÖRD QWEN MODELİ İLƏ METOD İŞLƏMİR.

Dörd model 36 sətirdə (6.9%) açara qarşı birləşdi və bu, təsadüf həddindən
(permutasiya, 95-ci persentil = 12) aydın şəkildə yuxarıdır. Yəni razılıq
təsadüfi deyil. Buna baxmayaraq şübhəlilər ƏL İLƏ yoxlananda yoxlana bilən
hər sətirdə AÇAR DOĞRU, modellər isə səhv çıxdı:

    adrenalini hansı vəzi ifraz edir   açar böyrəküstü (doğru), modellər epifiz
    benzin mühərrikini kim düzəldib    açar Daymler (doğru), modellər Dizel
    dəqiqə əqrəbi sutkada neçə dövr    açar 24 (doğru), modellər 1440
    perimetr 60, fərq 14, tərəflər     açar 8 və 22 (doğru), modellər 9 və 11

Səbəb yuxarıdakı müstəqillik məhdudiyyətidir və indi empirik olaraq
təsdiqlənib. Permutasiya testi TƏSADÜFİ razılığı nəzarətə alır, KORRELYASİYALI
SƏHVİ isə yox. Bir ailədən olan modellər eyni ön-təlim datasından eyni yanlış
faktı öyrənir və birlikdə səhv edirlər; statistik hədd bunu görmür.

NƏ LAZIMDIR: fərqli ailədən modellər (Llama, Gemma, GPT, Claude). Metod
özü sağlamdır, tətbiq edildiyi model dəsti sağlam deyil. Hazırkı nəticə
"TUMLU-nun 36 açarı şübhəlidir" yox, "Qwen ailəsi bu 36 sualda birlikdə səhv
edir" deməkdir; ikincisi də maraqlıdır, amma başqa sualdır.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

from src.format_contrast import LETTERS, letter_of


def load_choices(raw_dir: Path) -> dict[str, dict[str, str]]:
    """model -> {id: seçilmiş hərf}. Yalnız `mcq` şəraiti oxunur."""
    picks: dict[str, dict[str, str]] = defaultdict(dict)
    for path in sorted(raw_dir.glob("*__mcq.jsonl")):
        for line in path.open(encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            letter = letter_of(row["raw_response"])
            if letter:
                picks[row["model"]][row["id"]] = letter
    return dict(picks)


def find_suspects(
    items: Sequence[dict[str, Any]],
    picks: dict[str, dict[str, str]],
    min_models: int = 2,
) -> list[dict[str, Any]]:
    """Bütün modellərin birləşdiyi, amma açardan fərqlənən sətirlər.

    `min_models` ən azı neçə modelin cavab vermiş olmasını tələb edir. Bir
    modelin fikri razılıq deyil.
    """
    by_id = {i["id"]: i for i in items}
    suspects = []
    for record_id, item in by_id.items():
        votes = [p[record_id] for p in picks.values() if record_id in p]
        if len(votes) < min_models:
            continue
        agreed = set(votes)
        if len(agreed) != 1:
            continue
        choice = agreed.pop()
        if choice == item["answer_letter"]:
            continue
        index = LETTERS.index(choice)
        suspects.append(
            {
                "id": record_id,
                "subject": item["subject"],
                "question": item["question_az"],
                "key_letter": item["answer_letter"],
                "key_answer": item["answer"],
                "models_letter": choice,
                "models_answer": item["choices"][index],
                "n_models": len(votes),
            }
        )
    return sorted(suspects, key=lambda s: (s["subject"], s["id"]))


def chance_agreement(n_models: int, n_items: int, options: int = 4) -> float:
    """Modellər müstəqil və bərabər seçsəydi gözlənilən razılıq sayı.

    Kobud hesabdır və yalnız BÖYÜKLÜK SIRASI üçün verilir: modellər nə bərabər
    seçir, nə də müstəqildir. Dəqiq həddi `permutation_null` verir.
    """
    return n_items * (options - 1) * (1 / options) ** n_models


def permutation_null(
    items: Sequence[dict[str, Any]],
    picks: dict[str, dict[str, str]],
    n_permutations: int = 1000,
    seed: int = 0,
) -> tuple[float, float]:
    """Empirik sıfır fərziyyəsi: (orta, 95-ci persentil).

    NİYƏ DÜSTUR KİFAYƏT ETMİR. Modellər hərfləri bərabər seçmir; biri `D`-yə,
    digəri `B`-yə meyllidir. Belə meyl razılığı süni artırır və düsturdakı
    `(1/4)^n` bunu görmür.

    Sıfır fərziyyəsi belə qurulur: hər modelin cavabları öz aralarında
    QARIŞDIRILIR, yəni cavab dəsti olduğu kimi qalır, amma hansı suala aid
    olduğu təsadüfiləşir. Sonra "hamısı birləşir, açardan fərqlənir" hadisəsi
    yenidən sayılır. Beləcə modellərin hərf meyli sıfır fərziyyəsinə DAXİL
    olur və yalnız sual ilə əlaqə itir.
    """
    import random

    rng = random.Random(seed)
    by_id = {i["id"]: i for i in items}
    shared = sorted(set(by_id).intersection(*[set(p) for p in picks.values()]))
    if not shared:
        return 0.0, 0.0

    keys = [by_id[i]["answer_letter"] for i in shared]
    columns = [[picks[m][i] for i in shared] for m in sorted(picks)]

    counts: list[int] = []
    for _ in range(n_permutations):
        shuffled = []
        for column in columns:
            copy = list(column)
            rng.shuffle(copy)
            shuffled.append(copy)
        total = 0
        for index, key in enumerate(keys):
            votes = {column[index] for column in shuffled}
            if len(votes) == 1 and votes.pop() != key:
                total += 1
        counts.append(total)

    counts.sort()
    mean = sum(counts) / len(counts)
    high = counts[int(0.95 * (len(counts) - 1))]
    return mean, float(high)


def report(
    items: Sequence[dict[str, Any]],
    picks: dict[str, dict[str, str]],
    suspects: Sequence[dict[str, Any]],
) -> str:
    models = sorted(picks)
    lines = [
        "# Şübhəli cavab açarları",
        "",
        f"Dəst: {len(items)} sual. Modellər: {len(models)}.",
        "",
    ]
    for model in models:
        lines.append(f"- `{model}` ({len(picks[model])} cavab)")

    expected = chance_agreement(len(models), len(items))
    null_mean, null_high = permutation_null(items, picks)
    lines += [
        "",
        f"**{len(suspects)} sətirdə bütün modellər eyni variantda birləşir, "
        f"amma açar başqasını göstərir** ({100 * len(suspects) / len(items):.1f}%).",
        "",
        f"Kobud düstura görə təsadüfi gözlənti: {expected:.1f}.",
        "",
        f"Permutasiya ilə qurulmuş EMPİRİK sıfır fərziyyəsi: orta "
        f"{null_mean:.1f}, 95-ci persentil {null_high:.0f}. Bu hədd modellərin "
        "hərf meylini də nəzərə alır, ona görə düsturdan etibarlıdır. Tapılan "
        f"{len(suspects)} rəqəmi həmin həddi keçmirsə, razılıq təsadüfdən "
        "ayırd edilmir və siyahı məlumat daşımır.",
        "",
        "DİQQƏT: bu, hökm deyil, şübhə siyahısıdır. Modellərin hamısı Qwen "
        "ailəsindəndir (Qolda məhz Qwen3-VL-dən köklənib), yəni eyni səhvi "
        "etməyə meyllidirlər. Hər sətir insan tərəfindən yoxlanmalıdır.",
        "",
        "**ƏL İLƏ YOXLANDI VƏ SİYAHI ETİBARSIZ ÇIXDI.** Yoxlana bilən hər "
        "şübhəlidə açar DOĞRU, modellər isə səhv oldu (adrenalin, Daymler, "
        "dəqiqə əqrəbi, paraleloqram). Razılıq təsadüfi deyil, amma açarın "
        "səhvindən yox, modellərin ORTAQ səhvindən doğur: permutasiya testi "
        "təsadüfi razılığı nəzarətə alır, korrelyasiyalı səhvi yox. Metodun "
        "işləməsi üçün fərqli ailədən model lazımdır.",
        "",
        "## Fənn üzrə",
        "",
        "| Fənn | Şübhəli |",
        "|---|---|",
    ]
    for subject, count in Counter(s["subject"] for s in suspects).most_common():
        lines.append(f"| {subject} | {count} |")

    lines += ["", "## Sətirlər", ""]
    for suspect in suspects:
        lines += [
            f"### `{suspect['id']}` ({suspect['subject']})",
            "",
            f"{suspect['question']}",
            "",
            f"- açar: **{suspect['key_letter']}** = {suspect['key_answer']}",
            f"- {suspect['n_models']} modelin hamısı: "
            f"**{suspect['models_letter']}** = {suspect['models_answer']}",
            "",
        ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="audit_keys")
    parser.add_argument("--items", type=Path, default=Path("data/tumlu/tumlu_az_short.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/format_contrast"))
    parser.add_argument("--out", type=Path, default=Path("data/tumlu/TUMLU_SUSPECT_KEYS.md"))
    parser.add_argument("--min-models", type=int, default=2)
    args = parser.parse_args(argv)

    items = [
        json.loads(line)
        for line in args.items.open(encoding="utf-8")
        if line.strip()
    ]
    picks = load_choices(args.raw_dir)
    if not picks:
        print(f"`mcq` qaçışı tapılmadı: {args.raw_dir}", file=sys.stderr)
        return 1

    suspects = find_suspects(items, picks, args.min_models)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report(items, picks, suspects), encoding="utf-8")

    expected = chance_agreement(len(picks), len(items))
    print(f"{len(picks)} model, {len(items)} sual")
    print(f"şübhəli açar: {len(suspects)} ({100 * len(suspects) / len(items):.1f}%)")
    print(f"təsadüfdən gözlənilən: {expected:.1f}")
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
