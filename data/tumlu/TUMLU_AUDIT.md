# TUMLU-az auditi

Mənbə: `jafarisbarov/TUMLU-mini` / `azerbaijani`, lisenziya CC BY 4.0.
Sətir: 735

## Cavab açarının mövqeyi

| Variant | Say | Gözlənilən | Fərq |
|---|---|---|---|
| A | 124 | 184 | -60 |
| B | 155 | 184 | -29 |
| C | 147 | 184 | -37 |
| D | 309 | 184 | +125 |

chi2 = 116.7 (3 sərbəstlik dərəcəsi). Həmişə `D` deyən model **42.0%** yığır, təsadüfi seçim isə 25.0%.

## Qüsurlar

| Kod | Say | İzah |
|---|---|---|
| `list_reference` | 97 | sual variantlara istinad edir, variantsız cavabsızdır |
| `too_short` | 48 | kontekstsiz anlaşılmır |
| `formula_answer` | 26 | düstur, sətir kimi ölçülə bilmir |
| `long_answer` | 12 | qısa cavaba sığmır |
| `comma_split` | 12 | onluq vergüldən parçalanıb |
| `broken_decimal` | 11 | sual mətnində parçalanmış onluq |
| `enum_answer` | 8 | nömrə siyahısı, variantlara istinad edir |
| `duplicate_choice` | 8 | eyni variant iki dəfə |
| `answer_in_question` | 4 | cavab sualın içindədir |
| `meta_answer` | 3 | cavab variantlara istinad edir |
| `duplicate_question` | 3 | eyni sual iki dəfə |

Ən azı bir qüsuru olan sətir: **214** (29.1%).

## Fənn üzrə

| Fənn | Sətir | Qüsurlu | Pay |
|---|---|---|---|
| Biology | 105 | 30 | 29% |
| Chemistry | 105 | 21 | 20% |
| Geography | 105 | 24 | 23% |
| History | 105 | 19 | 18% |
| Maths | 105 | 36 | 34% |
| Native L&L | 105 | 48 | 46% |
| Physics | 105 | 36 | 34% |

## Aşkarlana bilməyən qüsur

Yuxarıdakılar STRUKTUR qüsurlarıdır və proqramla tapılır. Səhv AÇAR
belə tapılmır: sual düzgün görünür, sadəcə işarələnmiş variant yanlışdır.
Əl ilə yoxlanmış 14 riyaziyyat sualından birində belə səhv tapıldı
(`6 sm və 8 sm tərəfli düzbucaqlının diaqonalı` üçün açar 5 göstərir,
doğru cavab isə 10-dur və variantlar arasındadır). TUMLU məqaləsinin
özü icma mənbəli dillərdə təxminən 10% yararsızlıq etiraf edir.

Sitat: Isbarov et al. (2025). TUMLU: A Unified and Native Language Understanding Benchmark for Turkic Languages. ACL 2025. https://arxiv.org/abs/2502.11020
