# Robustness, negative results, limitations (draft, sections 8-10)

**Status:** first draft, 2026-09-08.

---

## 8 Robustness

Each subsection answers an objection a reader would reasonably raise, and
each is a separate module in the codebase, so the answer is computed rather
than asserted.

### 8.1 The results do not depend on the prompt

Four prompt styles differ structurally rather than lexically, since a
paraphrase would make the check ceremonial:

| Style | Examples | Labels |
|---|---|---|
| `default` | two | yes |
| `oneshot` | one | yes |
| `plain` | two | no |
| `zeroshot` | none | yes |

Both claims, the language gap and the pair difference, hold in the same
direction with intervals excluding zero across every usable style.

| Style | Pair difference (Kazakh 1, AZ) | 95% CI |
|---|---|---|
| `default` | +23.3 | [20.5, 26.1] |
| `plain` | +19.4 | [17.0, 22.1] |
| `oneshot` | +19.0 | [16.5, 21.5] |
| `zeroshot` | excluded, see below | |

**The magnitude moves and the sign does not.** We therefore state the claim at
the level of direction and significance, not magnitude.

**One condition is excluded, and the reason matters.** In `zeroshot` without
a chat template, the base model returned empty content on 42.7% of English
items; its English score fell from 55.2% to 7.1% and the gap "disappeared".
The gap did not disappear because Azerbaijani improved but because the
English side broke. This is a failed measurement, not a failed claim, and
conflating the two would misreport the result. The `oneshot` style was added
afterwards precisely so that the robustness claim would not rest on two
styles instead of three.

Diagnosing this took a wrong turn worth recording: we first assumed the
missing element was a structural cue (`Answer:`), which `zeroshot` already
contains. The common feature of the working styles is the presence of
*examples*.

*Source: `results/tables/prompts.md`.*

### 8.2 Tokenisation explains the gap in two pairs and cannot in the other two

The strongest competing explanation in the literature holds that the
tokeniser, not the script, governs cross-lingual transfer. We measured
whether the tokeniser is in fact held constant inside each pair, rather than
assuming it.

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

The distinction is categorical rather than a threshold. Control tokens such
as `<|audio_start|>` do not change how text is segmented; ordinary word
pieces (` Almaty`, ` Kazakh`, ` KZT`) do. `Qolda-AVL-5B` adds three audio
control tokens and no word pieces, so its text tokenisation is identical to
its base.

**The whole argument survives restricted to the five controlled pairs.** Two
Cyrillic targets damage Azerbaijani with the tokeniser identical (Kazakh 1
+9.2, Russian 2 +8.3), from different language families and different
laboratories; two Latin targets do not (Turkish 2 +1.5, Latin 3 -3.1); and the
one Cyrillic target that does no damage (Cyrillic 3, +0.1) is also controlled,
so the exception cannot be blamed on segmentation either. The three
extended-vocabulary pairs are confirmatory rather than load-bearing, and two
of the study's three extreme values (-16.0 and +10.6) belong to them.

We previously asserted the general rule that fine-tuning does not change the
tokeniser. Measurement refuted it, and the claim is now computed for every
pair and printed with the result.

*Source: `results/tables/tokenizer.md`.*

### 8.3 Benchmark contamination cannot explain the gap

The 236 algorithmically generated items post-date every model measured here.
The gap persists on that subset for every model able to do the task in
English, with values between 27 and 49 points and *p* = 0.0001.

The claim is precise: these *rows* were not in any training corpus. That the
underlying *facts* appear in training corpora is expected and necessary,
since what we measure is whether that knowledge can be expressed in
Azerbaijani.

Models scoring below 5% in English are marked, and models between 5% and 10%
are marked separately as near-threshold. A model with nothing to lose cannot
show a gap, and its near-zero value must not be read as evidence of good
Azerbaijani support. The threshold was fixed before the results were seen and
was not adjusted afterwards.

*Source: `results/tables/contamination.md`.*

