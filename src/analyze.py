"""Xam cavabları bala çevirir, cədvəlləri və xəta nümunəsini hazırlayır.

    python -m src.analyze

Bu modul modelə MÜRACİƏT ETMİR — yalnız `results/raw_outputs/` altındakı xam
faylları oxuyur. Ona görə metrikanı, cavab çıxarma qaydasını və ya normalizasiya
rejimini dəyişib istənilən qədər təkrar işlətmək olar; heç bir GPU saatı yenidən
xərclənmir. Bu ayrılıq brief-in 7-ci bölməsinin tələbidir.

İstehsal etdiyi cədvəllər:

  1. `main.md`      — model × dil × metrika, hər xana `62.4% ± 3.1` formatında
  2. `modes.md`     — STRICT / MORPH / LENIENT yan-yana (RQ3-ün kəmiyyət cavabı)
  3. `rq1.md`       — AZ vs EN cütləşdirilmiş fərq, CI və p qiyməti
  4. `rq2.md`       — modellərarası cütləşdirilmiş müqayisə (Qolda transfer sualı)
  5. `breakdown.md` — kateqoriya və sual variantı üzrə kəsim
  6. `errors.csv`   — əl ilə etiketlənmək üçün təbəqələndirilmiş səhv nümunəsi
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.build_dataset import load_jsonl
from src.metrics import (
    LENIENT,
    MODES,
    MORPH,
    STRICT,
    TRANSLIT,
    NormalizationConfig,
    bootstrap_ci,
    compare_paired,
    format_ci,
    holm_correction,
    normalize,
    score_example,
)

__all__ = [
    "extract_answer",
    "RunKey",
    "Run",
    "load_runs",
    "build_provenance_table",
    "run_label",
    "gold_answers",
    "score_run",
    "markdown_table",
    "build_main_table",
    "build_modes_table",
    "build_rq1_table",
    "build_rq2_table",
    "build_breakdown_table",
    "error_rows",
]


# --------------------------------------------------------------------------
# Cavabın xam mətndən çıxarılması
# --------------------------------------------------------------------------

#: Modellərin cavabdan əvvəl yazdığı adi prefikslər. İki ailə var:
#:
#:   etiket formalı  — "Cavab:", "Answer:", "A -"   (ayırıcı TƏLƏB OLUNUR)
#:   cümlə formalı   — "The answer is", "Cavab budur"
#:
#: Etiket ailəsində ayırıcının tələb olunması vacibdir: onsuz `a` qaydası
#: "Almaniya" və "Au" kimi həqiqi cavabların başını yeyərdi.
_ANSWER_PREFIXES = re.compile(
    r"^\s*(?:"
    r"(?:cavab|cavabı|answer|a)\s*[:\-—]"
    r"|the answer is\b"
    r"|cavab budur\b"
    # Cümlə formalı prefiksdən sonra ayırıcı GƏLƏ BİLƏR: "Cavab budur: Bakı".
    # Tutulmasa, iki nöqtə cavabın içində qalır və EM sınır. Etiket ailəsində
    # ayırıcı onsuz da məcburidir, ona görə burada isteğe bağlıdır.
    r")\s*[:\-—]?\s*",
    re.IGNORECASE,
)

#: "Fransanın paytaxtı Parisdir." kimi tam cümlə cavablarında son nöqtə.
_TRAILING_PUNCT = re.compile(r"[.!?,;:]+\s*$")

#: Düşünmə modellərinin gizli mühakimə bloku.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)

#: Markdown vurğusu — modellər cavabı tez-tez qalın yazır: "**Berlin**dır".
#: Ulduzlar normalizasiyada durğu işarəsi kimi silinmir (Unicode kateqoriyası
#: `Po` deyil, `Sm`/`Po` qarışığıdır) və EM-i sındırır.
_MARKDOWN_EMPHASIS = re.compile(r"(\*{1,3}|_{1,3}|`+)")


def extract_answer(raw_response: str, max_words: int = 12) -> str:
    """Modelin xam mətnindən qısa cavabı çıxarır.

    Bu qat metrikanı birbaşa dəyişir, ona görə qaydaları açıq saxlamaq lazımdır:

    1. `<think>...</think>` blokları silinir (düşünmə modelləri). Blok
       bağlanmayıbsa — yəni generasiya mühakimənin ortasında kəsilibsə — model
       cavaba ümumiyyətlə çatmayıb, ona görə nəticə BOŞ sayılır. `"<think>"`
       sətrini cavab kimi saxlamaq xəta taksonomiyasını korlayardı: sətir
       "səhv cavab" yox, "cavab yoxdur" kateqoriyasına aiddir.
    2. Yalnız BİRİNCİ sətir götürülür. Modellər çox vaxt cavabı yazıb sonrakı
       sətirlərdə izahat verir; izahatı saymaq token F1-i süni şəkildə aşağı salır.
    3. "Cavab:" / "Answer:" prefiksləri atılır.
    4. Dırnaqlar və sondakı durğu işarəsi təmizlenir.
    5. Nəticə `max_words` sözdən uzundursa, ilk cümlə götürülür — model
       təlimata baxmayaraq abzas yazıbsa, ilk cümlə adətən cavabı daşıyır.

    Qayda hər iki dilə EYNİ tətbiq olunur. Fərqli tətbiq olunsaydı, ölçülən
    AZ/EN fərqinin bir hissəsi bu qatdan gələrdi.

    Xam cavab diskdə toxunulmaz qalır — qayda dəyişsə, yalnız bu modul yenidən
    işlədilir, modellər yox.
    """
    text = (raw_response or "").strip()
    if not text:
        return ""

    text = _THINK_BLOCK.sub(" ", text)
    text = _UNCLOSED_THINK.sub("", text)   # kəsilmiş mühakimə -> cavab yoxdur
    text = text.strip()
    if not text:
        return ""

    text = text.splitlines()[0].strip()
    # MARKDOWN PREFİKSDƏN ƏVVƏL SİLİNİR. Modellər etiketi tez-tez qalın yazır:
    #
    #     **Cavab:** Washington D.C.
    #
    # Əvvəlcə prefiks axtarılsaydı, mətn `**` ilə başladığı üçün naxış uyğun
    # gəlməzdi; markdown sonra silinər və `Cavab:` cavabın içində qalardı.
    # `issai/Qwen3.5-4B-Base-Kazakh` məhz belə yazır və 604 cavabın 313-ü bu
    # yolla səhv sayılırdı. Səhv YALNIZ bu modeli cəzalandırırdı, yəni onun
    # bazası ilə fərqini süni böyüdürdü.
    text = _MARKDOWN_EMPHASIS.sub("", text)
    text = _ANSWER_PREFIXES.sub("", text, count=1)
    text = text.strip().strip('"“”«»\'')

    if len(text.split()) > max_words:
        first_sentence = re.split(r"(?<=[.!?])\s+", text)[0]
        text = first_sentence

    return _TRAILING_PUNCT.sub("", text).strip()


# --------------------------------------------------------------------------
# Qaçışların yüklənməsi
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RunKey:
    """Bir qaçışın kimliyi: model + dil + prompt üslubu.

    Prompt üslubu açarın hissəsidir, yoxsa eyni modelin iki fərqli promptla
    qaçışı BİR qaçış kimi birləşər və əlifba nəzarəti mənasını itirər.
    Standart üslub adda göstərilmir ki, mövcud cədvəllər dəyişməsin.
    """

    model: str
    language: str
    prompt_style: str = "default"

    def __str__(self) -> str:
        suffix = "" if self.prompt_style == "default" else f" ({self.prompt_style})"
        return f"{self.model}{suffix} [{self.language}]"


@dataclass
class Run:
    """Bir modelin bir dildəki qaçışı: id -> çıxarılmış cavab."""

    key: RunKey
    predictions: dict[str, str]
    raw: dict[str, str]

    #: Qaçışın necə alındığı: API backend metadatası (`backend` sahəsi) və
    #: generasiya parametrləri.
    #:
    #: NİYƏ SAXLANILIR: lokal qaçışlar greedy + sabit seed ilə təkrarlanır, API
    #: qaçışları təkrarlanmır. Bu iki sətir eyni cədvəldə yan-yana duranda
    #: oxucu onları eyni etibarlılıq sinfində sayır. Fərq sənədləşdirilməsə,
    #: müqayisə səssizcə yanıldıcı olur.
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def ids(self) -> set[str]:
        return set(self.predictions)

    @property
    def is_api(self) -> bool:
        return bool(self.provenance.get("backend"))


def load_runs(raw_dir: Path, max_words: int = 12) -> list[Run]:
    """`results/raw_outputs/*.jsonl` fayllarını oxuyur.

    Fayl adına yox, sətirlərin içindəki `model`/`language` sahələrinə güvənir —
    fayl əl ilə adı dəyişdirilsə də nəticə düzgün qalır.
    """
    grouped: dict[RunKey, dict[str, dict[str, str]]] = defaultdict(
        lambda: {"pred": {}, "raw": {}}
    )
    provenance: dict[RunKey, dict[str, Any]] = defaultdict(dict)

    for path in sorted(raw_dir.glob("*.jsonl")):
        for _, row in load_jsonl(path):
            if not isinstance(row, dict):
                continue
            key = RunKey(
                row.get("model", path.stem),
                row.get("language", "az"),
                row.get("prompt_style", "default"),
            )
            record_id = row.get("id")
            if not isinstance(record_id, str):
                continue
            raw = row.get("raw_response", "")
            grouped[key]["raw"][record_id] = raw
            grouped[key]["pred"][record_id] = extract_answer(raw, max_words=max_words)

            # Mənşə SONUNCU sətirdən götürülür, birincidən yox: API qaçışında
            # faktiki model versiyası və konfiqurasiya varianti yalnız birinci
            # cavabdan sonra məlum olur, ona görə erkən sətirlərdə sahələr boş
            # qala bilər.
            if row.get("backend"):
                provenance[key]["backend"] = row["backend"]
            if row.get("generation"):
                provenance[key]["generation"] = row["generation"]

    return [
        Run(
            key=key,
            predictions=data["pred"],
            raw=data["raw"],
            provenance=dict(provenance.get(key, {})),
        )
        for key, data in sorted(grouped.items(), key=lambda kv: str(kv[0]))
    ]


def build_provenance_table(runs: Sequence[Run]) -> str:
    """Hər qaçışın hansı şəraitdə alındığı.

    Bu cədvəl bal göstərmir və qəsdən belədir. Onun işi bir sualı bağlamaqdır:
    *bu rəqəm necə alınıb?* Lokal və API sətirləri əsas cədvəllərdə yan-yana
    durur, amma eyni şəraitdə ölçülmür — biri greedy və sabit seed ilə
    təkrarlanır, digəri təkrarlanmır. Fərqi ayrıca sənədə yazmaq onu
    gizlətməkdən yaxşıdır.
    """
    headers = [
        "Qaçış",
        "Mənbə",
        "Faktiki model",
        "Düşünmə",
        "Təkrarlanabilirlik",
        "Qeyd",
    ]
    rows: list[list[str]] = []

    for run in sorted(runs, key=lambda r: (not r.is_api, str(r.key))):
        backend = run.provenance.get("backend") or {}
        generation = run.provenance.get("generation") or {}

        if backend:
            source = backend.get("provider", "api")
            resolved = backend.get("resolved_model") or "—"
            thinking = backend.get("thinking", "—")
            repeatable = backend.get("determinism", "best-effort")
            note = backend.get("base_url") or ""
            variant = backend.get("config_variant")
            if variant:
                note = f"{note} · variant: {variant}".strip(" ·")
        else:
            # Lokal qaçış: `backend` sahəsi yoxdur, amma generasiya
            # parametrləri sətirdə var və təkrarlanabilirliyi onlar müəyyən edir.
            source = "lokal (transformers)"
            resolved = "—"
            thinking = "disabled"
            sampled = generation.get("do_sample", False)
            seed = generation.get("seed")
            repeatable = (
                f"deterministik (greedy, seed={seed})"
                if not sampled
                else "qeyri-deterministik (sampling)"
            )
            note = ""

        rows.append(
            [
                str(run.key),
                source,
                str(resolved),
                str(thinking),
                str(repeatable),
                note or "—",
            ]
        )

    table = markdown_table(headers, rows)
    return (
        table
        + "\n\n**Oxunuş qaydası.** `Təkrarlanabilirlik` sütunu `deterministik` "
        "olmayan sətirlər üçün rəqəm eyni əmrlə təkrar işlədiləndə dəyişə bilər. "
        "API provayderləri model çəkilərini xəbərdarlıqsız yeniləyir, ona görə "
        "`Faktiki model` və `Qeyd` sütunları saxlanılır — onlarsız rəqəm "
        "təkrarlana bilməz.\n"
    )


#: Qaçış "tam" sayılmaq üçün datasetin ən azı bu qədərini örtməlidir.
COVERAGE_THRESHOLD = 0.90


def partition_by_coverage(
    runs: Sequence[Run], dataset: dict[str, Any], threshold: float = COVERAGE_THRESHOLD
) -> tuple[list[Run], list[Run]]:
    """Qaçışları tam və qismən olmaqla ayırır.

    NİYƏ VACİBDİR: yarımçıq qaçışın sətirləri TƏSADÜFİ SEÇMƏ DEYİL. `run_eval`
    dataseti sıra ilə gəzir, ona görə 22 sətirlik qaçış datasetin ilk 22
    sətridir və onlar şablondan qurulmuş asan paytaxt suallarıdır. Belə qaçış
    83% alır, tam qaçış isə 16%. Fərq modelin gücündən yox, sual seçimindən
    gəlir.

    `N` sütununu göstərmək kifayət etmir: oxucu sütunları yan-yana görəndə
    müqayisə edir. Ona görə qismən qaçışlar müqayisə cədvəllərindən
    ÇIXARILIR və yalnız əsas siyahıda, xəbərdarlıqla qalır.
    """
    if not dataset:
        return list(runs), []
    needed = threshold * len(dataset)
    complete = [r for r in runs if len(r.ids & set(dataset)) >= needed]
    partial = [r for r in runs if r not in complete]
    return complete, partial


def coverage_note(partial: Sequence[Run], dataset: dict[str, Any]) -> str:
    """Qismən qaçışlar üçün cədvəlaltı xəbərdarlıq."""
    if not partial:
        return ""
    lines = [
        "",
        "> **Qismən qaçışlar müqayisə cədvəllərinə daxil edilmir.** Aşağıdakı",
        "> qaçışlar datasetin yalnız bir hissəsini örtür və həmin hissə təsadüfi",
        "> seçilməyib: `run_eval` dataseti sıra ilə gəzir, ona görə yarımçıq",
        "> qaçış ilk sətirlərdən ibarətdir və onlar sistematik olaraq daha",
        "> asandır. Bu sətirlərin faizi modelin gücünü göstərmir.",
        ">",
    ]
    for run in sorted(partial, key=lambda r: str(r.key)):
        covered = len(run.ids & set(dataset))
        lines.append(f"> - `{run.key}`: {covered}/{len(dataset)} sətir")
    return "\n".join(lines) + "\n"


def gold_answers(record: dict[str, Any], language: str) -> list[str]:
    """Bir sətrin qəbul edilən cavabları.

    AZ tərəfdə `answer_aliases` da daxil edilir (hallanmış formalar), EN tərəfdə
    yalnız `answer_en` — ingilis dilində hallanma yoxdur, alias generasiyası da
    yoxdur. Bu asimmetriya QƏSDƏNdir və hesabatda göstərilməlidir: AZ tərəfə bir
    az əlverişlidir, yəni ölçülən AZ/EN fərqi əsl fərqin AŞAĞI həddidir.
    """
    azerbaijani = str(record.get("answer", ""))
    english = str(record.get("answer_en", ""))

    if language == "az":
        return [azerbaijani, *(record.get("answer_aliases") or [])]

    # İngilis etalonu AZ-dən UZUNDURSA, ayrı-ayrı sözləri də qəbul edilir.
    #
    # Wikidata etiket konvensiyaları iki dildə fərqlidir və asimmetriya hər iki
    # istiqamətdə baş verir. AZ tərəfin uzun olduğu hal `build_dataset
    # .equivalence_aliases` ilə datasetdə həll olunur; burada TƏRSİ tutulur:
    #
    #     AZ "futbolçu"  vs  EN "association football player"
    #     AZ "Şimalda"   vs  EN "In the North"
    #
    # Model ingiliscə "footballer" və ya "North" desə, faktiki olaraq doğrudur,
    # amma exact match sıfır verər — halbuki azərbaycanca qarşılığı bal alır.
    # Düzəliş olmasa, ölçülən AZ/EN fərqinin bir hissəsi dildən yox, etiket
    # konvensiyasından gələr.
    english_words = english.split()
    if len(english_words) > max(1, len(azerbaijani.split())):
        return [english, *english_words]
    return [english]


def score_run(
    run: Run,
    dataset: dict[str, dict[str, Any]],
    mode: NormalizationConfig,
    ids: Sequence[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Qaçışı bal cədvəlinə çevirir: id -> {"em": ..., "f1": ...}."""
    target_ids = list(ids) if ids is not None else sorted(run.ids & set(dataset))
    return {
        record_id: score_example(
            run.predictions.get(record_id, ""),
            gold_answers(dataset[record_id], run.key.language),
            mode,
        )
        for record_id in target_ids
    }


