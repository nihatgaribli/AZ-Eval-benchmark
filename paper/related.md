# Related work (draft, section 2)

**Status:** first draft, 2026-09-08. Claims about other papers were checked
against their full text or, for TUMLU, against the data we imported from it.
Every load-bearing claim below has been checked; none remain unverified.

---

## 2 Related work

### 2.1 Azerbaijani is covered by existing benchmarks, but not in a way that
### can measure a language gap

We must be precise here, because the loose version of our motivation is
false. Azerbaijani is *not* absent from multilingual evaluation.

**TUMLU** (Isbarov et al., ACL 2025) is a natively developed benchmark for
eight Turkic languages, middle- and high-school level, across eleven school
subjects, totalling 38,139 four-choice items. Its Azerbaijani portion
contributes 735 items to the manually verified `TUMLU-mini` subset, which we
import and audit.

Our audit is not a criticism of that dataset; their own paper anticipates it,
reporting that in languages such as Azerbaijani, where questions were
community-developed, "around 10% of the questions were either invalid or had
incorrect answers". We retain 521 of 735 after filtering ten defect classes,
which is consistent with that estimate and is why the imported rows carry
`verified_by: external` rather than `human`.

**INCLUDE** (Romanou et al., ICLR 2025) covers 44 written languages with
197,243 QA pairs drawn from local examinations. Azerbaijani is among them,
with 6,937 items, listed as Latin script, Turkic, and mid-resource.

**KazMMLU** (Toğmanov et al., ACL 2025) is not about Azerbaijani but is
central to our motivation: it provides 10,969 Kazakh and 12,031 Russian
items. Kazakh has a resource that Azerbaijani lacked, and open Kazakh-adapted
models exist. That asymmetry is precisely what makes "adapt a Kazakh model"
an appealing shortcut, and what this paper tests.

**Two properties are shared by all three, and both matter for us.**

*They are not parallel.* Items are developed natively or drawn from local
exams, so there is no English counterpart of the same item. A model's
Azerbaijani score can be compared to another model's Azerbaijani score, but
not to its own English score on the same question. The quantity this paper
measures, the within-model within-item language gap, cannot be computed
from them.

*They are multiple choice.* This measures selection among given options, not
production of an answer. The distinction is not cosmetic: on identical items
from TUMLU-az, four models score 34.2 to 38.8 points higher under multiple
choice than under short answer.

That raw difference should not be read on its own, because guessing earns 25%
under four-way choice and close to nothing under free-form answering. The
chance-immune version of the statistic is retention: **of the items a model
answers correctly in multiple choice, only 0.5% to 10.3% are also produced
correctly in free form.** Recognition and production are close to
dissociated here, and a multiple-choice benchmark therefore overstates usable
ability in the generation setting where these models are actually deployed.

*Source: `results/format_contrast/tables.md`.*

AZ-Eval is complementary rather than competing. It is smaller than either
(1006 items), and it is parallel and free-form, which is what the questions
in this paper require.

### 2.2 Script and transliteration in cross-lingual transfer

A line of work establishes that script divergence obstructs transfer between
related languages, and that transliteration to a shared script recovers part
of it. Moosa et al. (2022) ask directly whether transliteration helps
multilingual language modelling; Xhelili, Liu, and Schütze (2024) propose
transliteration-based post-pretraining alignment and report improvements up to
50% on some tasks; RomanSetu (2024) romanises inputs to unlock multilingual capability;
and further work analyses why transliteration improves cross-lingual
alignment.

**Our question is the mirror image of theirs, and it is the gap we fill.**
All of these study the *pre-training* or *alignment* stage and ask whether
converting to a shared script improves transfer *to the target language*. We
ask what fine-tuning on a different-script relative does to a *third*
language, and we measure degradation rather than gain. To our knowledge that
question has not been asked in this literature, which we verified by reading
the alignment paper in full: it reports only improvements and does not
measure harm to any language.

Our transliteration result supports their mechanism from the other side.
`Qolda-AVL-5B` produces 85.9% of its Azerbaijani answers in Cyrillic, and
transliteration more than doubles its score: the knowledge is present and
the surface form is wrong.

**TUMLU already measures a script effect, on a different axis, and we must
not present ours as the first.** They build dual-script versions of their
Kazakh, Crimean Tatar and Uzbek subsets and compare model accuracy across
them (their Table 6). Their finding is that a model reads a language best in
whichever script dominates its training corpus: Crimean Tatar is better in
Latin, Kazakh better in Cyrillic, Uyghur better in Arabic.

