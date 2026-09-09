"""Datasetin yığılması və validasiyası.

İş axını:

    data/raw/*.jsonl   (qaralamalar, LLM tərcümələri, əl ilə yazılmış suallar)
            |
            |  validate  -> sxem + keyfiyyət yoxlaması
            |  build     -> yalnız verified_by="human" olan sətirlər keçir
            v
    data/az_eval_v0.jsonl   (yekun dataset)

Brief-in mərkəzi keyfiyyət qaydası budur: yoxlanılmamış maşın tərcüməsi bütün
nəticəni etibarsızlaşdırır. Ona görə `verified_by` sahəsi məlumat deyil, QAPI-dır:
`build` əmri "human" olmayan sətri yekun datasetə buraxmır. Qaralama sətirləri
`data/raw/` altında `verified_by="llm-draft"` və ya `"pending"` ilə saxlanılır.

İstifadə:

    python -m src.build_dataset validate data/raw/pilot.jsonl
    python -m src.build_dataset stats    data/az_eval_v0.jsonl
    python -m src.build_dataset build    --out data/az_eval_v0.jsonl
    python -m src.build_dataset template --out data/raw/pilot.jsonl -n 5

DİQQƏT — `data/az_eval_v0.jsonl` ARTEFAKTDIR, MƏNBƏ DEYİL.

`build` onu hər dəfə `data/raw/` altındakı fayllardan yenidən qurur. Yekun
faylda edilən düzəliş növbəti `build` zamanı SƏSSİZCƏ İTİR.

Bu, nəzəri risk deyil: 2026-09-08-də üç riyaziyyat sualının mətni yekun
faylda düzəldildi, sonra başqa səbəbdən `build` işlədildi və düzəliş silindi.
Səhv yalnız təsadüfən, həmin sətirlərə yenidən baxılanda tutuldu.

QAYDA: düzəliş HƏMİŞƏ `data/raw/` altındakı mənbə faylında edilir, sonra
`build` çağırılır.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.metrics import STRICT, normalize, tokenize
from src.morphology import aliases_for

__all__ = [
    "REQUIRED_FIELDS",
    "OPTIONAL_FIELDS",
    "DROPPED_FIELDS",
    "CATEGORIES",
    "VERIFICATION_STATES",
    "Issue",
    "ValidationReport",
    "load_jsonl",
    "write_jsonl",
    "validate_record",
    "validate_dataset",
    "build_dataset",
    "dataset_stats",
    "fill_aliases",
    "equivalence_aliases",
    "prepare_manual",
    "MANUAL_REQUIRED_FIELDS",
    "contains_token_sequence",
]


REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "question_az",
    "question_en",
    "answer",
    "answer_en",       # RQ1 cütləşdirilmiş AZ/EN müqayisəsi bunsuz qurulmur
    "category",
    "source",
    "provenance",
    "verified_by",
)

OPTIONAL_FIELDS: tuple[str, ...] = (
    "answer_aliases",  # qəbul edilən digər cavab formaları (`src.morphology`)
    "difficulty",      # xam faylda qəbul edilir, DƏSTƏ ÇIXMIR: `DROPPED_FIELDS`
    "notes",           # əl yoxlaması zamanı qeydlər
)

#: Xam fayllarda qəbul edilən, amma HAZIR DƏSTƏ YAZILMAYAN sahələr.
#:
#: `difficulty` niyə çıxarıldı (2026-09-09). Sahə sual-sual mühakimə kimi
#: görünürdü, amma heç vaxt belə mühakimə olmayıb: dəyər ŞABLON səviyyəsində
#: sabitdir. Yoxlanıldı — 26 şablon qrupundan yalnız birində iki dəyər var,
#: o da riyaziyyat ailəsinin öz sabitidir. Yəni sahə `notes`-dakı
#: `template=...` yazısından tam bərpa olunur və müstəqil məlumat daşımır.
#:
#: Üstəlik `build` komandası dəyər verilməyəndə səssizcə "medium" qoyurdu,
#: ona görə 1006 sətirdən 881-i "medium" idi. Bu, "orta çətinlik" kimi
#: oxunurdu, halbuki "heç kim baxmayıb" demək idi.
#:
#: Saxlamaqla düzəltmək mümkün deyildi: dəyər HƏMİŞƏ var, çünki hər şablon
#: onu qoyur. Ona görə seçim ya yanıltmaq, ya çıxarmaqdır. Çıxarılır.
DROPPED_FIELDS: tuple[str, ...] = ("difficulty",)

#: `world` qəsdən ayrıca kateqoriyadır, Azərbaycan mövzularının yanında.
#:
#: O, NƏZARƏT qrupunu işarələyir: model bu faktları ingiliscə mütləq bilir
#: (dünya paytaxtları, elementlər), ona görə azərbaycanca uğursuzluq bilik
#: çatışmazlığı yox, dil emalı problemidir. Azərbaycana xas kateqoriyalarda isə
#: uğursuzluğa bilik boşluğu da qarışır.
#:
#: İki qrupun AZ/EN fərqini müqayisə etmək işin əsas müşahidəsidir, ona görə
#: bölgü şablon adından çıxarılmaqdansa datada açıq saxlanılır.
#:
#: `mathematics` `science`-dən ayrı saxlanılır: riyazi terminologiya azərbaycancada
#: böyük ölçüdə alınmadır (`triqonometriya`, `inteqral`, `funksional analiz`), yəni
#: latın qrafikasına daha yaxındır. Ümumi elm suallarından ayrı ölçülməsə, bu qat
#: `science` sütununa qarışır və yazı sistemi effektini süni olaraq zəiflədir.
CATEGORIES: frozenset[str] = frozenset(
    {"history", "geography", "science", "culture", "language", "world", "mathematics"}
)

#: Yalnız "human" yekun datasetə keçir. `rejected` sətirlər SİLİNMİR — saxlanılır,
#: çünki qəbul faizi datasetin keyfiyyət göstəricisidir və məqalədə verilməlidir
#: ("N qaralamadan X%-i əl yoxlamasından keçdi").
#:
#: `external` — KƏNAR dəstin müəllifləri tərəfindən yoxlanılıb, BİZ yoxlamamışıq.
#:
#: Niyə ayrıca vəziyyət lazımdır. TUMLU-mini sətirləri öz müəllifləri
#: tərəfindən əl ilə yoxlanılıb və biz onları qüsur auditindən keçirmişik,
#: amma BİZİM annotatorumuz hər sətri təsdiqləməyib. Onları `pending`
#: adlandırmaq YANLIŞ idi: `pending` "heç kim baxmayıb" deməkdir və kənar
#: yoxlamanı gizlədirdi. `human` adlandırmaq isə daha pis olardı: bizim
#: etmədiyimiz işi iddia etmək olardı.
#:
#: `external` sətirlər YEKUN DATASETƏ KEÇMİR, `human` kimi davranmır. Onlar
#: yalnız kənar dəst üzərində aparılan analizlərdə (`format_contrast`)
#: işlədilir və orada mənbə açıq göstərilir.
VERIFICATION_STATES: frozenset[str] = frozenset(
    {"human", "external", "pending", "llm-draft", "rejected"}
)

#: Sətrin haradan gəldiyi. Etik tələb (brief 4-cü bölmə: LLM istifadəsi açıq
#: yazılmalıdır) və eyni zamanda məqalə üçün nəticə kəsimi — mənbə tipi üzrə
#: performans fərqi özü nəticədir.
PROVENANCE_STATES: frozenset[str] = frozenset(
    {
        "manual",             # tamamilə əl ilə yazılıb
        "wikidata-template",  # Wikidata faktından şablonla qurulub
        "llm-passage",        # mətn abzasından LLM qaralaması, cavab abzasda span
        "computed-template",  # cavabı alqoritm hesablayır (`src.generate_math`)
    }
)

DIFFICULTIES: frozenset[str] = frozenset({"easy", "medium", "hard"})

ID_PATTERN = re.compile(r"^az-\d{3,}$")

#: Azərbaycan əlifbasına xas hərflər — RQ3-ün mövzusu.
#:
#: Nöqtəsiz baş `I` siyahıda YOXDUR: o, ASCII `I` ilə eyni Unicode koddur
#: (U+0049), ona görə "bu mətndə Azərbaycan hərfi var" sualına cavab verə
#: bilmir — tərkibində istənilən baş `I` olan ingilis cümləsi də keçərdi.
#: Nöqtəli `İ` (U+0130) isə həqiqətən fərqləndiricidir.
AZ_SPECIFIC_CHARS = frozenset("əğıöşüçƏĞİÖŞÜÇ")

#: Diakritiksiz yazılmış yüksək tezlikli Azərbaycan sözləri.
#:
#: "Diakritik yoxdursa xəbərdarlıq ver" qaydası işləmir: "Qurban Qurbanov harada
#: anadan olub?" tamamilə düzgün Azərbaycan cümləsidir və içində bir dənə də
#: xüsusi hərf yoxdur. Belə yalançı siqnal istifadəçini xəbərdarlıqlara etinasız
#: olmağa öyrədir — ən pis nəticə budur.
#:
#: Ona görə əlamət konkretdir: bu sözlər Azərbaycan dilində HƏMİŞƏ diakritiklidir,
#: diakritiksiz formada görünürlərsə, mətn latınlaşdırılıb.
DIACRITIC_LOSS_MARKERS: frozenset[str] = frozenset(
    {
        "hansi", "hansisi", "nedir", "nece", "necedir", "seher", "seherdir",
        "olke", "olkenin", "ilde", "ildir", "yerlesir", "elifba", "elifbasi",
        "dilinde", "erazi", "erazisinde", "ehali", "ehalisi", "ve", "genc",
        "boyuk", "kicik", "dovlet", "dovletin", "muharibe", "resm", "sehife",
    }
)


# --------------------------------------------------------------------------
# Problem hesabatı
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Issue:
    """Bir validasiya problemi.

    `severity="error"` -> `build` datasetı yazmır.
    `severity="warning"` -> yazılır, amma ekrana çıxarılır (əl baxışı üçün).
    """

    severity: str
    line: int
    record_id: str | None
    field: str | None
    message: str

    def __str__(self) -> str:
        loc = f"sətir {self.line}"
        if self.record_id:
            loc += f" [{self.record_id}]"
        if self.field:
            loc += f" .{self.field}"
        return f"{self.severity.upper():7} {loc}: {self.message}"


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)
    n_records: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(
        self,
        severity: str,
        line: int,
        record_id: str | None,
        field_name: str | None,
        message: str,
    ) -> None:
        self.issues.append(Issue(severity, line, record_id, field_name, message))

    def summary(self) -> str:
        return (
            f"{self.n_records} sətir yoxlanıldı — "
            f"{len(self.errors)} xəta, {len(self.warnings)} xəbərdarlıq"
        )


# --------------------------------------------------------------------------
# G/Ç
# --------------------------------------------------------------------------


#: `run_eval` promptundakı few-shot nümunələrinin cavabları (normallaşdırılmış).
#:
#: NİYƏ QAPI LAZIMDIR: prompt modelə iki həll olunmuş nümunə göstərir
#: ("Su molekulunun kimyəvi formulu nədir? Cavab: H2O"). Həmin fakt datasetə
#: düşsə, model cavabı ÖZ PROMPTUNDA görür və bal biliyi yox, surətçıxarmanı
#: ölçür.
#:
#: v1-də bu, əl ilə yoxlanılırdı və bir sətir yayındı: `az-546`
#: ("Suyun kimyəvi formulu nədir?" -> H2O) sözlə fərqlənir, faktla eynidir.
#: Sual mətnini müqayisə etmək onu tutmur; CAVABI müqayisə etmək tutur, çünki
#: promptda modelə göstərilən məhz cavab sətridir.
#:
#: Siyahının `run_eval`-dakı promptla üst-üstə düşdüyünü
#: `tests/test_build_dataset.py::test_prompt_example_answers_match_run_eval`
#: yoxlayır, yəni prompt dəyişsə test xəbər verir.
PROMPT_EXAMPLE_ANSWERS: frozenset[str] = frozenset({"qahirə", "cairo", "h2o"})



def load_jsonl(path: str | Path) -> list[tuple[int, Any]]:
    """JSONL faylını (sətir nömrəsi, parse olunmuş dəyər) cütləri kimi oxuyur.

    Parse xətası olan sətir atılmır — dəyər yerinə `JSONDecodeError` qaytarılır ki,
    validator onu adi problem kimi hesabata sala bilsin. Beləliklə bir korlanmış
    sətir bütün faylın yoxlanışını dayandırmır.
    """
    records: list[tuple[int, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                records.append((lineno, json.loads(raw)))
            except json.JSONDecodeError as exc:
                records.append((lineno, exc))
    return records


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> int:
    """JSONL yazır (UTF-8, ensure_ascii=False ki, fayl əl ilə oxunaqlı qalsın)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


