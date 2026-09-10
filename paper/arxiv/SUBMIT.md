# arXiv submission

Upload `az-eval-arxiv.tar.gz`. It compiles standalone: tested in an empty
directory with `pdflatex` twice, no `bibtex` run and no `.bib` file present,
producing 39 pages with no undefined references. arXiv does not run `bibtex`,
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

    Under review at Computational Linguistics. 39 pages, 6 figures,
    27 tables. Benchmark, code and raw model outputs:
    https://doi.org/10.5281/zenodo.22695091 and
    https://github.com/nihatgaribli/AZ-Eval-benchmark

The journal's editorial office asked that the preprint state it is under
review, so the Comments line says so and the paper repeats it on page one.
Submission 4060, Computational Linguistics.

The Zenodo identifier is the concept DOI, which always resolves to the
newest release, so it does not go stale when the benchmark is updated.

**License.** CC BY 4.0 matches the dataset licence already declared in
`CITATION.cff`. Anything more restrictive would contradict it.

## Abstract for the arXiv form

**Paste this one.** arXiv caps the abstract at 1920 characters and the paper's
own abstract is 3834, so it will be rejected. This is a condensation at 1837
characters. It is written by hand, unlike the block below, so if the paper's
abstract changes in substance this one has to be re-checked against it.

---

Azerbaijani is not missing from multilingual evaluation, but the benchmarks that cover it are multiple choice and none is parallel, so a model's Azerbaijani cannot be compared with its own English on the same item. The formats are close to dissociated: of the items a model answers correctly under multiple choice, only 0.5% to 10.3% are also produced correctly in free form.

We introduce AZ-Eval, 1006 short-answer items stated in parallel Azerbaijani and English, 708 of them a control stratum whose subject matter is universal by construction. Every row is human-verified as a build gate rather than a label. Across 37 models the gap is concentrated in the class low-resource work actually deploys: 3.9 to 43.5 points for open models of 8B or smaller, against 3.7 to 14.2 for large commercial ones. Neither scale nor quantisation explains it.

Our main experiment asks what adapting a model to a neighbouring language costs a third language. Thirteen declared base/fine-tuned pairs, ten of which pass our measurement gates, cross relatedness against script. Reporting Azerbaijani loss minus English loss, so ordinary forgetting is subtracted, relatedness predicts nothing: Turkish, the closest relative, costs nothing, while unrelated Russian costs 8 to 10 points. Script predicts nine of ten, and whether the tuned model starts writing Azerbaijani in Cyrillic separates all ten. We report what the design cannot do: every damaged pair is built on a Qwen model, so target script and base family predict these outcomes almost equally well, and we name the experiment that would separate them.

We also show that the standard word-level language-confusion detector is blind to Azerbaijani answered in Turkish by construction, since the Turkish alphabet is a subset of the Azerbaijani one, and measure that it misses 92% of such errors.

---

## The paper's full abstract, plain text

Kept for reference and regenerated from the `.tex` on every rebuild, so it
cannot drift. Too long for the arXiv form.

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

Measuring 37 models under a single protocol, we find the gap concentrated in
the models that low-resource work actually deploys: 3.9 to 43.5 points across
29 open models of 8B or smaller, against 3.7 to 14.2 points for five large
commercial models. Scale does not explain it, since a 235B model trails four
smaller ones by roughly ten points; nor does quantisation, since an 8B model
served at full precision behaves like its 4-bit peers.

Our main experiment asks what adapting a model to a neighbouring language costs
a third language. Thirteen base/fine-tuned pairs, ten of which pass our
measurement gates, cross two factors: whether the adaptation target is related
to Azerbaijani, and whether it shares its script. Reporting Azerbaijani loss
minus English loss, so that ordinary forgetting is subtracted, relatedness
carries no predictive power and script carries most of it. The closest
relative, Turkish, does no damage in either of two pairs; a wholly unrelated
Slavic language, Russian, damages Azerbaijani in both of its pairs. Every
Latin-script target leaves Azerbaijani intact (four pairs); four of five
Cyrillic-script targets damage it by 8 to 11 points. A non-Latin target is not
by itself sufficient: a model adapted to Thai, Burmese and Tamil alongside four
Latin-script languages, sharing its base with the most damaged pair, costs
Azerbaijani nothing. The tokeniser is measured rather than assumed and is
identical in seven of the ten pairs, so the contrast survives with segmentation
held exactly constant. An exact permutation test over the ten pairs puts the
script account ahead of three rivals, and also shows what the design cannot do:
every damaged pair is built on a Qwen model, so the script of the target and
the family of the base predict these outcomes almost equally well. We name the
one experiment that would separate them.

The single exception, a Ukrainian-adapted model that does no damage, is
absorbed by a marker that separates all ten pairs without exception: whether
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
