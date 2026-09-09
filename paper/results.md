# Results (draft, sections 5-7)

**Status:** first full draft, 2026-09-08. Every number in this file is taken
from a regenerated table under `results/`; none is typed from memory. The
source table is named at the end of each subsection.

---

## 5 The Azerbaijani-English gap

### 5.1 The gap is present in every model we measured

We evaluate 28 open models from 22 independent organisations on all 1006
items, under identical greedy decoding and 4-bit quantisation. Every model
scores lower in Azerbaijani than in English, and every gap is significant at
*p* ≤ 0.0001 under a paired sign-flipping permutation test.

| Model | AZ | EN | Gap | 95% CI |
|---|---|---|---|---|
| `Qwen3.5-4B-Base` | 37.5% | 60.0% | 22.4 | [19.5, 25.3] |
| `Meta-Llama-3-8B` | 33.7% | 52.6% | 18.9 | [16.4, 21.5] |
| `Qwen3-VL-4B-Thinking` | 27.9% | 55.2% | 27.4 | [24.2, 30.3] |
| `Qwen3-VL-4B-Instruct` | 27.1% | 54.6% | 27.6 | [24.3, 30.4] |
| `Turkish-Llama-8b-v0.1` | 23.5% | 44.0% | 20.4 | [17.7, 23.3] |
| `gemma-3-4b-it` | 20.5% | 46.9% | 26.4 | [23.2, 29.8] |
| `Mistral-7B-v0.1` | 17.2% | 52.6% | 35.4 | [32.5, 38.3] |
| `Qwen3.5-4B-Base-Kazakh` | 17.1% | 50.1% | 33.0 | [30.0, 36.2] |
| `Phi-4-mini-instruct` | 11.2% | 44.6% | 33.4 | [30.4, 36.4] |
| `aya-expanse-8b` | 11.1% | 47.4% | 36.3 | [33.2, 39.4] |
| `Qwen3-1.7B` | 6.5% | 28.6% | 22.0 | [19.1, 24.7] |
| `Trendyol-LLM-7b-base-v1.0` | 6.3% | 25.8% | 19.4 | [16.7, 22.2] |
| `mGPT` | 5.6% | 14.7% | 9.1 | [7.0, 11.1] |
| `Qolda-AVL-5B` | 4.4% | 41.5% | 37.1 | [33.8, 40.2] |
| `Phi-3.5-mini-instruct` | 3.1% | 46.6% | 43.5 | [40.3, 46.5] |
| `next-1b` | 2.7% | 16.6% | 13.9 | [11.7, 16.2] |
| `Falcon3-3B-Instruct` | 1.4% | 34.3% | 32.9 | [29.9, 36.0] |
| `granite-3.1-2b-instruct` | 0.3% | 32.2% | 31.9 | [28.9, 34.5] |
| `stablelm-2-1_6b-chat` | 0.2% | 7.6% | 7.4 | [5.7, 9.1] |
| `EuroLLM-1.7B-Instruct` | 0.1% | 17.3% | 17.2 | [14.9, 19.6] |
| `SmolLM2-1.7B-Instruct` | 0.0% | 24.6% | 24.6 | [21.9, 27.6] |
| `bloomz-1b7` | 0.0% | 3.9% | 3.9 | [2.8, 5.1] |

Two readings of this table are wrong and we rule them out explicitly.

**A small gap does not indicate good Azerbaijani support.** `bloomz-1b7` has
the smallest gap in the table (3.9 points) because it scores 3.9% in English:
it has nothing to lose. The gap is interpretable only for models that can do
the task in English at all, which is why the English column is printed beside
it rather than in a separate table.

**The gap is not a small-model artefact.** The strongest Azerbaijani model,
`Qwen3.5-4B-Base`, still loses 22.4 points, and the strongest English model
in the set loses more, not less.

*Source: `results/tables/rq1.md`, `results/tables/main.md`.*

### 5.2 The gap is a language gap, not a knowledge gap

The most natural objection to a benchmark of this kind is that the items are
locally specific, so that a model fails in Azerbaijani because it does not
know the fact in any language. We answer this with a control stratum of 708
items (70% of the dataset) whose subject matter is universal by construction:
world facts, chemical elements, and computed mathematics. Models demonstrably
know these facts in English.

On the control stratum the gap does not shrink. It widens:

| Model | Gap, all items | Gap, control stratum |
|---|---|---|
| `Phi-3.5-mini-instruct` | 43.5 | **59.9** |
| `Qolda-AVL-5B` | 37.1 | **50.4** |
| `aya-expanse-8b` | 36.3 | **48.7** |
| `Qwen3.5-4B-Base` | 22.4 | **29.5** |

