# arXiv submission

Upload `az-eval-arxiv.tar.gz`. It compiles standalone: tested in an empty
directory with `pdflatex` twice, no `bibtex` run and no `.bib` file present,
producing 36 pages with no undefined references. arXiv does not run `bibtex`,
which is why `az-eval.bbl` is in the archive and `references.bib` is not.

`alocal.sty` from the publisher's template is deliberately absent. It patches
the older CLV2 class, and neither `clv2025.cls` nor this paper references it.

## Form fields

**Title**

    Script, Not Relatedness: What Fine-Tuning on a Neighbouring Language Costs Azerbaijani

**Authors**

    Nihat Garibli

**Primary category**

    cs.CL

**Cross-list**

    cs.LG

**Comments**

    36 pages, 6 figures, 24 tables. Benchmark and code: https://github.com/nihatgaribli/AZ-Eval-benchmark

Update that URL before submitting if the public repository lands somewhere
else. It must be live at submission time or the line should be dropped.

**License.** CC BY 4.0 matches the dataset licence already declared in
`CITATION.cff`. Anything more restrictive would contradict it.

## Abstract, plain text

arXiv's form takes plain text, so the LaTeX markup is stripped and percent
signs are literal. Paste from here rather than from the `.tex`.

---

Azerbaijani is not missing from multilingual evaluation: TUMLU contributes 735
items and INCLUDE 6,937. Both are multiple choice, and neither is parallel, so
neither can compare a model's Azerbaijani with its own English on the same
question. The format matters too: of the items a model answers correctly under
multiple choice, only 0.5% to 10.3% are also produced correctly in free form,
so selection and production are close to dissociated.

We introduce AZ-Eval, 1006 short-answer items stated in parallel Azerbaijani
and English, of which 708 form a control stratum whose subject matter is
universal by construction, so that failure there is a language failure rather
than a knowledge gap. Human verification is a build gate rather than a label:
the build refuses any row not individually checked. An independent annotator
re-checked a stratified sample of 200 items and agreed on 93.5%; the 11 items
they rejected were removed, one of which exposed a defective question template.

Measuring 34 models under a single protocol, we find the gap concentrated in
the models that low-resource work actually deploys: 3.9 to 43.5 points across
28 open models of 8B or smaller, against 3.7 to 15.2 points for five large
commercial models. Scale does not explain it, since a 235B model trails four
smaller ones by roughly ten points; nor does quantisation, since an 8B model
served at full precision behaves like its 4-bit peers.

Our main experiment asks what adapting a model to a neighbouring language costs
a third language. Eleven base/fine-tuned pairs, nine of which pass our
measurement gates, cross two factors: whether the adaptation target is related
to Azerbaijani, and whether it shares its script. Reporting Azerbaijani loss
minus English loss, so that ordinary forgetting is subtracted, relatedness
carries no predictive power and script carries most of it. The closest
relative, Turkish, does no damage in either of two pairs; a wholly unrelated
Slavic language, Russian, damages Azerbaijani in both of its pairs. Every
Latin-script target leaves Azerbaijani intact (three pairs); four of five
Cyrillic-script targets damage it by 8 to 11 points. A non-Latin target is not
by itself sufficient: a model adapted to Thai, Burmese and Tamil alongside four
Latin-script languages, sharing its base with the most damaged pair, costs
Azerbaijani nothing. The tokeniser is measured rather than assumed and is
identical in six of the nine pairs, so the contrast survives with segmentation
held exactly constant.

The single exception, a Ukrainian-adapted model that does no damage, is
absorbed by a marker that separates all nine pairs without exception: whether
the adapted model begins writing Azerbaijani answers in Cyrillic. Every pair
that emits any Cyrillic is damaged; every pair that emits none is not. We stop
short of calling this the mechanism, because transliteration recovers only part
of the Kazakh damage and almost none of the Russian.

The failure decomposes into two modes with opposite prospects. A Kazakh-adapted
model writes Azerbaijani answers in Cyrillic, and transliteration more than
doubles its score: the knowledge is present and the surface form is wrong. A
Turkish-adapted model writes them in Turkish, which no normalisation repairs
because the alphabet is already correct, and which the standard word-level
language-confusion detector misses in 92% of cases, since the Turkish alphabet
is a subset of the Azerbaijani one and no character ever leaves the expected
range.

---

## Order of operations

Computational Linguistics does not use blind review: authorship is known to the
editors and reviewers, and names and affiliations must appear on the first
page. Posting a preprint therefore does not compromise the CL submission, and
the two can go in either order.

The argument for arXiv first is priority. Three 2026 papers work in adjacent
space (arXiv:2604.06202, 2607.29355, 2608.09356), and one of them states the
script prediction this paper tests without running an experiment.

## Regenerating this archive

    sh paper/latex/build.sh          # refreshes figures and az-eval.bbl
    rm -rf paper/arxiv && mkdir -p paper/arxiv/figures
    cp paper/latex/az-eval.tex paper/latex/az-eval.bbl \
       paper/latex/clv2025.cls paper/latex/compling.bst paper/arxiv/
    cp paper/figures/fig_*.pdf paper/arxiv/figures/
    tar -czf paper/arxiv/az-eval-arxiv.tar.gz -C paper/arxiv \
        az-eval.tex az-eval.bbl clv2025.cls compling.bst figures

The `.bbl` only exists after `bibtex` has run, which `build.sh` does. Building
the archive without it produces a paper with no bibliography.
