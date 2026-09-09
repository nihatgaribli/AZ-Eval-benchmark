# Introduction (draft, section 1)

**Status:** third draft, 2026-09-09. The central claim changed twice in one
day as pairs five to ten arrived. The framing below is the one nine measured pairs
support. See the note at the end, which records both changes.

---

## 1 Introduction

Azerbaijani is spoken by roughly ten million people and is not absent from
multilingual evaluation: TUMLU contributes 735 items and INCLUDE 6,937. Both,
however, are multiple choice and neither is parallel, so neither can answer
the question this paper asks: how a single model's Azerbaijani compares with
its own English on the same item. Selecting among four options is also not
the same skill as producing an answer: on identical items, only 0.5% to 10.3%
of what a model gets right under multiple choice is also produced correctly in
free form.

Its closest well-resourced Turkic relative, Kazakh, has both a benchmark and
several openly released adapted models. That asymmetry suggests an appealing
shortcut: adapt a Kazakh model and inherit its Turkic competence.

We built a benchmark to test that shortcut, and it does not work. Adapting a
model to Kazakh makes it *worse* at Azerbaijani than the model it was adapted
from, beyond what general forgetting explains.

The cause is the script, and relatedness has nothing to do with it. Turkish is
a closer relative than Kazakh and shares the Latin alphabet; adapting to it
costs Azerbaijani nothing. Russian is not related to Azerbaijani at all and is
written in Cyrillic; adapting to it costs 8 to 10 points. Across nine measured pairs
**relatedness splits exactly evenly and predicts nothing, while every
Latin-script target is harmless and four of five Cyrillic-script targets are
not.**

Establishing that required a benchmark, and building the benchmark produced
findings of its own. This paper reports both.

### 1.1 Where the problem actually lives

We measure 34 models, and the picture is not uniform. Among 28 open models of
8B parameters or smaller, Azerbaijani trails English by 3.9 to 43.5 points,
every gap significant at *p* ≤ 0.0001. Among five large models accessed
through a commercial API, the gap narrows to between 3.7 and 15.2 points. A
sixth API model, `qwen3-8b`, is the same size as the local class and behaves
like it (27.5 points) despite full-precision serving.

This is a more precise claim than "Azerbaijani is poorly supported", and we
state it precisely because the imprecise version is now false. Three things
follow.

**The problem is concentrated in the models people actually deploy locally.**
Low-resource language work is done disproportionately with open, small,
quantised models: they run on one GPU, they cost nothing per call, and they
can be used where data cannot leave the building. That is exactly the class
where the gap is 20 to 40 points.

**At the very top the gap becomes hard to establish, and we report that
rather than overstate it.** For `gpt-4o` the Azerbaijani-English difference is
3.7 points with a bootstrap interval of [1.0, 6.4], but it does not survive
Holm correction within its family (*p* = 0.10), and under any looser
normalisation the interval covers zero. We therefore claim a gap for the
*class* of models we measure, not for the single strongest one.

Nor is the human baseline a ceiling. On the 50 items a speaker answered,
`claude-sonnet-5` scores 74.0% against the human's 70.0%. The frontier is
past the point where "models cannot do Azerbaijani" is a defensible summary,
which is precisely why the interesting question is where the failure remains.

**Model size does not predict Azerbaijani ability.** `qwen3-235b-a22b` is
larger than every one of the four leading models yet its gap is three to four
times wider. Four models from four independent organisations converge within
3.1 points of each other, while a much larger model sits far outside that
band. Whatever produces Azerbaijani competence, it is not parameter count.

### 1.2 Contributions

1. **AZ-Eval**, 1006 short-answer items stated in parallel Azerbaijani and
   English, to our knowledge the first open parallel, free-form set for the
   language, with every item human-verified as a gate rather than a label. An
   independent second annotator re-checked a stratified sample of 200 items;
   agreement was 93.5% and the 11 items they rejected were removed.

2. **A control stratum of 708 items** whose subject matter is universal by
   construction. Models demonstrably know these facts in English, so failure
   in Azerbaijani is a language failure, not a knowledge gap. The gap is
   *wider* on this stratum, not narrower.