The failure is therefore in producing Azerbaijani, not in possessing the
knowledge.

*Source: `results/tables/control.md`.*

### 5.3 The gap does not come from the composition of the dataset

Mathematics is the largest category (264 of 1006 items, 26%), and the gap is
widest there, so the headline number could in principle be inflated by
composition. We tested this by removing the largest category and recomputing.

| Subset | n | Mean gap |
|---|---|---|
| all items | 1006 | 24.7 |
| without mathematics | 742 | **25.6** |
| control stratum | 708 | 33.7 |
| control stratum without mathematics | 464 | **39.0** |

Removing mathematics makes the gap larger, not smaller. Mathematics dilutes
the effect rather than driving it, and the reason is mechanical: a
mathematics answer is usually a numeral, and numerals have no alphabet, so
the orthographic failure mode described in Section 7 cannot operate there.

*Source: `results/tables/composition.md`.*

### 5.4 The gap narrows sharply with model strength

All 22 models above are 8B parameters or smaller and were run in 4-bit
quantisation, so the obvious question is whether the gap is an artefact of
small open models. We therefore measured six further models through a
commercial routing API under the identical protocol: same items, same prompt,
same 32-token budget, greedy decoding. Five are substantially larger; the
sixth, `qwen3-8b`, is deliberately the same size as the local class but served
at full precision, which makes it the control for quantisation.

| Model | Organisation | AZ | EN | Gap | 95% CI |
|---|---|---|---|---|---|
| `gpt-4o` | OpenAI | 66.7% | 70.4% | **3.7** | [1.0, 6.4] |
| `claude-sonnet-5` | Anthropic | 65.5% | 71.0% | **5.5** | [3.0, 7.8] |
| `deepseek-v3.2` | DeepSeek | 64.1% | 70.0% | **5.9** | [3.5, 8.3] |
| `llama-4-maverick` | Meta | 63.6% | 68.5% | **4.9** | [2.6, 7.5] |
| `qwen3-235b-a22b` | Alibaba | 48.8% | 64.0% | 15.2 | [12.0, 18.2] |
| `qwen3-8b` | Alibaba | 28.1% | 55.7% | 27.5 | [24.6, 30.4] |
| `Qwen3.5-4B-Base` (local, best) | Alibaba | 37.5% | 60.0% | 22.4 | [19.5, 25.3] |

Three findings follow, and the second is the one we consider most useful.

**The gap narrows sharply, and at the very top we stop being able to
establish it.** It falls from 27.5 points at 8B to 3.7 points for `gpt-4o`.
That last value is where the honest reading matters. Its bootstrap interval,
[1.0, 6.4], excludes zero; its Holm-corrected *p* within the exploratory
family is 0.10, which does not. Under any looser normalisation chain the
interval covers zero as well ([-0.6, 4.6] at LENIENT).

We therefore do not claim a gap for `gpt-4o` individually. What the six models
support is a claim about the class: five of the six show Holm-significant
gaps, and the trend across them is clear. Declaring the sixth significant on
an uncorrected interval would contradict the correction policy we set out in
Section 4.4, and we are not willing to apply that policy selectively.

**The human baseline is not a ceiling either, and an earlier draft of this
section said it was.** On the 50 items answered by a speaker, `claude-sonnet-5`
scores 74.0% against the human's 70.0%. Comparing `gpt-4o`'s 66.7% on 1006
items with a 50-item human figure, as we previously did, is not a valid
comparison in the first place; the matched-item table in
`results/human/baseline_second.md` is the one to read.

**Size alone does not predict the gap.** `qwen3-235b-a22b` is far larger
than any of the four leading models yet its gap is three to four times wider
(15.2 against 3.7-5.9), and it is the only one of the six that produced empty
responses. In the other direction, `qwen3-8b` at full precision through the
same API shows a 27.5-point gap, close to its 4-bit local peers, so neither
the serving stack nor quantisation accounts for the difference between the
groups. Azerbaijani competence therefore does not arrive automatically with
scale; it appears to depend on what the training mixture contains. For a
practitioner choosing a model for Azerbaijani, parameter count is a poor
proxy.

**The narrow gap is not one laboratory's peculiarity.** Four models from
four independent organisations, trained on different data, land in a band of
3.1 points in Azerbaijani (63.6 to 66.7) and 2.2 points on the gap (3.7 to
5.9). Convergence this tight across OpenAI, Anthropic, DeepSeek and Meta is
not plausibly a property of any single training pipeline.

**Caveats, stated plainly.** These six runs used a routing API, so the
serving stack is not under our control and four of the six are not open
weights; they are reported separately from the 28 open models for that
reason.
`qwen3-235b-a22b` returned empty content on 59 Azerbaijani and 13 English
items (5.9% and 1.3%); excluding those rows its gap is 12.0 rather than 15.2,
and we report both.

