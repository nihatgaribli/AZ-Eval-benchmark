# Dataset and method (draft, sections 3-4)

**Status:** first draft, 2026-09-08. Numbers come from the regenerated tables
under `results/`; the source is named where relevant.

---

## 3 AZ-Eval

### 3.1 Design

AZ-Eval contains 1006 short-answer items, each stated in parallel Azerbaijani
and English. Parallelism is the property that makes the central measurement
possible: without it there is no within-item comparison, and a language gap
cannot be separated from a difficulty difference.

| | |
|---|---|
| Items | 1006 |
| Control stratum | 708 (70%) |
| Majority baseline | 0.8% |
| Distinct answers | 748 under scoring normalisation (769 surface forms) |
| Mean answer length | 1.34 words |

**Categories:** mathematics 264, geography 188, science 179, culture 109,
world 104, language 85, history 77.

**Provenance:** `wikidata-template` 524, `computed-template` 236, `manual`
246.

Answers are short by design. A one- or two-word answer can be scored by exact
match under an explicit normalisation policy; a sentence cannot, and any
attempt to score sentences would measure instruction-following rather than
knowledge. We return to this in Section 4.1.

### 3.2 Human verification is a build gate

The field `verified_by` is not metadata. `build_dataset` refuses to emit any
row whose value is not `human`, so the claim "every item was checked" is
enforced by the code that produces the artefact rather than asserted in the
paper.

Rejected drafts are retained under `data/raw/` with the reason recorded,
because the acceptance rate is itself a quality statistic and discarding
rejections would destroy it.

A separate state, `external`, marks rows verified by the authors of an
outside dataset and audited by us but not individually re-verified. Such rows
never enter the final dataset. Calling them `pending` would have hidden the
external verification; calling them `human` would have claimed work we did
not do.

### 3.3 The control stratum

The most predictable objection to a benchmark for a low-resource language is
that its items are locally specific, so a model fails in that language
because it does not know the fact in any language. The control stratum
answers this: 708 items whose subject matter is universal by construction:
world capitals and currencies, chemical elements, and computed mathematics.

Membership is decided by **template**, not by category label. A category
label is too coarse: `geography` contains both "the capital of Russia" and
"the mouth of the Oxchuchay", and only the first is universal. The
`country_capital` template, by contrast, harvests world countries under a
`sitelinks >= 8` filter and is universal by construction regardless of the
label its rows carry.

One universal template is deliberately excluded. `language_writing_system`
asks which script a language uses; since the paper's central claim concerns
script, including such items in the control stratum would create an
unnecessary coupling. Sixteen items are lost and an argument is gained.

### 3.4 Contamination-proof items

236 items are produced by algorithm from 20 question families (`polygon
angles`, `nth prime`, `remainder`, `binary to decimal`, and so on), in four
syntactic variants each, and were created *after* every model reported here.
They cannot appear in any training corpus, because they did not exist.

Correctness is verified two independent ways: a second implementation inside
the test suite that deliberately avoids the generator's own method
(subtraction instead of `%`, an explicit loop instead of a closed form,
bit-by-bit accumulation instead of `int(x, 2)`), and separately with `sympy`.
Both report zero errors.

Answers never appear inside their own question; the generator drops any item
where the answer string occurs in the question text.

Numeric answers bypass the morphological alias generator, which treats every
digit sequence as a year and would accept "180-ci il" ("the year 180") for a
question about degrees.

### 3.5 An imported subset, audited

The Azerbaijani portion of TUMLU-mini (521 items, CC BY 4.0) is imported for
one purpose only: a format contrast between multiple choice and short answer
on identical items. Importing another dataset means importing its defects, so
the rows were audited for ten defect classes (`comma_split`,
`broken_decimal`, `duplicate_choice`, `meta_answer`, `answer_in_question`,
and others). The correct option is placed at each position in turn, so the
uniform answer distribution is a property of construction rather than luck.

These rows carry `verified_by: external` and are not part of the 1006.

### 3.6 Quality measured from outside