Their axis is the script of the **input**, under multiple choice, with the
model unchanged. Ours is the script of the **output**, after adaptation, under
free-form generation. The two are complementary, and theirs supplies the
quantity that makes our mechanism concrete: in FineWeb 2 they count
1,837,049,585 Cyrillic and **zero** Latin Kazakh words. A model adapted to
Kazakh is, in corpus terms, adapted to Cyrillic. That is the sharpest external
support our script explanation has, and it comes from a benchmark paper rather
than from us.

They also observe, as we do, that generation is the harder setting: their
conclusion notes that models understand these languages reasonably well but
"are less capable of generating text in these languages".

### 2.3 The strongest competing explanation: tokenisation, not script

Tufa et al. (2024) conclude that **the tokeniser is a stronger factor than
shared script, language similarity, or model size**. Read carelessly, this
contradicts our central claim, and we treat it as the objection to beat rather
than a citation to bury.

Their setup differs from ours in three ways that matter. They use encoder
models (BERT, RoBERTa, ALBERT, Arabic-BERT, mBERT, CANINE) on NER and POS
tagging with Amharic as the target; they measure performance *on the target
language only*, never degradation of a third language after adaptation; and
their tokeniser result emerges from comparisons *across* six models whose
tokenisers differ by construction.

**They and we do not measure the same quantity, and saying so is necessary
rather than defensive.** Their tokeniser variable is the *algorithm class*:
their Table 1 varies WordPiece, BPE, SentencePiece and character-level
tokenisation across models. Ours is the *vocabulary difference within a single
base-tuned pair*, where the algorithm is identical by construction because the
tuned model inherits its base's tokeniser. Their finding is that the algorithm
class matters across models; ours is that within a pair where the vocabulary is
also unchanged, the script contrast survives. These are compatible claims, and
neither is evidence against the other.

Our design holds the tokeniser constant *within* a pair, and we verify that
it is in fact constant rather than assuming it (Section 8.2). In the two
pairs where it is, the Cyrillic-Latin contrast remains: +9.8 points of excess
damage against +1.5.

Their finding is therefore the reason our design controls what it controls,
not evidence against the result.

### 2.4 Catastrophic forgetting, and how our measure relates to existing ones

That fine-tuning degrades previously acquired capabilities is well
established (McCloskey and Cohen, 1989; Kemker et al., 2018; Luo et al.,
2023). The closest work to ours measures it in the multilingual setting
directly: Liu and Niehues (MRL 2025) fine-tune translation models and plot
per-language-pair performance before against after, and Koloski et al. (2023)
measure forgetting across chains of cross-lingual transfer.

**Normalised forgetting measures already exist, and we do not claim
otherwise.** Koloski et al. adopt the Kemker et al. (2018) family, of which
the relevant member is

```
Omega_base = mean over sessions of ( alpha_base,i / alpha_ideal )
```

where `alpha_ideal` is the model's own offline score. This is a **ratio of a
language to its own ideal**. Our excess damage is a **difference between two
languages** measured on the same items:

```
excess damage = (EN before - EN after) - (AZ before - AZ after)
```

The distinction is not cosmetic. In Kemker's Omega and in Koloski et al., the
reference language is the *source* language, which the model was trained on.
In Liu and Niehues, forgetting is an absolute change per language pair against
that pair's own pre-fine-tuning score. In our design **neither** language is a
fine-tuning target: Azerbaijani and English are both bystanders, and one
bystander calibrates the other. We have not found that construction in this
literature, and we state the claim at that resolution rather than claiming to
have invented forgetting normalisation.

The literature also justifies the choice. Absolute Azerbaijani loss is not
interpretable alone, because some of it is ordinary forgetting; using the
model's own English degradation as the baseline subtracts it. This is what
explains one of our pairs. `Trendyol` loses 26.9 points in English, which
is textbook catastrophic forgetting rather than Azerbaijani-specific harm, and
is why its excess damage is strongly negative without Azerbaijani being
spared.

### 2.5 Language confusion is a known failure with known metrics

Our second failure mode, an Azerbaijani prompt answered in Turkish, is not a
new observation, and an earlier draft of this paper overstated it by saying no
metric catches it. That is false as stated, and the corrected version is
sharper.

