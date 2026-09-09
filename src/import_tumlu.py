"""TUMLU-nun azərbaycan hissəsini audit edir və qısa cavab formatına çevirir.

    python -m src.import_tumlu --audit
    python -m src.import_tumlu --convert

MƏNBƏ. TUMLU-mini (Isbarov et al., ACL 2025), CC BY 4.0. Səkkiz türk dilində
universitet qəbul imtahanlarından yığılmış, tərcümə olunmamış çoxvariantlı
suallar. Azərbaycan hissəsi 735 sualdır, yeddi fənn üzrə bərabər bölünüb.

NİYƏ `data/tumlu/` ALTINDADIR. `build_dataset build` bütün `data/raw/`
qovluğunu gəzir və orada tapdığı hər sətri əsas sxemə görə yoxlayır. Bu
dəstin sxemi başqadır (`choices`, `answer_letter`, `tumlu-az-N` kimi id),
ona görə namizəd qovluğunda qalsaydı, hər qurma 2605 xəta ilə dayanardı.
Ayrı qovluq texniki tələbdir, zövq məsələsi deyil.

NİYƏ ƏSAS DATASETƏ QOŞULMUR. `build_dataset` hər sətirdən `question_en` və
`answer_en` tələb edir, çünki AZ-Eval-in bütün metodu paralel AZ/EN
müqayisəsidir. TUMLU yalnız azərbaycancadır. İngilis tərəfini qurmaq tərcümə
deməkdir, tərcümə isə README-dəki "no LLM was used to author, translate, or
answer any dataset item" zəmanətini pozar. Ona görə bu dəst AYRICA saxlanılır
və ayrıca suala cavab verir.

HANSI SUALA CAVAB VERİR. Format fərqi tamamilə azərbaycancanın içindədir və
ingilis tərəfi tələb etmir:

    çoxvariantlı:  model B deyir
    qısa cavab:    model cavabı YAZMALIDIR

İkisi arasındakı fərq cavabı Azərbaycan dilində istehsal etməyin qiymətidir.
Bu, AZ-Eval-in əsas tapıntısının davamıdır: Qolda cavabların 91.7%-ini kirillə
yazır, ona görə qısa cavabda 3.3%, transliterasiyadan sonra 10.5% alır.
Çoxvariantlı testdə isə kiril ÜMUMİYYƏTLƏ yazılmır, yəni effekt görünmür.
Dünyadakı bütün türk dili benchmarkları çoxvariantlıdır və məhz buna görə bu
effekti ölçə bilmir.

ÖLÇÜLMÜŞ QÜSURLAR. Mənbə olduğu kimi götürülmür:

  1. Cavab açarı mövqeyə görə əyilib: 735 sualdan 309-u D (42%, gözlənilən
     25%), chi2 = 116.7, p = 4e-25. Həmişə D deyən model heç nə bilmədən 42%
     yığır. Variantlar qarışdırılır və yeni açar yazılır.
  2. Onluq vergül parçalanıb: `['-0,', '5', '-1', '0,']` əslində `-0,5` və
     `0,5` olmalıdır. Azərbaycan dilində onluq ayırıcı vergüldür və toplayan
     skript variantları ondan bölüb.
  3. Səhv açar: əl ilə yoxlanmış 14 riyaziyyat sualından birində açar səhv idi
     ("6 və 8 tərəfli düzbucaqlının diaqonalı" -> açar 5, doğru cavab 10).
     Məqalənin özü icma mənbəli dillərdə ~10% yararsızlıq etiraf edir.

Qüsurlu sətirlər SİLİNMİR, işarələnir: qəbul faizi datasetin keyfiyyət
göstəricisidir və hesabatda verilməlidir.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

DATASET = "jafarisbarov/TUMLU-mini"
CONFIG = "azerbaijani"
LICENSE = "CC BY 4.0"
CITATION = (
    "Isbarov et al. (2025). TUMLU: A Unified and Native Language Understanding "
    "Benchmark for Turkic Languages. ACL 2025. https://arxiv.org/abs/2502.11020"
)

LETTERS = "ABCD"

#: Onluq vergüldən kəsilmiş qalıq: "0," "-3," və s.
_COMMA_FRAGMENT = re.compile(r"^-?\d+,$")

#: Sual mətnində parçalanmış onluq: "0, 8 m", "22, 4 l".
_BROKEN_DECIMAL = re.compile(r"\d,\s+\d")

#: Qısa cavaba çevrilə bilməyən cavablar. Bunlar variantlara İSTİNAD edir,
#: ona görə variantlar götürüləndə mənasız qalır.
_META_ANSWER = re.compile(
    r"heç ?bir|hamısı|yuxarıda|düzgün cavab|hər ikisi|variant", re.IGNORECASE
)

#: Düstur və ya riyazi ifadə. Çoxvariantlı testdə belə cavab problemsizdir,
#: çünki model sadəcə seçir. Qısa cavabda isə dəqiq ölçülə bilmir: "cərəyan
#: şiddətinin düsturu" sualına model tamamilə doğru olaraq `I=q/t` yaza bilər,
#: açar isə `q=it` göstərir. İkisi eyni fizikadır, sətir kimi fərqlidir.
_FORMULA_ANSWER = re.compile(r"[=√∏∆<>^+]")

#: Vahiddəki kəsr xətti: `km/saat`, `m/san`, `q/l`. Bunlar düstur DEYİL və
#: qısa cavab kimi tamamilə ölçülə bilir. Ayırd etmə əlaməti kəsr xəttinin
#: iki tərəfidir: hərf/hərf vahiddir, rəqəm iştirak edirsə ifadədir
#: (`mgh/2`, `-1/81`).
_UNIT_SLASH = re.compile(r"[A-Za-zƏĞİÖŞÇÜəğıöşçü]/[A-Za-zƏĞİÖŞÇÜəğıöşçü]")

#: Nömrələnmiş variantların siyahısı: "1,2,4". Sual mətnindəki nömrələrə
#: istinad edir, variantlar götürüləndə mənasını itirir.
_ENUM_ANSWER = re.compile(
    # Ərəb rəqəmləri: "1,2,4"
    r"^\s*\d\s*(,\s*\d\s*)+$"
    # Roma rəqəmləri: "I, III, IV", "II,III,IV, V", "Ic. IIa. IIIb". Bunlar
    # sual mətnindəki nömrələnmiş bəndlərə istinad edir və variantlar
    # götürüləndə mənasını itirir.
    r"|^[IVX]+[a-z]?([,.\s]+[IVX]+[a-z]?)+\s*$"
)

#: Sualın ÖZÜ variantlara istinad edir. Bu, cavabın variantlara istinad
#: etməsindən (`_META_ANSWER`) fərqli və daha gizli problemdir: sual düzgün
#: görünür, amma variantlar götürüləndə CAVABSIZ qalır.
#:
#: "Aşağıdakılardan hansı saf maddədir?" -> "Oksigen". Saf maddə minlərlədir,
#: siyahını görməyən adam hansını seçəcəyini bilə bilməz. Çoxvariantlı testdə
#: sual qüsursuzdur, qısa cavabda isə ölçülən şey bilik yox, təxmindir.
#:
#: Qayda QƏSDƏN geniş tutulub. Bəzi sətirlər ("Braziliya ilə sərhəddə
#: yerləşmir?") variantsız da cavablandırıla bilər, amma onları ayırd etmək
#: üçün mətni anlamaq lazımdır. Dəqiqlik həcmdən vacibdir: 34 sətri artıqdan
#: atmaq, cavabsız sualı içəri buraxmaqdan ucuzdur.
_LIST_REFERENCE = re.compile(
    r"aşağıdak|aşağıda (göstər|veril)|yuxarıda|verilmişlərdən|bunlardan|"
    r"hansı sırada|hansı bənddə|hansı bənd|verilmiş\w*dən hansı|"
    # "Biri skalyar kəmiyyətdir:" -> variantlardan birini seçmək deməkdir.
    r"\bbiri(si)?\b|"
    # "Azərbaycan suda bu ölkə ilə həmsərhəd deyil:" -> "bu" variantı göstərir.
    r"\bbu (ölkə|şəhər|dövlət|maddə|element|bənd|söz)\b|"
    # Sual İNKARLA bitirsə, "hansı X deyil" tipidir: siyahı olmadan cavab
    # sonsuzdur. "Aromatik karbohidrogen deyil" -> "Metil" doğrudur, amma
    # aromatik olmayan karbohidrogen minlərlədir.
    r"(deyil|olmayan|olmayanı|yoxdur)\s*[:?.]?\s*$",
    re.IGNORECASE,
)

#: Rəqəmə yapışmış vahid: "0.25kN". Model demək olar həmişə boşluqla yazır
#: ("0.25 kN"), normalizasiya isə boşluq ƏLAVƏ ETMİR, yalnız təkrarlananı
#: yığır. Sətir belə uyğun gəlmir, ona görə boşluqlu forma alias kimi verilir.
_GLUED_UNIT = re.compile(r"(\d)([A-Za-zƏĞİÖŞÇÜəğıöşçü]{1,6})")


@dataclass
class Issue:
    """Bir sətirdə tapılan qüsur."""

    code: str
    detail: str


@dataclass
class Item:
    """TUMLU sətri və onun haqqında bildiyimiz hər şey."""

    index: int
    question: str
    choices: list[str]
    answer_letter: str
    subject: str
    split: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def answer_text(self) -> str:
        return self.choices[LETTERS.index(self.answer_letter)].strip()

    @property
    def usable(self) -> bool:
        return not self.issues


def fetch(cache: Path, force: bool = False) -> list[dict[str, Any]]:
    """TUMLU-az sətirlərini gətirir və yerli faylda saxlayır.

    Şəbəkə hər qaçışda gəzilmir: audit və çevirmə eyni məzmun üzərində
    işləməlidir, yoxsa hesabatdakı rəqəm çıxarılan fayla uyğun gəlməz.
    """
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))

    rows: list[dict[str, Any]] = []
    for split in ("test", "dev"):
        offset = 0
        while True:
            url = (
                "https://datasets-server.huggingface.co/rows"
                f"?dataset={DATASET}&config={CONFIG}&split={split}"
                f"&offset={offset}&length=100"
            )
            request = urllib.request.Request(url, headers={"User-Agent": "AZ-Eval/2.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
            batch = [entry["row"] for entry in payload["rows"]]
            if not batch:
                break
            for row in batch:
                row["_split"] = split
            rows.extend(batch)
            offset += len(batch)
            if offset >= payload["num_rows_total"]:
                break
            time.sleep(0.3)

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows


def inspect(rows: Sequence[dict[str, Any]]) -> list[Item]:
    """Hər sətri yoxlayır və tapılan qüsurları ona yapışdırır."""
    items: list[Item] = []
    for index, row in enumerate(rows):
        choices = [str(c).strip() for c in row["choices"]]
        item = Item(
            index=index,
            question=str(row["question"]).strip(),
            choices=choices,
            answer_letter=str(row["answer"]).strip(),
            subject=str(row["subject"]).strip(),
            split=str(row.get("_split", "test")),
        )

        if item.answer_letter not in LETTERS:
            item.issues.append(Issue("bad_key", f"açar `{item.answer_letter}`"))
        if len(choices) != 4:
            item.issues.append(Issue("choice_count", f"{len(choices)} variant"))
        if any(not c for c in choices):
            item.issues.append(Issue("empty_choice", "boş variant"))
        if len(set(choices)) < len(choices):
            item.issues.append(Issue("duplicate_choice", "təkrarlanan variant"))
        if any(_COMMA_FRAGMENT.match(c) for c in choices):
            item.issues.append(Issue("comma_split", f"{choices}"))
        if _BROKEN_DECIMAL.search(item.question):
            item.issues.append(Issue("broken_decimal", item.question[:60]))
        if _LIST_REFERENCE.search(item.question):
            item.issues.append(Issue("list_reference", item.question[:60]))
        if len(item.question) < 25:
            item.issues.append(Issue("too_short", item.question))

        if not item.issues:
            answer = item.answer_text
            # Cavab sualın içində görünürsə, model faktı bilmədən onu KÖÇÜRƏ
            # bilər. "Taxta maddə yoxsa cisimdir?" -> "Maddə" belə sətirdir:
            # ölçülən şey bilik yox, sualdan söz seçməkdir.
            if len(answer) > 2 and answer.casefold() in item.question.casefold():
                item.issues.append(Issue("answer_in_question", answer))
            if _META_ANSWER.search(answer):
                item.issues.append(Issue("meta_answer", answer))
            elif len(answer.split()) > 6:
                item.issues.append(Issue("long_answer", answer))
            elif _ENUM_ANSWER.match(answer):
                item.issues.append(Issue("enum_answer", answer))
            elif _FORMULA_ANSWER.search(answer) or (
                "/" in answer and not _UNIT_SLASH.search(answer)
            ):
                item.issues.append(Issue("formula_answer", answer))

        items.append(item)

    # Təkrarlanan sual İKİNCİ dəfə görünəndə işarələnir. Eyni fakt iki dəfə
    # ölçülsə, o fakt cədvəldə ikiqat çəki alır və nəticə ona sürüşür.
    seen: set[str] = set()
    for item in items:
        key = item.question.strip().casefold()
        if key in seen:
            item.issues.append(Issue("duplicate_question", item.question[:60]))
        seen.add(key)
    return items


def audit_report(items: Sequence[Item]) -> str:
    """Qüsurların hesabatı, fənn və növ üzrə."""
    lines = [
        "# TUMLU-az auditi",
        "",
        f"Mənbə: `{DATASET}` / `{CONFIG}`, lisenziya {LICENSE}.",
        f"Sətir: {len(items)}",
        "",
        "## Cavab açarının mövqeyi",
        "",
    ]

    keys = Counter(i.answer_letter for i in items)
    expected = len(items) / 4
    lines += ["| Variant | Say | Gözlənilən | Fərq |", "|---|---|---|---|"]
    for letter in LETTERS:
        count = keys.get(letter, 0)
        lines.append(
            f"| {letter} | {count} | {expected:.0f} | {count - expected:+.0f} |"
        )
    chi2 = sum((keys.get(l, 0) - expected) ** 2 / expected for l in LETTERS)
    top = keys.most_common(1)[0]
    lines += [
        "",
        f"chi2 = {chi2:.1f} (3 sərbəstlik dərəcəsi). Həmişə `{top[0]}` deyən "
        f"model **{100 * top[1] / len(items):.1f}%** yığır, təsadüfi seçim isə 25.0%.",
        "",
        "## Qüsurlar",
        "",
        "| Kod | Say | İzah |",
        "|---|---|---|",
    ]

    explain = {
        "comma_split": "onluq vergüldən parçalanıb",
        "broken_decimal": "sual mətnində parçalanmış onluq",
        "duplicate_choice": "eyni variant iki dəfə",
        "too_short": "kontekstsiz anlaşılmır",
        "meta_answer": "cavab variantlara istinad edir",
        "long_answer": "qısa cavaba sığmır",
        "empty_choice": "boş variant",
        "choice_count": "dörd variant deyil",
        "bad_key": "açar hərfi tanınmır",
        "enum_answer": "nömrə siyahısı, variantlara istinad edir",
        "formula_answer": "düstur, sətir kimi ölçülə bilmir",
        "list_reference": "sual variantlara istinad edir, variantsız cavabsızdır",
        "answer_in_question": "cavab sualın içindədir",
        "duplicate_question": "eyni sual iki dəfə",
    }
    codes = Counter(issue.code for item in items for issue in item.issues)
    for code, count in codes.most_common():
        lines.append(f"| `{code}` | {count} | {explain.get(code, '')} |")

    flawed = [i for i in items if i.issues]
    lines += [
        "",
        f"Ən azı bir qüsuru olan sətir: **{len(flawed)}** "
        f"({100 * len(flawed) / len(items):.1f}%).",
        "",
        "## Fənn üzrə",
        "",
        "| Fənn | Sətir | Qüsurlu | Pay |",
        "|---|---|---|---|",
    ]
    for subject in sorted({i.subject for i in items}):
        group = [i for i in items if i.subject == subject]
        bad = [i for i in group if i.issues]
        lines.append(
            f"| {subject} | {len(group)} | {len(bad)} | {100 * len(bad) / len(group):.0f}% |"
        )

    lines += [
        "",
        "## Aşkarlana bilməyən qüsur",
        "",
        "Yuxarıdakılar STRUKTUR qüsurlarıdır və proqramla tapılır. Səhv AÇAR",
        "belə tapılmır: sual düzgün görünür, sadəcə işarələnmiş variant yanlışdır.",
        "Əl ilə yoxlanmış 14 riyaziyyat sualından birində belə səhv tapıldı",
        "(`6 sm və 8 sm tərəfli düzbucaqlının diaqonalı` üçün açar 5 göstərir,",
        "doğru cavab isə 10-dur və variantlar arasındadır). TUMLU məqaləsinin",
        "özü icma mənbəli dillərdə təxminən 10% yararsızlıq etiraf edir.",
        "",
        f"Sitat: {CITATION}",
        "",
    ]
    return "\n".join(lines)


def _unit_aliases(answer: str) -> list[str]:
    """Rəqəmə yapışmış vahid üçün boşluqlu forma.

    "0.25kN" cavabına model demək olar həmişə "0.25 kN" yazır. Normalizasiya
    boşluğu YIĞIR, amma ƏLAVƏ ETMİR, ona görə bu fərq olduğu kimi qalsa,
    doğru cavab səhv sayılardı.
    """
    spaced = _GLUED_UNIT.sub(r"\1 \2", answer)
    return [spaced] if spaced != answer else []


def to_short_answer(
    items: Sequence[Item], start_id: int, seed: int = 0
) -> list[dict[str, Any]]:
    """Qüsursuz sətirləri qısa cavab namizədinə çevirir.

    Variantlar SAXLANILIR (`choices` sahəsində), çünki eyni faktı iki formatda
    soruşmaq bu işin bütün məqsədidir. Amma qarışdırılmış sıra ilə saxlanılır
    və yeni açar yazılır, yoxsa mövqe əyilməsi bizim ölçüyə də keçər.

    `question_en` və `answer_en` YOXDUR və qəsdən yoxdur: onları qurmaq tərcümə
    deməkdir. Bu fayl `build_dataset`-ə verilmir, ayrı dəstdir.
    """
    rng = random.Random(seed)
    out: list[dict[str, Any]] = []
    for offset, item in enumerate(i for i in items if i.usable):
        answer = item.answer_text
        distractors = [c for c in item.choices if c != answer]
        rng.shuffle(distractors)
        # Doğru cavab növbə ilə A, B, C, D mövqelərinə düşür. Sadəcə
        # qarışdırmaq balansı ZƏMANƏT ETMİR: qüsurlu sətirlər çıxarıldıqdan
        # sonra paylanma yenidən sürüşür və mənbədəki əyilməni tam
        # təmizləmiş olmuruq.
        position = offset % 4
        shuffled = distractors[:position] + [answer] + distractors[position:]
        out.append(
            {
                "id": f"tumlu-az-{start_id + offset}",
                "question_az": item.question,
                "answer": answer,
                "answer_aliases": _unit_aliases(answer),
                "choices": shuffled,
                "answer_letter": LETTERS[shuffled.index(answer)],
                "subject": item.subject,
                "split": item.split,
                "source": f"{DATASET} ({CONFIG}), {LICENSE}",
                "citation": CITATION,
                "provenance": "tumlu-import",
                "verified_by": "pending",
            }
        )
    return out


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="import_tumlu")
    parser.add_argument("--cache", type=Path, default=Path("data/tumlu/tumlu_az_source.json"))
    parser.add_argument("--out", type=Path, default=Path("data/tumlu/tumlu_az_short.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("data/tumlu/TUMLU_AUDIT.md"))
    parser.add_argument("--refresh", action="store_true", help="şəbəkədən yenidən çək")
    parser.add_argument("--convert", action="store_true", help="namizəd faylını yaz")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    rows = fetch(args.cache, force=args.refresh)
    items = inspect(rows)
    usable = [i for i in items if i.usable]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(audit_report(items), encoding="utf-8")
    print(f"{len(items)} sətir, {len(usable)} qüsursuz -> {args.report}")

    if args.convert:
        if args.out.exists():
            raise SystemExit(
                f"{args.out} artıq var. Əl yoxlamasından keçmiş faylın üstündən "
                "yazmaq olmaz; başqa ad ver və ya faylı özün sil."
            )
        candidates = to_short_answer(usable, start_id=1, seed=args.seed)
        with args.out.open("w", encoding="utf-8") as handle:
            for row in candidates:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        keys = Counter(row["answer_letter"] for row in candidates)
        print(f"{len(candidates)} namizəd -> {args.out}")
        print(f"  qarışdırmadan sonra açar: {dict(sorted(keys.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