A stratified sample of 200 items was re-checked by a second annotator who had
not seen the dataset. Their file carried no trace of the first annotator's
decision: `verified_by`, `notes` and `source` were removed, because the
template name and source URL would have biased the judgement. This is
enforced by a test.

| | |
|---|---|
| Agreement | 93.5% |
| Flagged | 13 (6.5%) |
| Removed after review | 11 (5.5%) |
| Retained after review | 2 |

The number is credible in both directions: zero rejections would indicate an
easy sample or an inattentive pass, and a high rate would indicate a poor
dataset.

One rejection led to a **systematic** fix. The annotator rejected an item
reading "Find the third angle: 47 degrees and 63 degrees" on the grounds that
the figure is never named, so the answer is undetermined. Inspection showed
this was not a single bad row but one variant of a generator family,
affecting three items in both languages. The template was corrected.

**The statistic is asymmetric and we say so.** Every row in the dataset was
accepted by the first annotator, so their label is always "correct" and
Cohen's kappa reduces to a function of the second annotator's rejection rate.
A symmetric measurement would require both annotators to judge the same rows
from scratch, blind to each other; that is future work.

---

## 4 Method

### 4.1 Prompting and decoding

All models receive the same prompt in the language of the question, with two
few-shot examples and an explicit instruction to answer briefly. Decoding is
greedy with a fixed seed and a 32-token budget.

The few-shot examples are not decoration. With instruction alone, one model
answered eight of eight questions correctly in substance while scoring 1/8,
because it produced "The capital of France is Paris" rather than "Paris".
Such a number measures output format, not knowledge. The two example facts do
not appear in the dataset.

The Azerbaijani and English prompts ask about the same two example facts,
because differing examples would leak a difficulty difference into the
language comparison.

### 4.2 Four nested normalisations

Exact match requires an explicit policy about what counts as the same answer.
Ours is a chain, and each link adds exactly one transformation:

```
STRICT  → MORPH     + suffix stripping
MORPH   → LENIENT   + diacritic folding
LENIENT → TRANSLIT  + Cyrillic-to-Latin transliteration
```

Every transformation is applied symmetrically to prediction and gold. Because
the chain is nested, the question "which step recovered this error" has
exactly one answer, and that answer identifies the cause. The chain is
therefore the paper's measuring instrument, not merely a cleanup step, and
Section 7 reads it as such.

Accepted-answer sets are additionally expanded by rule-based Azerbaijani
morphological generation, so that inflected forms of a correct answer are
credited.

### 4.3 Statistics

All model comparisons are paired at the item level. We report percentile
bootstrap confidence intervals (1000 resamples, fixed seed) and *p* values
from a sign-flipping permutation test. Multiple comparisons are corrected by
the Holm procedure.

### 4.4 Confirmatory and exploratory families are separated

This is the paper's main methodological commitment and it is stated openly.

The analysis code compares every model pair it encounters and applies Holm
correction across that list. When fourteen models were added for breadth, the
family grew to 474 tests and the *p* value of the project's founding
hypothesis drifted from 0.018 to 0.047, even though those fourteen models do
not test that hypothesis at all.

Penalising a pre-declared hypothesis for exploratory tests added later is
wrong. The declared pairs therefore form their own family of 88 tests (11
pairs × 4 chains × 2 languages), corrected within it. The exploratory sweep is
not deleted: it remains in the tables and is corrected within its own family.

This is not narrowing a family until a result appears. The pair list is fixed
in the module and in the commit history, and it predates the sweep. When a
fourth pair was added the family grew from 24 to 32 tests, and when a fifth
was added it grew to 40. Each enlargement makes Holm *stricter*: growing a
family can only cost significance, never grant it. The fifth pair was declared
before its result was computed, for a reason given in Section 6.1.

### 4.5 Coverage gate

A run covering less than 90% of the dataset is excluded from comparison
tables. The reason is that a truncated run is not a random sample: the
evaluation walks the dataset in order, so a 22-row run consists of the first
22 rows, which are template-built capital-city questions and systematically
easier. Such a run scores 83% where the complete run scores 16%.

Printing an `N` column is not sufficient protection, because readers compare
percentages that sit side by side.