Marchisio et al. (EMNLP 2024) name the phenomenon **language confusion**, build
the Language Confusion Benchmark over 15 languages, and define line-level and
word-level pass rates (LPR, WPR) using off-the-shelf language identification.
Liu and Niehues report LangID accuracy for the same purpose and observe it
collapse to 22.1% on unseen pairs. The failure mode is established and
measured.

**What we add is that these detectors are structurally blind to the Azerbaijani
and Turkish case.** For languages in Latin script, Marchisio et al. define
word-level detection as the presence of a character outside the target script's
Unicode range. The Turkish alphabet's 29 letters are a subset of Azerbaijani's
32; Azerbaijani adds only `ə`, `x` and `q`. A word written in Turkish
orthography therefore cannot leave the Azerbaijani range, and the detector is
silent by construction rather than by accident.

We measured this rather than arguing it. Applying the rule to our 159
human-labelled errors, it fires on 2 of the 24 wrong-language rows and misses
92%. Both rows it catches contain `w`, a letter in neither alphabet, so the
two hits are English intrusions and not the Turkish confusion at issue.

| | n |
|---|---|
| Human-labelled errors | 159 |
| Labelled wrong-language | 24 |
| Word-level rule fires | 2 |
| Missed | 22 (92%) |

Azerbaijani is not among the benchmark's 15 languages, which is consistent
with this being an untested configuration rather than a known limitation.

We do not extend the claim to the line-level rule. That rule splits a response
into lines and checks each with fastText, whereas our answers average 1.34
words; fastText is not installed in our environment and we therefore assert
nothing about how it would behave on this pair.

*Source: `results/tables/language_confusion.md`, `src/language_confusion.py`.*

### 2.6 The closest prior work is Turkic-specific, and one paper predicts our
### result without testing it

Three 2026 papers work on cross-lingual transfer within the Turkic family, and
they are the nearest neighbours of this study.

**Ibrahimzade and Tabasaransky (2026)** develop a theoretical framework for
adaptation across Azerbaijani, Kazakh, Uzbek, Turkmen and Gagauz. They propose
a Turkic Transfer Coefficient combining morphological similarity, lexical
overlap, syntactic structure and **script compatibility**, and they predict
that "Kazakh demonstrates somewhat lower TTC values with the Latin-script
languages due to the continued use of Cyrillic orthography", and that
"orthographic divergence, particularly the coexistence of Latin and Cyrillic
scripts, may partially reduce effective transfer despite high morphological
similarity".

That is close to our hypothesis, in our language family, stated six months
earlier. It is also explicitly untested: they write that "the goal is not to
report experimental outcomes, but rather to establish a conceptual model", and
the paper contains no experiments. **We therefore present this work as the
empirical test of a published prediction rather than as an independent idea.**

The test returns a verdict favourable to the script half of their coefficient
and unfavourable to the typological half. Their TTC combines script
compatibility with morphological and lexical similarity, so it predicts that a
typologically close, script-compatible target transfers best and that
typological distance costs something. Across nine pairs we find that script
compatibility does the work and typological similarity does none: Turkish, the
most similar target available, costs Azerbaijani nothing, while Russian, about
as distant as a target can be, costs 8 to 10 points.

The concrete amendment our measurement supports is therefore to weight the
script term heavily and the typological terms near zero, at least for damage
to a third language. One of our nine pairs (Ukrainian) is script-incompatible
and costs nothing, so even the script term is not deterministic.

**Cinar, Dalkilic and Toraman (2026)** build pairwise transfer matrices for
machine translation among Turkish, Azerbaijani, Uzbek, Kazakh and Kyrgyz with
mT5, and report that latinisation improves BLEU and chrF when the transfer
target is Cyrillic, by as much as 63.6% BLEU for Azerbaijani to Kyrgyz. Their
transliteration acts on the *input* of a translation system; ours acts on the
*output* of a generative model that has already been adapted. Their finding
that transfer is strongest for Turkish-Azerbaijani also underwrites our design
choice: Turkish is the closer relative, which is why a relatedness account
predicts the Turkish pairs should be the damaging ones.

**Zhang (2026)** compares two script-unification schemes, general-purpose
romanisation against the family-specific Common Turkic Script, using fastText
on eleven Turkic languages evaluated on NER and POS. Like the transliteration
literature in Section 2.2, the aim is to *improve* transfer by removing script
differences, not to measure what script differences destroy.

None of the three measures degradation of a language that is not a target of
the adaptation, and none evaluates free-form generation.