### 8.4 The gap does not come from the composition of the dataset

Mathematics is the largest category and shows the widest gap, so the headline
number could be inflated by composition. Removing the largest category
*increases* the mean gap from 24.7 to 25.6 points, and on the control stratum
from 33.7 to 39.0.

Mathematics dilutes the effect rather than driving it, for a mechanical
reason: a mathematics answer is usually a numeral, numerals have no alphabet,
and the orthographic failure mode cannot operate there.

*Source: `results/tables/composition.md`.*

### 8.5 The dataset is solvable

A speaker who had not seen the dataset scored 70.0% on a stratified sample of
50 items, against 36.0% for the best *local* model on the same items, under
the same scoring pipeline and with lookup prohibited. Blanks (14%) count as
errors, so the figure is a lower bound.

The baseline establishes solvability, not a ceiling, and the distinction is
not rhetorical: `claude-sonnet-5` reaches 74.0% on those same items. A
benchmark that no human can pass would not measure models, which is what this
check is for; it was never intended to bound what a model can achieve.

We correct an earlier claim here. A first baseline, answered by the dataset's
own author, scored 26.5% with 59% blanks, and from it we had concluded that
the dataset was hard for humans as well. That conclusion was an artefact of a
compromised measurement: the annotator had written the items and was applying
a stricter blank-if-unsure policy than a naive respondent would.

*Source: `results/human/baseline_second.md`.*

---

## 9 Negative results

We report these because the failures cost us the most time, and because a
reader's next idea is likely to be one of them.

### 9.1 Prompting for the Latin alphabet does not work

Instructed explicitly to answer in the Azerbaijani Latin alphabet,
`Qolda-AVL-5B` barely complies: the Cyrillic share falls from 91.7% to 88.8%,
and of the seventeen answers that change, one becomes correct.

The behaviour is therefore in the weights, not at the prompt level. This
matters practically: a deployment cannot be fixed by prompt engineering, and
transliteration as post-processing is the cheaper remedy.

### 9.2 Auditing gold answers by model agreement does not work

If several models agree on an answer that differs from the gold, that gold
answer might be wrong. We implemented this, with a permutation test to
establish the chance ceiling: four Qwen models produced 36 suspect items
against a ceiling of 12.

Every suspect we checked by hand had a **correct** gold answer.

The reason is instructive. A permutation test controls for *chance*
agreement, not for *correlated* agreement. Four models from one family share
training data and share mistakes, so they agree on wrong answers far more
often than independence predicts. The method requires genuinely independent
model families, and the statistic that appeared to validate it was measuring
the wrong null.

### 9.3 Searching for more Cyrillic pairs, and what the first search cost

Our Cyrillic evidence originally rested on two pairs adapting to one language
from one laboratory. Our first search for a third concluded that the obstacle
was structural: nearly every Cyrillic adaptation we examined extended the
tokeniser, which breaks the control of Section 8.2, so we stopped looking.

**That conclusion was wrong, and stopping was the most expensive mistake in
the project.** A systematic search over fine-tunes derived from bases we had
already measured produced four usable pairs within an hour, three of them with
an identical tokeniser. They doubled the design and twice overturned its
central claim.

The reasoning error is worth naming, because it is general. We had two gaps:
an uncontrolled tokeniser and a single target language. We ranked them by how
easy each was to describe rather than by how much each threatened the
conclusion. The single-language gap was much the larger threat, and a pair
with an extended tokeniser would still have been worth measuring.

Two candidates were rejected on inspection rather than on results, and both
rejections mattered. `Zubr1.0-VL-4B` states in its own model card that its
weights are unchanged from the base: it is a re-host, not an adaptation, and
would have produced a guaranteed null that looked like evidence. `BgGPT-7B`
(Bulgarian) is a genuine adaptation on a base we had already measured, but no
7B model would load in our environment; the original `Mistral-7B-v0.1`
segfaults there too, so this is an environment limit rather than a property of
the model, and the Bulgarian cell remains unfilled.

