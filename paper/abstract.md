# Abstract (draft)

**Status:** third draft, 2026-09-09. The claim changed twice in one day as
pairs five to ten came in, and the version below is the one nine measured pairs
support. Every number appears in `results/tables/` and is reproducible with a
fixed seed.

---

## Title

**Script, not relatedness: what fine-tuning on a neighbouring language costs
Azerbaijani**

Alternatives, in case the venue wants something shorter:

- *Adapting to Cyrillic harms Azerbaijani; adapting to Latin does not*
- *AZ-Eval: a parallel Azerbaijani-English benchmark and eight fine-tuning pairs*

**Two titles we went through and discarded, in one day.** "Script, not
relatedness" was the first draft's title; a fifth pair (Ukrainian, Cyrillic,
unrelated, no damage) appeared to refute it and we retitled around an
interaction of relatedness and script. Pairs six and seven (Russian, Cyrillic,
unrelated, clear damage) refuted *that*, and left relatedness with no
predictive power at all. The original title is right, for reasons the original
draft did not have.

## Abstract

Azerbaijani is not missing from multilingual evaluation: TUMLU contributes 735
items and INCLUDE 6,937. Both are multiple choice, and neither is parallel, so
neither can compare a model's Azerbaijani with its own English on the same
question. The format matters too: of the items a model answers correctly under
multiple choice, only 0.5% to 10.3% are also produced correctly in free form,
so selection and production are close to dissociated.

We introduce **AZ-Eval**, 1006 short-answer items stated in parallel
Azerbaijani and English, of which 708 form a control stratum whose subject
matter is universal by construction, so that failure there is a language
failure rather than a knowledge gap. Human verification is a build gate rather
than a label: the build refuses any row not individually checked. An
independent annotator re-checked a stratified sample of 200 items and agreed
on 93.5%; the 11 items they rejected were removed, one of which exposed a
defective question template.

Measuring 34 models under a single protocol, we find the gap concentrated in
the models that low-resource work actually deploys: 3.9 to 43.5 points across
28 open models of 8B or smaller, against 3.7 to 15.2 points for five large
commercial models. Scale does not explain it, since a 235B model trails four
smaller ones by roughly ten points; nor does quantisation, since an 8B model
served at full precision behaves like its 4-bit peers.

Our main experiment asks what adapting a model to a neighbouring language
costs a third language. Eleven base/fine-tuned pairs, nine of which pass our
measurement gates, cross two factors: whether the adaptation target is related
to Azerbaijani, and whether it shares its script. Reporting Azerbaijani loss minus English loss, so that ordinary
forgetting is subtracted, **relatedness carries no predictive power and script
carries most of it.** The closest relative, Turkish, does no damage in either
of two pairs; a wholly unrelated Slavic language, Russian, damages Azerbaijani
in both of its pairs. Every Latin-script target leaves Azerbaijani intact
(three pairs); four of five Cyrillic-script targets damage it by 8 to 11
points. A non-Latin target is not by itself sufficient: a model adapted to
Thai, Burmese and Tamil alongside four Latin-script languages, sharing its base
with the most damaged pair, costs Azerbaijani nothing. The tokeniser is
measured rather than assumed and is identical in six of the nine pairs, so the
contrast survives with segmentation held exactly constant.

The single exception, a Ukrainian-adapted model that does no damage, is
absorbed by a marker that separates all nine pairs without exception: whether
the adapted model begins writing Azerbaijani answers in Cyrillic. Every pair
that emits any Cyrillic is damaged; every pair that emits none is not. We stop
short of calling this the mechanism, because transliteration recovers only
part of the Kazakh damage and almost none of the Russian.

The failure decomposes into two modes with opposite prospects. A
Kazakh-adapted model writes Azerbaijani answers in Cyrillic, and
transliteration more than doubles its score: the knowledge is present and the
surface form is wrong. A Turkish-adapted model writes them in Turkish, which
no normalisation repairs because the alphabet is already correct, and which
the standard word-level language-confusion detector misses in 92% of cases,
since the Turkish alphabet is a subset of the Azerbaijani one and no character
ever leaves the expected range.

## Short version (~150 words, for venues with a hard limit)

Azerbaijani appears in multilingual benchmarks only as multiple choice and
never in parallel with English, so a model's Azerbaijani cannot be compared
with its own English on the same item. We introduce AZ-Eval: 1006 parallel
Azerbaijani-English short-answer items, 708 of them universal by construction,
every row human-verified as a build gate.

Across 34 models the gap is concentrated in small open models (3.9 to 43.5
points) rather than large commercial ones (3.7 to 15.2), and is explained by
neither scale nor quantisation.

Nine fine-tuning pairs then show that the script of the adaptation target
predicts damage to Azerbaijani and its relatedness does not. Turkish, the
closest relative, costs nothing; Russian, entirely unrelated, costs 8 to 10
points. Every pair that damages Azerbaijani also begins writing it in
Cyrillic, and every pair that does not, does not.

## What is deliberately not in the abstract

Left out on purpose, so the reviewer meets them where they can be qualified:

1. **The `Trendyol` pair's -16.0.** It looks like Latin fine-tuning *protects*
   Azerbaijani. It does not; the model loses 26.9 points in English and a
   collapsing denominator drives the difference negative. Stating it without
   that explanation would be misleading, and the explanation does not fit.

2. **The Ukrainian exception.** One Cyrillic-script pair does no damage, and
   the abstract says "four of five" rather than hiding it. Why it is the
   exception is not settled: the model barely moved in any direction, but that
   restates the result rather than explaining it. Sections 6.3 and 10 carry
   the full treatment.

3. **`gpt-4o`'s 3.7-point gap.** The bootstrap interval excludes zero but Holm
   correction gives *p* = 0.10, so we make no claim for that model
   individually. The abstract gives the range, which is what the data supports.

4. **The human baseline.** 70.0% on 50 items establishes solvability, not a
   ceiling: `claude-sonnet-5` scores 74.0% on the same items. Too easy to
   misread in a summary.

5. **Negative results.** Prompting for the Latin alphabet fails, and auditing
   gold answers by model agreement fails. They belong in the paper, not here.
