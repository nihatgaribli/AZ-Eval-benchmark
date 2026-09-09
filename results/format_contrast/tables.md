# Format müqayisəsi: seçmək və yazmaq

Dəst: TUMLU-az, 521 sual. Dekodlama hər iki şəraitdə eynidir.

| Model | Zəncir | MCQ | Qısa cavab | Fərq | 95% CI | p |
|---|---|---|---|---|---|---|
| Qwen/Qwen3-1.7B | strict | 37.0% | 2.9% | +34.2pp | [29.9, 38.6] | 0.0001 |
| Qwen/Qwen3-1.7B | morph | 37.0% | 3.3% | +33.8pp | [29.6, 38.2] | 0.0001 |
| Qwen/Qwen3-1.7B | lenient | 37.0% | 3.3% | +33.8pp | [29.6, 38.2] | 0.0001 |
| Qwen/Qwen3-1.7B | translit | 37.0% | 3.3% | +33.8pp | [29.6, 38.2] | 0.0001 |
| Qwen/Qwen3-VL-4B-Instruct | strict | 44.9% | 7.5% | +37.4pp | [33.0, 42.2] | 0.0001 |
| Qwen/Qwen3-VL-4B-Instruct | morph | 44.9% | 7.5% | +37.4pp | [33.0, 42.2] | 0.0001 |
| Qwen/Qwen3-VL-4B-Instruct | lenient | 44.9% | 7.5% | +37.4pp | [33.0, 42.2] | 0.0001 |
| Qwen/Qwen3-VL-4B-Instruct | translit | 44.9% | 7.5% | +37.4pp | [33.0, 42.2] | 0.0001 |
| Qwen/Qwen3-VL-4B-Thinking | strict | 43.2% | 5.8% | +37.4pp | [33.2, 42.0] | 0.0001 |
| Qwen/Qwen3-VL-4B-Thinking | morph | 43.2% | 6.0% | +37.2pp | [33.0, 41.7] | 0.0001 |
| Qwen/Qwen3-VL-4B-Thinking | lenient | 43.2% | 6.0% | +37.2pp | [33.0, 41.7] | 0.0001 |
| Qwen/Qwen3-VL-4B-Thinking | translit | 43.2% | 6.0% | +37.2pp | [33.0, 41.7] | 0.0001 |
| issai/Qolda-AVL-5B | strict | 39.0% | 0.2% | +38.8pp | [34.5, 42.8] | 0.0001 |
| issai/Qolda-AVL-5B | morph | 39.0% | 0.2% | +38.8pp | [34.5, 42.8] | 0.0001 |
| issai/Qolda-AVL-5B | lenient | 39.0% | 0.2% | +38.8pp | [34.5, 42.8] | 0.0001 |
| issai/Qolda-AVL-5B | translit | 39.0% | 1.3% | +37.6pp | [33.4, 41.7] | 0.0001 |

Təsadüfi seçim MCQ-də 25.0% verir, qısa cavabda isə sıfıra yaxındır.
Ona görə fərqin ÖZÜ tək başına oxunmur; iki modelin fərqləri arasındakı
məsafə oxunur.


## Saxlanma: tanınan biliyin yazıya keçən payı

| Model | Zəncir | MCQ-də düz | Yazıda da düz | 95% CI |
|---|---|---|---|---|
| Qwen/Qwen3-1.7B | strict | 193 | 3.6% | [1.6, 6.7] |
| Qwen/Qwen3-1.7B | translit | 193 | 4.7% | [2.1, 7.8] |
| Qwen/Qwen3-VL-4B-Instruct | strict | 234 | 10.3% | [6.4, 14.1] |
| Qwen/Qwen3-VL-4B-Instruct | translit | 234 | 10.3% | [6.4, 14.1] |
| Qwen/Qwen3-VL-4B-Thinking | strict | 225 | 10.2% | [6.2, 14.2] |
| Qwen/Qwen3-VL-4B-Thinking | translit | 225 | 10.7% | [6.7, 15.1] |
| issai/Qolda-AVL-5B | strict | 203 | 0.5% | [0.0, 1.5] |
| issai/Qolda-AVL-5B | translit | 203 | 3.4% | [1.0, 6.4] |

| Model | Kirillə | Promptu təkrarlayan | MCQ hərfi çıxarılmayan |
|---|---|---|---|
| Qwen/Qwen3-1.7B | 3/521 | 16/521 | 36/521 |
| Qwen/Qwen3-VL-4B-Instruct | 0/521 | 9/521 | 0/521 |
| Qwen/Qwen3-VL-4B-Thinking | 0/521 | 3/521 | 61/521 |
| issai/Qolda-AVL-5B | 502/521 | 84/521 | 0/521 |

| Model | Şərait | Kirillə yazılmış cavab |
|---|---|---|
| Qwen/Qwen3-1.7B | mcq | 5/521 (1.0%) |
| Qwen/Qwen3-1.7B | short | 3/521 (0.6%) |
| Qwen/Qwen3-VL-4B-Instruct | mcq | 0/521 (0.0%) |
| Qwen/Qwen3-VL-4B-Instruct | short | 0/521 (0.0%) |
| Qwen/Qwen3-VL-4B-Thinking | mcq | 2/521 (0.4%) |
| Qwen/Qwen3-VL-4B-Thinking | short | 0/521 (0.0%) |
| issai/Qolda-AVL-5B | mcq | 5/521 (1.0%) |
| issai/Qolda-AVL-5B | short | 502/521 (96.4%) |