### 4.6 Degenerate runs are not measurements

A run in which more than 20% of raw responses are empty is excluded from the
robustness comparison. If a model emitted nothing, there is nothing to score.

This rule is not tuned to a result. It was introduced after a hybrid
reasoning model, asked without few-shot examples, returned empty content on
42.7% of English items, which collapsed its English score and made the
language gap appear to vanish. The gap did not vanish because Azerbaijani
improved; it vanished because the English side broke. Reporting that as
evidence about the hypothesis would have been wrong.

Measured across all runs before the rule was adopted: 53 of 56 had exactly
zero empty responses, one model unable to do the task at all had 79-84%, and
the degenerate condition had 42.7%. The gate creates no borderline cases.

The rate is computed on **raw** text rather than extracted answers: an empty
extraction may indicate a defective extractor, whereas empty raw text means
the model produced nothing.

### 4.7 Three more ways a run stops being a measurement

A run in which more than 20% of responses begin by repeating a few-shot
example answer is likewise excluded. The pathology is that the model emits the
example answers on their own lines and only then the real one, so an extractor
that takes the first line scores a correct answer as wrong.

This gate was added after it cost us a result. One model did this on 67.8% of
Azerbaijani items and 0% of English items, which broke one side of a two-sided
comparison and produced 7.0 points of excess damage where the correct value is
0.1. Section 6.6 reports the episode.

The rule is derived from the production prompt templates rather than restated:
a response counts as an echo when it has more than one line and its first line
appears in the prompt prefix that the run itself was given. Restating the
example answers in the checking code would let a template change slip past the
gate unnoticed.

Measured across all runs, one exceeds the threshold at 68.2% and the next
highest is 8.7%, so the gate creates no borderline cases. As with the
empty-response rule, the threshold was chosen from a gap in the data rather
than tuned to a result.

**A second variant of the same pathology has to be checked separately.** Some
models return the *question* instead of an answer. That is not caught by the
rule above, because such a response is a single line and matches the question
rather than the examples, so we detect it by comparing each response against
the question the item actually posed.

This rule found a run we had already excluded for a different reason. The
`zeroshot` condition that produced 42.7% empty English responses (Section 8.1)
also repeats the Azerbaijani question in 31.4% of items. Two independent gates
rejecting the same run is a useful sign that neither is arbitrary.

**A third gate generalises both.** Whatever the model does wrong, the
consequence is the same: the answer is present in the text and does not reach
the score. We therefore measure the share of scored-wrong items whose gold
answer appears in the raw response. Over 106 runs the distribution is one run
at 42.4% and then a 26-point gap down to 16.4%, so the threshold sits at 30%,
inside the only gap the data contains. A first attempt at 15% was wrong: it
fell in the middle of the dense cluster and made five runs borderline.

Response *length* is deliberately not the rule. `Mistral-7B-v0.1` answers in
full sentences on 100% of English items and still scores 52.6%, because the
extractor handles them. The pathology is a lost answer, not a long one.

*Source: `results/tables/echo_gate.md`, `results/tables/extraction_gate.md`,
`src/echo_gate.py`, `src/extraction_gate.py`.*

### 4.8 Generation is separate from scoring

`run_eval.py` writes raw model output only; all scoring happens in
`analyze.py`. A change to a scoring rule therefore never requires re-running a
model, and every historical run can be re-scored under a new rule.

### 4.9 Two protocol constraints for API models

Hybrid reasoning models must have reasoning disabled. Otherwise the 32-token
budget is consumed by internal reasoning and the visible answer is empty; we
measured 9 empty responses out of 10 in that condition. The local reasoning
model is run with reasoning disabled for the same reason, so this preserves
comparability rather than saving cost.

Some endpoints do not permit it. Three we intended to include return
`Reasoning is mandatory for this endpoint and cannot be disabled`. Raising
the token budget for those models alone would have made them incomparable
with the other 28, so they were excluded rather than run under different
conditions. We record this because it is a practical obstacle for anyone
building a short-answer benchmark today, not a property of our setup.