def run_label(key: "RunKey") -> str:
    """Cədvəl üçün qaçış adı: model + (standartdan fərqlidirsə) prompt üslubu.

    Dil ayrıca sütundadır, ona görə `str(key)`-dən fərqli olaraq bura salınmır.
    Prompt üslubu MÜTLƏQ görünməlidir: əlifba nəzarəti qaçışı əsas qaçışla eyni
    modeldəndir və etiketsiz cədvəldə iki fərqləndirilməyən sətir kimi görünür.
    """
    suffix = "" if key.prompt_style == "default" else f" ({key.prompt_style})"
    return f"{key.model}{suffix}"


def error_file_name(key: "RunKey") -> str:
    """Xəta nümunəsi faylının adı: model VƏ prompt üslubu.

    ÜSLUB ADA GİRMƏLİDİR. Girmədiyi müddətdə eyni modelin dörd üslub qaçışı
    eyni fayla yazırdı və sonuncudan başqa hamısı SƏSSİZCƏ itirdi:
    `Qolda-AVL-5B` üçün default, script, zeroshot və plain nümunələrindən
    cədvəldə yalnız biri qalırdı, özü də hansı olduğu heç yerdə yazılmırdı.
    """
    safe = key.model.replace("/", "__").replace(":", "_")
    if key.prompt_style != "default":
        safe = f"{safe}__{key.prompt_style}"
    return f"errors__{safe}.csv"


