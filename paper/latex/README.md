# Computational Linguistics submission

`az-eval.tex` is the paper. 36 journal pages, six figures, 24 tables, zero
overfull boxes.

## Building

    pdflatex az-eval
    bibtex   az-eval
    pdflatex az-eval
    pdflatex az-eval

Built with TinyTeX (TeX Live 2026). No packages beyond `amsmath`, `booktabs`
and `fontenc`, all of which ship with a standard distribution.

## What to upload

Everything the paper needs is inside this directory:

    az-eval.tex        the paper
    references.bib     19 entries, every one verified against arXiv metadata
    clv2025.cls        journal class file (do not edit)
    compling.bst       journal bibliography style (do not edit)
    figures/*.pdf      six figures, copies of `paper/figures/`

`figures/` holds copies rather than links so the directory can be zipped and
uploaded as it stands. Regenerate the originals with `python -m src.figures`
and copy them across again.

The rest of the files here are the publisher's own template
(`COLI_template.*`, `COLI_manual.pdf`, the zips, `__MACOSX/`, `alocal.sty`,
`ex.pdf`) and are kept only for reference. Do not upload them.

## Three traps in `clv2025.cls`, all of which cost a build

**`\pageonefooter` needs a `\thanks`.** The class builds the page-one footer by
calling `\@footnotetext` without ever setting `\@thefnmark`, so `\maketitle`
dies with `Undefined control sequence \H@@footnotetext` unless at least one
`\thanks` has run first. The publisher's own template hides this because its
example author list is full of them. Ours carries a corresponding-author note.

**`\paragraph{}` supplies its own full stop.** Writing one yourself renders as
`uninformative..`. All 24 D heads in this paper are therefore written without a
trailing period.

**Azerbaijani `ə` (U+0259) has no T1 slot.** The obvious fix, `tipa`, conflicts
with the `hyperref` that the class loads internally and reproduces the same
`\H@@footnotetext` failure; loading `tipa` first is not possible for the same
reason. The letter is instead a rotated `e` in whatever font surrounds it,
which is what a schwa is and which matches the body face exactly. Cyrillic
examples use T2A through the `\cyr{}` wrapper.

## Figures

All six are generated from the run data by `src/figures.py`, never drawn by
hand. That is deliberate: which cell of the design damages Azerbaijani is a
*result*, and that result changed three times as pairs were added. A
hand-drawn figure would still be showing the refuted version.

## A caution about the tables

Every number in the paper is transcribed from a regenerated table under
`results/`. When checking one, confirm the table itself is current: the
tokeniser table was stale for two days because `src/tokenizer_fertility.py`
kept a hand-copied duplicate of the declared pair list. It now derives from
`fine_tune_pairs.PAIRS` directly.
