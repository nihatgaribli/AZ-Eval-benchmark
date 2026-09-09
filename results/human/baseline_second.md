# İnsan bazası

Cavablanan sual: 50. Boş buraxılan (bilmirəm): 7 (14.0%).

| Zəncir | EM | 95% CI |
|---|---|---|
| strict | 64.0% | [50.0, 76.0] |
| morph | 68.0% | [56.0, 80.0] |
| lenient | 70.0% | [58.0, 82.0] |
| translit | 70.0% | [58.0, 82.0] |

## Kateqoriya üzrə (STRICT)

| Kateqoriya | n | EM |
|---|---|---|
| culture | 6 | 66.7% |
| geography | 9 | 33.3% |
| history | 4 | 50.0% |
| language | 4 | 25.0% |
| mathematics | 13 | 100.0% |
| science | 9 | 55.6% |
| world | 5 | 80.0% |

Boş cavablar SƏHV sayılır, çünki model də cavabsız sətirdə bal almır.
Onların payı ayrıca verilir: insanın bilmədiyi sual modelin də
bilmədiyi sual ola bilər və bu, uçurumun bir hissəsini izah edir.

## İnsan və modellər, eyni suallar (TRANSLIT)

| | AZ |
|---|---|
| `openai:anthropic/claude-sonnet-5` | 74.0% |
| **İNSAN** | 70.0% |
| `openai:deepseek/deepseek-v3.2` | 68.0% |
| `openai:meta-llama/llama-4-maverick` | 66.0% |
| `openai:openai/gpt-4o` | 66.0% |
| `openai:qwen/qwen3-235b-a22b-2507` | 52.0% |
| `Qwen/Qwen3.5-4B-Base` | 36.0% |
| `meta-llama/Meta-Llama-3-8B` | 36.0% |
| `openai:qwen/qwen3-8b` | 36.0% |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | 34.0% |
| `Qwen/Qwen3-VL-4B-Instruct` | 32.0% |
| `Qwen/Qwen3-VL-4B-Thinking` | 32.0% |
| `google/gemma-3-4b-it` | 20.0% |
| `mistralai/Mistral-7B-v0.1` | 20.0% |
| `issai/Qwen3.5-4B-Base-Kazakh` | 18.0% |
| `CohereLabs/aya-expanse-8b` | 14.0% |
| `microsoft/Phi-4-mini-instruct` | 14.0% |
| `Qwen/Qwen3-1.7B` | 12.0% |
| `issai/Qolda-AVL-5B` | 12.0% |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | 8.0% |
| `ai-forever/mGPT` | 8.0% |
| `microsoft/Phi-3.5-mini-instruct` | 4.0% |
| `tiiuae/Falcon3-3B-Instruct` | 4.0% |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 0.0% |
| `bigscience/bloomz-1b7` | 0.0% |
| `ibm-granite/granite-3.1-2b-instruct` | 0.0% |
| `stabilityai/stablelm-2-1_6b-chat` | 0.0% |
| `thelamapi/next-1b` | 0.0% |
| `utter-project/EuroLLM-1.7B-Instruct` | 0.0% |

## Bu cədvəli necə oxumaq lazımdır

İnsan bazası TAVAN QURMUR: 70.0%, ən yaxşı model
74.0%. Dataset insan üçün də çətindir.

MƏHDUDİYYƏTLƏR:

1. **Azsaylı sual (50).** İntervallar genişdir.
2. **Boş cavab SƏHV sayılır** (7 sual, 14%). Model həmişə nəsə yazır, insan
   isə bilmədiyini boş buraxa bilər. İnsan təxmin etsəydi, balı
   bir qədər yuxarı olardı.
3. **Cavablayanın dəstlə əlaqəsi nəticəni əyir.** Datasetin müəllifi
   sualları görüb, yəni meyl onun xeyrinədir; dəsti görməmiş adamın
   balı isə təmiz ölçüdür. Hansı halda olduğu ayrıca yazılmalıdır.