# --------------------------------------------------------------------------
# Validasiya
# --------------------------------------------------------------------------


def _is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def contains_token_sequence(haystack: Sequence[str], needle: Sequence[str]) -> bool:
    """`needle` token ardıcıllığı `haystack` içində bütöv keçirmi."""
    if not needle or len(needle) > len(haystack):
        return False
    return any(
        list(haystack[i : i + len(needle)]) == list(needle)
        for i in range(len(haystack) - len(needle) + 1)
    )


def validate_record(record: Any, line: int, report: ValidationReport) -> str | None:
    """Bir sətri yoxlayır, ID-ni qaytarır (təkrar yoxlaması üçün)."""
    if isinstance(record, json.JSONDecodeError):
        report.add("error", line, None, None, f"JSON parse xətası: {record.msg}")
        return None

    if not isinstance(record, dict):
        report.add(
            "error", line, None, None, f"obyekt gözlənilirdi, {type(record).__name__} gəldi"
        )
        return None

    record_id = record.get("id") if isinstance(record.get("id"), str) else None

    # --- məcburi sahələr -------------------------------------------------
    for name in REQUIRED_FIELDS:
        if name not in record:
            report.add("error", line, record_id, name, "məcburi sahə yoxdur")
        elif _is_blank(record[name]):
            report.add("error", line, record_id, name, "boş və ya mətn deyil")

    # --- naməlum sahələr -------------------------------------------------
    known = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for name in record:
        if name not in known:
            report.add("warning", line, record_id, name, "sxemdə olmayan sahə")

    # --- ID formatı ------------------------------------------------------
    if record_id and not ID_PATTERN.match(record_id):
        report.add(
            "error", line, record_id, "id", "format `az-001` şablonuna uyğun deyil"
        )

    # --- sabit dəyər siyahıları ------------------------------------------
    category = record.get("category")
    if isinstance(category, str) and category.strip() and category not in CATEGORIES:
        report.add(
            "error",
            line,
            record_id,
            "category",
            f"`{category}` icazə verilən siyahıda yoxdur: {sorted(CATEGORIES)}",
        )

    verified_by = record.get("verified_by")
    if (
        isinstance(verified_by, str)
        and verified_by.strip()
        and verified_by not in VERIFICATION_STATES
    ):
        report.add(
            "error",
            line,
            record_id,
            "verified_by",
            f"`{verified_by}` icazə verilən siyahıda yoxdur: {sorted(VERIFICATION_STATES)}",
        )

    provenance = record.get("provenance")
    if (
        isinstance(provenance, str)
        and provenance.strip()
        and provenance not in PROVENANCE_STATES
    ):
        report.add(
            "error",
            line,
            record_id,
            "provenance",
            f"`{provenance}` icazə verilən siyahıda yoxdur: {sorted(PROVENANCE_STATES)}",
        )

    difficulty = record.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTIES:
        report.add(
            "error",
            line,
            record_id,
            "difficulty",
            f"`{difficulty}` icazə verilən siyahıda yoxdur: {sorted(DIFFICULTIES)}",
        )

    # --- alias siyahısı --------------------------------------------------
    aliases = record.get("answer_aliases")
    if aliases is not None:
        if not isinstance(aliases, list):
            report.add("error", line, record_id, "answer_aliases", "siyahı olmalıdır")
        elif any(_is_blank(a) for a in aliases):
            report.add(
                "error",
                line,
                record_id,
                "answer_aliases",
                "siyahıda boş və ya mətn olmayan element var",
            )
        elif not aliases:
            report.add(
                "warning",
                line,
                record_id,
                "answer_aliases",
                "boşdur — `build_dataset aliases` əmri ilə avtomatik doldurula bilər",
            )

    # --- keyfiyyət xəbərdarlıqları ---------------------------------------
    question_az = record.get("question_az")
    question_en = record.get("question_en")
    answer = record.get("answer")

    if isinstance(question_az, str) and isinstance(question_en, str):
        if question_az.strip() and question_az.strip() == question_en.strip():
            report.add(
                "warning",
                line,
                record_id,
                "question_az",
                "ingilis variantı ilə eynidir — tərcümə olunmayıb?",
            )

    if isinstance(question_az, str) and question_az.strip():
        if not AZ_SPECIFIC_CHARS & set(question_az):
            latinised = DIACRITIC_LOSS_MARKERS & set(normalize(question_az, STRICT).split())
            if latinised:
                report.add(
                    "warning",
                    line,
                    record_id,
                    "question_az",
                    f"diakritiklər itib — {sorted(latinised)} diakritiksiz yazılıb",
                )
        # Sual işarəsi TƏLƏB EDİLMİR: datasetdə əmr formalı tapşırıqlar da var
        # ("Fransanın paytaxtını yaz."). Yoxlanılan şey yarımçıq kəsilmiş
        # mətndir — ona görə hər hansı bitirici durğu işarəsi kifayətdir.
        if not question_az.strip().endswith(("?", ".", "!", ":")):
            report.add(
                "warning",
                line,
                record_id,
                "question_az",
                "bitirici durğu işarəsi yoxdur — mətn yarımçıq kəsilib?",
            )

    if isinstance(answer, str) and isinstance(question_az, str):
        # Sızma yoxlaması TOKEN səviyyəsindədir, alt-sətir səviyyəsində deyil.
        # Alt-sətir yoxlaması qısa cavabları yandırır: "H" cavabı "hidrogen"
        # sualının içində keçir, halbuki heç bir sızma yoxdur.
        answer_tokens = tokenize(answer, STRICT)
        question_tokens = tokenize(question_az, STRICT)
        if answer_tokens and contains_token_sequence(question_tokens, answer_tokens):
            report.add(
                "warning",
                line,
                record_id,
                "answer",
                "cavab sualın içində birbaşa keçir — sualın sızması (leakage)",
            )

    # Qapı yalnız DATASETƏ DÜŞƏCƏK sətirlərə tətbiq olunur. Rədd edilmiş sətir
    # onsuz da kənardadır və layihə onu qəsdən saxlayır (qəbul faizi auditə
    # açıq qalsın deyə); ona xəta vermək build-i həmişəlik bloklayardı.
    if (
        verified_by == "human"
        and isinstance(answer, str)
        and normalize(answer, STRICT) in PROMPT_EXAMPLE_ANSWERS
    ):
        report.add(
            "error",
            line,
            record_id,
            "answer",
            "cavab promptdakı few-shot nümunəsi ilə eynidir — model onu öz "
            "promptunda görür, ona görə bu sətir bilik ölçmür",
        )

    if verified_by != "human":
        report.add(
            "warning",
            line,
            record_id,
            "verified_by",
            f"`{verified_by}` — əl yoxlamasından keçməyib, yekun datasetə buraxılmayacaq",
        )

    return record_id


