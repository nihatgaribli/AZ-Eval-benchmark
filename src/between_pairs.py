"""Cütlər ARASI iddianı sınayır: kiril hədəflər latınlardan fərqlənirmi.

    python -m src.between_pairs

NİYƏ AYRICA MODUL. `analyze.py`-nin təsdiqləyici ailəsi 88 testdir və hamısı
CÜT DAXİLİNDƏDİR: baza modeli ilə köklənmiş model eyni cütün içində
müqayisə olunur. Məqalənin başlıq iddiası isə cütlər ARASINDADIR: kiril
hədəfli adaptasiyalar azərbaycancaya zərər verir, latın hədəflilər yox.
O iddianın arxasında indiyə qədər yalnız 8/9 sayımı dururdu, test yox.
Sayım nə interval verir, nə də rəqib izahla müqayisə imkanı.

ƏN VACİB İŞİ: RƏQİB İZAHI DA SINAYIR. Zərər verən dörd cütün hamısının
bazası Qwen-dir, zərər verməyən dörd cütün heç birininki deyil. Yəni
"hədəf kirildir" və "bazası Qwen-dir" bu dizaynda demək olar ki, eyni
proqnozu verir. Bunu gizlətmək olmaz; ölçmək lazımdır. Modul hər iki izahı
EYNİ testdən keçirir və p qiymətlərini yan-yana yazır.

TEST DƏQİQDİR, TƏXMİNİ DEYİL. Doqquz cüt 5/4 bölünəndə cəmi 126 düzülüş
var, ona görə permutasiyaların hamısı sayılır. Bootstrap və ya təsadüfi
permutasiya burada mənasızdır: hesablama onsuz da tamdır.

NƏ SÜBUT ETMİR. n=9-dur. 5/4 bölgüdə iki tərəfli p-nin ala biləcəyi ƏN
KİÇİK qiymət 1/126 = 0.0079-dur, yəni bu dizayn ondan aşağı heç nə göstərə
bilməz, nə qədər güclü effekt olsa da. Bu, testin məhdudiyyətidir və
cədvəldə açıq yazılır.

(Bərabər bölgüdə hədd 2/total olardı, çünki tamamlayıcı çoxluq da eyni
ölçüdə olub sadalanmaya girərdi. 5-ə qarşı 4-də girmir.)
"""

from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Sequence

from src.build_dataset import load_jsonl
from src.figures import load_runs, pair_stats

#: Bir cüt hər iki üslubda ölçülə bilər, ona görə "hansını götürək" sualı
#: qaçılmazdır. CAVAB BİRDƏN ÇOXDUR və nəticə seçimdən ASILIDIR: `Rus 2`
#: `default`-da +2.2 (interval sıfırı kəsir), `oneshot`-da +8.3 (kəsmir).
#: Bir qayda seçib susmaq həmin asılılığı gizlətmək olardı, ona görə modul
#: hər iki qaydanı işlədir və fərqi cədvəldə yazır.
STYLE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("`default` üstün", ("default", "oneshot")),
    ("`oneshot` üstün", ("oneshot", "default")),
)


def measure_styles(dataset, all_runs, seed: int = 0) -> dict[str, dict[str, Any]]:
    """Üslub -> {cüt etiketi -> sətir}, yalnız qapıdan keçən cütlər."""
    out: dict[str, dict[str, Any]] = {}
    for style in ("default", "oneshot"):
        runs = {
            (r.key.model, r.key.language): r
            for r in all_runs
            if r.key.prompt_style == style
        }
        rows = pair_stats(dataset, runs, seed)
        out[style] = {r["pair"].label: r for r in rows if r.get("excluded") is None}
    return out