**A protocol limitation worth recording.** Three endpoints we intended to
include (`gpt-5`, `gpt-5-mini`, `gemini-3.1-pro-preview`) refuse to disable
reasoning, returning `Reasoning is mandatory for this endpoint and cannot be
disabled`. Under a 32-token budget the entire allowance is consumed by
internal reasoning and the visible answer is empty. Raising the budget for
those models alone would have made them incomparable with the other 28, so
they were excluded rather than run under different conditions. Short-answer
benchmarking of such endpoints is not currently possible without changing the
protocol for every model.

*Source: `results/tables/rq1.md`, `results/raw_outputs/unsupported_protocol/README.md`.*

### 5.5 The dataset is solvable

A benchmark that no one can solve does not measure models; it merely holds
all of them near zero. We therefore measured a human baseline on a stratified
sample of 50 items, answered by a speaker who had not seen the dataset, under
the same scoring pipeline as the models and with lookup prohibited.

| | Score on the same 50 items (TRANSLIT) |
|---|---|
| `claude-sonnet-5` | **74.0%** |
| **Human** | **70.0%** |
| `deepseek-v3.2` | 68.0% |
| `llama-4-maverick` | 66.0% |
| `gpt-4o` | 66.0% |
| `qwen3-235b-a22b` | 52.0% |
| `Qwen3.5-4B-Base` (best local) | 36.0% |
| six models | 0.0% |

The human left 7 of 50 items blank (14%), and blanks are scored as errors, so
this figure is a lower bound on human performance under the stated rules.

**The baseline establishes solvability, not a ceiling, and the table is
printed in full for that reason.** One model scores above the human and three
more sit within four points. Showing only the models below the human would
have made the same data support a claim it does not support.

We report a correction here. An earlier version of this baseline was answered
by the dataset's own author, who had seen every item and left 59% blank,
scoring 26.5%; from that measurement we had concluded that the dataset was
hard for humans too. That conclusion was an artefact of a compromised
measurement and does not survive an independent annotator.

**Limitation.** One annotator, 50 items, wide interval. The figure
establishes that the task is solvable; it does not establish a precise
ceiling.

*Source: `results/human/baseline_second.md`.*

### 5.6 Multiple choice and free-form answering are close to dissociated

The imported TUMLU-az rows exist for one measurement: the same 521 items put
to the same models in both formats, under identical decoding. This is what
justifies building a free-form set when multiple-choice sets for the language
already exist.

| Model | MCQ | Short answer | Difference |
|---|---|---|---|
| `Qwen3-1.7B` | 37.0% | 2.9% | +34.2 |
| `Qwen3-VL-4B-Instruct` | 44.9% | 7.5% | +37.4 |
| `Qwen3-VL-4B-Thinking` | 43.2% | 5.8% | +37.4 |
| `Qolda-AVL-5B` | 39.0% | 0.2% | +38.8 |

All four differences have *p* = 0.0001. **The raw difference overstates the
effect and we do not rest the claim on it**, because four-way choice pays 25%
for guessing while free-form answering pays almost nothing.

The chance-immune statistic is retention: among the items a model answers
correctly under multiple choice, how many does it also produce correctly in
free form?

| Model | Correct under MCQ | Also correct free-form |
|---|---|---|
| `Qwen3-1.7B` | 193 | 3.6% |
| `Qwen3-VL-4B-Instruct` | 234 | 10.3% |
| `Qwen3-VL-4B-Thinking` | 225 | 10.2% |
| `Qolda-AVL-5B` | 203 | 0.5% |

Nine out of ten items a model can recognise, it cannot produce. The two
formats are therefore not two ways of measuring one ability, and a
multiple-choice score is not a usable estimate of what a model will do when
asked to answer.

This also bears on `Qolda-AVL-5B` specifically. Its 0.5% retention rises to
3.4% under transliteration, which is the same orthographic story reported in
Section 7 appearing in an independent dataset.

*Source: `results/format_contrast/tables.md`.*

---

## 6 Relatedness or script?

### 6.1 The question

Two open models adapted to Kazakh degrade sharply in Azerbaijani. Kazakh
differs from Azerbaijani in two ways at once: it is a related Turkic language,
and it is written in Cyrillic where Azerbaijani uses Latin. No conclusion
about cause is possible while both factors move together.

We separate them with eleven declared fine-tuning pairs, nine of which pass
our measurement gates. Each is a base model and a variant adapted from it, and
they cross two factors: whether the adaptation target
is genealogically related to Azerbaijani, and whether it shares its script.