def _column(scores: dict[str, dict[str, float]], metric: str, ids: Sequence[str]):
    return [scores[i][metric] for i in ids]


# --------------------------------------------------------------------------
# Bazalar
# --------------------------------------------------------------------------


def majority_baseline(
    dataset: dict[str, dict[str, Any]], ids: Sequence[str], language: str
) -> float:
    """"Həmişə ən çox rast gəlinən cavabı de" strategiyasının balı.

    Modelin balı bu rəqəmdən yuxarı deyilsə, model heç nə öyrənməyib —
    sadəcə paylanmanı təkrarlayır. Avtomatik yığılmış datasetlərdə bu, real
    risqdir, ona görə hər cədvəldə göstərilir.
    """
    counts: dict[str, int] = defaultdict(int)
    for record_id in ids:
        counts[normalize(gold_answers(dataset[record_id], language)[0], STRICT)] += 1
    if not counts:
        return 0.0
    return max(counts.values()) / len(ids)


# --------------------------------------------------------------------------
# Cədvəl qurucuları
# --------------------------------------------------------------------------


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    body = [list(map(str, row)) for row in rows]
    widths = [
        max(len(str(headers[i])), *(len(r[i]) for r in body)) if body else len(headers[i])
        for i in range(len(headers))
    ]
    line = lambda cells: "| " + " | ".join(
        str(c).ljust(widths[i]) for i, c in enumerate(cells)
    ) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    return "\n".join([line(headers), sep, *(line(r) for r in body)])


