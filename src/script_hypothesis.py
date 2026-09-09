"""Əlifba fərziyyəsinin sınağı: fərq artefaktdır, yoxsa real zəiflik?

    python -m src.script_hypothesis

SUAL. Qolda azərbaycanca STRICT rejimdə bazadan xeyli aşağıdır. İki fərqli
izah var və ikisi də eyni rəqəmi verir:

  ARTEFAKT   modelin bildiyi cavab doğrudur, sadəcə kirillə yazılır və
             sətir müqayisəsi onu səhv sayır.
  ZƏİFLİK    model faktı bilmir; əlifba ikinci dərəcəli məsələdir.

Bu modul ikisini bir-birindən ayıran İKİ MÜSTƏQİL sınaq aparır:

  1. NORMALİZASİYA NƏRDİVANI (yeni inference tələb etmir)
     STRICT -> MORPH -> LENIENT -> TRANSLIT zənciri hər addımda bir çevirmə
     əlavə edir. Fərq TRANSLIT-də yox olursa, ölçülən şey bilikdən çox yazı
     sistemi idi.

  2. ƏLİFBANIN MƏCBUR EDİLMƏSİ (yeni inference tələb edir)
     Eyni suallar "latın əlifbası ilə cavab ver" promptu ilə təkrarlanır.
     Model latına keçib DOĞRU cavab verirsə, artefakt təsdiqlənir; latına
     keçib yenə səhv edirsə, zəiflik təsdiqlənir.

İki sınaq bir-birini yoxlayır. Yalnız birincisi aparılsa, etiraz açıq qalır:
"transliterasiya balı süni qaldırır". Yalnız ikincisi aparılsa, başqa etiraz
açıq qalır: "prompt sualın özünü də asanlaşdırmış ola bilər".

NİYƏ AYRI QOVLUQ. Xam cavablar `results/script_hypothesis/generations/`
altındadır, `results/raw_outputs/` altında yox. Səbəb texniki deyil, statistik:
`analyze.py` gördüyü hər qaçışı Holm ailəsinə salır, ailə böyüyəndə isə ƏSAS
cədvəllərin bütün p qiymətləri sürüşür. Bu modulun sualı ayrı sualdır və əsas
cədvəllərin rəqəmlərini dəyişməməlidir.

Nəticələr: `results/script_hypothesis/` altında `tables.md` və `config.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from src.analyze import (
    Run,
    _column,
    load_runs,
    markdown_table,
    run_label,
    score_run,
)
from src.build_dataset import load_jsonl
from src.metrics import (
    MODES,
    STRICT,
    TRANSLIT,
    bootstrap_ci,
    compare_paired,
    holm_correction,
)

BASE_MODEL = "Qwen/Qwen3-VL-4B-Thinking"
TUNED_MODEL = "issai/Qolda-AVL-5B"

#: Kiril əlifbası bloku. Cavabda ƏN AZI bir belə hərf varsa, sətir kirilə aid
#: sayılır: qarışıq yazı (latın rəqəm + kiril söz) da bura düşür, çünki sətir
#: müqayisəsi onu da uğursuz sayacaq.
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

N_RESAMPLES = 1000


@dataclass(frozen=True)
class Cell:
    """2x2 matrisinin bir xanası: model x prompt üslubu."""

    model: str
    prompt_style: str


CELLS = [
    Cell(BASE_MODEL, "default"),
    Cell(BASE_MODEL, "script"),
    Cell(TUNED_MODEL, "default"),
    Cell(TUNED_MODEL, "script"),
]


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _pp(value: float) -> str:
    return f"{100 * value:+.1f}pp"


def _ci(low: float, high: float) -> str:
    return f"[{100 * low:.1f}, {100 * high:.1f}]"


def load_cells(
    raw_dir: Path, dataset: dict[str, Any]
) -> tuple[dict[Cell, Run], list[str]]:
    """Dörd xananı yükləyir və ORTAQ id siyahısını qaytarır.

    Ortaq siyahı məcburidir. Xanaların id dəstləri fərqlənsə, rəqəmlər fərqli
    suallar üzərində hesablanar və sətirlər arasındakı fərq həm modeldən, həm
    də sual dəstindən gələ bilər. Hansının nə qədər pay verdiyi isə ayırd
    edilə bilməz.
    """
    runs: dict[Cell, Run] = {}
    for run in load_runs(raw_dir):
        if run.key.language != "az":
            continue
        runs[Cell(run.key.model, run.key.prompt_style)] = run

    missing = [c for c in CELLS if c not in runs]
    if missing:
        names = ", ".join(f"{c.model} [{c.prompt_style}]" for c in missing)
        raise SystemExit(
            f"2x2 tamamlanmayıb, çatışmayan xana(lar): {names}\nQovluq: {raw_dir}"
        )

    common = set(dataset)
    for cell in CELLS:
        common &= runs[cell].ids
    return runs, sorted(common)


def matrix_table(runs: dict[Cell, Run], dataset, ids) -> str:
    """2x2 bir baxışda: sətir model, sütun prompt, xanada STRICT / TRANSLIT.

    İki rəqəm bir xanada verilir, çünki sualın cavabı məhz onların ARASINDAKI
    məsafədədir: böyük məsafə yazı sistemi problemi, kiçik məsafə bilik
    problemi deməkdir.
    """
    rows = []
    for model in (BASE_MODEL, TUNED_MODEL):
        cells = []
        for prompt_style in ("default", "script"):
            run = runs[Cell(model, prompt_style)]
            strict = _column(score_run(run, dataset, STRICT, ids), "em", ids)
            translit = _column(score_run(run, dataset, TRANSLIT, ids), "em", ids)
            cells.append(
                f"{_pct(sum(strict) / len(strict))} / "
                f"{_pct(sum(translit) / len(translit))}"
            )
        rows.append([model, *cells])
    return markdown_table(
        ["Model (STRICT / TRANSLIT)", "Adi prompt", "Latın tələbi"], rows
    )


def ladder_table(runs: dict[Cell, Run], dataset, ids, seed: int) -> str:
    """Hər xananın balı dörd normalizasiya zəncirində, CI ilə."""
    rows = []
    for cell in CELLS:
        for mode in MODES:
            scores = _column(score_run(runs[cell], dataset, mode, ids), "em", ids)
            ci = bootstrap_ci(scores, n_resamples=N_RESAMPLES, seed=seed)
            rows.append(
                [
                    run_label(runs[cell].key),
                    cell.prompt_style,
                    mode.name,
                    _pct(ci.mean),
                    _ci(ci.low, ci.high),
                ]
            )
    return markdown_table(["Model", "Prompt", "Zəncir", "EM", "95% CI"], rows)


def gap_table(runs: dict[Cell, Run], dataset, ids, seed: int) -> str:
    """ANALİZ 1: baza ilə fine-tune arasındakı fərq zəncir-zəncir.

    "Bağlanan pay" sütunu əsas rəqəmdir: STRICT fərqinin nə qədəri həmin
    zəncirdə itir. Mənfi qiymət fərqin GENİŞLƏNDİYİNİ bildirir və bu, real
    haldır: bir çevirmə iki modelə eyni ölçüdə fayda vermir.
    """
    rows: list[list[Any]] = []
    raw_p: list[float] = []
    strict_gap: dict[str, float] = {}

    for prompt_style in ("default", "script"):
        base = runs[Cell(BASE_MODEL, prompt_style)]
        tuned = runs[Cell(TUNED_MODEL, prompt_style)]
        for mode in MODES:
            a = _column(score_run(base, dataset, mode, ids), "em", ids)
            b = _column(score_run(tuned, dataset, mode, ids), "em", ids)
            result = compare_paired(a, b, n_resamples=N_RESAMPLES, seed=seed)
            if mode is STRICT:
                strict_gap[prompt_style] = result.diff
            reference = strict_gap[prompt_style]
            if mode is STRICT:
                closed = "0%"
            elif abs(reference) < 1e-9:
                closed = "n/a"
            else:
                closed = f"{100 * (reference - result.diff) / reference:.0f}%"
            rows.append(
                [
                    prompt_style,
                    mode.name,
                    _pct(result.mean_a),
                    _pct(result.mean_b),
                    _pp(result.diff),
                    _ci(result.diff_low, result.diff_high),
                    closed,
                ]
            )
            raw_p.append(result.p_value)

    return _with_holm(
        ["Prompt", "Zəncir", "Baza EM", "Qolda EM", "Fərq", "95% CI", "Bağlanan pay"],
        rows,
        raw_p,
    )


def script_effect_table(runs: dict[Cell, Run], dataset, ids, seed: int) -> str:
    """ANALİZ 2: eyni modelin daxilində latın tələbinin təsiri.

    Müqayisə MODEL DAXİLİNDƏ aparılır, modellər arasında yox. Səbəb: sual
    "prompt bu modelin balını qaldırırmı" sualıdır və ona yalnız eyni modelin
    iki qaçışı cavab verə bilər.
    """
    rows: list[list[Any]] = []
    raw_p: list[float] = []
    for model in (BASE_MODEL, TUNED_MODEL):
        default = runs[Cell(model, "default")]
        forced = runs[Cell(model, "script")]
        for mode in MODES:
            a = _column(score_run(forced, dataset, mode, ids), "em", ids)
            b = _column(score_run(default, dataset, mode, ids), "em", ids)
            result = compare_paired(a, b, n_resamples=N_RESAMPLES, seed=seed)
            rows.append(
                [
                    model,
                    mode.name,
                    _pct(result.mean_b),
                    _pct(result.mean_a),
                    _pp(result.diff),
                    _ci(result.diff_low, result.diff_high),
                ]
            )
            raw_p.append(result.p_value)
    return _with_holm(
        ["Model", "Zəncir", "Adi prompt", "Latın tələbi", "Fərq", "95% CI"],
        rows,
        raw_p,
    )


def script_counts_table(runs: dict[Cell, Run], ids) -> str:
    """Kirillə yazılmış cavabların sayı.

    BU RƏQƏM ZƏNCİRDƏN ASILI DEYİL, ona görə cədvəldə zəncir sütunu yoxdur.
    Zəncir balın necə hesablandığını dəyişir, modelin nə yazdığını yox. Zəncir
    üzrə ayrı sətirlər dörd eyni rəqəm verər və oxucuda "transliterasiya cavabı
    dəyişir" təəssüratı yaradardı.
    """
    rows = []
    for cell in CELLS:
        run = runs[cell]
        cyrillic = sum(1 for i in ids if _CYRILLIC.search(run.predictions.get(i, "")))
        rows.append(
            [
                run.key.model,
                cell.prompt_style,
                cyrillic,
                len(ids) - cyrillic,
                f"{100 * cyrillic / len(ids):.1f}%",
            ]
        )
    return markdown_table(["Model", "Prompt", "Kiril", "Latın", "Kiril payı"], rows)


def _with_holm(headers, rows: list[list[Any]], raw_p: list[float]) -> str:
    """Xam p sütununu düzəldilmiş p ilə birlikdə verir.

    Ailə HƏR CƏDVƏL ÜÇÜN AYRIDIR və bu, şüurlu seçimdir: iki cədvəl iki fərqli
    sual verir, onları bir ailəyə yığmaq hər ikisinin gücünü lazımsız azaldar.
    Ailənin ölçüsü cədvəlin altında yazılır ki, oxucu düzəlişin niyə məhz bu
    qədər olduğunu yoxlaya bilsin.
    """
    adjusted = holm_correction(raw_p)
    out = [
        [*row, f"{p:.4f}", f"{p_adj:.4f}", "bəli" if p_adj < 0.05 else "xeyr"]
        for row, p, p_adj in zip(rows, raw_p, adjusted, strict=True)
    ]
    table = markdown_table([*headers, "p", "p (Holm)", "Mənalı"], out)
    return f"{table}\n\n_Holm ailəsi: {len(raw_p)} test._"


def _git_revision() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def build_config(
    dataset_path: Path, raw_dir: Path, runs: dict[Cell, Run], ids, seed: int
) -> dict[str, Any]:
    """Nəticəni təkrar istehsal etmək üçün lazım olan hər şey.

    Xam faylların SHA-sı da daxildir: fayl sonradan dəyişsə, cədvəlin hansı
    məzmuna aid olduğu bilinsin.
    """
    digests = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        for path in sorted(raw_dir.glob("*.jsonl"))
    }
    return {
        "generated": date.today().isoformat(),
        "git_revision": _git_revision(),
        "dataset": str(dataset_path),
        "dataset_sha256_16": hashlib.sha256(dataset_path.read_bytes()).hexdigest()[:16],
        "n_items_common": len(ids),
        "seed": seed,
        "n_resamples": N_RESAMPLES,
        "chains": [m.name for m in MODES],
        "generations_sha256_16": digests,
        "runs": {
            f"{cell.model} [{cell.prompt_style}]": {
                "n_answers": len(runs[cell].ids),
                "provenance": runs[cell].provenance or {"backend": "local"},
            }
            for cell in CELLS
        },
    }


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="script_hypothesis")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument(
        "--raw-dir", type=Path, default=Path("results/script_hypothesis/generations")
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("results/script_hypothesis")
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs, ids = load_cells(args.raw_dir, dataset)
    print(f"{len(ids)} ortaq sual, {len(CELLS)} xana")

    sections = [
        ("2x2 bir baxışda", matrix_table(runs, dataset, ids)),
        (
            "Analiz 1: normalizasiya nərdivanı",
            ladder_table(runs, dataset, ids, args.seed),
        ),
        ("Analiz 1: fərq və bağlanan pay", gap_table(runs, dataset, ids, args.seed)),
        (
            "Analiz 2: latın tələbinin təsiri",
            script_effect_table(runs, dataset, ids, args.seed),
        ),
        ("Yazı sistemi (zəncirdən asılı deyil)", script_counts_table(runs, ids)),
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    body = "\n\n".join(f"## {title}\n\n{table}" for title, table in sections)
    header = (
        "# Əlifba fərziyyəsi\n\n"
        f"Dataset: `{args.dataset}` | ortaq sual: {len(ids)} | "
        f"seed: {args.seed} | bootstrap: {N_RESAMPLES}\n\n"
        "Bütün müqayisələr cütləşdirilib və eyni sual dəsti üzərində aparılıb.\n"
    )
    (args.out_dir / "tables.md").write_text(f"{header}\n{body}\n", encoding="utf-8")

    config = build_config(args.dataset, args.raw_dir, runs, ids, args.seed)
    (args.out_dir / "config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"tables.md, config.json -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