| Pair | Base | Adapted | Target | Related? | Script |
|---|---|---|---|---|---|
| Kazakh 1 | `Qwen3-VL-4B-Thinking` | `Qolda-AVL-5B` | Kazakh | yes | Cyrillic |
| Kazakh 2 | `Qwen3.5-4B-Base` | `Qwen3.5-4B-Base-Kazakh` | Kazakh | yes | Cyrillic |
| Turkish 1 | `Mistral-7B-v0.1` | `Trendyol-LLM-7b-base` | Turkish | yes | Latin |
| Turkish 2 | `Meta-Llama-3-8B` | `Turkish-Llama-8b` | Turkish | yes | Latin |
| Cyrillic 3 | `gemma-3-4b-it` | `MamayLM-Gemma-3-4B-IT` | Ukrainian | no | Cyrillic |
| Russian 1 | `Qwen3-4B` | `RuadaptQwen3-4B-Hybrid` | Russian | no | Cyrillic |
| Russian 2 | `Qwen3-4B` | `QVikhr-3-4B-Instruction` | Russian | no | Cyrillic |
| Latin 3 | `gemma-3-4b-it` | `borealis-4b` | Norwegian | no | Latin |
| SEA | `Qwen3-VL-4B-Instruct` | `Qwen-SEA-LION-v4-4B-VL` | SE Asian | no | mixed |

Turkish is a *closer* relative than Kazakh while sharing Azerbaijani's script,
so a relatedness account predicts more damage from the Turkish pairs, not
less. Six target-language groups, eight laboratories, seven distinct base models.

The SEA pair is deliberately mixed rather than clean. `SEA-LION` is adapted to
Vietnamese, Indonesian, Malay and Filipino (Latin) together with Thai, Burmese
and Tamil (three non-Latin scripts), and it shares its base with Kazakh 1, the
pair with the largest damage in the study. It is the closest thing we have to
a test of whether *any* non-Latin adaptation target is enough.

**The last seven pairs were added after the first four were analysed, and we
say so rather than presenting eleven pre-registered pairs.** Each was chosen to
attack a limitation of the previous round: Cyrillic 3 because both Cyrillic
pairs adapted to one language from one laboratory; the two Russian pairs
because Cyrillic 3 turned out to be an unusually gentle adaptation; Latin 3 to
fill the last empty cell. Every pair was declared in the module, growing the
confirmatory family from 32 to 88 tests, before its result was computed.
Enlarging a Holm family can only cost significance, never grant it.

### 6.2 Measuring excess damage rather than absolute loss

Any fine-tuning degrades other languages to some extent, so absolute
Azerbaijani loss cannot answer the question. We report **excess damage**:
Azerbaijani loss minus English loss, paired item by item, with a bootstrap
interval. English loss serves as the model's own measure of general
forgetting.

| Pair | Related | Script | AZ loss | EN loss | Excess damage | 95% CI |
|---|---|---|---|---|---|---|
| Kazakh 1 | yes | Cyrillic | +23.4 | +13.7 | **+9.8** | [+6.2, +13.4] |
| Kazakh 2 | yes | Cyrillic | +20.4 | +9.9 | **+10.6** | [+7.0, +14.2] |
| Turkish 1 | yes | Latin | +10.9 | +26.9 | -16.0 | [-19.2, -12.8] |
| Turkish 2 | yes | Latin | +10.2 | +8.7 | +1.5 | [-1.0, +4.5] |
| Russian 1 | no | Cyrillic | +2.8 | -3.1 | **+5.9** | [+2.9, +8.8] |
| Russian 2 | no | Cyrillic | +1.7 | -0.5 | +2.2 | [-0.7, +5.1] |
| Latin 3 | no | Latin | -1.1 | +2.0 | -3.1 | [-6.1, -0.2] |
| SEA | no | mixed | -1.1 | +0.1 | -1.2 | [-3.3, +0.7] |
| Cyrillic 3 | no | Cyrillic | *not measurable under this prompt, see 6.6* | | | |

Five of the eight also have a second measurement under the `oneshot` prompt,
which is the only one valid for Cyrillic 3:

| Pair | AZ loss | EN loss | Excess damage | 95% CI |
|---|---|---|---|---|
| Kazakh 1 | +19.1 | +10.0 | **+9.2** | [+6.0, +12.5] |
| Russian 1 | +8.6 | -1.5 | **+10.1** | [+7.0, +13.0] |
| Russian 2 | +7.6 | -0.8 | **+8.3** | [+5.4, +11.4] |
| Cyrillic 3 | +1.2 | +1.1 | +0.1 | [-2.9, +3.2] |
| Latin 3 | -0.1 | +3.0 | -3.1 | [-6.0, -0.5] |
| SEA | -0.7 | +0.2 | -0.9 | [-2.8, +1.1] |

