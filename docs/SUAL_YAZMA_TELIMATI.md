# Sual yazma təlimatı

Sən **altı sahə** yazırsan. Qalanını `prepare` əmri özü doldurur.

---

## Format

JSONL faylı — hər sətir bir JSON obyekti, sətir sonunda vergül **yoxdur**.

```json
{"question_az": "Möminə Xatun türbəsinin memarı kimdir?", "question_en": "Who is the architect of the Momine Khatun Mausoleum?", "answer": "Əcəmi Naxçıvani", "answer_en": "Ajami Nakhchivani", "category": "history", "source": "https://az.wikipedia.org/wiki/Möminə_Xatun_türbəsi"}
```

## Altı sahə

| Sahə | Nədir |
|---|---|
| `question_az` | Sual, azərbaycanca. Təbii səslənməlidir |
| `question_en` | **Eyni** sual, ingiliscə. Tərcümə yox, ekvivalent |
| `answer` | Cavab, azərbaycanca. **1–3 söz** |
| `answer_en` | Eyni cavab, ingiliscə |
| `category` | `history` · `geography` · `science` · `culture` · `language` |
| `source` | Mənbə linki (Vikipediya, kitab, sayt) |

İstəsən `difficulty` (`easy` / `medium` / `hard`) da yaza bilərsən; yazmasan `medium` olur.

## Mən nə dolduracağam

| Sahə | Necə |
|---|---|
| `id` | ardıcıl nömrə — `az-142`, `az-143`, ... |
| `answer_aliases` | morfoloji generasiya: `Əcəmi Naxçıvanidə`, `Əcəmi Naxçıvanidən`, `Əcəmi Naxçıvanidir` və s. |
| `provenance` | `manual` |
| `verified_by` | `human` — sualı sən yazmısan, yəni onsuz da yoxlanılıb |
| `notes` | boş |

**Alias yazmağa ehtiyac yoxdur.** Model `Əcəmi Naxçıvanidə` desə də bal alacaq.

---

## Beş qayda

**1. Cavab qısa və birmənalı olsun — 1–3 söz.** `Əcəmi Naxçıvani` ✓, `XII əsrdə Naxçıvanda yaşamış görkəmli memar` ✗. Exact match uzun cavabda mənasını itirir.

**2. İngilis sualı ekvivalent olsun, hərfi tərcümə yox.** Ölçmənin bütün mənası ondadır ki, model **eyni faktı** iki dildə bilir, ya yox.

**3. Cavab sualın içində keçməsin.** `Xocalı soyqırımı hansı rayonda baş verib? → Xocalı rayonu` ✗ — cavabı sualdan oxumaq olur.

**4. Fakt sabit olsun.** Vaxtla dəyişən cavab (kim nazirdir, əhali neçədir) problem yaradır.

**5. Kiril yazma.** Nə sualda, nə cavabda. Layihənin əsas tapıntısı əlifba haqqındadır; kiril etalon onu tərsinə çevirər.

---

## Nə yazmaq yaxşıdır

Rədd etdiyin 218 sətrin problemi bu idi: *"az tanınan bir yazıçı harada vəfat edib"* tipli suallar həqiqi bilik yoxlamır. Keçən sətirlərə bax — nümunə odur:

```
Təzəpir məscidi kimin layihəsidir?          -> Yevgeni Skibinski
Möminə Xatun türbəsi kimin layihəsidir?     -> Əcəmi Naxçıvani
Habil Əliyevin ifa etdiyi alət hansıdır?    -> kamança
Ramiz Quliyev hansı alətin ifaçısıdır?      -> tar
Astaraçay hansı su hövzəsinə qovuşur?       -> Xəzər dənizi
```

Ortaq cəhət: **əşya, yer, əsər, hadisə** haqqındadır və cavab **mədəni cəhətdən spesifikdir**.

Faydalı sahələr: memarlıq irsi, muğam və milli musiqi, ədəbiyyat və əsərlər, tarixi hadisələr və dövlətlər, coğrafiya, dil və əlifba tarixi, milli mətbəx, xalq sənəti.

---

## Bitirəndə

```bash
python -m src.build_dataset prepare data/raw/menim_suallarim.jsonl --start-id 142
python -m src.build_dataset validate data/raw/menim_suallarim.jsonl
python -m src.build_dataset build
```

`prepare` problem tapsa **faylı yazmır** və nəyin səhv olduğunu sətir-sətir göstərir.

`--start-id 142` vacibdir — mövcud dataset `az-141`-də bitir, ID toqquşmasın.

---

## Neçə sual lazımdır

Hazırda **105** təsdiqlənmiş sətir var. Statistik güc hesabı göstərir:

| Cəmi | Əsas müqayisənin həll olunma ehtimalı |
|---|---|
| 105 | ~38% |
| 200 | 66% |
| **300** | **88%** |

Yəni **~200 yeni sual** hədəfdir. Amma 50 yaxşı sual 200 zəif sualdan dəyərlidir — sən özün yazdığın üçün keyfiyyət onsuz da yüksək olacaq.

Hissə-hissə göndər, mən hər dəfə əlavə edim.
