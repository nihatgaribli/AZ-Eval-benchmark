"""AZ-Eval v2-nin işləmə prinsipi: iki etibarlılıq sinfi bir boru xəttində.

    python talk/diagram_v2.py

v1 sxemi bir model qatı göstərirdi. v2-də qat İKİYƏ bölünür və fərq
kosmetik deyil:

  lokal   — `do_sample=False` + sabit seed. Eyni əmr eyni rəqəmi verir.
  API     — determinizm zəmanəti YOXDUR. Claude 5 ailəsi `temperature`
            parametrini ümumiyyətlə qəbul etmir; ən yaxşı hal `seed`-dir.

İki sətri eyni cədvəldə yan-yana qoymaq onları eyni sinfə aid göstərir.
Ona görə v2 hər sətrə mənşə damğası vurur və örtüyü 90%-dən aşağı olan
qaçışları müqayisədən çıxarır.

SXEMDƏ BU FƏRQ FORMA İLƏ VERİLİR: lokal yol bütöv xətt, API yolu qırıq xətt.
Rəng tək kanaldır; qırıq xətt ikinci kanaldır və çap olunanda da qalır.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import (  # noqa: E402
    Circle,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)

HERE = Path(__file__).resolve().parent

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
MUTED = "#898781"
SURFACE = "#fcfcfb"
PANEL = "#f1f0ea"
HERO = "#fdeee8"
FONT = "Segoe UI"


def label(ax, x, y, text, size, color=INK, weight="normal", ha="center"):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va="center", zorder=6, fontname=FONT)


def disc(ax, x, y, r, face=PANEL, ring=None):
    ax.add_patch(Circle((x, y), r, facecolor=face, edgecolor="none", zorder=1))
    if ring:
        ax.add_patch(Circle((x, y), r, facecolor="none", edgecolor=ring,
                            linewidth=2.4, zorder=2))


def arrow(ax, x0, y0, x1, y1, color=MUTED, dashed=False, width=1.8):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=18,
        color=color, linewidth=width, zorder=2,
        linestyle=(0, (5, 3)) if dashed else "solid",
    ))


def node_label(ax, x, y, title, module, detail, above: bool, accent=ORANGE):
    step = 0.32
    lines = [(title, 18, INK, "bold"), (module, 12, accent, "normal"),
             (detail, 12, MUTED, "normal")]
    for i, (text, size, color, weight) in enumerate(lines):
        offset = (len(lines) - 1 - i) * step if above else i * step
        label(ax, x, y + offset if above else y - offset,
              text, size, color, weight)


# --------------------------------------------------------------------------
# İkonlar
# --------------------------------------------------------------------------


def icon_dataset(ax, x, y):
    ax.add_patch(FancyBboxPatch((x - 0.66, y - 0.48), 1.32, 0.96,
                                boxstyle="round,pad=0,rounding_size=0.09",
                                facecolor="white", edgecolor=ORANGE,
                                linewidth=2.3, zorder=3))
    for dy, shade in ((0.20, ORANGE), (-0.20, BLUE)):
        ax.add_patch(Rectangle((x - 0.50, y + dy - 0.10), 1.00, 0.20,
                               facecolor=shade, alpha=0.20, edgecolor="none",
                               zorder=4))
        ax.add_patch(Rectangle((x - 0.50, y + dy - 0.10), 0.09, 0.20,
                               facecolor=shade, edgecolor="none", zorder=5))


def icon_local(ax, x, y):
    """Şəbəkə + lövbər: yerli, təkrarlanan."""
    left = [(x - 0.44, y + d) for d in (0.42, 0.0, -0.42)]
    right = [(x + 0.44, y + d) for d in (0.23, -0.23)]
    for lx, ly in left:
        for rx, ry in right:
            ax.plot([lx, rx], [ly, ry], color=MUTED, linewidth=1.0,
                    alpha=0.5, zorder=2)
    for px, py in left + right:
        ax.add_patch(Circle((px, py), 0.13, facecolor=BLUE, edgecolor="none",
                            zorder=4))


def icon_api(ax, x, y):
    """Bulud: uzaq provayder."""
    for cx, cy, r in ((-0.34, -0.02, 0.30), (0.02, 0.20, 0.38),
                      (0.36, -0.02, 0.28)):
        ax.add_patch(Circle((x + cx, y + cy), r, facecolor=ORANGE,
                            edgecolor="none", zorder=3))
    ax.add_patch(FancyBboxPatch((x - 0.60, y - 0.30), 1.20, 0.34,
                                boxstyle="round,pad=0,rounding_size=0.14",
                                facecolor=ORANGE, edgecolor="none", zorder=3))


def icon_raw(ax, x, y):
    """Xam cavab + mənşə damğası."""
    ax.add_patch(FancyBboxPatch((x - 0.42, y - 0.52), 0.84, 1.04,
                                boxstyle="round,pad=0,rounding_size=0.07",
                                facecolor="white", edgecolor=INK_SOFT,
                                linewidth=2.0, zorder=3))
    for i, w in enumerate((0.54, 0.44, 0.58)):
        ax.add_patch(Rectangle((x - 0.28, y + 0.24 - i * 0.22), w, 0.08,
                               facecolor=MUTED, alpha=0.5, edgecolor="none",
                               zorder=4))
    # Damğa
    ax.add_patch(Circle((x + 0.30, y - 0.40), 0.22, facecolor=ORANGE,
                        edgecolor=SURFACE, linewidth=2.0, zorder=5))


def icon_gate(ax, x, y):
    """Örtük qapısı: az örtüklü qaçış kənara düşür."""
    ax.add_patch(Polygon([[x - 0.62, y + 0.50], [x + 0.62, y + 0.50],
                          [x + 0.14, y - 0.06], [x + 0.14, y - 0.52],
                          [x - 0.14, y - 0.52], [x - 0.14, y - 0.06]],
                         closed=True, facecolor=BLUE, edgecolor="none",
                         zorder=3))
    for dx, dy, r in ((0.88, 0.26, 0.10), (1.04, -0.02, 0.08)):
        ax.add_patch(Circle((x + dx, y + dy), r, facecolor=MUTED,
                            edgecolor="none", zorder=3, alpha=0.7))


def build(path: Path) -> None:
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    fig.patch.set_facecolor(SURFACE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)

    ax.add_patch(Rectangle((1.05, 8.62), 0.95, 0.06, facecolor=BLUE,
                           edgecolor="none", zorder=3))
    label(ax, 1.05, 8.28, "AZ-Eval v2", 34, INK, "bold", ha="left")
    label(ax, 4.95, 8.28, "two classes of evidence", 17, MUTED, ha="left")

    r = 0.88
    mid = 4.45
    dataset_x = 2.1
    lane_x = 6.0
    raw_x = 9.9
    gate_x = 13.6
    # Zolaqlar mərkəzə yaxınlaşdırılıb: yuxarıdakı etiket bloku başlıqla,
    # aşağıdakı isə alt izahla toqquşurdu.
    upper, lower = 5.70, 3.20

    # ---- Dəst -------------------------------------------------------
    disc(ax, dataset_x, mid, r)
    icon_dataset(ax, dataset_x, mid)
    node_label(ax, dataset_x, mid - r - 0.40, "DATASET", "build_dataset.py",
               "484 parallel AZ / EN items", above=False)

    # ---- İki zolaq ---------------------------------------------------
    disc(ax, lane_x, upper, r)
    icon_local(ax, lane_x, upper)
    node_label(ax, lane_x, upper + r + 0.38, "LOCAL", "transformers",
               "greedy, fixed seed: reproducible", above=True, accent=BLUE)

    disc(ax, lane_x, lower, r, face=HERO, ring=ORANGE)
    icon_api(ax, lane_x, lower)
    node_label(ax, lane_x, lower - r - 0.40, "API", "any OpenAI-compatible",
               "no determinism guarantee", above=False)

    # Dəstdən zolaqlara. Bütöv xətt təkrarlanan yolu, qırıq xətt
    # təkrarlanmayanı bildirir: fərq rəngdən əlavə FORMA ilə də verilir.
    #
    # ORTAQ GÖVDƏ BİR DƏFƏ ÇƏKİLİR. İki rəngli xətt eyni seqmentin üstünə
    # çəkiləndə biri digərini örtür və nəticə çirkli görünür.
    split = lane_x - r - 1.05
    ax.plot([dataset_x + r + 0.15, split], [mid, mid], color=MUTED,
            linewidth=1.8, zorder=2)
    for y_target, dashed, color in ((upper, False, BLUE), (lower, True, ORANGE)):
        ax.plot([split, split], [mid, y_target], color=color, linewidth=1.8,
                zorder=2, linestyle=(0, (5, 3)) if dashed else "solid")
        arrow(ax, split, y_target, lane_x - r - 0.15, y_target,
              color=color, dashed=dashed)

    # ---- Xam cavab ---------------------------------------------------
    disc(ax, raw_x, mid, r)
    icon_raw(ax, raw_x, mid)
    node_label(ax, raw_x, mid - r - 0.40, "RAW OUTPUT",
               "provenance stamped per row",
               "model version · endpoint · determinism", above=False)

    merge = raw_x - r - 1.05
    for y_source, dashed, color in ((upper, False, BLUE), (lower, True, ORANGE)):
        ax.plot([lane_x + r + 0.15, merge], [y_source, y_source],
                color=color, linewidth=1.8, zorder=2,
                linestyle=(0, (5, 3)) if dashed else "solid")
        ax.plot([merge, merge], [y_source, mid], color=color, linewidth=1.8,
                zorder=2, linestyle=(0, (5, 3)) if dashed else "solid")
    arrow(ax, merge, mid, raw_x - r - 0.15, mid)

    # ---- Örtük qapısı ------------------------------------------------
    disc(ax, gate_x, mid, r)
    icon_gate(ax, gate_x, mid)
    node_label(ax, gate_x, mid - r - 0.40, "COVERAGE GATE", "analyze.py",
               "under 90% never enters a comparison", above=False,
               accent=BLUE)
    arrow(ax, raw_x + r + 0.15, mid, gate_x - r - 0.15, mid)

    label(ax, 8.0, 0.62,
          "a partial run is not a random sample: it is the easy opening of the set",
          13, MUTED)

    fig.savefig(path, dpi=100, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    target = HERE / "diagram_v2_principle.png"
    build(target)
    print(f"{target.name}  ({target.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
