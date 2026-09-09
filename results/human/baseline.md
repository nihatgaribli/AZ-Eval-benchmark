# İnsan bazası

Cavablanan sual: 68. Boş buraxılan (bilmirəm): 29 (42.6%).

| Zəncir | EM | 95% CI |
|---|---|---|
| strict | 41.2% | [29.4, 52.9] |
| morph | 44.1% | [32.4, 57.4] |
| lenient | 45.6% | [33.8, 57.4] |
| translit | 45.6% | [33.8, 57.4] |

## Kateqoriya üzrə (STRICT)

| Kateqoriya | n | EM |
|---|---|---|
| culture | 9 | 22.2% |
| geography | 11 | 27.3% |
| history | 8 | 25.0% |
| language | 7 | 14.3% |
| mathematics | 18 | 72.2% |
| science | 9 | 44.4% |
| world | 6 | 50.0% |

Boş cavablar SƏHV sayılır, çünki model də cavabsız sətirdə bal almır.
Onların payı ayrıca verilir: insanın bilmədiyi sual modelin də
bilmədiyi sual ola bilər və bu, uçurumun bir hissəsini izah edir.

## İnsan və modellər, eyni suallar (TRANSLIT)

| | AZ |
|---|---|
| **İNSAN** | 45.6% |
| `meta-llama/Meta-Llama-3-8B` | 38.2% |
| `Qwen/Qwen3.5-4B-Base` | 32.4% |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | 27.9% |
| `Qwen/Qwen3-VL-4B-Thinking` | 25.0% |
| `Qwen/Qwen3-VL-4B-Instruct` | 23.5% |
| `google/gemma-3-4b-it` | 17.6% |
| `mistralai/Mistral-7B-v0.1` | 14.7% |
| `issai/Qwen3.5-4B-Base-Kazakh` | 10.3% |
| `microsoft/Phi-4-mini-instruct` | 10.3% |
| `CohereLabs/aya-expanse-8b` | 8.8% |
| `ai-forever/mGPT` | 8.8% |
| `issai/Qolda-AVL-5B` | 8.8% |
| `Qwen/Qwen3-1.7B` | 7.4% |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | 5.9% |
| `microsoft/Phi-3.5-mini-instruct` | 5.9% |
| `tiiuae/Falcon3-3B-Instruct` | 2.9% |
| `thelamapi/next-1b` | 1.5% |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 0.0% |
| `bigscience/bloomz-1b7` | 0.0% |
| `ibm-granite/granite-3.1-2b-instruct` | 0.0% |
| `stabilityai/stablelm-2-1_6b-chat` | 0.0% |
| `utter-project/EuroLLM-1.7B-Instruct` | 0.0% |

## Bu cədvəli necə oxumaq lazımdır

İnsan bazası TAVAN DEYİL və bu ölçmə onu göstərdi. Dataset insan
üçün də çətindir: sualların yarıdan çoxu boş qalıb və ən yaxşı
model insanı üstələyir.

ÜÇ MƏHDUDİYYƏT, hər biri nəticəni fərqli istiqamətə əyir:

1. **Bir nəfər, azsaylı sual.** İntervallar genişdir və insanla
   model arasındakı fərq statistik olaraq ayırd edilmir.
2. **İnsan boş buraxdı, model həmişə cavab verir.** Boş cavab səhv
   sayılır. İnsan modellər kimi təxmin etsəydi, balı yuxarı olardı.
3. **Cavablayan datasetin müəllifidir.** Sualları görmüş adamdır,
   yəni meyl onun XEYRİNƏdir. Buna baxmayaraq bal 30%-dən aşağıdır.
   Naiv insanın balı, ehtimal ki, bundan da aşağı olardı.

Üçüncüsü ən vacibidir: təmiz baza üçün datasetı görməmiş ikinci
adam lazımdır. Hazırkı rəqəm istiqamət verir, tavan qurmur.