def build_main_table(
    runs: Sequence[Run], dataset: dict[str, dict[str, Any]], seed: int = 0
) -> str:
    """Model × dil × metrika, STRICT rejimdə (əsas, ən müdafiə olunan rəqəm)."""
    rows = []
    for run in runs:
        ids = sorted(run.ids & set(dataset))
        if not ids:
            continue
        scores = score_run(run, dataset, STRICT, ids)
        em = bootstrap_ci(_column(scores, "em", ids), seed=seed)
        f1 = bootstrap_ci(_column(scores, "f1", ids), seed=seed)
        rows.append(
            [
                run_label(run.key),
                run.key.language.upper(),
                len(ids),
                format_ci(em),
                format_ci(f1),
                f"{100 * majority_baseline(dataset, ids, run.key.language):.1f}%",
            ]
        )
    return markdown_table(
        ["Model", "Dil", "N", "EM (STRICT)", "Token F1 (STRICT)", "Əksəriyyət bazası"],
        rows,
    )


def build_modes_table(
    runs: Sequence[Run], dataset: dict[str, dict[str, Any]], seed: int = 0
) -> str:
    """Üç normalizasiya rejimi yan-yana — RQ3-ün kəmiyyət cavabı.

    STRICT -> MORPH morfologiyadan, MORPH -> LENIENT diakritikadan,
    LENIENT -> TRANSLIT isə YAZI SİSTEMİNDƏN gələn xəta payını verir.

    Sonuncu sütun layihənin əsas tapıntısını ölçür: qazax dilinə köklənmiş model
    azərbaycan sualına kiril əlifbası ilə düzgün cavab verir. Onun balı
    transliterasiyadan sonra kəskin qalxırsa, bu, biliyin transfer olunduğunu,
    yazı sisteminin isə olunmadığını göstərir.
    """
    rows = []
    for run in runs:
        ids = sorted(run.ids & set(dataset))
        if not ids:
            continue
        means = {}
        for mode in MODES:
            scores = score_run(run, dataset, mode, ids)
            means[mode.name] = 100 * sum(_column(scores, "em", ids)) / len(ids)
        rows.append(
            [
                run_label(run.key),
                run.key.language.upper(),
                f"{means['strict']:.1f}%",
                f"{means['morph']:.1f}%",
                f"{means['lenient']:.1f}%",
                f"{means['translit']:.1f}%",
                f"+{means['morph'] - means['strict']:.1f}pp",
                f"+{means['lenient'] - means['morph']:.1f}pp",
                f"+{means['translit'] - means['lenient']:.1f}pp",
            ]
        )
    return markdown_table(
        [
            "Model", "Dil", "STRICT", "MORPH", "LENIENT", "TRANSLIT",
            "morfologiya", "diakritika", "yazı sistemi",
        ],
        rows,
    )


#: NƏZARƏT qatı: modelin ingiliscə nümayişkaranə bildiyi faktlar.
#:
#: RQ2-nin təmiz ölçüsü buradadır. Azərbaycana xas suallarda hər iki model
#: uğursuz olur (bilik yoxluğu), ona görə onlar fərqi SEYRƏLDİR və ümumi rəqəm
#: effekti olduğundan kiçik göstərir. Nəzarət qatında isə ingilis balları
#: üst-üstə düşür, yəni ümumi qabiliyyət fərqi istisna olunur və azərbaycanca
#: qalan fərq yalnız dilə aid ola bilər.
CONTROL_CATEGORIES: frozenset[str] = frozenset({"world", "science"})

#: Universal riyaziyyat: kateqoriya `mathematics`-dir, amma yarısı Azərbaycan
#: riyaziyyat tarixidir. Bunlar isə üçbucaq, sadə ədəd, ƏBOB tipli suallardır.
_UNIVERSAL_MATH_IDS: frozenset[str] = frozenset(
    {"az-920", "az-921", "az-922", "az-923", "az-924", "az-925", "az-926", "az-927"}
)


#: Kateqoriya etiketindən asılı olmayaraq universal sayılan Wikidata
#: şablonları. Hər biri DÜNYA obyektlərini gəzir, Azərbaycana xas deyil.
UNIVERSAL_TEMPLATES: frozenset[str] = frozenset(
    {"country_capital", "country_currency", "country_official_language"}
)

_TEMPLATE_IN_NOTES = re.compile(r"template=([a-z_]+)")


def _universal_template(record: dict[str, Any]) -> bool:
    """Sətir universal elan edilmiş şablondan gəlirmi?

    Şablon adı `notes` sahəsində saxlanılır (`template=country_capital;...`).
    Əl ilə yazılmış sətirlərdə belə qeyd olmur və onlar buradan keçmir; bu,
    QƏSDƏNDİR, çünki əl ilə yazılanlar Azərbaycana xas ola bilir.
    """
    match = _TEMPLATE_IN_NOTES.search(str(record.get("notes", "")))
    return bool(match) and match.group(1) in UNIVERSAL_TEMPLATES