Kazakh 1 anchors both tables and agrees across them (+9.8 against +9.2), as
does Latin 3 (-3.1 in both). The Russian pairs move a great deal between
styles (+5.9 to +10.1, +2.2 to +8.3) while keeping their sign, which is why
Section 8.1 states this paper's pair claims at the level of direction and
significance rather than magnitude.

### 6.3 Relatedness predicts nothing; script predicts eight of nine

Sorting the same nine pairs by each factor in turn is the whole argument.

**By relatedness, the split is exactly even and therefore uninformative.**

| | damages Azerbaijani | does not |
|---|---|---|
| Related target (Turkic) | Kazakh 1, Kazakh 2 | Turkish 1, Turkish 2 |
| Unrelated target | Russian 1, Russian 2 | Cyrillic 3, Latin 3, SEA |

Two of four each way among related targets, two of five among unrelated ones.
The closest relative we could find, Turkish, does no damage; a completely
unrelated Slavic language, Russian, does. **Relatedness carries no predictive
power at all**, which is a stronger statement than the one an earlier draft of
this paper made and the opposite of the one before it.

**By script, eight of nine fall in line.**

| | damages | does not |
|---|---|---|
| Cyrillic target | Kazakh 1, Kazakh 2, Russian 1, Russian 2 | Cyrillic 3 |
| Latin target | | Turkish 1, Turkish 2, Latin 3 |
| Mixed target | | SEA |

Every Latin-script adaptation leaves Azerbaijani intact. Four of five
Cyrillic-script adaptations damage it, by 8 to 11 points of excess damage
across three target-language and laboratory combinations.

**A non-Latin target is not sufficient, which the SEA pair establishes.**
`SEA-LION` is adapted to Thai, Burmese and Tamil alongside four Latin-script
languages, shares its base with the most damaged pair in the study, and costs
Azerbaijani nothing (-0.9, [-2.8, +1.1]). If merely training on a
different-script language were enough, this pair should show it.

**The one exception is real and we do not explain it away.** Adapting to
Ukrainian costs Azerbaijani nothing measurable. The most visible difference is
that `MamayLM` barely moved the model in any direction: its combined absolute
change across both languages is 2.3 points, against 8.4 to 37.8 for every
other pair. But "the model hardly changed" is close to restating "Azerbaijani
hardly changed", so we record it as an observation rather than an explanation.

### 6.4 One marker separates all nine pairs

There is a variable that does what neither factor above manages: whether the
adapted model starts writing Azerbaijani answers in Cyrillic.

| Pair | Cyrillic share of AZ answers | Excess damage |
|---|---|---|
| Kazakh 1 | 84.9% | +9.2 |
| Kazakh 2 | 18.9% | +10.6 |
| Russian 1 | 13.8% | +10.1 |
| Russian 2 | 7.7% | +8.3 |
| SEA | 0.2% | -0.9 |
| Cyrillic 3 | 0.0% | +0.1 |
| Turkish 1 | 0.0% | -16.0 |
| Turkish 2 | 0.0% | +1.5 |
| Latin 3 | 0.0% | -3.1 |

The separation is complete: every pair that emits Cyrillic above its base rate
is damaged, every pair that does not is not, and the Ukrainian exception stops
being an exception. `SEA-LION` sits at its base model's own 0.2%, so it counts
as emitting none. A Cyrillic-script target usually pushes a model into writing
Cyrillic Azerbaijani, but not always, and the damage follows the writing
rather than the target.

**We stop short of calling this the mechanism, because transliteration does
not behave as a purely orthographic account requires.** If the damage were
only the wrong alphabet, mapping Cyrillic back to Latin should recover it. It
recovers 2.5 of Kazakh 1's 19.1 points, and essentially none of Russian 1's
8.6 (8.6 to 8.4) or Russian 2's 7.6 (unchanged). The Cyrillic answers of the
Russian-adapted models are wrong in content as well as in script.

Cyrillic emission is therefore a reliable **marker** of the damage and not a
sufficient account of it. Section 7 examines what the errors actually contain.

*Source: `results/tables/pairs.md`, `results/tables/pairs_oneshot.md`.*

### 6.5 Tokenisation is controlled in six of the nine pairs

The strongest competing explanation in the literature holds that the tokeniser
matters more than the script for cross-lingual transfer (Tufa et al., 2024).
We measured, rather than assumed, whether the tokeniser is held constant inside
each pair.