def validate_dataset(records: Sequence[tuple[int, Any]]) -> ValidationReport:
    """Bütün faylı yoxlayır: sətir səviyyəsi + ID unikallığı + sual təkrarı."""
    report = ValidationReport(n_records=len(records))

    seen_ids: dict[str, int] = {}
    seen_questions: dict[str, tuple[int, str | None]] = {}

    for line, record in records:
        record_id = validate_record(record, line, report)

        if record_id:
            if record_id in seen_ids:
                report.add(
                    "error",
                    line,
                    record_id,
                    "id",
                    f"təkrar ID — ilk dəfə {seen_ids[record_id]}-ci sətirdə görünüb",
                )
            else:
                seen_ids[record_id] = line

        if isinstance(record, dict):
            question = record.get("question_az")
            if isinstance(question, str) and question.strip():
                key = normalize(question, STRICT)
                if key in seen_questions:
                    prev_line, prev_id = seen_questions[key]
                    report.add(
                        "warning",
                        line,
                        record_id,
                        "question_az",
                        f"sual {prev_line}-ci sətirlə ([{prev_id}]) eynidir",
                    )
                else:
                    seen_questions[key] = (line, record_id)

    return report


# --------------------------------------------------------------------------
# Yığma
# --------------------------------------------------------------------------