def universal_ids(dataset: dict[str, dict[str, Any]]) -> list[str]:
    """NƏZARƏT təbəqəsi: mövzusu quruluşca universal olan suallar.

    NİYƏ KATEQORİYA KİFAYƏT ETMİR. Nəzarət qatının məqsədi modelin ingiliscə
    BİLDİYİ faktları seçməkdir: yalnız orada azərbaycanca uğursuzluq dil
    problemidir, bilik boşluğu yox. `geography` və `language` bu meyara
    uyğun gəlmir, çünki QARIŞIQDIR: eyni kateqoriyada həm "Rusiyanın
    paytaxtı", həm "Oxçuçayın mənsəbi" var.
    Ölçülüb: `history`-də model ingiliscə 2.2%, `culture`-də 6.3% bilir, ona
    görə həmin sətirlərdə itiriləcək bal demək olar yoxdur və uçurum 1-5 bənd
    çıxır. Onları nəzarətə salmaq effekti seyrəldir.

    MEXANİKİ QAYDA DA İŞLƏMİR. "Azərbaycan" sözünə görə süzgəc yer adlarını
    tutur, şəxs adlarını yox (`İlham Əliyev`, `Şəhriyar Məmmədyarov`), ad
    siyahısı isə sonsuzdur.

    Ona görə tərif MÖVZUYA görə verilir və quruluşca universal olan üç qrupu
    əhatə edir: `world` (paytaxt, valyuta), `science` (kimyəvi simvol, fiziki
    sabit) və hesablanan riyaziyyat.

    ŞABLON KATEQORİYADAN DƏQİQDİR (2026-09-08 əlavəsi). Yuxarıdakı etiraz
    kateqoriyaya aiddir, ŞABLONA yox. `country_capital` şablonu `geography`
    etiketi daşıyır, amma özü quruluşca universaldır: harvester `sitelinks>=8`
    süzgəci ilə DÜNYA ölkələrini gəzir, Azərbaycana xas obyekt seçmir. Yəni
    "Fransanın paytaxtı" sətri yalnız ETİKETİNƏ görə nəzarətdən kənarda
    qalırdı, məzmununa görə yox.

    `notes` sahəsində şablon adı yazılır, ona görə seçim dəqiqləşdirilə bilir.
    Bu, təbəqəni GENİŞLƏTMƏK üçün edilən güzəşt deyil, tərifin öz məntiqinin
    ardıcıl tətbiqidir: universallığı mövzu müəyyən edir, etiket yox.

    `language_writing_system` QƏSDƏN KƏNARDADIR, halbuki o da universaldır.
    Səbəb metodikidir: layihənin əsas iddiası yazı sistemi haqqındadır və
    nəzarət təbəqəsinə yazı sistemi haqqında suallar qoymaq lazımsız
    bağlılıq yaradır. 16 sətir itirilir, mübahisə isə qazanılır.
    """
    return sorted(
        record_id
        for record_id, record in dataset.items()
        if record.get("category") in CONTROL_CATEGORIES
        or _universal_template(record)
        or (
            record.get("category") == "mathematics"
            and (
                record_id in _UNIVERSAL_MATH_IDS
                or record.get("provenance") == "computed-template"
            )
        )
    )


def _paired(
    run_a: Run,
    run_b: Run,
    dataset: dict[str, dict[str, Any]],
    mode: NormalizationConfig,
    metric: str,
    seed: int,
    restrict_to: Sequence[str] | None = None,
):
    ids = sorted(run_a.ids & run_b.ids & set(dataset))
    if restrict_to is not None:
        allowed = set(restrict_to)
        ids = [i for i in ids if i in allowed]
    if not ids:
        return None, []
    a = _column(score_run(run_a, dataset, mode, ids), metric, ids)
    b = _column(score_run(run_b, dataset, mode, ids), metric, ids)
    return compare_paired(a, b, seed=seed), ids


def _table_with_holm(headers: Sequence[str], rows: list[list[Any]]) -> str:
    """Xam p sütununu düzəldilmiş p ilə birlikdə verir.

    Sətirlərin sondan əvvəlki elementi XAM `p` (float), sonuncusu isə xam
    həddə görə "bəli/xeyr" olmalıdır. Funksiya cədvəldəki bütün testləri bir
    ailə sayır, Holm düzəlişini tətbiq edir və nəticəni əlavə sütun kimi verir.

    Xam p qiyməti də saxlanılır — gizlətmək düzəlişin təsirini görünməz edərdi.
    """
    raw_p = [row[-2] for row in rows]
    adjusted = holm_correction(raw_p)

    out = []
    for row, p_adj in zip(rows, adjusted, strict=True):
        out.append(
            [*row[:-2], f"{row[-2]:.4f}", f"{p_adj:.4f}", "bəli" if p_adj < 0.05 else "xeyr"]
        )
    return markdown_table([*headers, "p", "p (Holm)", "Mənalı"], out)


def build_rq1_table(
    runs: Sequence[Run], dataset: dict[str, dict[str, Any]], seed: int = 0
) -> str:
    """RQ1: eyni modelin EN və AZ balları arasındakı cütləşdirilmiş fərq."""
    # Açar model + prompt üslubudur. Yalnız modelə görə qruplaşdırsaq, əlifba
    # nəzarəti qaçışı əsas qaçışı SƏSSİZCƏ əvəz edər və cədvəl yanlış cütləri
    # müqayisə edərdi.
    by_model: dict[str, dict[str, Run]] = defaultdict(dict)
    for run in runs:
        by_model[run_label(run.key)][run.key.language] = run

    rows = []
    for model, langs in sorted(by_model.items()):
        if "az" not in langs or "en" not in langs:
            continue
        for mode in MODES:
            result, ids = _paired(langs["en"], langs["az"], dataset, mode, "em", seed)
            if result is None:
                continue
            rows.append(
                [
                    model,
                    mode.name,
                    len(ids),
                    f"{100 * result.mean_b:.1f}%",
                    f"{100 * result.mean_a:.1f}%",
                    f"{100 * result.diff:.1f}pp",
                    f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}]",
                    result.p_value,
                    "bəli" if result.significant else "xeyr",
                ]
            )
    if not rows:
        return "_AZ və EN qaçışı olan model yoxdur._"
    return _table_with_holm(
        ["Model", "Rejim", "N", "AZ EM", "EN EM", "Fərq", "95% CI"], rows
    )


