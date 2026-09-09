# AZ-Eval

[![tests](https://github.com/nihatgaribli/AZ-Eval/actions/workflows/tests.yml/badge.svg)](https://github.com/nihatgaribli/AZ-Eval/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Kod lisenziyası: MIT](https://img.shields.io/badge/kod%20lisenziyas%C4%B1-MIT-green.svg)](LICENSE)
[![Data lisenziyası: CC BY 4.0](https://img.shields.io/badge/data%20lisenziyas%C4%B1-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)

Azərbaycan dili üçün açıq LLM qiymətləndirmə dəsti. İngiliscə sənədləşdirmə və tam nəticələr: [README.md](README.md).

**Status:** bütün boru xətti hazırdır və test olunub — yığım, əl yoxlaması,
metriklər, model qaçışları, təhlil. Qalan iş datasetin əl ilə təsdiqidir.

## Quraşdırma

```bash
pip install -r requirements.txt
python -m pytest          # 517 test
```

Model qaçışları üçün əlavə: `pip install torch transformers` (yalnız
`--backend transformers` istifadə edəndə lazımdır).

## Dataset iş axını

```
Wikidata  --[harvest]-->  data/raw/*.jsonl  --[review: əl ilə]-->  verified_by=human
                                 |                                        |
                                 +--[validate]--> xəta / xəbərdarlıq       |
                                                                          v
                                                          [build] --> data/az_eval_v0.jsonl
```

```bash
# 1. Avtomatik qaralama yığımı (paralel AZ/EN, ~2 dəqiqə)
python -m src.harvest_wikidata --per-template 12 --max-per-answer 2

# 2. Əl yoxlaması — brauzerdə açılır, klaviatura: A təsdiq / R rədd / S atla
python -m src.review data/raw/wikidata.jsonl

# 3. Yekun dataset (yalnız verified_by=human keçir)
python -m src.build_dataset build
python -m src.build_dataset stats data/az_eval_v0.jsonl
```

Əlavə əmrlər:

```bash
python -m src.build_dataset template --out data/raw/manual.jsonl -n 20  # əl ilə yazmaq üçün
python -m src.build_dataset validate data/raw/manual.jsonl              # sxem + keyfiyyət
python -m src.build_dataset aliases  data/raw/manual.jsonl              # alias avtodoldurma
```

`verified_by` sahəsi məlumat deyil, **qapı**dır: `build` əmri `human` olmayan sətri
yekun datasetə buraxmır. Rədd edilən sətirlər silinmir — qəbul faizi datasetin
keyfiyyət göstəricisidir və məqalədə verilir.

Validator xəta (dataset yazılmır) və xəbərdarlıq (yazılır, amma göstərilir) ayırır.

## Avtomatlaşdırma — nə avtomatikdir, nə yox

**Avtomatik:** fakt yığımı, AZ/EN paralelliyi, alias generasiyası, keyfiyyət triajı.
**Əl ilə:** hər sətrin təsdiqi. Bu, avtomatlaşdırıla bilməz — avtomatlaşdırılsa,
dataset maşın məhsuluna çevrilir və işin elmi dəyəri itir. Alət yoxlamanı əvəz
etmir, sürətləndirir (~5 dəq → ~15 san).

### Niyə Wikidata

Faktlar üçlük kimi saxlanılır və etiketlər **həm AZ, həm EN** dilində mövcuddur.
Yəni AZ/EN cütü tərcümə ilə deyil, konstruksiya ilə alınır — RQ1-in müqayisəsi
tərcümə keyfiyyətindən asılı olmur. Bu, maşın tərcüməsindən keyfiyyətcə fərqli mövqedir.

### Filtrlər və nəyə qarşı olduqları

| Filtr | Tələ |
|---|---|
| `--max-per-answer` | **Cavab skew-i.** "Azərbaycanlı şəxs → doğum yeri" sorğusunda cavabların əksəriyyəti "Bakı" çıxır; kvotasız datasetdə heç nə bilməyən model 60-70% alır |
| təkdəyərlilik | Wikidata əhali kimi xassələri illər üzrə saxlayır — bir şəhər üçün 5 rəqəm, birmənalı etalon yoxdur |
| bloklanmış cavablar | "doğum yeri: SSRİ" faktiki doğrudur, amma xəta taksonomiyasını çirkləndirir |
| cavab sualın içində | "Astara rayonunun mərkəzi?" → "Astara" — cavabı sualdan köçürmək kifayətdir, bilik ölçülmür |
| EN etiketi ingilis deyil | Wikidata-da ingilis etiketi tez-tez yerli adın kopyasıdır ("Diana Hacıyeva"); ingilis şərti azərbaycanca mətnlə çirklənsə, RQ1 iki dilin müqayisəsi olmaqdan çıxır |
| tanınırlıq həddi, cavab uzunluğu, mötərizəli etiketlər, cavab≠subyekt | — |

Hər `build` və `harvest` sonunda **`majority_baseline`** göstərilir: "həmişə ən çox
rast gəlinən cavabı de" strategiyasının balı. 15%-i keçirsə, kvota sərtləşdirilməlidir.
Cari yığımda: **1.1%** (n=356).

### Sual quruluşlarının müxtəlifliyi

Hər şablonun **4 fərqli sual quruluşu** var — 8 şablon × 4 variant = **32 sintaktik qəlib**.
Variantlar sətirlərə növbə ilə paylanır, ona görə hər qəlib tanınırlıq spektrinin
hər yerindən subyekt alır (variantla çətinlik arasında süni korrelyasiya yaranmır).

```text
v0  Fransanın paytaxtı hansı şəhərdir?        What is the capital city of France?
v1  Hansı şəhər Fransanın paytaxtıdır?        Which city is the capital of France?
v2  Fransanın paytaxtının adı nədir?          What is the name of the capital of France?
v3  Fransanın paytaxtını yaz.                 Name the capital city of France.
```

Səbəb: bütün suallar bir qəlibdə olsa, benchmark modelin **biliyini** yox, həmin
bir qəlibə **tanışlığını** ölçər — bu, hakimin verəcəyi ilk suallardandır.

İki tələb:

1. **AZ[i] ilə EN[i] eyni quruluşda olmalıdır.** Əks halda AZ tərəf çətin, EN tərəf
   asan qəlibə düşür və ölçülən fərqin bir hissəsi dildən yox, sual quruluşundan gəlir.
2. **İşlənən variant `notes` sahəsinə yazılır** (`template=...;variant=2`) — xəta
   təhlilində "sual quruluşu nəticəyə təsir edirmi?" sualına cavab vermək üçün.

Variantlar həm hal şəkilçisini dəyişdirir (adlıq / yiyəlik / yerlik), həm də sual
tipini (wh-sual, tərsinə çevrilmiş wh-sual, əmr formalı tapşırıq) — yəni müxtəliflik
təkcə söz seçimində deyil, morfologiya və sintaksis səviyyəsindədir.

### Cavabın dili

Şablonların bir hissəsi **qəsdən** cavabı azərbaycanca söz olan faktları hədəfləyir
(`person_occupation` → "müğənni", "cüdoçu"; `country_official_language` → "fransız dili").

Səbəb: paytaxt, kimyəvi simvol və il şablonlarının cavabları beynəlxalq yazılışlardır
(`Paris`, `Au`, `1961`) və Azərbaycan diakritiki daşımır. Yalnız onlarla RQ3-ün
diakritika ölçüsü ölçülə bilmir — MORPH→LENIENT fərqi həmişə sıfır çıxır, çünki
qatlanacaq hərf yoxdur. İki yeni şablon örtüyü **31% → 42%**-ə qaldırdı.

### Metodoloji qaydalar

1. **Qaralama modeli eval siyahısında olmamalıdır.** Sualları Qwen ilə yazıb Qwen-i
   ölçsən, nəticə onun xeyrinə əyilir — bu, hakimin verəcəyi ilk sualdır.
2. **Model nəticəsinə görə sual filtrləmə.** Benchmarkı süni çətinləşdirir.
   Əvəzinə `majority_baseline` ver.
3. **`provenance` sahəsi** hər sətrin mənbəyini saxlayır (`manual` /
   `wikidata-template` / `llm-passage`) — həm brief-in etik tələbi (LLM istifadəsi
   açıq yazılmalıdır), həm də məqalə üçün nəticə kəsimi.

## Model qaçışları

```bash
# AZ və EN eyni sətirlər üzərində — cütləşdirilmiş müqayisə bunu tələb edir
python -m src.run_eval --model Qwen/Qwen3-1.7B --language az
python -m src.run_eval --model Qwen/Qwen3-1.7B --language en

# Az yaddaşlı kartda (8 GB VRAM-da 5B model yalnız belə sığır)
python -m src.run_eval --model issai/Qolda-AVL-5B --language az --load-in-4bit

# Model yükləmədən borunu sınamaq üçün
python -m src.run_eval --model sinaq --language az --backend oracle --allow-oracle
```

`run_eval.py` **metrika hesablamır** — yalnız xam cavabı `results/raw_outputs/`-a
yazır. Metrik düsturu sonra dəyişsə, bütün eksperimenti yenidən işlətmək lazım
gəlməsin deyə (brief 7-ci bölmə).

| Qərar | Səbəb |
|---|---|
| `do_sample=False`, sabit seed | Məqalədəki rəqəm təkrar işlədiləndə eyni çıxmalıdır |
| Davam etdirilə bilən (`id` əsasında) | 500 sətirlik qaçış kəsilsə, iş itmir |
| Prompt sualın dilindədir | İngilis təlimatı + AZ sualı ölçmə şərtini korlayır — modelin bilikləri yox, təlimat izləmə qabiliyyəti ölçülərdi |
| AZ/EN eyni `id` dəsti | `compare_paired` cütləşdirilmiş sətir tələb edir |

## Təhlil

```bash
python -m src.analyze
```

Xam cavabları oxuyur, `results/tables/` altına altı fayl yazır: `main.md`,
`modes.md`, `rq1.md`, `rq2.md`, `breakdown.md` və hər AZ qaçışı üçün `errors__*.csv`.
Modelə müraciət etmir — metrikanı və ya cavab çıxarma qaydasını dəyişib
istənilən qədər təkrar işlətmək olar, bir GPU saatı da yenidən xərclənmir.

**Cavabın xam mətndən çıxarılması** (`extract_answer`) metrikanı birbaşa dəyişir,
ona görə qaydalar açıqdır: yalnız birinci sətir, `Cavab:` / `Answer:` prefiksləri
atılır, dırnaq və sondakı durğu işarəsi təmizlənir, mətn çox uzundursa ilk cümlə
götürülür. Qayda hər iki dilə **eyni** tətbiq olunur.

`errors__*.csv` faylında `error_type` sütunu qəsdən boşdur — RQ3-ün cavabı əl ilə
etiketlənməlidir. Nümunə kateqoriyalar üzrə **təbəqələndirilmişdir**: sadə təsadüfi
seçim ən böyük kateqoriyanı üstün göstərib taksonomiyanı əyərdi.

## Metrik qatı

Hər metrika **üç normalizasiya rejimində** hesablanır və üçü də hesabatda verilir:

| Rejim | Nə edir |
|---|---|
| `STRICT` | kiçik hərf + durğu işarəsi + boşluq |
| `MORPH` | STRICT + hal/mənsubiyyət/cəm şəkilçilərinin kəsilməsi |
| `LENIENT` | MORPH + diakritiklərin qatlanması (ə→e, ğ→g, ...) |

Səbəb: aqlütinativ dildə `EM("Bakıda", "Bakı") = 0`, halbuki model haqlıdır. Bir rejimlə
ölçsək, rəqəm "model nə qədər bilir" yox, "model nə qədər səliqəli yazır" olur.

Rejimlər arası fərq özü nəticədir:

- **STRICT → MORPH** = xətanın morfologiyadan gələn payı
- **MORPH → LENIENT** = xətanın diakritikadan gələn payı

Bu, RQ3-ün (xətalar harada cəmlənir) birbaşa kəmiyyət cavabıdır.

```python
from src.metrics import MODES, score_example, bootstrap_ci, compare_paired, format_ci

scores = [score_example(pred, [gold, *aliases], mode)["em"] for ...]
print(format_ci(bootstrap_ci(scores, n_resamples=1000, seed=0)))   # 62.4% ± 3.1

gap = compare_paired(en_scores, az_scores, seed=0)
print(gap.diff, gap.p_value, gap.significant)
```

- `bootstrap_ci` — persentil bootstrap, sabit `seed` (reproduksiya üçün)
- `compare_paired` — fərqin bootstrap CI-si + işarə dəyişdirmə permutasiya testi.
  0/1 dəyərli EM balları üçün t-test normallıq fərziyyəsi tələb edir, permutasiya testi etmir.
- `format_ci` — interval asimmetrikdirsə tam həddi də göstərir, `±` arxasında gizlətmir.

### Şəkilçi kəsmənin məhdudiyyətləri

`strip_suffixes` morfoloji analizator deyil, lüğətsiz evristikadır. 28 hallanma
cütündən ibarət batareya `tests/test_metrics.py::test_morphology_battery`-də sabitlənib.
Bilinən uğursuzluqlar `test_known_stripping_limitations`-da **açıq təsdiq olunub**,
gizlədilməyib — məqalədə göstərilməlidir:

| Hal | Nəticə | Səbəb |
|---|---|---|
| `Gəncənin` → `Gəncə` | uyğunlaşmır | `n` bağlayıcı samitli variantlar siyahıdan çıxarılıb |
| `avtobusu` → `avtobus` | uyğunlaşmır | `s` ilə bitən kökdə açılma yolu yoxdur |
| `evindən` → `ev` | uyğunlaşmır | üç hərf həddi |

`n` variantlarının çıxarılması şüurlu ticarətdir: saxlanılsaydı, `n` ilə bitən **bütün**
köklər sınırdı (`Naxçıvanın` → `naxçıv`, halbuki etalon `Naxçıvan` toxunulmaz qalırdı) —
yəni normalizasiya doğru cavabı itirirdi. `n`-final köklər AZ-də daha çoxdur.

**Praktik nəticə:** morfoloji evristikadansa datasetdə `answer_aliases` yazmaq daha
etibarlıdır. Evristika yalnız ikinci dərəcəli rəqəm kimi verilir, əsas rəqəm `STRICT`-dir.

## Repo strukturu

```
az-eval/
├── data/raw/                 # qaralamalar (verified_by: pending | llm-draft)
├── data/az_eval_v0.jsonl     # yekun dataset (yalnız human)
├── src/build_dataset.py      # sxem validasiyası + yığma  ✓
├── src/morphology.py         # hallanmış formaların generasiyası  ✓
├── src/harvest_wikidata.py   # avtomatik qaralama yığımı  ✓
├── src/review.py             # sürətli əl yoxlaması (brauzer)  ✓
├── src/metrics.py            # normalizasiya, EM, F1, bootstrap, paired test  ✓
├── src/run_eval.py           # model qaçışları  ✓
├── src/analyze.py            # cədvəllər, xəta taksonomiyası  ✓
├── results/raw_outputs/      # xam model cavabları (MÜTLƏQ saxlanılır)
├── results/tables/
└── tests/                    # 517 test
```

## Qeyd (Windows)

Konsol cp1252-yə düşüb `ə` hərfində çökə bilər. CLI bunu özü həll edir; öz
skriptlərini işlədəndə `PYTHONIOENCODING=utf-8` təyin et.