| Pair | Added word pieces | Added control tokens | Control holds? |
|---|---|---|---|
| Kazakh 1 | 0 | 3 | **yes** |
| Kazakh 2 | 16 000 | 0 | no |
| Turkish 1 | 12 312 | 0 | no |
| Turkish 2 | 0 | 0 | **yes** |
| Cyrillic 3 | 0 | 0 | **yes** |
| Russian 1 | 43 047 | 21 | no |
| Russian 2 | 0 | 0 | **yes** |
| Latin 3 | 0 | 0 | **yes** |
| SEA | 0 | 0 | **yes** |

The distinction is categorical rather than a threshold. Control tokens such as
`<|audio_start|>` do not change how text is segmented; ordinary word pieces
(` Almaty`, ` Kazakh`, ` KZT`) do. `Qolda-AVL-5B` adds three audio control
tokens and no word pieces, so its text tokenisation is identical to its base.
`RuadaptQwen3-4B-Hybrid` sits at the other extreme: its vocabulary was
deliberately rebuilt for Russian, which is why it adds 43 047 pieces.

**The argument survives restricted to the six controlled pairs alone**, and
this is the cleanest form of it:

| Pair | Script | Tokeniser | Excess damage |
|---|---|---|---|
| Kazakh 1 | Cyrillic | identical | **+9.2** |
| Russian 2 | Cyrillic | identical | **+8.3** |
| Cyrillic 3 | Cyrillic | identical | +0.1 |
| Turkish 2 | Latin | identical | +1.5 |
| Latin 3 | Latin | identical | -3.1 |
| SEA | mixed | identical | -0.9 |

Two Cyrillic targets from different language families (Turkic and Slavic),
different laboratories and different base models both damage Azerbaijani with
the tokeniser held exactly constant, while both Latin targets and the mixed
target do not. Whatever the tokeniser contributes elsewhere, it is not what
produces this contrast. The two Cyrillic bases are both Qwen models, which we
note rather than overstate as independence.

The three uncontrolled pairs are confirmatory rather than load-bearing. It is
worth noting that two of the three extreme values in the study (-16.0 and
+10.6) belong to them.

*Source: `results/tables/tokenizer.md`.*

### 6.6 Three measurement failures, and how each was caught

The first two share a shape: the measurement broke on **one side** of a
two-sided comparison, which is the only kind of error this design cannot
absorb, because the quantity reported is a difference. The third broke both
sides at once and would have entered the tables as a large negative number.

**The chat template asymmetry.** Two of the first four pairs were initially
measured with the base model receiving a chat template while the adapted
model, having none, received the raw prompt. A pair comparison is meaningless
unless both halves are asked identically, so we re-ran both base models
without a chat template. The correction moved the two Kazakh pairs in opposite
directions and left the conclusion unchanged. It also contradicted our
expectation: the template was not helping the base models but hurting them,
because neither is instruction-tuned.

**The example-echo artefact, which agreed with us.** The fifth pair first
produced **+7.0 points of excess damage**, comfortably confirming the
hypothesis it was built to test. It was an artefact.

Under the `default` prompt, which carries two few-shot examples, `MamayLM`
reproduces the two example answers on their own lines before giving the real
one, so a question whose answer is `120` is answered with the two example
answers followed by `120`. It does this on 67.8% of Azerbaijani items and **0%
of English items**; the base model does it on neither. Our extractor takes the
first line, so the model was scored wrong on items it had in fact answered
correctly: 55% of the supposedly lost items carry the gold answer in the raw
text.

The cause is the number of examples, not their content:

| Prompt style | Examples | Example-echo rate, AZ |
|---|---|---|
| `default` | two | 67.8% |
| `plain` | two | 100% |
| `oneshot` | one | 0.3% |
| `zeroshot` | none | 0% |

Both halves of the pair were re-run under `oneshot`, where all four runs are
clean (no empty responses, at most 0.3% echo), and the excess damage falls
from +7.0 to +0.1.

**A fourth attempt failed a different gate, and it is worth one paragraph
because it validates the gates rather than the claim.** We obtained access to a
Hungarian-adapted model (`Racka-4B`) built on `Qwen3-4B`, the same base as both
Russian pairs, which would have given a same-base Latin against Cyrillic
comparison, the one contrast the design still lacks. Its tokeniser turned out
to be interesting on its own: the vocabulary is the *same size* as the base's
but 32 768 entries differ, so a size check would have called it unchanged.

The model never answers. Given few-shot examples it continues the pattern by
inventing further question-and-answer pairs instead of responding, and it does
this under all four prompt styles. The question-echo rule, written the previous
day for an unrelated Georgian model, catches it at 68.4% of Azerbaijani items
against 1.6% of English ones. That is the same one-sided break as every other
failure in this section.