### 2.7 A finding that points the other way, and why we report it

Khelli, Cahyawijaya, Purwarianti and Winata (2025) study knowledge loss across
52 languages with XLM-R and LoRA adapters on MASSIVE slot filling, and
conclude that **languages written in Latin script are strong donors and stable
receivers, suffering less catastrophic forgetting** than non-Latin ones.

Read naively, this predicts that Azerbaijani, a Latin-script language, should
be relatively safe, and in four of our nine pairs it is not. The resolution
is that we are not varying the same thing. Their variable is the script of the
language being **forgotten**; ours is the script of the language being adapted
**to**. A Latin-script bystander enjoys no protection when the adaptation
target is Cyrillic, because the damage arrives through what the model is being
taught to write rather than through what it is being asked to retain. Their
design contains no case where the target and the bystander differ in script,
so the two results do not actually conflict.

Their models are also encoders performing sequence labelling, and Azerbaijani
is not among their 52 languages. We report the tension rather than omit it,
because a reader who knows that paper will otherwise think we do not.

---

## Verification status

| Claim | Status |
|---|---|
| TUMLU: 735 AZ items, multiple choice, not parallel | verified against imported data (`choices`, `answer_letter`, no `question_en`) |
| INCLUDE: includes Azerbaijani, 6,937 items, multiple choice, region-specific | verified in full text, Table 8 |
| KazMMLU: 10,969 KK + 12,031 RU | verified in abstract |
| KazMMLU is entirely Cyrillic | verified in full text, direct quote |
| TUMLU: 38,139 items, natively developed, ~10% defect rate in community-built AZ | verified in full text (§3) |
| TUMLU Table 6: dual-script comparison; Kazakh better in Cyrillic | verified in full text |
| FineWeb 2: 1,837,049,585 Cyrillic vs 0 Latin Kazakh words | verified in full text (§5) |
| arXiv:2406.19759 measures gain only, no third-language harm | verified in full text |
| arXiv:2404.18810 is Tufa, Markov and Vossen, *Unknown Script*, not Purkayastha | verified against arXiv metadata; earlier drafts misattributed it |
| TUMLU's first author is Isbarov, not İbrahimov | verified against arXiv metadata; earlier drafts misattributed it |
| arXiv:2406.19759 is Xhelili, Liu and Schütze, not Liu et al. | verified against arXiv metadata; earlier drafts misattributed it |
| arXiv:2309.06089 is *Cross-Lingual Transfer Paradigms: Exploring Tuning Strategies*, 2023 | verified against arXiv metadata; earlier drafts gave a garbled title and the year 2025. arXiv records no DOI or journal reference, only "Accepted to IEEE Access", so it is cited as a preprint |
| arXiv:2404.18810 appeared at the NAACL 2024 Student Research Workshop | verified against arXiv metadata (comment field); earlier drafts cited it as a bare preprint |
| Tufa et al.: encoder models, target-language performance only | verified in full text |
| Their tokeniser variable is algorithm class (Table 1), not vocabulary size | verified in full text |
| Kemker/Koloski normalise by a language's own ideal, not by another language | verified in full text (Eq. 1-3) |
| Liu and Niehues measure absolute per-pair change, and report LangID | verified in full text (Fig. 2-3, Table 4) |
| Marchisio et al.: 15 languages, Azerbaijani not among them; word-level rule is Unicode-range | verified in full text (§2.2-2.3) |
| Turkish alphabet is a subset of Azerbaijani; detector misses 92% | computed, `src/language_confusion.py` |
| Ukrainian (Cyrillic, unrelated) adaptation costs Azerbaijani nothing | computed, `results/tables/pairs_oneshot.md` |
| Russian (Cyrillic, unrelated) adaptation costs 8 to 10 points, in two pairs | computed, `results/tables/pairs_oneshot.md` |
| Norwegian (Latin, unrelated) adaptation costs nothing | computed, `results/tables/pairs_oneshot.md` |
| Ibrahimzade and Tabasaransky propose TTC with script compatibility and run no experiments | verified in full text, direct quotes |
| Cinar et al.: latinisation +63.6% BLEU az to ky when target is Cyrillic | verified in full text, Table 2 |
| Zhang: fastText, NER/POS, script unification for transfer gain | verified in abstract and §1 |
| Khelli et al.: Latin-script languages forget less; XLM-R, MASSIVE, no Azerbaijani | verified in full text, §5.2 |