def build_rq2_table(
    runs: Sequence[Run],
    dataset: dict[str, dict[str, Any]],
    language: str = "az",
    seed: int = 0,
) -> str:
    """RQ2: modellərarası cütləşdirilmiş müqayisə (qazax modelinin transferi).

    DİQQƏT — hesabatda mütləq qeyd olunmalıdır: "Qolda AZ-də zəifdir" nəticəsi
    tək başına "türk dilləri arasında transfer yoxdur" demək DEYİL. Zəiflik
    qazax fine-tune-undan yox, modelin bazasından gələ bilər. Bu suala cavab
    vermək üçün Qolda-nın BAZA modeli də ölçülməli və bu cədvələ salınmalıdır.

    Müqayisə BÜTÜN rejimlərdə verilir, çünki yalnız STRICT-ə baxmaq nəticəni
    tərsinə çevirə bilər: kirillə cavab verən model STRICT-də zəif, TRANSLIT-də
    güclü görünür. Bir rejimli cədvəl bu fərqi gizlədərdi.
    """
    same_language = [r for r in runs if r.key.language == language]
    rows = []
    for i, run_a in enumerate(same_language):
        for run_b in same_language[i + 1 :]:
            # YALNIZ EYNİ PROMPT ÜSLUBU DAXİLİNDƏ. Fərqli üslublu iki qaçışı
            # tutuşdurmaq model fərqi ilə prompt fərqini qarışdırır və nəticə
            # heç birini ölçmür. Üstəlik kombinasiya sayı partlayır: robustluq
            # qaçışları əlavə olunanda bu cədvəl 42 sətirdən 684-ə çıxdı və
            # Holm ailəsi ilə birlikdə bütün p qiymətləri seyrəldi.
            if run_a.key.prompt_style != run_b.key.prompt_style:
                continue
            for mode in MODES:
                result, ids = _paired(run_a, run_b, dataset, mode, "em", seed)
                if result is None:
                    continue
                rows.append(
                    [
                        run_label(run_a.key),
                        run_label(run_b.key),
                        mode.name,
                        len(ids),
                        f"{100 * result.mean_a:.1f}%",
                        f"{100 * result.mean_b:.1f}%",
                        f"{100 * result.diff:.1f}pp",
                        f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}]",
                        result.p_value,
                        "bəli" if result.significant else "xeyr",
                    ]
                )
    if not rows:
        return f"_`{language}` dilində müqayisə üçün ən azı iki model lazımdır._"
    return _table_with_holm(
        ["Model A", "Model B", "Rejim", "N", "A EM", "B EM", "Fərq", "95% CI"],
        rows,
    )


def build_control_table(
    runs: Sequence[Run],
    dataset: dict[str, dict[str, Any]],
    seed: int = 0,
) -> str:
    """RQ2, yalnız NƏZARƏT qatında — işin ən təmiz ölçüsü.

    Ümumi RQ2 rəqəmi Azərbaycana xas suallarla seyrəlir: orada hər iki model
    uğursuzdur, ona görə aralarındakı fərq kiçilir. Bu cədvəl ölçünü yalnız
    modelin ingiliscə bildiyi faktlarla aparır.

    İNGİLİS sətri təsadüfi əlavə deyil, TƏLƏBDİR: o, "bəlkə qazax modeli sadəcə
    zəifdir?" etirazına cavabdır. İngilis balları statistik olaraq fərqlənmirsə,
    azərbaycanca qalan fərq ümumi qabiliyyətdən gələ bilməz.
    """
    control = universal_ids(dataset)
    rows: list[list[Any]] = []
    for language in ("en", "az"):
        same = [r for r in runs if r.key.language == language]
        for i, run_a in enumerate(same):
            for run_b in same[i + 1 :]:
                # Eyni prompt üslubu şərti, `build_rq2_table`-dakı ilə eyni
                # səbəbə görə: fərqli üslublu qaçışların müqayisəsi model
                # fərqini prompt fərqi ilə qarışdırır.
                if run_a.key.prompt_style != run_b.key.prompt_style:
                    continue
                for mode in MODES:
                    if language == "en" and mode is not STRICT:
                        continue  # ingilis tərəfdə rejimlərin təsiri sıfırdır
                    result, ids = _paired(
                        run_a, run_b, dataset, mode, "em", seed, control
                    )
                    if result is None:
                        continue
                    rows.append(
                        [
                            language.upper(),
                            run_label(run_a.key),
                            run_label(run_b.key),
                            mode.name,
                            len(ids),
                            f"{100 * result.mean_a:.1f}%",
                            f"{100 * result.mean_b:.1f}%",
                            f"{100 * result.diff:.1f}pp",
                            f"[{100 * result.diff_low:.1f}, {100 * result.diff_high:.1f}]",
                            result.p_value,
                            "bəli" if result.significant else "xeyr",
                        ]
                    )
    if not rows:
        return "_Nəzarət qatı boşdur._"
    return _table_with_holm(
        ["Dil", "Model A", "Model B", "Rejim", "N", "A EM", "B EM",
         "Fərq", "95% CI"],
        rows,
    )


def _group_key(record: dict[str, Any], dimension: str) -> str:
    """Kəsim ölçüsü: `category`, `variant` və ya `template`.

    `template` kəsimi ən vacibidir: dataset iki hissədən ibarətdir — universal
    NƏZARƏT faktları (Fransanın paytaxtı; model onları ingiliscə mütləq bilir)
    və AZƏRBAYCANA XAS məzmun (Təzəpir məscidinin memarı). İki qrupdakı AZ/EN
    fərqini müqayisə etmək məqalənin əsas müşahidəsidir: nəzarət qrupunda fərq
    təmiz dil emalı problemidir, AZ məzmununda isə üstünə bilik boşluğu gəlir.
    """
    if dimension == "category":
        return str(record.get("category", "—"))

    marker = "template=" if dimension == "template" else "variant="
    notes = str(record.get("notes", ""))
    return notes.split(marker)[1].split(";")[0] if marker in notes else "—"