It also exposed a hole in our own code. The pair report was checking only the
extraction gate, and `Racka-4B` passes that one (12.0%). A pair can fail any
gate, so the check now runs all of them; the same fix retroactively removed the
Ukrainian pair's invalid `default` figure from the table, which had been
sitting there because only one gate was consulted.

**We report this at length because the artefact pointed our way.** A wrong
number that contradicts the hypothesis gets investigated as a matter of
course; a wrong number that confirms it often does not. The check that caught
this one was not statistical but mechanical: read what the model actually
emitted before trusting what it scored. Had we not, the paper would have
reported a confirmation of a claim its own data refutes.

**A third pair was declared and then excluded by a gate, which is what gates
are for.** We attempted a Georgian target (`Kolkha-Mini-Georgian`, base
`Qwen3-1.7B`) to test whether the script effect extends past Cyrillic. Its
Azerbaijani fell from 6.5% to 0.1% and its English from 28.6% to 4.4%, which
looks like a model destroyed by adaptation and would have entered the table as
-17.8 points of excess damage.

Reading its output shows something else. Asked for the capital of Turkey it
answers "The capital of Turkey is Ankara.", which is correct and which our
exact-match scoring rejects. Across its English errors, **42.4% contain the
gold answer in the raw text**; the same figure is 1.4% to 4.2% for every other
model in the study, including `Mistral-7B-v0.1` and `Trendyol`, which produce
full sentences in 100% and 99.9% of items respectively and still score
normally because the extractor handles them.

So response length is not the pathology and we do not gate on it. The gate is
on *recoverable errors*: the share of scored-wrong items whose gold answer is
present in the raw text. Measured over 106 runs, the distribution is 42.4% and
then a 26-point gap to 16.4%, so the threshold sits at 30%, inside the only
gap there is. One run fails it.

The pair remains declared in the module and is reported as excluded rather
than deleted, so the attempt and its reason stay in the record.

*Source: `results/tables/extraction_gate.md`, `src/extraction_gate.py`,
`results/raw_outputs/invalid_chat_template/README.md`,
`results/tables/pairs_oneshot.md`.*

---

## 7 What the failures look like

### 7.1 Two failure modes, not one

"The model is bad at Azerbaijani" conflates at least two different events,
and separating them is practically consequential because only one of them is
recoverable by post-processing.

| Mode | What happens | Does normalisation help? |
|---|---|---|
| **Orthographic** | the model knows the fact and writes it in Cyrillic | yes, transliteration recovers it |
| **Capability** | the model cannot produce the answer at all | no |
| **Both at once** | the model writes Cyrillic *and* the wrong content | no |

The third row is the one the Russian pairs forced us to add, and Section 7.3
reports it.

We separate them with four nested normalisation chains, each adding exactly
one transformation and applied symmetrically to prediction and gold:

```
STRICT  -> MORPH     + suffix stripping
MORPH   -> LENIENT   + diacritic folding
LENIENT -> TRANSLIT  + Cyrillic-to-Latin transliteration
```

Because the chain is nested, the question "which step recovered this error"
has an unambiguous answer, and that answer is the cause.

### 7.2 The two Kazakh models fail differently

| Model | STRICT | MORPH | LENIENT | TRANSLIT | Recovered by script |
|---|---|---|---|---|---|
| `Qolda-AVL-5B` | 4.4% | 4.4% | 4.4% | 9.2% | **+4.7** |
| `Qwen3.5-4B-Base-Kazakh` | 17.1% | 17.7% | 17.9% | 19.2% | +1.3 |

`Qolda-AVL-5B` produces 85.9% of its Azerbaijani answers in Cyrillic;
transliteration more than doubles its score. `Qwen3.5-4B-Base-Kazakh`
produces 18.9% in Cyrillic, and transliteration barely moves it. Two models
adapted to the same language, by the same laboratory, fail in measurably
different ways.

*Source: `results/tables/modes.md`, `results/tables/pairs.md`.*

### 7.3 Cyrillic output is not always an orthographic failure

The Russian-adapted models complicate the tidy two-mode picture, and the
complication is worth stating because it bears directly on the marker in
Section 6.4.

| Model | Cyrillic share of AZ answers | AZ loss STRICT | AZ loss TRANSLIT | Recovered |
|---|---|---|---|---|
| `Qolda-AVL-5B` (Kazakh) | 84.9% | +19.1 | +16.6 | +2.5 |
| `RuadaptQwen3-4B-Hybrid` (Russian) | 13.8% | +8.6 | +8.4 | +0.2 |
| `QVikhr-3-4B-Instruction` (Russian) | 7.7% | +7.6 | +7.6 | 0.0 |

