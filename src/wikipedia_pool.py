"""Sual obyektlərinin seçilməsi — az.wikipedia-nın öz kurasiyasına söykənir.

NİYƏ AYRICA MODUL

İlk yığımda obyektlər `sitelinks >= 8` həddi ilə seçilirdi. Bu, texniki cəhətdən
işləyirdi, amma seçimi BEYNƏLXALQ populyarlıq idarə edirdi: nəticədə Fransanın
paytaxtı və kimyəvi simvollar gəlirdi, Azərbaycan məzmunu isə demək olar yox idi.
"AZ-Eval" adlı dəst üçün bu, məzmun problemidir.

Bu modul seçimi Azərbaycan Vikipediyasının öz redaktorlarına həvalə edir. İki qat:

  1. KEYFİYYƏT QATI — "Seçilmiş" və ya "Yaxşı" məqalə statusu almış Azərbaycan
     mövzulu məqalələr. Bu status formal qiymətləndirmə prosesindən keçir, yəni
     bir redaktorun şəxsi seçimi deyil.

  2. MÖVZU QATI — Azərbaycan mövzu kateqoriyalarındakı məqalələr, həcmə görə
     süzülmüş. Qısa qaralamalar (stub) atılır; uzun məqalə mövzunun işlənmiş
     olduğunu göstərir.

Hər iki meyar sənədləşdirilə biləndir və məqalədə bir cümlə ilə əsaslandırıla
bilər — `sitelinks >= 8` haqqında bunu demək mümkün deyildi.

Nəticə `data/raw/entity_pool.json` faylına keşlənir; təkrar çağırışlar API-yə
yenidən müraciət etmir.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "WIKI_HOST",
    "AZ_TOPIC_CATEGORIES",
    "EntityPool",
    "quality_article_titles",
    "category_article_titles",
    "titles_to_qids",
    "build_pool",
    "load_pool",
]

WIKI_HOST = "az.wikipedia.org"

USER_AGENT = (
    "az-eval/0.1 (Azerbaijani LLM evaluation benchmark; academic research) "
    "python-urllib"
)

#: Qiymətləndirmə kateqoriyaları müzakirə səhifələrinə (ns=1) qoyulur, məqalənin
#: özünə yox. Ona görə üzvlərdən məqalə adı çıxarılmalıdır.
QUALITY_CATEGORY_PATTERNS = (
    "Seçilmiş məqalə statuslu {topic} məqalələri",
    "Yaxşı məqalə statuslu {topic} məqalələri",
)

QUALITY_TOPICS = ("Azərbaycan tarixi", "Azərbaycan mədəniyyəti")

#: İkinci qat üçün mövzu kateqoriyaları. Alt-kateqoriyalara enilmir — enildikdə
#: siyahı sürətlə mövzudan uzaqlaşır.
AZ_TOPIC_CATEGORIES = (
    "Azərbaycan tarixi",
    "Azərbaycan yazıçıları",
    "Azərbaycan şairləri",
    "Azərbaycan xanlıqları",
    "Azərbaycan bəstəkarları",
    "Azərbaycan rəssamları",
)

#: Stub həddi. Bundan qısa məqalə mövzunun işlənmədiyini göstərir və oradan
#: çıxarılan fakt çox vaxt yoxlanılmamış olur.
MIN_ARTICLE_BYTES = 8000

DEFAULT_CACHE = Path("data/raw/entity_pool.json")


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------


#: Sorğular arası minimal fasilə. Wikimedia anonim müraciətlərdə sürət həddi
#: tətbiq edir və hədd aşılanda HTTP 429 qaytarır. Yığım bir dəfəlik işdir,
#: ona görə ehtiyatlı sürət seçilib.
REQUEST_DELAY = 1.0

#: 429 üçün geri çəkilmə pilləsi (saniyə). Adi şəbəkə xətasından fərqli olaraq
#: sürət həddi qısa gözləmə ilə keçmir.
RATE_LIMIT_BACKOFF = (10, 30, 60, 120)


def _api(params: dict[str, str], retries: int = 5, timeout: int = 60) -> dict[str, Any]:
    """MediaWiki API sorğusu, sürət həddinə uyğunlaşan geri çəkilmə ilə."""
    query = urllib.parse.urlencode({**params, "format": "json"})
    url = f"https://{WIKI_HOST}/w/api.php?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.load(response)
            time.sleep(REQUEST_DELAY)
            return result
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429 and attempt < retries - 1:
                wait = RATE_LIMIT_BACKOFF[min(attempt, len(RATE_LIMIT_BACKOFF) - 1)]
                print(f"    sürət həddi; {wait}s gözlənilir...", flush=True)
                time.sleep(wait)
                continue
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as exc:  # şəbəkə xətaları müxtəlif tiplidir
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"az.wikipedia API sorğusu uğursuz: {last}")


def _category_members(category: str, namespace: int) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    continue_token: str | None = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Kateqoriya:{category}",
            "cmlimit": "500",
            "cmnamespace": str(namespace),
        }
        if continue_token:
            params["cmcontinue"] = continue_token
        data = _api(params)
        members += data.get("query", {}).get("categorymembers", [])
        continue_token = data.get("continue", {}).get("cmcontinue")
        if not continue_token:
            return members


# --------------------------------------------------------------------------
# Qatlar
# --------------------------------------------------------------------------


def quality_article_titles(topics: Sequence[str] = QUALITY_TOPICS) -> set[str]:
    """"Seçilmiş" və ya "Yaxşı" statusu olan Azərbaycan mövzulu məqalələr.

    Status məqalənin MÜZAKİRƏ səhifəsində saxlanılır (ad fəzası 1), ona görə
    üzvün adından `Müzakirə:` prefiksi kəsilir.
    """
    titles: set[str] = set()
    for topic in topics:
        for pattern in QUALITY_CATEGORY_PATTERNS:
            category = pattern.format(topic=topic)
            try:
                members = _category_members(category, namespace=1)
            except RuntimeError:
                continue
            titles |= {m["title"].split(":", 1)[1] for m in members if ":" in m["title"]}
    return titles


def category_article_titles(
    categories: Sequence[str] = AZ_TOPIC_CATEGORIES,
    min_bytes: int = MIN_ARTICLE_BYTES,
) -> set[str]:
    """Mövzu kateqoriyalarındakı məqalələr, həcmə görə süzülmüş.

    Siyahı məqalələri ("... siyahısı") atılır — onlar mövzu deyil, naviqasiyadır.
    """
    candidates: set[str] = set()
    for category in categories:
        try:
            members = _category_members(category, namespace=0)
        except RuntimeError:
            continue
        candidates |= {
            m["title"] for m in members if not m["title"].endswith("siyahısı")
        }

    return {t for t, size in _article_sizes(candidates).items() if size >= min_bytes}


def _article_sizes(titles: Iterable[str]) -> dict[str, int]:
    ordered = sorted(titles)
    sizes: dict[str, int] = {}
    for start in range(0, len(ordered), 50):
        batch = ordered[start : start + 50]
        data = _api(
            {"action": "query", "prop": "revisions", "rvprop": "size",
             "titles": "|".join(batch)}
        )
        for page in data.get("query", {}).get("pages", {}).values():
            revisions = page.get("revisions")
            if revisions:
                sizes[page["title"]] = revisions[0].get("size", 0)
    return sizes


def titles_to_qids(titles: Iterable[str]) -> dict[str, str]:
    """Məqalə adlarını Wikidata identifikatorlarına çevirir."""
    ordered = sorted(titles)
    mapping: dict[str, str] = {}
    for start in range(0, len(ordered), 40):
        batch = ordered[start : start + 40]
        data = _api(
            {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
             "titles": "|".join(batch)}
        )
        for page in data.get("query", {}).get("pages", {}).values():
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                mapping[page["title"]] = qid
    return mapping


# --------------------------------------------------------------------------
# Hovuz
# --------------------------------------------------------------------------


@dataclass
class EntityPool:
    """Seçilmiş obyektlər və onların hansı qatdan gəldiyi.

    Qat məlumatı saxlanılır ki, hesabatda "keyfiyyət təsdiqli məqalələrdən gələn
    suallarda nəticə fərqlidirmi" sualına cavab verilə bilsin.
    """

    quality: dict[str, str] = field(default_factory=dict)
    topical: dict[str, str] = field(default_factory=dict)

    @property
    def qids(self) -> list[str]:
        """Bütün identifikatorlar, təkrarsız və determinist sırada."""
        return sorted({*self.quality.values(), *self.topical.values()})

    def tier_of(self, qid: str) -> str:
        return "quality" if qid in set(self.quality.values()) else "topical"

    def as_dict(self) -> dict[str, Any]:
        return {"quality": self.quality, "topical": self.topical}


def build_pool(
    cache_path: Path | str = DEFAULT_CACHE,
    refresh: bool = False,
    min_bytes: int = MIN_ARTICLE_BYTES,
) -> EntityPool:
    """Hovuzu qurur; keş varsa oradan oxuyur."""
    cache_path = Path(cache_path)
    if cache_path.exists() and not refresh:
        return load_pool(cache_path)

    quality_titles = quality_article_titles()
    topical_titles = category_article_titles(min_bytes=min_bytes) - quality_titles

    pool = EntityPool(
        quality=titles_to_qids(quality_titles),
        topical=titles_to_qids(topical_titles),
    )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(pool.as_dict(), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return pool


def load_pool(cache_path: Path | str = DEFAULT_CACHE) -> EntityPool:
    data = json.loads(Path(cache_path).read_text(encoding="utf-8"))
    return EntityPool(quality=data.get("quality", {}), topical=data.get("topical", {}))


def main() -> int:
    import sys

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    pool = build_pool(refresh="--refresh" in sys.argv)
    print(f"keyfiyyət qatı : {len(pool.quality):4} məqalə")
    print(f"mövzu qatı     : {len(pool.topical):4} məqalə")
    print(f"cəmi obyekt    : {len(pool.qids):4}")
    print()
    for title in sorted(pool.quality)[:8]:
        print("  [keyfiyyət]", title)
    for title in sorted(pool.topical)[:8]:
        print("  [mövzu]    ", title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
