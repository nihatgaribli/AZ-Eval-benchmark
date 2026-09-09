"""Hansı model revizyonu işlədilib: təkrarlanma üçün qeyd.

    python -m src.model_revisions

NİYƏ LAZIMDIR. HuggingFace-də çəkilər dəyişə bilər və bəzi kartlar bunu açıq
yazır (`RuadaptQwen3-4B-Hybrid`: "веса модели могут обновляться"). Yalnız
model ADI ilə qaçış təkrarlana bilməz; commit hash ilə təkrarlanır.

MƏNBƏ. Yerli HuggingFace keşindəki `snapshots/<hash>` qovluğu HƏQİQƏTİN
mənbəyidir: qaçış məhz onu oxuyub. Uzaqdakı cari revizyonu yazmaq yanlış
olardı, çünki o, bu gün dəyişmiş ola bilər.

DÜRÜSTLÜK QEYDİ. Bəzi modellər keşdən SİLİNİB (disk yeri üçün, 2026-09-09).
Onların revizyonu geri qaytarıla bilmir və `qeyd edilməyib` yazılır. Uydurma
hash yazmaqdansa boşluğu göstərmək düzgündür; həmin modellərin xam cavabları
`results/raw_outputs/` altında qalır və nəticələr onlardan hesablanır.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from src.analyze import load_runs

#: HuggingFace keşinin standart yeri.
DEFAULT_CACHE = Path(os.path.expanduser("~/.cache/huggingface/hub"))

def is_api_model(model: str) -> bool:
    """API ilə qaçırılan model adı `backend:` ön şəkilçisi daşıyır.

    `openai:openai/gpt-4o`, `google:gemini-3.5-flash` -> API.
    `Qwen/Qwen3-4B` -> yerli. Ayırıcı: ilk `/`-dən əvvəl `:` varmı.
    """
    return ":" in model.split("/", 1)[0]


def cache_dir(model: str, cache: Path = DEFAULT_CACHE) -> Path:
    return cache / ("models--" + model.replace("/", "--"))


def local_revisions(model: str, cache: Path = DEFAULT_CACHE) -> list[str]:
    """Keşdəki snapshot hash-ları (adətən bir dənə)."""
    snapshots = cache_dir(model, cache) / "snapshots"
    if not snapshots.is_dir():
        return []
    return sorted(p.name for p in snapshots.iterdir() if p.is_dir())


def current_ref(model: str, cache: Path = DEFAULT_CACHE) -> str | None:
    """`refs/main` faylının göstərdiyi hash, varsa."""
    ref = cache_dir(model, cache) / "refs" / "main"
    if not ref.is_file():
        return None
    value = ref.read_text(encoding="utf-8").strip()
    return value or None


def revision_of(model: str, cache: Path = DEFAULT_CACHE) -> str | None:
    """Bir revizyon varsa onu qaytarır; yoxdursa və ya birdən çoxdursa `None`."""
    found = local_revisions(model, cache)
    return found[0] if len(found) == 1 else None


def build_report(models: Sequence[str], cache: Path = DEFAULT_CACHE) -> str:
    lines = [
        "# İşlədilən model revizyonları",
        "",
        "Mənbə: yerli HuggingFace keşi. Qaçış məhz həmin snapshot-u oxuyub,",
        "ona görə uzaqdakı cari revizyon yox, bu yazılır.",
        "",
        "| Model | Revizyon |",
        "|---|---|",
    ]
    missing = 0
    for model in sorted(models):
        if is_api_model(model):
            note = "API ilə qaçırılıb, yerli çəki yoxdur"
        else:
            found = local_revisions(model, cache)
            if len(found) == 1:
                note = f"`{found[0]}`"
            elif len(found) > 1:
                head = current_ref(model, cache)
                note = "birdən çox snapshot: " + ", ".join(f"`{f}`" for f in found)
                if head:
                    note += f"; hazırkı ref `{head}` (qaçış digərini işlətmiş ola bilər)"
            else:
                note = "**qeyd edilməyib** (keşdən silinib)"
                missing += 1
        lines.append(f"| `{model}` | {note} |")
    lines += [
        "",
        f"Revizyonu bərpa edilə bilməyən model: **{missing}**.",
        "",
    ]
    if missing:
        lines += [
            "Bunlar 2026-09-09-da disk yeri üçün keşdən silinib. Hamısı yalnız",
            "kəşfiyyatçı süpürgədə iştirak edir, heç biri elan edilmiş cütdə",
            "deyil, və xam cavabları `results/raw_outputs/` altında qalır.",
            "",
        ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="model_revisions")
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--out", type=Path, default=Path("results/model_revisions.md")
    )
    args = parser.parse_args(argv)

    models = {run.key.model for run in load_runs(args.raw_dir)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(sorted(models), args.cache)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