def build_breakdown_table(
    runs: Sequence[Run],
    dataset: dict[str, dict[str, Any]],
    dimension: str = "category",
    seed: int = 0,
) -> str:
    """Kateqoriya və ya sual variantı üzrə kəsim.

    Variant kəsimi ayrıca dəyərlidir: eyni faktı fərqli quruluşda soruşduqda bal
    kəskin dəyişirsə, ölçdüyümüz şeyin bir hissəsi bilik yox, qəlibə tanışlıqdır.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for record_id, record in dataset.items():
        groups[_group_key(record, dimension)].append(record_id)

    header = ["Qrup", "N"] + [str(r.key) for r in runs]
    rows = []
    for group, group_ids in sorted(groups.items()):
        row: list[Any] = [group, len(group_ids)]
        for run in runs:
            ids = sorted(set(group_ids) & run.ids)
            if not ids:
                row.append("—")
                continue
            scores = score_run(run, dataset, STRICT, ids)
            row.append(f"{100 * sum(_column(scores, 'em', ids)) / len(ids):.1f}%")
        rows.append(row)
    return markdown_table(header, rows)


# --------------------------------------------------------------------------
# Xəta taksonomiyası üçün nümunə
# --------------------------------------------------------------------------


#: Avtomatik təsnifat etiketləri. Sıra ƏHƏMİYYƏTLİDİR: ilk uyğun gələn qalib.
AUTO_ERROR_TYPES = (
    "boş cavab",
    "yazı sistemi",
    "kiril, zəncir bərpa etmir",
    "diakritika",
    "morfologiya",
    "qismən üst-üstə düşmə",
    "",
)

#: Kiril əlifbasının hərf diapazonu. Sətirdə bir dənə də olsa varsa, model
#: cavabı latınla yazmayıb.
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def classify_error(
    prediction: str,
    gold: Sequence[str],
    f1_strict: float,
) -> str:
    """Səhvin bir hissəsini MAŞINLA, qərar vermədən etiketləyir.

    NİYƏ BU LEGİTİMDİR. Normalizasiya zənciri YUVALANMIŞDIR və hər həlqə
    DƏQİQ BİR çevrilmə əlavə edir:

        STRICT  -> MORPH     şəkilçi soyulması
        MORPH   -> LENIENT   diakritika qatlanması
        LENIENT -> TRANSLIT  kirildən latına transliterasiya

    Ona görə "hansı həlqə xətanı düzəltdi" sualının cavabı səbəbin ÖZÜDÜR,
    evristika deyil. Bu, zəncirin qurulma səbəbidir; burada sadəcə oxunur.

    ZƏNCİR HƏR KİRİLİ BƏRPA ETMİR və bu, ayrıca səbət tələb edir. Nümunə:
    model `Вашингтон` yazır, transliterasiya `vaşington` verir, qızıl cavab
    isə `vaşinqton`-dur. Kiril `г` latın `g`-yə düşür, azərbaycanca isə həmin
    səsi `q` ilə yazır. Cavab MƏZMUNCA düzdür, zəncir isə onu tutmur.

    Belə sətirləri "faktual səhv" kimi qeyd etmək ölçünü əyərdi, ona görə
    onlar `kiril, zəncir bərpa etmir` səbətinə düşür. AD SƏBƏB DEYİL: sətrin
    kirillə yazıldığı MÜŞAHİDƏDİR, faktın düz olub-olmadığı isə insanın
    qərarıdır. Səbət ölçülür, iddia edilmir.

    NƏYİ ETİKETLƏMİR. Latın yazılıb, zəncirin heç bir həlqəsi düzəltmirsə,
    səhv faktualdır, formatdandır, yoxsa başqa səbəbdəndir — bunu AYIRD ETMƏK
    MÜHAKİMƏ tələb edir və maşın onu boş buraxır. Boş qalan sətirlər
    `error_type` sütununda insan tərəfindən doldurulmalıdır.

    `error_type_auto` və `error_type` AYRI sütunlardır. Maşın etiketi insan
    etiketinin yerini tutmur; onu daraldır.
    """
    text = prediction.strip()
    if not text:
        return "boş cavab"

    def hits(mode) -> bool:
        return score_example(text, list(gold), mode)["em"] == 1.0

    if hits(STRICT):
        # STRICT düzdürsə bu sətir səhv siyahısına düşməməli idi.
        return ""
    if hits(MORPH):
        return "morfologiya"
    if hits(LENIENT):
        return "diakritika"
    if hits(TRANSLIT):
        return "yazı sistemi"
    if _CYRILLIC.search(text):
        return "kiril, zəncir bərpa etmir"
    if f1_strict > 0.0:
        return "qismən üst-üstə düşmə"
    return ""


def auto_error_summary(rows: Sequence[dict[str, Any]]) -> str:
    """Avtomatik etiketlərin payı: insana nə qədər iş qaldığını göstərir."""
    counts = Counter(str(row.get("error_type_auto", "")) for row in rows)
    total = sum(counts.values()) or 1
    lines = [
        "| Avtomatik növ | n | pay |",
        "|---|---|---|",
    ]
    for label in AUTO_ERROR_TYPES:
        name = label or "_(insan qərarı lazımdır)_"
        n = counts.get(label, 0)
        lines.append(f"| {name} | {n} | {100 * n / total:.1f}% |")
    return "\n".join(lines)


def error_rows(
    run: Run,
    dataset: dict[str, dict[str, Any]],
    sample_size: int = 100,
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Səhv cavabların kateqoriya üzrə TƏBƏQƏLƏNDİRİLMİŞ nümunəsi.

    Təbəqələndirmə vacibdir: sadə təsadüfi nümunə ən böyük kateqoriyanı üstün
    göstərir və xəta taksonomiyası əyilir.

    `error_type` sütunu QƏSDƏN boş qalır — RQ3-ün cavabı əl ilə etiketlənməlidir.
    Sütun adları brief-in 6-cı bölməsindəki kateqoriyalara uyğundur.
    """
    ids = sorted(run.ids & set(dataset))
    strict = score_run(run, dataset, STRICT, ids)
    lenient = score_run(run, dataset, LENIENT, ids)

    wrong = [i for i in ids if strict[i]["em"] == 0.0]
    by_category: dict[str, list[str]] = defaultdict(list)
    for record_id in wrong:
        by_category[str(dataset[record_id].get("category", "—"))].append(record_id)

    rng = random.Random(seed)
    per_group = max(1, sample_size // max(1, len(by_category)))
    chosen: list[str] = []
    for group_ids in by_category.values():
        pool = sorted(group_ids)
        rng.shuffle(pool)
        chosen.extend(pool[:per_group])

    # Kvota bütün yerləri doldurmayıbsa, qalanı ümumi hovuzdan tamamlanır.
    if len(chosen) < min(sample_size, len(wrong)):
        remaining = sorted(set(wrong) - set(chosen))
        rng.shuffle(remaining)
        chosen.extend(remaining[: sample_size - len(chosen)])

    chosen = sorted(chosen)[:sample_size]

    return [
        {
            "id": record_id,
            "category": dataset[record_id].get("category", ""),
            "variant": _group_key(dataset[record_id], "variant"),
            "question": dataset[record_id].get(
                "question_az" if run.key.language == "az" else "question_en", ""
            ),
            "gold": gold_answers(dataset[record_id], run.key.language)[0],
            "prediction": run.predictions.get(record_id, ""),
            "raw_response": run.raw.get(record_id, ""),
            "em_lenient": lenient[record_id]["em"],
            "f1_strict": round(strict[record_id]["f1"], 3),
            # Maşın doldurur: zəncirin hansı həlqəsi xətanı düzəltdiyindən
            # birbaşa çıxarılır. Qərar tələb edən sətirlərdə boş qalır.
            "error_type_auto": classify_error(
                run.predictions.get(record_id, ""),
                gold_answers(dataset[record_id], run.key.language),
                strict[record_id]["f1"],
            ),
            # Əl ilə doldurulur: faktual | format | digər. Maşın etiketi olan
            # sətirlərdə də insan fikri üstündür.
            "error_type": "",
        }
        for record_id in chosen
    ]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="analyze", description="Xam cavabları cədvəllərə çevirir"
    )
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/tables"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--error-sample", type=int, default=100)
    parser.add_argument("--max-answer-words", type=int, default=12)
    args = parser.parse_args(argv)

    dataset = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    if not dataset:
        print(f"Dataset boşdur: {args.dataset}", file=sys.stderr)
        return 1

    runs = load_runs(args.raw_dir, max_words=args.max_answer_words)
    if not runs:
        print(f"Qaçış tapılmadı: {args.raw_dir}", file=sys.stderr)
        return 1

    print(f"{len(dataset)} sətir, {len(runs)} qaçış\n")
    for run in runs:
        missing = set(dataset) - run.ids
        if missing:
            print(f"  DİQQƏT: {run.key}: {len(missing)} sətir üçün cavab yoxdur")

    # Qismən qaçışlar müqayisə cədvəllərindən kənarda qalır. Səbəb
    # `partition_by_coverage` sənədində: yarımçıq qaçışın sətirləri təsadüfi
    # seçmə deyil, datasetin asan başlanğıcıdır.
    complete_runs, partial_runs = partition_by_coverage(runs, dataset)
    if partial_runs:
        print(
            f"\n  {len(partial_runs)} qismən qaçış müqayisədən çıxarıldı "
            f"(örtük < {COVERAGE_THRESHOLD:.0%}):"
        )
        for run in partial_runs:
            print(f"    {run.key}: {len(run.ids & set(dataset))}/{len(dataset)}")

    # ÇIXARIŞ QAPISI. Örtük qapısı qaçışın TAM olub-olmadığına baxır; bu qapı
    # isə balın MƏNALI olub-olmadığına. Cavab xam mətndədirsə və bala
    # çevrilmirsə, rəqəm modelin biliyini yox, çıxış formatını ölçür və
    # müqayisə cədvəlində olmamalıdır. Bax `src/extraction_gate.py`.
    #
    # İdxal FUNKSİYANIN İÇİNDƏDİR: `extraction_gate` bu moduldan `score_run`
    # götürür, ona görə modul səviyyəsində idxal dairəvi olardı.
    from src.extraction_gate import degenerate as extraction_degenerate

    unextractable = [
        run for run in complete_runs if extraction_degenerate(run, dataset) is not None
    ]
    if unextractable:
        print(f"\n  {len(unextractable)} qaçış ÇIXARIŞ qapısından keçmədi:")
        for run in unextractable:
            share = extraction_degenerate(run, dataset)
            print(f"    {run.key}: səhvlərin {100 * share:.1f}%-ində cavab xam mətndə")
        dropped = {id(run) for run in unextractable}
        complete_runs = [run for run in complete_runs if id(run) not in dropped]

    tables = {
        "main.md": (
            "Əsas nəticələr (STRICT)",
            build_main_table(runs, dataset, args.seed)
            + coverage_note(partial_runs, dataset),
        ),
        "modes.md": (
            "Normalizasiya rejimləri — RQ3 dekompozisiyası",
            build_modes_table(complete_runs, dataset, args.seed),
        ),
        "rq1.md": ("RQ1 — AZ vs EN", build_rq1_table(complete_runs, dataset, args.seed)),
        "rq2.md": (
            "RQ2 — modellərarası müqayisə (AZ)",
            build_rq2_table(complete_runs, dataset, "az", args.seed),
        ),
        "control.md": (
            "RQ2 nəzarət qatında (world + science) — ən təmiz ölçü",
            build_control_table(complete_runs, dataset, args.seed),
        ),
        "provenance.md": (
            "Mənşə — hər rəqəm hansı şəraitdə alınıb",
            build_provenance_table(runs),
        ),
        "breakdown.md": (
            "Kateqoriya üzrə kəsim",
            build_breakdown_table(complete_runs, dataset, "category", args.seed)
            + "\n\n### Sual variantı üzrə kəsim\n\n"
            + build_breakdown_table(complete_runs, dataset, "variant", args.seed),
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for filename, (title, table) in tables.items():
        (args.out_dir / filename).write_text(
            f"# {title}\n\n{table}\n", encoding="utf-8"
        )
        print(f"\n## {title}\n\n{table}")

    # Xəta nümunəsi — hər AZ qaçışı üçün ayrıca fayl.
    taxonomy: list[str] = [
        "# Xəta taksonomiyası (avtomatik hissə)",
        "",
        "`error_type_auto` sütunu normalizasiya zəncirindən ÇIXARILIR: hansı",
        "həlqə xətanı düzəldirsə, səbəb odur. `error_type` sütunu isə boş",
        "qalır və insan tərəfindən doldurulur. Aşağıdakı cədvəllər insana nə",
        "qədər iş qaldığını göstərir.",
        "",
    ]
    for run in runs:
        if run.key.language != "az":
            continue
        rows = error_rows(run, dataset, args.error_sample, args.seed)
        if not rows:
            continue
        path = args.out_dir / error_file_name(run.key)
        with open(path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n{len(rows)} səhv cavab -> {path}")
        print("  `error_type` sütununu əl ilə doldur (RQ3).")
        taxonomy += [f"## `{run_label(run.key)}`", "", auto_error_summary(rows), ""]

    (args.out_dir / "errors.md").write_text("\n".join(taxonomy), encoding="utf-8")

    print(f"\nCədvəllər: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