A purely orthographic reading predicts that transliteration recovers roughly
the Cyrillic share. It does so partially for the Kazakh model and not at all
for the Russian ones. Inspecting the Russian errors shows why: the Cyrillic
answers are usually wrong in content too, so restoring the alphabet leaves a
wrong answer in the right alphabet. The model returns `Москва` where the gold
is `Moskva`, which transliteration does repair, but it also returns `İstanbul`
for a question about Ankara, which nothing repairs.

**This is why Section 6.4 calls Cyrillic emission a marker rather than a
mechanism.** It separates the damaged pairs from the undamaged ones perfectly,
yet the damage it marks is not, in general, the recoverable kind.

*Source: `results/tables/modes.md`, `results/tables/pairs_oneshot.md`.*

### 7.4 An automatic taxonomy, and what it leaves to a human

The chain also yields an error taxonomy without human judgement: whichever
step repairs an error names its cause. On a stratified sample of 100 errors
per model:

| Model | Target | Orthographic | Left to a human |
|---|---|---|---|
| `Qolda-AVL-5B` | Kazakh / Cyrillic | **95%** | 4% |
| `Qwen3.5-4B-Base-Kazakh` | Kazakh / Cyrillic | 21% | 61% |
| `Turkish-Llama-8b-v0.1` | Turkish / Latin | 0% | 87% |
| `Falcon3-3B-Instruct` | (base) | 1% | 98% |

One bucket deserves comment. Transliterating `Вашингтон` yields `vaşington`
while the gold answer is `vaşinqton`: Cyrillic `г` maps to Latin `g`, but
Azerbaijani writes that sound as `q`. The model knows the fact and the chain
still fails to credit it. Counting such rows as factual errors would inflate
the factual category, so they are reported separately.

### 7.5 The human half: a second wrong-language failure

The machine is silent wherever the chain does not help, which is 87-98% of
errors for capability-type models. We labelled 159 of those residual errors
by hand, across two models chosen to span the two modes.

| Label | Kazakh-adapted | Turkish-adapted |
|---|---|---|
| factual | 29 (41%) | 37 (42%) |
| format | 4 (6%) | 1 (1%) |
| **wrong language** | **1 (1%)** | **23 (26%)** |
| unrelated | 37 (52%) | 27 (31%) |

This completes the picture. The Kazakh-adapted model fails by writing in
Cyrillic; the Turkish-adapted model fails by writing **in Turkish**
(`yapon dili` → `Japonca`, `güləşçi` → `Güreş`).

Both are the same kind of event: the model has the fact and emits it in the
wrong linguistic form. The difference is decisive for measurement.
Transliteration recovers the Cyrillic case; **no normalisation can recover
the Turkish case**, because the alphabet is already correct. That is a claim
about normalisation, not about detectability, and the next paragraphs
separate the two.

This has a consequence for benchmark design beyond the present study, and it
needs stating carefully, because the strong version is false. The failure mode
itself is known and measurable: Marchisio et al. (2024) call it language
confusion and define word- and line-level pass rates for it.

What we show is that the standard word-level detector is **structurally blind
to this particular pair**. It flags, for a Latin-script target, any character
outside that language's Unicode range; but the Turkish alphabet is a subset of
the Azerbaijani one, which adds only `ə`, `x` and `q`. A Turkish word cannot
leave the Azerbaijani range, so the detector is silent by construction.

Applied to our 159 human-labelled errors, the rule fires on 2 of the 24
wrong-language rows and misses 92%. Both hits contain `w`, a letter in neither
alphabet, so what it catches is English intrusion rather than the Turkish
confusion.

| | n |
|---|---|
| Labelled wrong-language | 24 |
| Word-level rule fires | 2 |
| Missed | 22 (92%) |

The practical statement is therefore narrower than "no metric catches this"
and more useful: exact-match accuracy does not distinguish this failure from a
knowledge failure, transliteration cannot repair it, and the off-the-shelf
script-range detector does not see it. A detector for this pair must compare
against a Turkish lexicon rather than an alphabet.

*Source: `results/tables/language_confusion.md`.*

**Disclosure.** 24 of these rows were relabelled after the first pass, from
`format` to `wrong language`, after the criterion was tightened: an answer
that expresses the same concept in another language is a language error, not
a formatting error, whereas an answer that is simply wrong remains a factual
error even if it contains a Turkish place name. Each relabelled row retains
its original label in a comment field.

*Source: `results/tables/errors.md`, `results/tables/errors_human.md`.*

---

## Editorial notes

- §6.4 could be moved to the limitations section if space is short.
- §7 should end with a forward reference to the negative results (§9), since
  prompt-based script forcing is the natural thing a reader would try next.

The majority baseline (0.8%) and mean answer length (1.34 words) are stated in
§3.1 and are not repeated here.