def collect(by_style: dict[str, dict[str, Any]], order: Sequence[str]) -> list[dict[str, Any]]:
    """Verilmiş üstünlük sırasına görə hər cüt üçün bir sətir.

    Seçim üslubun VERDİYİ RƏQƏMƏ baxmadan edilir, yalnız sıraya və qapıya
    görə, yoxsa bu, nəticəyə görə üslub seçmək olardı.
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for style in order:
        for label, row in by_style.get(style, {}).items():
            if label in seen:
                continue
            seen.add(label)
            out.append({**row, "style": style})
    out.sort(key=lambda r: -r["excess"])
    return out


def exact_permutation(
    values: Sequence[float],
    in_group: Sequence[bool],
    statistic: Callable[[Sequence[float], Sequence[float]], float],
) -> tuple[float, float, int]:
    """(müşahidə, iki tərəfli dəqiq p, düzülüş sayı).

    Qrup etiketləri bütün mümkün yollarla paylanır və müşahidə olunan
    statistikadan ZƏİF OLMAYAN nəticələrin payı hesablanır.
    """
    n = len(values)
    k = sum(in_group)
    if k == 0 or k == n:
        raise ValueError("qrup boş və ya hamısını əhatə edir, test mənasızdır")

    def stat(idx: tuple[int, ...]) -> float:
        inside = [values[i] for i in idx]
        outside = [values[i] for i in range(n) if i not in idx]
        return statistic(inside, outside)

    observed_idx = tuple(i for i, flag in enumerate(in_group) if flag)
    observed = stat(observed_idx)
    total = 0
    extreme = 0
    for combo in combinations(range(n), k):
        total += 1
        if abs(stat(combo)) >= abs(observed) - 1e-9:
            extreme += 1
    return observed, extreme / total, total


def diff_in_means(inside: Sequence[float], outside: Sequence[float]) -> float:
    return mean(inside) - mean(outside)


def diff_in_mean_ranks(
    inside: Sequence[float], outside: Sequence[float]
) -> float:
    """Sıraya əsaslanan variant, bir kənar dəyər nəticəni sürükləməsin deyə.

    `Türk 1` -16.0-dadır, çünki ingiliscəsi çöküb. Ortalar üzərində o, öz
    qazanmadığı çəkini daşıyır; sıralarda daşımır.
    """
    pool = sorted(list(inside) + list(outside))
    rank = {}
    for i, v in enumerate(pool):
        rank.setdefault(v, i + 1)
    return mean(rank[v] for v in inside) - mean(rank[v] for v in outside)


#: Sınanan izahlar. Hər biri bir cüt üçün "zərər gözlənilirmi" deyir.
#: `Qwen` sətri MÜDAFİƏ ÜÇÜN DEYİL, ƏLEYHİMİZƏ sınaqdır: əgər o da eyni
#: qədər yaxşı işləyirsə, dizayn iki izahı ayıra bilmir və bunu yazmaq
#: lazımdır.
ACCOUNTS: tuple[tuple[str, Callable[[Any], bool]], ...] = (
    ("hədəfin yazısı kirildir", lambda r: r["pair"].script == "kiril"),
    ("bazanın ailəsi Qwen-dir", lambda r: r["pair"].base_family == "Qwen"),
    (
        "adaptasiya güclüdür (|AZ|+|EN| > 3.5)",
        lambda r: abs(r["az_loss"]) + abs(r["en_loss"]) > 3.5,
    ),
    ("hədəf dil azərbaycancaya qohumdur", lambda r: r["pair"].target in {"qazax", "türk"}),
)


def is_damaged(row: dict[str, Any]) -> bool:
    """Cüt azərbaycancaya ZƏRƏR verirmi.

    İKİ ŞƏRT LAZIMDIR, biri yox. Artıq zərər FƏRQ metrikidir və hər iki dil
    yüksələndə də müsbət çıxa bilər. `Latın 5` (fransız) məhz belədir:
    azərbaycanca 6.5%-dən 10.7%-ə QALXIR, ingiliscə 28.6%-dən 38.8%-ə. Artıq
    zərər +6.1-dir, çünki ingiliscə daha çox qazanıb, amma azərbaycancaya
    dəyən zərər YOXDUR.

    Ona görə interval sıfırı kəsməməlidir VƏ azərbaycanca faktiki olaraq
    aşağı düşməlidir. Bu şərt `Trendyol` halının güzgüsüdür: orada mənfi
    artıq zərər "qorunub" kimi oxunurdu, halbuki ingiliscə çökmüşdü.
    """
    return row["low"] > 0 and row["az_loss"] > 0


def test_accounts(rows: Sequence[dict[str, Any]]) -> list[tuple[str, int, float, float, float, int]]:
    """Hər izah üçün (ad, doğru proqnoz, müşahidə, p_orta, p_sıra, düzülüş)."""
    values = [r["excess"] for r in rows]
    damaged = [is_damaged(r) for r in rows]
    results = []
    for name, predicate in ACCOUNTS:
        in_group = [predicate(r) for r in rows]
        if not any(in_group) or all(in_group):
            continue
        correct = sum(1 for flag, dmg in zip(in_group, damaged) if flag == dmg)
        obs, p_mean, total = exact_permutation(values, in_group, diff_in_means)
        _, p_rank, _ = exact_permutation(values, in_group, diff_in_mean_ranks)
        results.append((name, correct, obs, p_mean, p_rank, total))
    return results


def sensitivity_section(by_style: dict[str, dict[str, Any]]) -> list[str]:
    """Nəticə üslub seçimi qaydasından nə qədər asılıdır.

    BU BÖLMƏ MƏQALƏNİN ƏN ZƏİF YERİNİ ÖLÇÜR. `Rus 2` `default`-da sıfırdan
    ayırd edilmir, `oneshot`-da ayırd edilir; deməli "beş kirildən dördü
    zərər verir" sayımı hansı üslubun götürülməsindən asılıdır.
    """
    lines = [
        "## Üslub seçiminə həssaslıq",
        "",
        "Bir cüt hər iki üslubda ölçülə bilər. Hansının götürülməsi",
        "NƏTİCƏNİ DƏYİŞİR, ona görə hər iki qayda hesablanır.",
        "",
        "| Qayda | Cüt | Yazı izahı doğru | p (orta) | Qwen izahı doğru | p (orta) |",
        "|---|---|---|---|---|---|",
    ]
    for rule_name, order in STYLE_RULES:
        rows = collect(by_style, order)
        if len(rows) < 4:
            continue
        res = {r[0]: r for r in test_accounts(rows)}
        script = next((v for k, v in res.items() if "kiril" in k), None)
        rival = next((v for k, v in res.items() if "Qwen" in k), None)
        if not script or not rival:
            continue
        lines.append(
            f"| {rule_name} | {len(rows)} | {script[1]}/{len(rows)} | "
            f"{script[3]:.4f} | {rival[1]}/{len(rows)} | {rival[3]:.4f} |"
        )
    lines += [
        "",
        "Sayım qayda ilə dəyişir, İŞARƏ dəyişmir. Məqalə iddianı ona görə",
        "istiqamət və əhəmiyyət səviyyəsində saxlayır, kəmiyyət səviyyəsində",
        "yox.",
        "",
    ]
    return lines


def build_table(rows: Sequence[dict[str, Any]], by_style: dict[str, dict[str, Any]] | None = None) -> str:
    values = [r["excess"] for r in rows]
    labels = [r["pair"].label_en or r["pair"].label for r in rows]
    damaged = [is_damaged(r) for r in rows]

    lines = [
        "# Cütlər arası: yazı, yoxsa başqa nə?",
        "",
        "`analyze.py`-nin təsdiqləyici ailəsi cüt DAXİLİNDƏ ölçür. Bu cədvəl",
        "cütlər ARASINDAKI iddianı sınayır və rəqib izahları eyni testdən",
        "keçirir.",
        "",
        "Test dəqiq permutasiyadır: qrup etiketləri bütün mümkün yollarla",
        "paylanır, təxmin yoxdur.",
        "",
        f"Ölçülən cüt sayı: **{len(rows)}**.",
        "",
        "| Cüt | Üslub | Artıq zərər | 95% CI | Zərər? | Yazı | Baza ailəsi |",
        "|---|---|---|---|---|---|---|",
    ]
    for r, dmg in zip(rows, damaged):
        pair = r["pair"]
        lines.append(
            f"| {pair.label_en or pair.label} | `{r['style']}` | "
            f"{r['excess']:+.1f}pp | [{r['low']:+.1f}, {r['high']:+.1f}] | "
            f"{'**bəli**' if dmg else 'xeyr'} | "
            f"{pair.script_en or pair.script} | {pair.base_family} |"
        )

    lines += [
        "",
        "## Rəqib izahlar, eyni testdə",
        "",
        "Hər sətir bir izahı yoxlayır: həmin izahın zərər gözlədiyi cütlərin",
        "artıq zərəri qalanlardan fərqlənirmi?",
        "",
        "| İzah | Doğru proqnoz | Orta fərq | p (orta) | p (sıra) |",
        "|---|---|---|---|---|",
    ]

    results = test_accounts(rows)
    total = results[0][5] if results else 0
    for name, correct, obs_m, p_mean, p_rank, _ in results:
        lines.append(
            f"| {name} | {correct}/{len(rows)} | {obs_m:+.2f}pp | "
            f"{p_mean:.4f} | {p_rank:.4f} |"
        )

    # Ən kiçik p 1/total-dır, 2/total deyil: müşahidə olunan düzülüş həmişə
    # özünü sayır, TAMAMLAYICI çoxluq isə fərqli ölçüdə olduğu üçün (5-ə
    # qarşı 4) sadalanmaya ümumiyyətlə girmir. Bərabər bölgüdə 2/total
    # olardı; burada olmur.
    floor = 1 / total if total else 0.0
    lines += [
        "",
        f"Bu bölgüdə iki tərəfli p-nin ala biləcəyi ƏN KİÇİK qiymət",
        f"**{floor:.4f}**-dir ({total} düzülüş). Effekt nə qədər güclü olsa da,",
        "bu dizayn ondan aşağı heç nə göstərə bilməz.",
        "",
    ]

    script = next((r for r in results if "kiril" in r[0]), None)
    rival = next((r for r in results if "Qwen" in r[0]), None)
    if script and rival:
        damaged_rows = [r for r, d in zip(rows, damaged) if d]
        all_qwen = bool(damaged_rows) and all(
            r["pair"].base_family == "Qwen" for r in damaged_rows
        )
        lines += [
            "## Baza modeli konfaundu",
            "",
            f"Yazı izahı {script[1]}/{len(rows)}, baza ailəsi izahı"
            f" {rival[1]}/{len(rows)} doğru proqnoz verir;"
            f" p qiymətləri {script[3]:.4f} və {rival[3]:.4f}.",
            "",
        ]
        if all_qwen:
            lines += [
                "**Zərər verən cütlərin HAMISININ bazası Qwen-dir.** Bu, p",
                "qiymətlərinin nə qədər yaxın olmasından asılı olmayan struktur",
                "faktdır: dizayn yazı ilə baza ailəsini tam ayıra bilmir.",
                "",
                "Ayırıcı təcrübə **Qwen bazası + latın hədəf**dir. Yazı izahı",
                "orada zərər GÖZLƏMİR, baza izahı GÖZLƏYİR. Macar cütü",
                "(`Racka-4B`, Qwen3-4B üzərində, latın hədəf) məhz bu idi və",
                "sual-təkrarı qapısından keçmədi, yəni məsələni həll edəcək cüt",
                "artıq tapılmışdı, sadəcə ölçülə bilmədi.",
                "",
                "İkinci yol: Qwen olmayan bazada zərər VERƏN kiril cütü. Hazırda",
                "yeganə Qwen olmayan kiril cütü (gemma + ukraynaca) zərər vermir,",
                "yəni o, baza izahının proqnozuna da uyğun gəlir.",
                "",
            ]
        else:
            lines += [
                "Zərər verən cütlərin bazaları eyni ailədən deyil, yəni baza",
                "ailəsi konfaundu bu ölçmədə qırılıb.",
                "",
            ]
    if by_style:
        lines += sensitivity_section(by_style)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="between_pairs")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument(
        "--out", type=Path, default=Path("results/tables/between_pairs.md")
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    by_style = measure_styles(dataset, load_runs(args.raw_dir), args.seed)
    rows = collect(by_style, STYLE_RULES[0][1])
    if len(rows) < 4:
        print("çox az cüt ölçülür, test qurulmur", file=sys.stderr)
        return 1

    table = build_table(rows, by_style)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(table + "\n", encoding="utf-8")
    print(table)
    print("\n-> " + str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
