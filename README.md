# AZ-Eval

[![tests](https://github.com/nihatgaribli/AZ-Eval-benchmark/actions/workflows/tests.yml/badge.svg)](https://github.com/nihatgaribli/AZ-Eval-benchmark/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code license: MIT](https://img.shields.io/badge/code%20license-MIT-green.svg)](LICENSE)
[![Data license: CC BY 4.0](https://img.shields.io/badge/data%20license-CC%20BY%204.0-green.svg)](LICENSE-DATA)

A parallel Azerbaijani-English benchmark, and a study of what fine-tuning on a
neighbouring language costs Azerbaijani. The short answer is that the target's
**script** predicts the damage and its **relatedness** does not.

**1006 items**, each stated in both languages, each verified by a human
before it enters the dataset. **34 models** measured under identical
conditions.

---

## What we found

### The gap depends on which models you use

| Model class | Azerbaijani-English gap |
|---|---|
| 28 open models, ≤8B, 4-bit | 3.9 to 43.5 points |
| 5 large models via API | 3.7 to 15.2 points |
| `qwen3-8b` via API (8B, full precision) | 27.5 points |

Every open-model gap is Holm-significant. `gpt-4o`'s 3.7 points is the one
exception at the top: the bootstrap interval is [1.0, 6.4] but Holm-corrected
*p* = 0.10, so we do not claim a gap for that model individually.

`qwen3-8b` is listed separately on purpose. It is served through the same API
at full precision, yet its gap matches the local 8B class rather than the
large models. Serving stack and quantisation are therefore not what separates
the two groups.

This is more precise than "Azerbaijani is poorly supported", and the
precision matters. The problem is concentrated in **open, small, locally
deployed models**, which is exactly the class used for low-resource language
work, because it runs on one GPU and costs nothing per call.

### Model size does not predict Azerbaijani ability

| Model | Organisation | AZ | EN | Gap |
|---|---|---|---|---|
| `gpt-4o` | OpenAI | 66.7% | 70.4% | **3.7** |
| `claude-sonnet-5` | Anthropic | 65.5% | 71.0% | 5.5 |
| `deepseek-v3.2` | DeepSeek | 64.1% | 70.0% | 5.9 |
| `llama-4-maverick` | Meta | 63.6% | 68.5% | 4.9 |
| `qwen3-235b-a22b` | Alibaba | 48.8% | 64.0% | **15.2** |

Four models from four independent organisations land within 3.1 points of
each other. A much larger model sits far outside that band. Parameter count
is a poor guide when choosing a model for Azerbaijani.

### The script of the target predicts the damage; relatedness does not

Eleven declared base/fine-tuned pairs, nine of which pass the measurement
gates, cross two factors: is the adaptation
target related to Azerbaijani, and does it share its script? We report
**excess damage**: Azerbaijani loss minus English loss, paired per item, so
that the model's own general forgetting is subtracted.

| Pair | Target | Related | Script | Excess damage | 95% CI |
|---|---|---|---|---|---|
| `Qwen3-VL-4B-Thinking` → `Qolda-AVL-5B` | Kazakh | yes | Cyrillic | **+9.8** | [+6.2, +13.4] |
| `Qwen3.5-4B-Base` → `…-Base-Kazakh` | Kazakh | yes | Cyrillic | **+10.6** | [+7.0, +14.2] |
| `Qwen3-4B` → `RuadaptQwen3-4B-Hybrid` | Russian | no | Cyrillic | **+10.1** | [+7.0, +13.0] |
| `Qwen3-4B` → `QVikhr-3-4B-Instruction` | Russian | no | Cyrillic | **+8.3** | [+5.4, +11.4] |
| `gemma-3-4b-it` → `MamayLM-Gemma-3-4B` | Ukrainian | no | Cyrillic | +0.1 | [-2.9, +3.2] |
| `Meta-Llama-3-8B` → `Turkish-Llama-8b` | Turkish | yes | Latin | +1.5 | [-1.0, +4.5] |
| `Mistral-7B-v0.1` → `Trendyol-LLM-7b` | Turkish | yes | Latin | -16.0 | [-19.2, -12.8] |
| `gemma-3-4b-it` → `borealis-4b` | Norwegian | no | Latin | -3.1 | [-6.0, -0.5] |
| `Qwen3-VL-4B-Instruct` → `Qwen-SEA-LION-v4-4B` | SE Asian | no | mixed | -0.9 | [-2.8, +1.1] |

**Relatedness splits exactly evenly and predicts nothing.** Turkish is the
closest relative we could find and costs nothing. Russian is unrelated and
costs 8 to 10 points.

**Script predicts eight of nine.** Every Latin target is harmless; four of
five Cyrillic targets are not. The exception, Ukrainian, is reported rather
than smoothed away.

**A non-Latin target is not enough by itself.** `SEA-LION` is adapted to Thai,
Burmese and Tamil alongside four Latin-script languages and shares its base
with the most damaged pair in the study. It costs Azerbaijani nothing.

**One marker separates all nine**: whether the tuned model starts writing
Azerbaijani in Cyrillic. Every damaged pair does (84.9%, 18.9%, 13.8%, 7.7%);
no undamaged pair does (0.0% to 0.2%, the latter matching its own base).

The tokeniser is measured, not assumed, and is **identical in six of the nine
pairs**, so the contrast survives with segmentation held exactly constant.

**This claim changed twice in one day.** The Ukrainian pair briefly appeared
to refute the script account, and we rewrote the paper around an interaction
of relatedness and script; the two Russian pairs then refuted that. The
history is in [paper/intro.md](paper/intro.md).

### Two failure modes, and only one is recoverable

| Mode | What happens | Does normalisation help? |
|---|---|---|
| Orthographic | model knows the fact, writes it in Cyrillic | yes, transliteration recovers it |
| Wrong language | model knows the fact, writes it in Turkish | **no** |
| Capability | model cannot produce the answer | no |
| Both at once | model writes Cyrillic *and* the wrong content | **no** |

The last row is why the Cyrillic marker in the pair table is a *marker* and
not a mechanism: transliteration recovers 2.5 of the Kazakh model's 19.1
points and essentially none of the Russian models'.

`Qolda-AVL-5B` writes 85.9% of its Azerbaijani answers in Cyrillic;
transliteration more than doubles its score. `Turkish-Llama-8b` writes 26% of
its residual errors in Turkish (`yapon dili` → `Japonca`), where the alphabet
is already correct and no normalisation helps.

**The standard detector is blind to this pair by construction.** Language
confusion is a known failure with known metrics (Marchisio et al., EMNLP
2024), but their word-level rule flags characters outside the target script's
Unicode range, and the Turkish alphabet is a *subset* of the Azerbaijani one
(which adds only `ə`, `x`, `q`). A Turkish word cannot leave the Azerbaijani
range. Measured on our human-labelled errors, the rule misses **92%** of them;
the 2 it catches contain `w` and are English intrusions, not Turkish ones.

```bash
python -m src.language_confusion
```

### Why another benchmark, when Azerbaijani already has two

It does: TUMLU contributes 735 items and INCLUDE 6,937. Both are multiple
choice, and neither is parallel with English, so neither can answer the
question this project asks: how a model's Azerbaijani compares with *its own*
English on the *same* item.

Format matters as much as parallelism. Running the same 521 TUMLU-az items
through the same models in both formats:

| Model | MCQ | Short answer | Of what it recognises, it can produce |
|---|---|---|---|
| `Qwen3-1.7B` | 37.0% | 2.9% | 3.6% |
| `Qwen3-VL-4B-Instruct` | 44.9% | 7.5% | 10.3% |
| `Qwen3-VL-4B-Thinking` | 43.2% | 5.8% | 10.2% |
| `Qolda-AVL-5B` | 39.0% | 0.2% | 0.5% |

Nine out of ten items a model can pick out of four options, it cannot write
down. The last column is the one to read: the raw difference is inflated by
the 25% a guesser earns under four-way choice, and retention is immune to
that.

---

## The dataset

| | |
|---|---|
| Items | 1006 |
| Languages | Azerbaijani + English, parallel line by line |
| Control stratum | 708 items (70%) with universal subject matter |
| Verification | every item `verified_by: human`, enforced as a build gate |
| Majority baseline | 0.8% |
| Distinct answers | 748 under scoring normalisation (769 surface forms) |
| Mean answer length | 1.34 words |

**Categories:** mathematics 264, geography 188, science 179, culture 109,
world 104, language 85, history 77.

**Provenance:** `wikidata-template` 524, `computed-template` 236, `manual`
246.

### Human verification is a gate, not a label

`build_dataset` refuses to admit a row whose `verified_by` is not `human`.
The claim "every item was checked" is therefore enforced by code rather than
asserted in prose.

### Independent quality check

A stratified sample of 200 items was re-checked by a second annotator who had
not seen the dataset. Their file contained no trace of the first annotator's
decision: `verified_by`, `notes` and `source` were stripped, because the
template name and source URL would have biased the judgement.

| | |
|---|---|
| Agreement | **93.5%** |
| Flagged as wrong | 13 (6.5%) |
| Removed after review | **11 (5.5%)** |

One of those rejections found a *systematic* defect: a question template that
never named the figure ("Find the third angle given 47 and 63 degrees"),
affecting three items in both languages. The template was fixed.

### The dataset is solvable

A benchmark nobody can solve does not measure models. On a stratified sample
of 50 items, a speaker who had not seen the dataset scored **70.0%**, against
36.0% for the best *local* model on the same items. Lookup was prohibited; 14%
of items were left blank and blanks count as errors, so this is a lower bound.

The human is not a ceiling: `claude-sonnet-5` reaches 74.0% on those same
items. The baseline establishes that the questions are answerable, which is
what it is for.

### Contamination cannot explain the gap

236 items are generated by algorithm (`src/generate_math.py`) and were
created *after* every model measured here. They cannot be in any training
corpus. The gap persists on that subset.

Answers are verified two independent ways: a second implementation in the
test suite (subtraction instead of `%`, loops instead of closed forms,
bit-by-bit instead of `int(x, 2)`), and separately with `sympy`.

---

## Reproducing

```bash
pip install -r requirements.txt

# harvest draft items from Wikidata (parallel AZ/EN by construction)
python -m src.harvest_wikidata --templates country_capital --per-template 40

# human verification in a local browser UI: A accept / R reject / S skip
python -m src.review data/raw/wikidata.jsonl

# build the dataset (only verified_by=human passes)
python -m src.build_dataset build

# evaluate a local model; add --load-in-4bit on small GPUs
python -m src.run_eval --model Qwen/Qwen3-1.7B --language az --load-in-4bit
python -m src.run_eval --model Qwen/Qwen3-1.7B --language en --load-in-4bit

# evaluate through an OpenAI-compatible API (key in .env, gitignored)
python -m src.run_eval --backend api --model "openai:openai/gpt-4o" \
  --language az --base-url https://openrouter.ai/api/v1 \
  --api-key-env OPENROUTER_API_KEY --no-reasoning

# score and produce tables
python -m src.analyze
```

`--no-reasoning` matters. A hybrid reasoning model spends the whole 32-token
budget on internal reasoning and returns an empty answer; we measured 9 empty
responses out of 10 without it.

Some endpoints (`gpt-5`, `gpt-5-mini`, `gemini-3.1-pro-preview`) refuse to
disable reasoning at all and cannot be evaluated under a short-answer
protocol without changing the budget for every other model. See
`results/raw_outputs/unsupported_protocol/README.md`.

---

## How the measurement works

### Four nested normalisations

```
STRICT  → MORPH     + suffix stripping
MORPH   → LENIENT   + diacritic folding
LENIENT → TRANSLIT  + Cyrillic-to-Latin transliteration
```

Each step adds exactly one transformation and is applied symmetrically to
prediction and gold. Because the chain is nested, "which step recovered this
error" has a single answer, and that answer is the cause. This is the
project's measuring instrument, not merely cleanup.

### Generation is separate from scoring

`run_eval.py` writes raw text only; `analyze.py` computes scores. Changing a
scoring rule therefore never requires re-running a model.

### Confirmatory and exploratory families are separated

`analyze.py` compares every model pair it sees and Holm-corrects over that
list. Adding 14 models grew the family to 474 tests and pushed the founding
hypothesis from *p* = 0.018 to 0.047, even though those 14 models do not
test that hypothesis at all. The declared pairs therefore have their own
family of 88 tests; the exploratory sweep is kept, corrected within its own
family, and reported.

### Four ways a run stops being a measurement

| Gate | Rule | Threshold |
|---|---|---|
| Empty | raw response is blank | 20% |
| Example echo | repeats a few-shot answer before the real one | 20% |
| Question echo | returns the question instead of an answer | 20% |
| Extraction | gold answer is in the raw text but not in the score | 30% |

Each was added after it cost us something. The example-echo gate exists
because one model did this on 67.8% of Azerbaijani items and 0% of English
ones, inflating a pair's excess damage from 0.1 points to 7.0. The extraction
gate exists because a Georgian-adapted model answered in full sentences and
would have entered the tables at -17.8 points.

Thresholds sit in gaps in the measured distribution, not at round numbers. For
the extraction gate the distribution is one run at 42.4% and then nothing until
16.4%, so the threshold is 30%.

Response length is deliberately not a rule: `Mistral-7B-v0.1` answers in full
sentences on 100% of English items and scores 52.6% because the extractor
handles them.

```bash
python -m src.echo_gate
python -m src.extraction_gate
```

### Runs below 90% coverage are excluded from comparisons

`run_eval` walks the dataset in order, so a truncated run consists of the
first rows, which are systematically easier. A 22-row run scores 83% where
the full run scores 16%. Printing an `N` column is not enough, because
readers compare percentages side by side.

---

## Known limitations

1. **One Cyrillic pair does no damage and we cannot say why.** Adapting to
   Ukrainian leaves Azerbaijani intact. The model barely moved in any
   direction, but that restates the result rather than explaining it, so the
   claim is stated as "four of five".

2. **The contrast is Cyrillic against everything else.** We have no clean pair
   for a third script in either direction: a Georgian attempt was excluded by
   a measurement gate, and Greek models exist only at 7B and larger, which our
   environment cannot load. Both Kazakh pairs also come from one laboratory.

3. **Tokenisation is controlled in six of the nine pairs.** Measured, not
   assumed. The contrast is visible among the controlled pairs alone: Cyrillic
   targets +9.2 and +8.3, Latin targets +1.5 and -3.1, with segmentation
   identical throughout.

4. **Local models are ≤8B and 4-bit.** Pair comparisons are internally
   controlled, but absolute scores are not directly comparable to
   full-precision serving.

5. **The human baseline is one person on 50 items.** It establishes that the
   task is solvable; it does not set a precise ceiling.

6. **Agreement is not symmetric.** The first annotator's label is always
   "correct" for rows that are in the dataset, so the statistic measures a
   rejection rate rather than two independent judgement distributions.

7. **API models were served through a router.** The serving stack is not
   under our control and four of the six are not open weights, so they are
   reported separately from the 28 open models.

8. **A `difficulty` field was removed, not fixed.** It read as a per-item
   judgement but was a template-level constant, silently defaulted to
   "medium" for rows that had none. It is fully recoverable from the template
   recorded in `notes`, so it carried no information. The built dataset no
   longer contains it.

---

## Negative results

Documented so that others do not repeat them.

**Prompting for the Latin alphabet does not work.** Told explicitly to answer
in Latin script, `Qolda-AVL-5B` barely complies. The behaviour lives in the
weights, not at the prompt level.

**Auditing gold answers by model agreement does not work.** Four Qwen models
agreeing on a different answer crossed the chance ceiling (36 suspects
against 12 expected), but every suspect we checked by hand had a *correct*
gold answer. A permutation test controls for chance agreement, not for
correlated error inside one model family.

---

## Layout

```
data/az_eval_v0.jsonl     the dataset (a build artifact: edit data/raw/)
data/raw/                 drafts and rejected rows, with reasons
src/                      harvesting, verification UI, evaluation, analysis
results/tables/           regenerated reports
results/raw_outputs/      raw model responses, one file per run
tests/                    839 tests
paper/                    manuscript sections, in markdown
paper/latex/              the submitted paper: az-eval.tex, references.bib
paper/figures/            six figures, all generated by src/figures.py
```

The figures are generated from the run data, never drawn by hand. That is
deliberate: which cell of the design damages Azerbaijani is a *result*, and it
changed three times as pairs were added. A hand-drawn figure would still be
showing the version the data refuted.

Build the paper with `sh paper/latex/build.sh`. It needs `clv2025.cls` and
`compling.bst` from the journal, which are the publisher's files and are not
redistributed here.

`data/az_eval_v0.jsonl` is **generated**. Editing it directly is silently
undone by the next build; edit the source under `data/raw/` instead.

---

## Data construction and AI use

No language model authored, translated, or answered any dataset item.

Draft items come from Wikidata templates (parallel by construction) or are
computed by algorithm; every one was then checked by a human before entering
the dataset. Rejected rows are kept with their reasons, because the
acceptance rate is itself a quality figure.

---

## License

Code MIT ([LICENSE](LICENSE)). Data CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)).

If you use this benchmark, please cite it: see [CITATION.cff](CITATION.cff).
