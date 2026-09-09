"""Məqalə şəkillərini XAM MƏLUMATDAN qurur.

    python -m src.figures

NİYƏ MODULDUR. Şəkil əl ilə çəkilsə, cədvəl dəyişəndə səssizcə köhnəlir və
məqalədə bir-birinə zidd iki rəqəm qalır. Burada hər nöqtə qaçış fayllarından
yenidən hesablanır, yəni şəkil cədvəllə ayrıla bilmir.

QAPILAR BURADA DA İŞLƏYİR. Qapıdan keçməyən cüt şəkilə düşmür; onu göstərmək
etibarsız rəqəmi ölçmə kimi təqdim etmək olardı.

ÜSLUB. Rəngkorluğa uyğun palitra (Okabe-Ito), ağ-qara çapda da ayırd edilən
işarə formaları, şəbəkə yoxdur, çərçivə minimaldır. PDF (vektor) və PNG
birlikdə yazılır: LaTeX PDF-i, sürətli baxış PNG-ni işlədir.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.analyze import _column, load_runs, score_run  # noqa: E402
from src.build_dataset import load_jsonl  # noqa: E402
from src.fine_tune_pairs import (  # noqa: E402
    _CYRILLIC,
    PAIRS,
    _common,
    _gate_failure,
)
from src.metrics import STRICT, TRANSLIT, bootstrap_ci, compare_paired  # noqa: E402

#: Rəngkorluğa uyğun palitra (Okabe-Ito).
COLOURS = {
    "kiril": "#D55E00",
    "latın": "#0072B2",
    "qarışıq": "#009E73",
    "digər": "#666666",
}

#: Forma da rəngdən asılı olmayan ayırd etmə verir (ağ-qara çap üçün).
MARKERS = {"kiril": "o", "latın": "s", "qarışıq": "^", "digər": "D"}


def style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.constrained_layout.use": True,
        }
    )


def save(fig, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png"):
        fig.savefig(out_dir / (name + "." + suffix), bbox_inches="tight")
    plt.close(fig)
    print("  -> " + name + ".pdf / .png")


def short(pair) -> str:
    """Şəkildə görünən ad. MƏQALƏ İNGİLİSCƏDİR, ona görə `label_en`."""
    return pair.label_en or pair.label.split(" (")[0]


def pair_stats(dataset, runs, seed: int = 0) -> list[dict[str, Any]]:
    """Hər cüt üçün artıq zərər, interval, kiril payı və mütləq itkilər.

    Qapıdan keçməyən cüt hesablanmır; sətir yalnız səbəbi daşıyır.
    """
    rows: list[dict[str, Any]] = []
    for pair in PAIRS:
        ids = _common(runs, pair, dataset)
        if not ids:
            continue
        failure = _gate_failure(runs, pair, dataset)
        if failure is not None:
            rows.append({"pair": pair, "excluded": failure})
            continue

        def column(model, language, mode=STRICT):
            scored = score_run(runs[(model, language)], dataset, mode, ids)
            return _column(scored, "em", ids)

        base_az, tuned_az = column(pair.base, "az"), column(pair.tuned, "az")
        base_en, tuned_en = column(pair.base, "en"), column(pair.tuned, "en")
        excess = [
            (base_az[i] - tuned_az[i]) - (base_en[i] - tuned_en[i])
            for i in range(len(ids))
        ]
        ci = bootstrap_ci(excess, seed=seed)
        az = compare_paired(base_az, tuned_az, seed=seed)
        en = compare_paired(base_en, tuned_en, seed=seed)
        az_translit = compare_paired(
            column(pair.base, "az", TRANSLIT),
            column(pair.tuned, "az", TRANSLIT),
            seed=seed,
        )
        tuned_run = runs[(pair.tuned, "az")]
        cyr = sum(1 for i in ids if _CYRILLIC.search(tuned_run.predictions[i]))
        rows.append(
            {
                "pair": pair,
                "excluded": None,
                "excess": 100 * ci.mean,
                "low": 100 * ci.low,
                "high": 100 * ci.high,
                "az_loss": 100 * az.diff,
                "az_loss_translit": 100 * az_translit.diff,
                "en_loss": 100 * en.diff,
                "cyrillic": 100 * cyr / len(ids),
                "n": len(ids),
            }
        )
    return rows


def _place_labels(ax, points, x_span, y_span, fontsize=7.5) -> None:
    """Etiketləri toqquşmayacaq şəkildə yerləşdirir.

    Nöqtələrin çoxu x=0 ətrafında toplanır və sabit sürüşmə ilə etiketlər
    bir-birinin üstünə düşür. Burada hər etiket üçün sağda tutulacaq sahə
    hesablanır; sahə doludursa, etiket aşağı sürüşür və lazım gələrsə sola
    keçir.
    """
    taken: list[tuple[float, float, float, float]] = []
    width = 0.16 * x_span
    height = 0.055 * y_span
    for x, y, text in sorted(points, key=lambda p: -p[1]):
        placed = False
        for dx, dy, ha in (
            (0.015 * x_span, 0.0, "left"),
            (0.015 * x_span, -0.06 * y_span, "left"),
            (0.015 * x_span, 0.06 * y_span, "left"),
            (-0.015 * x_span, 0.0, "right"),
            (-0.015 * x_span, -0.06 * y_span, "right"),
        ):
            lx = x + dx if ha == "left" else x + dx - width
            ly = y + dy
            box = (lx, ly - height / 2, lx + width, ly + height / 2)
            if any(
                box[0] < t[2] and t[0] < box[2] and box[1] < t[3] and t[1] < box[3]
                for t in taken
            ):
                continue
            ax.annotate(
                text,
                (x, y),
                xytext=(x + dx, y + dy),
                textcoords="data",
                fontsize=fontsize,
                va="center",
                ha=ha,
            )
            taken.append(box)
            placed = True
            break
        if not placed:
            ax.annotate(
                text,
                (x, y),
                textcoords="offset points",
                xytext=(9, -9),
                fontsize=fontsize,
                va="center",
            )


def figure_marker(by_style: dict[str, list[dict[str, Any]]], out_dir: Path) -> None:
    """Kiril payı vs artıq zərər, hər prompt üslubu üçün ayrıca.

    İKİ PANEL QƏSDƏNDİR. Ayrılma `oneshot` altında qüsursuzdur; `default`
    altında `Rus 2` sıfırdan ayırd edilmir. Tək panel göstərmək üslub
    həssaslığını gizlətmək olardı.
    """
    styles = [s for s in ("default", "oneshot") if by_style.get(s)]
    fig, axes = plt.subplots(
        1, len(styles), figsize=(4.9 * len(styles), 3.8), sharey=True
    )
    if len(styles) == 1:
        axes = [axes]

    # `sharey` olduğuna görə hüdud BİR DƏFƏ, hər iki panelin məlumatından
    # hesablanır. Panel-panel qoyulsaydı, sonuncu birincini üstələyər və
    # `Türk 1` kimi kənar nöqtə səssizcə kadrdan düşərdi.
    every = [r for name in styles for r in by_style[name] if r["excluded"] is None]
    y_lo = min(r["low"] for r in every) - 2
    y_hi = max(r["high"] for r in every) + 2

    for ax, name in zip(axes, styles):
        good = [r for r in by_style[name] if r["excluded"] is None]
        ax.axhline(0, color="#999999", lw=0.8, zorder=1)
        labels = []
        for r in good:
            script = r["pair"].script
            ax.errorbar(
                r["cyrillic"],
                r["excess"],
                yerr=[[r["excess"] - r["low"]], [r["high"] - r["excess"]]],
                fmt=MARKERS.get(script, "D"),
                color=COLOURS.get(script, COLOURS["digər"]),
                markersize=7,
                capsize=3,
                lw=1.2,
                zorder=3,
            )
            labels.append((r["cyrillic"], r["excess"], short(r["pair"])))
        ax.set_xlim(-8, 104)
        ax.set_ylim(y_lo, y_hi)
        _place_labels(ax, labels, 112, y_hi - y_lo)
        ax.set_xlabel("Cyrillic share of Azerbaijani answers (%)")
        ax.set_title("`" + name + "` prompt, " + str(len(good)) + " pairs")
    axes[0].set_ylabel("Excess damage (points)")
    handles = [
        plt.Line2D([], [], marker=MARKERS[k], color=COLOURS[k], ls="", label=v)
        for k, v in (("kiril", "Cyrillic"), ("latın", "Latin"), ("qarışıq", "mixed"))
    ]
    axes[0].legend(
        handles=handles, title="target script", loc="lower right", frameon=False
    )
    fig.suptitle(
        "Pairs that emit Cyrillic Azerbaijani are damaged; pairs that do not are not",
        fontsize=10,
    )
    save(fig, out_dir, "fig_marker")


def figure_forest(rows, out_dir: Path) -> None:
    """Artıq zərər və 95% intervallar, kiçikdən böyüyə."""
    good = sorted(
        [r for r in rows if r["excluded"] is None], key=lambda r: r["excess"]
    )
    fig, ax = plt.subplots(figsize=(5.6, 3.7))
    ax.axvline(0, color="#999999", lw=0.8)
    for y, r in enumerate(good):
        script = r["pair"].script
        ax.errorbar(
            r["excess"],
            y,
            xerr=[[r["excess"] - r["low"]], [r["high"] - r["excess"]]],
            fmt=MARKERS.get(script, "D"),
            color=COLOURS.get(script, COLOURS["digər"]),
            markersize=6,
            capsize=3,
            lw=1.2,
        )
    ax.set_yticks(range(len(good)))
    ax.set_yticklabels([short(r["pair"]) + "  " + r["pair"].target_en for r in good])
    ax.set_xlabel("Excess damage (points), 95% bootstrap interval")
    ax.set_title("Every pair above zero has a Cyrillic-script target")
    save(fig, out_dir, "fig_forest")


def figure_losses(rows, out_dir: Path) -> None:
    """Mütləq itkilər: fərq metrikasının niyə lazım olduğu."""
    good = [r for r in rows if r["excluded"] is None]
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    lo, hi = -6, 30
    ax.plot([lo, hi], [lo, hi], color="#999999", lw=0.8, ls="--", zorder=1)
    ax.axhline(0, color="#DDDDDD", lw=0.6, zorder=0)
    ax.axvline(0, color="#DDDDDD", lw=0.6, zorder=0)
    labels = []
    for r in good:
        script = r["pair"].script
        ax.scatter(
            r["en_loss"],
            r["az_loss"],
            marker=MARKERS.get(script, "D"),
            color=COLOURS.get(script, COLOURS["digər"]),
            s=55,
            zorder=3,
        )
        labels.append((r["en_loss"], r["az_loss"], short(r["pair"])))
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    _place_labels(ax, labels, hi - lo, hi - lo)
    ax.set_xlabel("English loss (points)")
    ax.set_ylabel("Azerbaijani loss (points)")
    ax.set_title("Above the diagonal: Azerbaijani damaged beyond general forgetting")
    ax.set_aspect("equal")
    handles = [
        plt.Line2D([], [], marker=MARKERS[k], color=COLOURS[k], ls="", label=v)
        for k, v in (("kiril", "Cyrillic"), ("latın", "Latin"), ("qarışıq", "mixed"))
    ]
    ax.legend(
        handles=handles, title="target script", loc="lower right", frameon=False
    )
    save(fig, out_dir, "fig_losses")


def figure_design(rows, out_dir: Path, style_name: str = "default") -> None:
    """2x2 dizayn: hansı xanada zərər var.

    ŞƏKİL MƏLUMATDAN QURULUR, əl ilə çəkilmir. Səbəb: hansı xananın zərər
    verdiyi NƏTİCƏDİR və o nəticə bir gündə üç dəfə dəyişdi. Əl ilə
    çəkilsəydi, indi təkzib edilmiş "qarşılıqlı təsir" versiyası qalardı.

    Qarışıq yazılı hədəf (SEA) 2x2-yə sığmır, ona görə altda ayrıca sətir
    kimi verilir; onu xanalardan birinə soxmaq yanlış olardı.
    """
    good = [r for r in rows if r["excluded"] is None]
    related = {"qazax", "türk"}
    cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
    extra: list[dict[str, Any]] = []
    for r in good:
        script = r["pair"].script
        if script not in ("kiril", "latın"):
            extra.append(r)
            continue
        key = ("qohum" if r["pair"].target in related else "qohum deyil", script)
        cells.setdefault(key, []).append(r)

    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    ax.set_xlim(-0.05, 2.05)
    ax.set_ylim(-0.62, 2.42)
    ax.axis("off")
    rows_order = ["qohum", "qohum deyil"]
    row_names = {"qohum": "related", "qohum deyil": "not related"}
    cols_order = ["latın", "kiril"]
    for ci, col in enumerate(cols_order):
        for ri, row in enumerate(rows_order):
            entries = cells.get((row, col), [])
            x, y = ci, 1 - ri
            ax.add_patch(
                plt.Rectangle(
                    (x, y), 1, 1, facecolor="white", edgecolor="#888888", lw=1.0
                )
            )
            for k, r in enumerate(entries):
                damaged = r["low"] > 0
                ax.text(
                    x + 0.5,
                    y + 0.72 - 0.26 * k,
                    ("● " if damaged else "○ ")
                    + r["pair"].target_en
                    + "  "
                    + format(r["excess"], "+.1f"),
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=COLOURS["kiril"] if damaged else "#444444",
                )
    for ci, col in enumerate(cols_order):
        ax.text(
            ci + 0.5,
            2.10,
            "same script (Latin)" if col == "latın" else "different script (Cyrillic)",
            ha="center",
            fontsize=9,
        )
    for ri, row in enumerate(rows_order):
        ax.text(-0.04, 1.5 - ri, row_names[row], ha="right", va="center", fontsize=9)
    note = "; ".join(
        r["pair"].target_en + " " + format(r["excess"], "+.1f") for r in extra
    )
    if note:
        ax.text(
            1.0,
            -0.22,
            "mixed-script target, outside the 2x2: " + note,
            ha="center",
            fontsize=8,
            color="#444444",
        )
    ax.text(
        1.0,
        -0.42,
        "● interval excludes zero (damage)    ○ not distinguishable from zero",
        ha="center",
        fontsize=8,
        color="#444444",
    )
    ax.text(
        1.0,
        2.34,
        "Damage follows the COLUMN, not the row",
        ha="center",
        fontsize=10.5,
    )
    ax.text(
        1.0,
        -0.56,
        "`" + style_name + "` prompt; numbers are excess damage in points",
        ha="center",
        fontsize=7.5,
        color="#666666",
    )
    save(fig, out_dir, "fig_design")


def figure_gates(dataset, all_runs, out_dir: Path) -> None:
    """Qapıların NEÇƏ qaçış kəsdiyi, saylarla.

    SXEMATİK QUTU DİAQRAMI YOX, MƏLUMAT. Qutulardan ibarət axın sxemi
    yalnız mətni təkrarlayardı; buradakı saylar isə qapıların bəzək
    olmadığını göstərir: hər beşi nəyisə tutub.
    """
    from src.analyze import partition_by_coverage
    from src.echo_gate import MAX_ECHO, MAX_QUESTION_ECHO, echo_rate, question_echo_rate
    from src.extraction_gate import MAX_RECOVERABLE, recoverable_rate

    def empty_share(run):
        return sum(1 for v in run.raw.values() if not (v or "").strip()) / max(
            len(run.raw), 1
        )

    complete, _ = partition_by_coverage(all_runs, dataset)
    stages = [("all runs", list(all_runs))]
    stages.append(("coverage ≥ 90%", complete))
    step = [r for r in stages[-1][1] if empty_share(r) <= 0.20]
    stages.append(("< 20% empty", step))
    step = [r for r in step if echo_rate(r) <= MAX_ECHO]
    stages.append(("no example echo", step))
    step = [r for r in step if question_echo_rate(r, dataset) <= MAX_QUESTION_ECHO]
    stages.append(("no question echo", step))
    step = [r for r in step if recoverable_rate(r, dataset)[0] <= MAX_RECOVERABLE]
    stages.append(("answer extractable", step))

    names = [n for n, _ in stages]
    counts = [len(v) for _, v in stages]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.barh(range(len(counts)), counts, color="#BBBBBB", height=0.55)
    ax.barh(
        range(len(counts)),
        [counts[-1]] * len(counts),
        color=COLOURS["latın"],
        height=0.55,
    )
    for i, (n, c) in enumerate(zip(names, counts)):
        dropped = 0 if i == 0 else counts[i - 1] - c
        text = str(c) + (("   −" + str(dropped)) if dropped else "")
        ax.text(c + 1.2, i, text, va="center", fontsize=8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) * 1.18)
    ax.set_xlabel("Runs surviving")
    ax.set_title("Every gate excluded something", fontsize=10)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, out_dir, "fig_gates")


def figure_recovery(rows, out_dir: Path, style_name: str = "oneshot") -> None:
    """Transliterasiya nə qədər bərpa edir: markerin mexanizm OLMADIĞI.

    Sırf orfoqrafik izah bərpanın kiril payı ilə artmasını gözləyir.
    Artmır: `Kazakh 1` cavabların 84.9%-ni kirillə yazır və 19.1 bənddən
    yalnız 2.5-i geri gəlir; rus cütlərində demək olar sıfır.
    """
    good = [r for r in rows if r["excluded"] is None and r["az_loss"] > 0.5]
    good.sort(key=lambda r: -r["cyrillic"])
    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    y = range(len(good))
    ax.barh(
        [i + 0.18 for i in y],
        [r["az_loss"] for r in good],
        height=0.34,
        color="#BBBBBB",
        label="exact match (STRICT)",
    )
    ax.barh(
        [i - 0.18 for i in y],
        [r["az_loss_translit"] for r in good],
        height=0.34,
        color=COLOURS["kiril"],
        label="after transliteration",
    )
    for i, r in enumerate(good):
        ax.text(
            max(r["az_loss"], r["az_loss_translit"]) + 0.35,
            i,
            "Cyrillic " + format(r["cyrillic"], ".1f") + "%,  recovers "
            + format(r["az_loss"] - r["az_loss_translit"], ".1f"),
            va="center",
            fontsize=7.5,
        )
    ax.set_yticks(list(y))
    ax.set_yticklabels([short(r["pair"]) for r in good])
    ax.invert_yaxis()
    ax.set_xlabel("Azerbaijani loss (points)")
    ax.set_xlim(0, max(r["az_loss"] for r in good) * 1.75)
    ax.set_title(
        "Cyrillic output is a marker, not a repairable cause", fontsize=10
    )
    ax.legend(loc="lower right", frameon=False, title="`" + style_name + "` prompt")
    save(fig, out_dir, "fig_recovery")


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="figures")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("paper/figures"))
    parser.add_argument("--prompt-style", default="default")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    style()
    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    all_runs = load_runs(args.raw_dir)

    by_style: dict[str, list[dict[str, Any]]] = {}
    for name in ("default", "oneshot"):
        runs = {
            (r.key.model, r.key.language): r
            for r in all_runs
            if r.key.prompt_style == name
        }
        rows = pair_stats(dataset, runs, args.seed)
        by_style[name] = rows
        kept = [r for r in rows if r["excluded"] is None]
        dropped = [r for r in rows if r["excluded"] is not None]
        print(
            name
            + ": "
            + str(len(kept))
            + " cüt ölçülür, "
            + str(len(dropped))
            + " qapıdan keçmir"
        )
        for r in dropped:
            print("    buraxıldı: " + r["pair"].label)

    figure_marker(by_style, args.out_dir)
    figure_forest(by_style[args.prompt_style], args.out_dir)
    figure_losses(by_style[args.prompt_style], args.out_dir)
    figure_design(by_style[args.prompt_style], args.out_dir, args.prompt_style)
    figure_gates(dataset, all_runs, args.out_dir)
    # Bərpa şəkli `oneshot` üzərindədir: kiril cütlərinin hamısı orada
    # etibarlıdır, `default`-da `Cyrillic 3` qapıdan keçmir.
    figure_recovery(by_style["oneshot"], args.out_dir, "oneshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