---

### 9.4 A Georgian pair we declared and could not use

We attempted a Georgian target to test whether the script effect reaches past
Cyrillic. `Kolkha-Mini-Georgian` writes Georgian script in 17.0% of its
Azerbaijani answers, which is exactly the contamination the marker predicts,
and its scores collapse in both languages.

It is not a measurement. The model answers in full sentences ("The capital of
Turkey is Ankara."), and 42.4% of its scored-wrong English items contain the
gold answer in the raw text, against 1.4% to 4.2% for every other model here.
The score reflects our extractor, not the model's knowledge.

We report the attempt for two reasons. It is the third distinct way a run has
stopped being a measurement in this project, after empty responses and prompt
echo, and the gate that catches it was written for this case and then applied
to all 106 runs. And the pair would have entered the tables at -17.8 points of
excess damage, a number with the wrong sign for our own claim, which is a
useful reminder that gates have to run before the result is read, not after.

---

## 10 Limitations

1. **One Cyrillic-script pair does no damage and we cannot say why.** Adapting
   to Ukrainian leaves Azerbaijani intact while adapting to Kazakh or Russian
   does not. The visible difference is that `MamayLM` barely moved the model at
   all (2.3 points of combined absolute change against 8.4 to 37.8 elsewhere),
   but that restates the result rather than explaining it. Until a second
   Ukrainian pair or a second gentle Cyrillic pair exists, "four of five" is
   the honest form of the claim. A Bulgarian pair (`BgGPT-7B`) would have
   helped and could not be loaded in our environment.

2. **The script contrast is Cyrillic against everything else.** Damage is
   demonstrated for Kazakh and Russian targets, absence of damage for Turkish,
   Norwegian, Ukrainian and a mixed South-East Asian target. We have no clean
   pair for a third script in either direction. A Georgian attempt was
   declared and excluded by a measurement gate (Section 9.4), a Hungarian one
   on the same base as both Russian pairs was excluded by another, and Greek
   candidates exist only at 7B and larger, which our environment cannot load.
   The same-base Latin against Cyrillic comparison therefore remains open.
   "Script matters" therefore means "Cyrillic targets damage Azerbaijani and
   Latin ones do not", and the SEA pair shows that a non-Latin target is not
   by itself enough.

3. **Tokenisation is controlled in six of nine pairs.** The design survives
   because the contrast is visible among the controlled pairs alone, but the
   three extended-vocabulary pairs carry less weight than their numbers
   suggest.

4. **Local models are 8B or smaller and 4-bit quantised.** Pair comparisons
   are internally controlled, so quantisation cannot explain a within-pair
   difference, but absolute scores are not comparable to full-precision
   serving.

5. **API models were served through a router.** The serving stack is outside
   our control, four of the six are not open weights, and results may shift
   as providers change. They are reported separately for this reason.

6. **The human baseline is one person on 50 items.** It establishes
   solvability, not a ceiling. The interval is wide and the respondent was an
   educated adult rather than a representative speaker.

7. **Inter-annotator agreement is asymmetric.** Every row in the dataset was
   accepted by the first annotator, so the statistic measures a rejection
   rate rather than two independent judgement distributions.

8. **The error taxonomy's human half covers two models and 159 items.** It is
   sufficient to contrast the two failure modes but not to estimate
   population proportions.

9. **Short answers only.** The results do not transfer to open-ended
   generation or multi-step reasoning, where formatting and length interact
   with scoring differently.

10. **A `difficulty` field was removed rather than fixed.** It looked like a
   per-item judgement but was a template-level constant: across 26 template
   groups only one carried more than a single value, and rows without one were
   silently defaulted to "medium", which is why 881 of 1006 read as medium.
   Since the value is recoverable from the template recorded in `notes`, it
   carried no information and could only mislead. Raw files may still contain
   it; the built dataset does not.
