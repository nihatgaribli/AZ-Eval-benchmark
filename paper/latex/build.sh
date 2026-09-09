#!/bin/sh
# Build the Computational Linguistics submission, figures included.
#
# The figures under `figures/` are COPIES of `paper/figures/`, kept so that
# this directory can be zipped and uploaded as it stands. Copies drift: a
# hand-copied duplicate of the declared pair list left the tokeniser table two
# days stale earlier in this project. So the copy happens here, on every
# build, rather than by hand.
#
# Usage:  sh paper/latex/build.sh          (from the repository root)
set -e

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"

echo "== regenerating figures from the run data =="
python -m src.figures

echo "== refreshing the submission's figure copies =="
mkdir -p paper/latex/figures
cp paper/figures/fig_*.pdf paper/latex/figures/

echo "== typesetting =="
cd paper/latex
pdflatex -interaction=nonstopmode az-eval.tex > /dev/null
bibtex az-eval > /dev/null
pdflatex -interaction=nonstopmode az-eval.tex > /dev/null
pdflatex -interaction=nonstopmode az-eval.tex > /dev/null

echo "== checks =="
if grep -q "^!" az-eval.log; then
    echo "FAIL: LaTeX errors"
    grep -n "^!" az-eval.log
    exit 1
fi
overfull=$(grep -c "Overfull" az-eval.log || true)
if [ "$overfull" != "0" ]; then
    echo "WARNING: $overfull overfull boxes"
    grep -n "Overfull" az-eval.log
fi
# Narrowly: only real dangling \ref and \cite. A bare "undefined" also matches
# hyperref's harmless \thepage note and the T2A font substitution for the three
# Cyrillic examples, so grepping for the word alone reports a false alarm.
if grep -qE "(Citation|Reference) .* undefined" az-eval.log; then
    echo "FAIL: undefined references or citations"
    grep -nE "(Citation|Reference) .* undefined" az-eval.log
    exit 1
fi

echo "OK -> paper/latex/az-eval.pdf"