def _iter_raw_files(raw_dir: Path) -> Iterator[Path]:
    yield from sorted(p for p in raw_dir.glob("*.jsonl") if p.is_file())


def build_dataset(
    raw_dir: str | Path,
    out_path: str | Path,
    require_human: bool = True,
) -> tuple[list[dict[str, Any]], ValidationReport]:
    """`data/raw/*.jsonl` fayllarını birləşdirib yekun dataseti hazırlayır.

    Xəta varsa fayl YAZILMIR — qayıdan siyahı boş olur və hesabatdakı xətalar
    çağıran tərəfindən göstərilir. `require_human=False` yalnız pilot mərhələdə
    qaralama üzərində metrik borusunu sınamaq üçündür; yekun rəqəmlərdə istifadə
    edilməməlidir.
    """
    raw_dir = Path(raw_dir)
    all_records: list[tuple[int, Any]] = []
    origins: dict[int, str] = {}

    offset = 0
    for path in _iter_raw_files(raw_dir):
        for line, record in load_jsonl(path):
            all_records.append((offset + line, record))
            origins[offset + line] = path.name
        offset += 100_000  # fayllar arası sətir nömrələri toqquşmasın

    report = validate_dataset(all_records)
    if not report.ok:
        return [], report

    accepted: list[dict[str, Any]] = []
    for _, record in all_records:
        if require_human and record.get("verified_by") != "human":
            continue
        accepted.append(record)

    accepted.sort(key=lambda r: r["id"])
    accepted = [
        {k: v for k, v in record.items() if k not in DROPPED_FIELDS}
        for record in accepted
    ]
    write_jsonl(out_path, accepted)
    return accepted, report