3. **A nine-pair design crossing relatedness with script**, over six target
   groups, eight laboratories and seven distinct base models. Relatedness turns out to
   carry no predictive power; script carries eight of nine. The tokeniser is
   identical within six of the pairs, so the contrast holds with segmentation
   exactly constant. Two further pairs were declared and then excluded by
   measurement gates, and are reported rather than dropped. Ibrahimzade and
   Tabasaransky (2026) predicted a script effect for this language family six
   months earlier, in a framework paper with no experiments; this is its test.

4. **A marker that separates every pair without exception**: whether the
   adapted model begins writing Azerbaijani in Cyrillic. All four damaged
   pairs do; none of the five undamaged pairs does, including the one
   Cyrillic-script target that causes no damage and a model adapted to three
   non-Latin scripts that also causes none. We report it as a marker
   rather than a mechanism, because transliteration recovers only part of the
   damage where the account predicts it should recover all of it.
   We further show that the standard word-level language-confusion detector is
   blind to this pair by construction, since the Turkish alphabet is a subset
   of the Azerbaijani one, and measure that it misses 92% of these errors.

5. **The scale result above**, including the negative finding that size does
   not predict the gap.

6. **A set of documented negative results and measurement failures**, because
   the ones that cost us the most time will cost others the same. One of them
   is a measurement that confirmed our hypothesis and was wrong, caught by
   reading raw model output rather than by any statistic.

### 1.3 What this paper is not

It is not a claim that frontier models cannot handle Azerbaijani. They handle
it reasonably well, and we report the numbers that show it.

It is not a scaling study. Six API models cannot establish a scaling law, and
the largest of them contradicts the monotone reading anyway.

It is not a general theory of script effects. Our Cyrillic evidence comes
from two model pairs adapted to a single language by a single laboratory, and
we say so in the limitations rather than generalising past it.

---

## Note on framing, for the co-authors

**This introduction is not the one the project began with**, and the change
should be deliberate rather than accidental.

The project started from "Azerbaijani is poorly supported by language
models". After measuring six API models that framing became false as stated:
`gpt-4o` reaches 66.7% in Azerbaijani, and on the items where a human answered,
`claude-sonnet-5` scores above that person. Had we written the introduction first and the results later, we would
have been defending a claim our own data refutes.

The revised framing is narrower and, we think, more useful: it says *where*
the problem is (open, small, locally deployed models), *what does not fix it*
(scale alone), and *what specifically breaks* (script, and a wrong-language
failure the standard detector cannot see).

A reviewer will notice the frontier numbers and ask whether the paper still
has a subject. Section 1.1 answers that before the question is asked, which
is the only reliable way to answer it.

**The framing changed twice on 2026-09-09, and both changes are instructive.**

The first draft claimed script, not relatedness. A fifth pair, added to attack
our own weakest limitation (both Cyrillic pairs adapted to Kazakh, from one
laboratory), appeared to refute it: adapting to Ukrainian, a Cyrillic language
unrelated to Azerbaijani, cost nothing. We retitled the paper around an
interaction of relatedness and script.

Pairs six and seven refuted that in turn. Adapting to Russian, equally
unrelated and equally Cyrillic, costs 8 to 10 points in both pairs. Relatedness
was left predicting nothing at all, and the original claim was right for
reasons the original draft did not have. An eighth pair (Norwegian, Latin,
unrelated) filled the last cell and did no damage, as every Latin pair does not.

Two things are worth recording. **The fifth pair's first measurement confirmed
the claim we were testing, at +7.0 points, and was an extraction artefact**
found by reading raw model output rather than by any statistic. And **the
interaction hypothesis we adopted in between was a real hypothesis that a
single further pair could kill**, which is what happened within hours.

The claim is now supported by nine measured pairs, six target groups and
eight laboratories, with the tokeniser held constant in six of them. It has one
documented exception, and Section 6.3 states it rather than smoothing it away.
