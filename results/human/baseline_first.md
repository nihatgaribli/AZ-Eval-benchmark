# İnsan bazası

Cavablanan sual: 49. Boş buraxılan (bilmirəm): 29 (59.2%).

| Zəncir | EM | 95% CI |
|---|---|---|
| strict | 26.5% | [14.3, 38.8] |
| morph | 28.6% | [16.3, 40.8] |
| lenient | 28.6% | [16.3, 40.8] |
| translit | 28.6% | [16.3, 40.8] |

## Kateqoriya üzrə (STRICT)

| Kateqoriya | n | EM |
|---|---|---|
| culture | 9 | 22.2% |
| geography | 7 | 0.0% |
| history | 6 | 0.0% |
| language | 6 | 0.0% |
| mathematics | 12 | 58.3% |
| science | 5 | 40.0% |
| world | 4 | 50.0% |

Boş cavablar SƏHV sayılır, çünki model də cavabsız sətirdə bal almır.
Onların payı ayrıca verilir: insanın bilmədiyi sual modelin də
bilmədiyi sual ola bilər və bu, uçurumun bir hissəsini izah edir.

## İnsan və modellər, eyni suallar (TRANSLIT)

| | AZ |
|---|---|
| `meta-llama/Meta-Llama-3-8B` | 36.7% |
| `Qwen/Qwen3.5-4B-Base` | 32.7% |
| **İNSAN** | 28.6% |
| `Qwen/Qwen3-VL-4B-Instruct` | 24.5% |
| `Qwen/Qwen3-VL-4B-Thinking` | 24.5% |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | 22.4% |
| `google/gemma-3-4b-it` | 20.4% |
| `mistralai/Mistral-7B-v0.1` | 14.3% |
| `ai-forever/mGPT` | 10.2% |
| `issai/Qolda-AVL-5B` | 10.2% |
| `issai/Qwen3.5-4B-Base-Kazakh` | 10.2% |
| `microsoft/Phi-4-mini-instruct` | 10.2% |
| `CohereLabs/aya-expanse-8b` | 8.2% |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | 6.1% |
| `microsoft/Phi-3.5-mini-instruct` | 6.1% |
| `Qwen/Qwen3-1.7B` | 4.1% |
| `thelamapi/next-1b` | 2.0% |
| `tiiuae/Falcon3-3B-Instruct` | 2.0% |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 0.0% |
| `bigscience/bloomz-1b7` | 0.0% |
| `ibm-granite/granite-3.1-2b-instruct` | 0.0% |
| `stabilityai/stablelm-2-1_6b-chat` | 0.0% |
| `utter-project/EuroLLM-1.7B-Instruct` | 0.0% |

## Bu cədvəli necə oxumaq lazımdır

İnsan bazası TAVAN QURMUR: 28.6%, ən yaxşı model
36.7%. Dataset insan üçün də çətindir.

MƏHDUDİYYƏTLƏR:

1. **Azsaylı sual (49).** İntervallar genişdir.
2. **Boş cavab SƏHV sayılır** (29 sual, 59%). Model həmişə nəsə yazır, insan
   isə bilmədiyini boş buraxa bilər. İnsan təxmin etsəydi, balı
   bir qədər yuxarı olardı.
3. **Cavablayanın dəstlə əlaqəsi nəticəni əyir.** Datasetin müəllifi
   sualları görüb, yəni meyl onun xeyrinədir; dəsti görməmiş adamın
   balı isə təmiz ölçüdür. Hansı halda olduğu ayrıca yazılmalıdır.