def dataset_stats(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Kateqoriya/mənbə paylanması, hərf örtüyü və ƏKSƏRİYYƏT BAZASI.

    `majority_baseline` ən vacib rəqəmdir və hər `build`-dan sonra oxunmalıdır.
    O, "həmişə ən çox rast gəlinən cavabı de" strategiyasının alacağı baldır.

    Avtomatik yığılmış datasetlərdə bu rəqəm asanlıqla partlayır: Wikidata-dan
    "azərbaycanlı şəxs -> doğum yeri" sorğusu çəksən, cavabların çoxu "Bakı"
    çıxır və heç nə bilməyən model 60-70% alır. Belə dataset benchmark deyil.

    Praktik hədd: `majority_baseline` 15%-i keçirsə, cavab dəyəri başına kvota
    sərtləşdirilməlidir (`harvest_wikidata.py --max-per-answer`).
    """
    answer_lengths = [len(str(r.get("answer", "")).split()) for r in records]
    az_char_rows = sum(
        1 for r in records if AZ_SPECIFIC_CHARS & set(str(r.get("question_az", "")))
    )

    answer_counts = Counter(
        normalize(str(r.get("answer", "")), STRICT) for r in records
    )
    top_answer, top_count = (
        answer_counts.most_common(1)[0] if answer_counts else ("—", 0)
    )

    return {
        "n": len(records),
        "by_category": dict(sorted(Counter(r.get("category") for r in records).items())),
        "by_provenance": dict(
            sorted(Counter(r.get("provenance") for r in records).items())
        ),
        "by_verified_by": dict(
            sorted(Counter(r.get("verified_by") for r in records).items())
        ),
        "with_aliases": sum(1 for r in records if r.get("answer_aliases")),
        "rows_with_az_chars": az_char_rows,
        "distinct_answers": len(answer_counts),
        "most_common_answer": top_answer,
        "majority_baseline": (
            round(100 * top_count / len(records), 1) if records else 0.0
        ),
        "answer_words_mean": (
            round(sum(answer_lengths) / len(answer_lengths), 2) if answer_lengths else 0
        ),
        "answer_words_max": max(answer_lengths, default=0),
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

TEMPLATE_ROW: dict[str, Any] = {
    "id": "az-000",
    "question_az": "SUALI BURA YAZ?",
    "question_en": "WRITE THE ENGLISH PARALLEL HERE?",
    "answer": "CAVAB",
    "answer_en": "ANSWER",
    "answer_aliases": [],
    "category": "history",
    "source": "https://... (mənbə linki və ya kitab)",
    "difficulty": "medium",
    "provenance": "manual",
    "verified_by": "pending",
    "notes": "",
}


def _print_report(report: ValidationReport, show_warnings: bool = True) -> None:
    for issue in report.issues:
        if issue.severity == "warning" and not show_warnings:
            continue
        print(issue)
    print(report.summary())


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_dataset(load_jsonl(args.path))
    _print_report(report, show_warnings=not args.quiet)
    return 0 if report.ok else 1


def _cmd_build(args: argparse.Namespace) -> int:
    accepted, report = build_dataset(
        args.raw_dir, args.out, require_human=not args.allow_unverified
    )
    _print_report(report, show_warnings=not args.quiet)

    if not report.ok:
        print("\nXətalar var — dataset YAZILMADI.", file=sys.stderr)
        return 1

    print(f"\n{len(accepted)} sətir yazıldı -> {args.out}")
    for key, value in dataset_stats(accepted).items():
        print(f"  {key}: {value}")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    records = [r for _, r in load_jsonl(args.path) if isinstance(r, dict)]
    for key, value in dataset_stats(records).items():
        print(f"{key}: {value}")
    return 0


def equivalence_aliases(answer_az: str, answer_en: str) -> list[str]:
    """AZ və EN etalonlarını informasiya baxımından bərabərləşdirir.

    Wikidata etiket konvensiyaları iki dildə fərqlidir və bu, ölçməni ƏYİR:

        AZ "fransız dili"    vs  EN "French"
        AZ "Meksika pesosu"  vs  EN "peso"
        AZ "Yapon yeni"      vs  EN "yen"

    AZ tərəfdə model iki söz deməlidir, EN tərəfdə bir söz kifayətdir. "fransız"
    cavabı FAKTİKİ OLARAQ DOĞRUDUR, amma exact match-də sıfır alır — halbuki
    ingilis ekvivalenti "French" bal alır. Nəticədə ölçülən AZ/EN fərqinin bir
    hissəsi dildən yox, etiket konvensiyasından gəlir.

    Düzəliş: AZ etalonu EN-dən uzundursa, onun ayrı-ayrı sözləri də qəbul edilən
    forma sayılır. Hansı sözün EN etalona uyğun gəldiyini semantikasız müəyyən
    etmək mümkün olmadığı üçün hər ikisi verilir — artıq generasiya bu layihədə
    şüurlu prinsipdir (bax `morphology`).

    Bu, yalnız `answer_en` sahəsi doldurulmuş sətirlərə tətbiq olunur və token
    F1-ə təsir etmir (o, onsuz da qismən bal verir).
    """
    az_words = answer_az.split()
    en_words = answer_en.split()
    if len(az_words) < 2 or len(az_words) <= len(en_words):
        return []
    return az_words


def fill_aliases(
    records: Sequence[dict[str, Any]], overwrite: bool = False
) -> tuple[list[dict[str, Any]], int]:
    """`answer_aliases` sahəsini `src.morphology` ilə avtomatik doldurur.

    Mövcud aliaslara toxunulmur (əl ilə əlavə edilmiş forma itməsin), yalnız
    boş sahələr doldurulur. `overwrite=True` hamısını yenidən qurur.
    """
    filled = 0
    updated: list[dict[str, Any]] = []
    for record in records:
        record = dict(record)
        answer = record.get("answer")
        if isinstance(answer, str) and answer.strip():
            existing = record.get("answer_aliases") or []
            if overwrite or not existing:
                generated = aliases_for(answer)
                equivalent = equivalence_aliases(answer, str(record.get("answer_en", "")))
                # Bərabərləşdirmə formalarının özləri də hallanır: model
                # "fransız dili" yerinə "fransız dilində" deyə bilər.
                for form in list(equivalent):
                    equivalent.extend(aliases_for(form))
                merged = list(dict.fromkeys([*existing, *generated, *equivalent]))
                if merged != existing:
                    record["answer_aliases"] = merged
                    filled += 1
        updated.append(record)
    return updated, filled


#: Əl ilə sual yazarkən doldurulması TƏLƏB OLUNAN sahələr. Qalanları
#: `prepare` əmri avtomatik hesablayır — ona görə əl işi altı sahə ilə bitir.
MANUAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "question_az",
    "question_en",
    "answer",
    "answer_en",
    "category",
    "source",
)


def prepare_manual(
    records: Sequence[dict[str, Any]], start_id: int = 1
) -> tuple[list[dict[str, Any]], list[str]]:
    """Əl ilə yazılmış sətirləri tam sxemə tamamlayır.

    Avtomatik doldurulan sahələr:
      `id`             ardıcıl nömrələmə
      `answer_aliases` morfoloji generasiya (`src.morphology`)
      `provenance`     "manual"
      `verified_by`    "human" — sualı müəllif özü yazıb, yəni onsuz da yoxlanılıb
      `difficulty`     verilməyibsə "medium"
      `notes`          verilməyibsə boş

    Qaytarır: (tamamlanmış sətirlər, problem mesajları). Problem varsa sətir
    yenə də qaytarılır ki, istifadəçi hamısını bir dəfəyə görüb düzəltsin.
    """
    prepared: list[dict[str, Any]] = []
    problems: list[str] = []

    for offset, raw in enumerate(records):
        row = dict(raw)
        position = offset + 1

        missing = [f for f in MANUAL_REQUIRED_FIELDS if _is_blank(row.get(f))]
        if missing:
            problems.append(f"sətir {position}: doldurulmamış sahə {missing}")

        category = row.get("category")
        if isinstance(category, str) and category.strip() and category not in CATEGORIES:
            problems.append(
                f"sətir {position}: `{category}` kateqoriya deyil; "
                f"mümkün: {sorted(CATEGORIES)}"
            )

        row["id"] = f"az-{start_id + offset:03d}"
        row.setdefault("difficulty", "medium")
        row.setdefault("notes", "")
        row["provenance"] = "manual"
        row["verified_by"] = "human"

        answer = row.get("answer")
        if isinstance(answer, str) and answer.strip():
            existing = row.get("answer_aliases") or []
            generated = aliases_for(answer)
            equivalent = equivalence_aliases(answer, str(row.get("answer_en", "")))
            for form in list(equivalent):
                equivalent.extend(aliases_for(form))
            row["answer_aliases"] = list(
                dict.fromkeys([*existing, *generated, *equivalent])
            )

        prepared.append(row)

    return prepared, problems


def _cmd_prepare(args: argparse.Namespace) -> int:
    records = [r for _, r in load_jsonl(args.path) if isinstance(r, dict)]
    if not records:
        print(f"Fayl boşdur: {args.path}", file=sys.stderr)
        return 1

    prepared, problems = prepare_manual(records, start_id=args.start_id)
    for problem in problems:
        print(f"  {problem}")

    if problems and not args.force:
        print(f"\n{len(problems)} problem var — fayl YAZILMADI.", file=sys.stderr)
        print("Düzəlt və yenidən işlət (və ya --force ilə keç).", file=sys.stderr)
        return 1

    out = args.out or args.path
    write_jsonl(out, prepared)
    print(f"{len(prepared)} sətir tamamlandı -> {out}")
    if prepared:
        sample = prepared[0]
        print(f"  {sample['id']}  {sample['question_az']}")
        print(f"     -> {sample['answer']}  (alias: {len(sample.get('answer_aliases', []))})")
    return 0


def _cmd_aliases(args: argparse.Namespace) -> int:
    records = [r for _, r in load_jsonl(args.path) if isinstance(r, dict)]
    updated, filled = fill_aliases(records, overwrite=args.overwrite)
    write_jsonl(args.path, updated)
    print(f"{filled}/{len(records)} sətrin aliasları dolduruldu -> {args.path}")
    if updated:
        sample = updated[0]
        print(f"  nümunə: {sample.get('answer')} -> {sample.get('answer_aliases')}")
    return 0


def _cmd_template(args: argparse.Namespace) -> int:
    rows = []
    for i in range(1, args.n + 1):
        row = dict(TEMPLATE_ROW)
        row["id"] = f"az-{i:03d}"
        rows.append(row)
    count = write_jsonl(args.out, rows)
    print(f"{count} şablon sətir yazıldı -> {args.out}")
    print("Doldurduqdan sonra `verified_by` sahəsini `human` et.")
    return 0


def _force_utf8_console() -> None:
    """Windows konsolu susmadan cp1252-yə düşür və `ə` hərfində çökür.

    Bu olmadan `validate` əmri Azərbaycan mətnli sətri çap etməyə çalışanda
    UnicodeEncodeError verir — yəni məhz problemli sətri göstərə bilmir.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8_console()

    parser = argparse.ArgumentParser(
        prog="build_dataset", description="AZ-Eval dataset yığma və validasiya"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="bir JSONL faylını yoxla")
    p_validate.add_argument("path", type=Path)
    p_validate.add_argument("-q", "--quiet", action="store_true", help="yalnız xətalar")
    p_validate.set_defaults(func=_cmd_validate)

    p_build = sub.add_parser("build", help="data/raw/*.jsonl -> yekun dataset")
    p_build.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p_build.add_argument("--out", type=Path, default=Path("data/az_eval_v0.jsonl"))
    p_build.add_argument(
        "--allow-unverified",
        action="store_true",
        help="əl yoxlamasından keçməyən sətirləri də daxil et (yalnız sınaq üçün)",
    )
    p_build.add_argument("-q", "--quiet", action="store_true")
    p_build.set_defaults(func=_cmd_build)

    p_stats = sub.add_parser("stats", help="dataset statistikası")
    p_stats.add_argument("path", type=Path)
    p_stats.set_defaults(func=_cmd_stats)

    p_prepare = sub.add_parser(
        "prepare", help="əl ilə yazılmış sətirləri tam sxemə tamamla"
    )
    p_prepare.add_argument("path", type=Path)
    p_prepare.add_argument("--out", type=Path, default=None)
    p_prepare.add_argument("--start-id", type=int, default=1)
    p_prepare.add_argument("--force", action="store_true", help="problemlərə baxmayaraq yaz")
    p_prepare.set_defaults(func=_cmd_prepare)

    p_aliases = sub.add_parser("aliases", help="answer_aliases sahəsini avtomatik doldur")
    p_aliases.add_argument("path", type=Path)
    p_aliases.add_argument(
        "--overwrite", action="store_true", help="mövcud aliasları da yenidən qur"
    )
    p_aliases.set_defaults(func=_cmd_aliases)

    p_template = sub.add_parser("template", help="boş şablon sətirlər yarat")
    p_template.add_argument("--out", type=Path, required=True)
    p_template.add_argument("-n", type=int, default=5)
    p_template.set_defaults(func=_cmd_template)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
