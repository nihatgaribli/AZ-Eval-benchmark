# Sızma uçurumu izah edə bilərmi?

Dataset 1006 sual: `computed-template` 236, `manual` 246, `wikidata-template` 524.

## Sızma üçün əlçatmaz altdəst

`computed-template` mənşəli **236 sual** `src/generate_math.py` tərəfindən istehsal olunub və ölçülən modellərin hamısından sonra yaradılıb. Onlar heç bir təlim korpusunda ola bilməz, çünki mövcud deyildilər.

| Model | EN | AZ | Fərq | 95% CI | p |
|---|---|---|---|---|---|
| `CohereLabs/aya-expanse-8b` | 40.3% | 7.2% | 33.1pp | [27.1, 39.4] | 0.0001 |
| `GiorgiGE/Kolkha-Mini-Georgian` * | 1.7% | 0.0% | 1.7pp | [0.4, 3.4] | 0.1184 |
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | 57.2% | 18.2% | 39.0pp | [32.2, 46.2] | 0.0001 |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` † | 7.2% | 0.0% | 7.2pp | [3.8, 10.6] | 0.0001 |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | 36.9% | 4.2% | 32.6pp | [26.3, 38.6] | 0.0001 |
| `NbAiLab/borealis-4b` | 41.5% | 19.9% | 21.6pp | [14.8, 28.0] | 0.0001 |
| `Qwen/Qwen3-1.7B` | 33.5% | 11.0% | 22.5pp | [17.4, 27.5] | 0.0001 |
| `Qwen/Qwen3-4B` | 51.7% | 31.4% | 20.3pp | [13.1, 27.1] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Instruct` | 73.3% | 39.0% | 34.3pp | [27.5, 40.7] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Thinking` | 74.2% | 44.5% | 29.7pp | [23.7, 36.0] | 0.0001 |
| `Qwen/Qwen3.5-4B-Base` | 76.7% | 49.2% | 27.5pp | [21.6, 33.9] | 0.0001 |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` | 56.8% | 25.4% | 31.4pp | [25.4, 37.7] | 0.0001 |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` † | 5.5% | 2.5% | 3.0pp | [-0.4, 6.4] | 0.1395 |
| `Vikhrmodels/QVikhr-3-4B-Instruction` | 51.3% | 26.3% | 25.0pp | [18.6, 32.2] | 0.0001 |
| `ai-forever/mGPT` * | 0.4% | 0.4% | 0.0pp | [-1.3, 1.3] | 1.0000 |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` | 72.9% | 42.8% | 30.1pp | [23.7, 36.0] | 0.0001 |
| `bigscience/bloomz-1b7` * | 0.0% | 0.0% | 0.0pp | [0.0, 0.0] | 1.0000 |
| `elte-nlp/Racka-4B` | 19.1% | 17.4% | 1.7pp | [-4.7, 8.5] | 0.7105 |
| `google/gemma-3-4b-it` | 41.1% | 16.9% | 24.2pp | [17.8, 30.1] | 0.0001 |
| `ibm-granite/granite-3.1-2b-instruct` | 23.7% | 0.4% | 23.3pp | [17.8, 28.8] | 0.0001 |
| `issai/Qolda-AVL-5B` | 51.7% | 7.6% | 44.1pp | [37.3, 50.4] | 0.0001 |
| `issai/Qwen3.5-4B-Base-Kazakh` | 57.2% | 14.4% | 42.8pp | [36.4, 49.6] | 0.0001 |
| `kurakurai/Luth-1.7B-Instruct` | 44.5% | 11.9% | 32.6pp | [26.7, 38.6] | 0.0001 |
| `meta-llama/Meta-Llama-3-8B` | 47.9% | 22.0% | 25.8pp | [19.5, 31.8] | 0.0001 |
| `microsoft/Phi-3.5-mini-instruct` | 52.5% | 5.5% | 47.0pp | [41.1, 53.0] | 0.0001 |
| `microsoft/Phi-4-mini-instruct` | 49.6% | 8.5% | 41.1pp | [34.3, 47.5] | 0.0001 |
| `mistralai/Mistral-7B-v0.1` | 46.2% | 12.7% | 33.5pp | [27.1, 39.4] | 0.0001 |
| `openai:anthropic/claude-sonnet-5` | 95.8% | 93.6% | 2.1pp | [-0.4, 5.1] | 0.2286 |
| `openai:deepseek/deepseek-v3.2` | 95.8% | 92.8% | 3.0pp | [0.4, 5.9] | 0.0626 |
| `openai:meta-llama/llama-4-maverick` | 92.4% | 89.0% | 3.4pp | [-0.4, 7.2] | 0.1176 |
| `openai:openai/gpt-4o` | 91.5% | 90.7% | 0.8pp | [-3.0, 4.7] | 0.8203 |
| `openai:qwen/qwen3-235b-a22b-2507` | 89.8% | 78.0% | 11.9pp | [6.8, 17.4] | 0.0001 |
| `openai:qwen/qwen3-8b` | 64.0% | 33.9% | 30.1pp | [23.7, 36.0] | 0.0001 |
| `stabilityai/stablelm-2-1_6b-chat` * | 0.4% | 0.0% | 0.4pp | [0.0, 1.3] | 1.0000 |
| `thelamapi/next-1b` * | 3.4% | 1.3% | 2.1pp | [-0.4, 4.7] | 0.2269 |
| `tiiuae/Falcon3-3B-Instruct` | 47.9% | 2.1% | 45.8pp | [39.4, 51.3] | 0.0001 |
| `utter-project/EuroLLM-1.7B-Instruct` * | 0.8% | 0.0% | 0.8pp | [0.0, 2.1] | 0.4952 |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | 40.7% | 17.8% | 22.9pp | [16.9, 29.2] | 0.0001 |

\* İngilis balı 5%-dən aşağı: `GiorgiGE/Kolkha-Mini-Georgian`, `ai-forever/mGPT`, `bigscience/bloomz-1b7`, `stabilityai/stablelm-2-1_6b-chat`, `thelamapi/next-1b`, `utter-project/EuroLLM-1.7B-Instruct` tapşırığı ingiliscə də bacarmır. Onların sıfıra yaxın fərqi 'uçurum yoxdur' demək DEYİL: itirəcək balları yoxdur.

† EŞİYƏ YAXIN (5%-10% arası): `HuggingFaceTB/SmolLM2-1.7B-Instruct` (7.2%), `Trendyol/Trendyol-LLM-7b-base-v1.0` (5.5%). Bunlar `*` almır, çünki eşik əvvəlcədən elan edilib və nəticə göründükdən sonra dəyişdirilmir. Amma onların da itirəcək balı azdır, ona görə kiçik fərqləri yuxarıdakılar kimi ehtiyatla oxunmalıdır.

Uçurum bu altdəstdə də qalır. Deməli **benchmark sızması onu izah edə bilmir.**

İddia dəqiqdir: bu SƏTİRLƏR sızmayıb. Bu FAKTLARIN korpusda olması isə həm gözləniləndir, həm də lazımdır, çünki ölçdüyümüz şey elə həmin biliyin azərbaycanca işlədilə bilməsidir.

## Mənşəyə görə bal (kontekst, dəlil deyil)

| Model | Dil | `computed-template` | `manual` | `wikidata-template` |
|---|---|---|---|---|
| `CohereLabs/aya-expanse-8b` | EN | 40.3% | 23.2% | 62.3% |
| `CohereLabs/aya-expanse-8b` | AZ | 7.2% | 5.3% | 15.8% |
| `GiorgiGE/Kolkha-Mini-Georgian` | EN | 1.7% | 0.4% | 8.0% |
| `GiorgiGE/Kolkha-Mini-Georgian` | AZ | 0.0% | 0.0% | 0.2% |
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | EN | 57.2% | 24.0% | 58.6% |
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | AZ | 18.2% | 5.7% | 20.2% |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | EN | 7.2% | 17.9% | 36.1% |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | AZ | 0.0% | 0.0% | 0.0% |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | EN | 36.9% | 23.6% | 62.6% |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | AZ | 4.2% | 11.4% | 19.1% |
| `NbAiLab/borealis-4b` | EN | 41.5% | 19.9% | 59.0% |
| `NbAiLab/borealis-4b` | AZ | 19.9% | 11.0% | 29.2% |
| `Qwen/Qwen3-1.7B` | EN | 33.5% | 18.3% | 31.2% |
| `Qwen/Qwen3-1.7B` | AZ | 11.0% | 5.7% | 4.9% |
| `Qwen/Qwen3-4B` | EN | 51.7% | 23.2% | 53.1% |
| `Qwen/Qwen3-4B` | AZ | 31.4% | 9.3% | 20.0% |
| `Qwen/Qwen3-VL-4B-Instruct` | EN | 73.3% | 22.8% | 61.3% |
| `Qwen/Qwen3-VL-4B-Instruct` | AZ | 39.0% | 13.4% | 28.1% |
| `Qwen/Qwen3-VL-4B-Thinking` | EN | 74.2% | 24.8% | 61.1% |
| `Qwen/Qwen3-VL-4B-Thinking` | AZ | 44.5% | 12.6% | 27.5% |
| `Qwen/Qwen3.5-4B-Base` | EN | 76.7% | 25.2% | 68.9% |
| `Qwen/Qwen3.5-4B-Base` | AZ | 49.2% | 20.3% | 40.4% |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` | EN | 56.8% | 24.8% | 55.9% |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` | AZ | 25.4% | 5.7% | 18.9% |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | EN | 5.5% | 18.7% | 38.5% |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | AZ | 2.5% | 4.9% | 8.8% |
| `Vikhrmodels/QVikhr-3-4B-Instruction` | EN | 51.3% | 24.0% | 53.8% |
| `Vikhrmodels/QVikhr-3-4B-Instruction` | AZ | 26.3% | 8.1% | 19.5% |
| `ai-forever/mGPT` | EN | 0.4% | 12.6% | 22.3% |
| `ai-forever/mGPT` | AZ | 0.4% | 8.5% | 6.6% |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` | EN | 72.9% | 24.4% | 60.9% |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` | AZ | 42.8% | 12.2% | 29.8% |
| `bigscience/bloomz-1b7` | EN | 0.0% | 6.9% | 4.3% |
| `bigscience/bloomz-1b7` | AZ | 0.0% | 0.0% | 0.0% |
| `elte-nlp/Racka-4B` | EN | 19.1% | 12.2% | 30.0% |
| `elte-nlp/Racka-4B` | AZ | 17.4% | 4.5% | 10.9% |
| `google/gemma-3-4b-it` | EN | 41.1% | 26.4% | 59.4% |
| `google/gemma-3-4b-it` | AZ | 16.9% | 11.8% | 26.4% |
| `ibm-granite/granite-3.1-2b-instruct` | EN | 23.7% | 15.0% | 44.3% |
| `ibm-granite/granite-3.1-2b-instruct` | AZ | 0.4% | 0.0% | 0.4% |
| `issai/Qolda-AVL-5B` | EN | 51.7% | 22.8% | 45.9% |
| `issai/Qolda-AVL-5B` | AZ | 7.6% | 0.8% | 4.7% |
| `issai/Qwen3.5-4B-Base-Kazakh` | EN | 57.2% | 24.8% | 59.2% |
| `issai/Qwen3.5-4B-Base-Kazakh` | AZ | 14.4% | 10.2% | 21.7% |
| `kurakurai/Luth-1.7B-Instruct` | EN | 44.5% | 21.5% | 44.7% |
| `kurakurai/Luth-1.7B-Instruct` | AZ | 11.9% | 6.5% | 12.2% |
| `meta-llama/Meta-Llama-3-8B` | EN | 47.9% | 27.2% | 67.0% |
| `meta-llama/Meta-Llama-3-8B` | AZ | 22.0% | 20.7% | 45.3% |
| `microsoft/Phi-3.5-mini-instruct` | EN | 52.5% | 17.1% | 58.0% |
| `microsoft/Phi-3.5-mini-instruct` | AZ | 5.5% | 0.8% | 3.1% |
| `microsoft/Phi-4-mini-instruct` | EN | 49.6% | 19.5% | 54.3% |
| `microsoft/Phi-4-mini-instruct` | AZ | 8.5% | 5.3% | 15.2% |
| `mistralai/Mistral-7B-v0.1` | EN | 46.2% | 30.1% | 66.4% |
| `mistralai/Mistral-7B-v0.1` | AZ | 12.7% | 7.7% | 23.8% |
| `openai:anthropic/claude-sonnet-5` | EN | 95.8% | 35.4% | 76.5% |
| `openai:anthropic/claude-sonnet-5` | AZ | 93.6% | 37.4% | 66.0% |
| `openai:deepseek/deepseek-v3.2` | EN | 95.8% | 31.3% | 76.5% |
| `openai:deepseek/deepseek-v3.2` | AZ | 92.8% | 35.8% | 64.5% |
| `openai:meta-llama/llama-4-maverick` | EN | 92.4% | 30.9% | 75.4% |
| `openai:meta-llama/llama-4-maverick` | AZ | 89.0% | 31.3% | 67.4% |
| `openai:openai/gpt-4o` | EN | 91.5% | 32.9% | 78.4% |
| `openai:openai/gpt-4o` | AZ | 90.7% | 37.4% | 69.7% |
| `openai:qwen/qwen3-235b-a22b-2507` | EN | 89.8% | 24.8% | 70.8% |
| `openai:qwen/qwen3-235b-a22b-2507` | AZ | 78.0% | 22.8% | 49.8% |
| `openai:qwen/qwen3-8b` | EN | 64.0% | 26.8% | 65.5% |
| `openai:qwen/qwen3-8b` | AZ | 33.9% | 15.4% | 31.5% |
| `stabilityai/stablelm-2-1_6b-chat` | EN | 0.4% | 6.5% | 11.5% |
| `stabilityai/stablelm-2-1_6b-chat` | AZ | 0.0% | 0.4% | 0.2% |
| `thelamapi/next-1b` | EN | 3.4% | 15.0% | 23.4% |
| `thelamapi/next-1b` | AZ | 1.3% | 3.7% | 2.9% |
| `tiiuae/Falcon3-3B-Instruct` | EN | 47.9% | 17.5% | 36.1% |
| `tiiuae/Falcon3-3B-Instruct` | AZ | 2.1% | 0.0% | 1.8% |
| `utter-project/EuroLLM-1.7B-Instruct` | EN | 0.8% | 15.0% | 26.0% |
| `utter-project/EuroLLM-1.7B-Instruct` | AZ | 0.0% | 0.0% | 0.2% |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | EN | 40.7% | 17.5% | 58.2% |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | AZ | 17.8% | 6.1% | 34.6% |

Wikidata mənşəli suallar əl ilə yazılanlardan asandır. Bu, sızma dəlili SAYILA BİLMƏZ: harvester `sitelinks >= 8` filtri ilə məşhur obyektləri seçir, əl ilə yazılanlar isə Azərbaycana xas və qaranlıqdır. Fərq çətinlikdən də gələ bilər və iki izahı ayırd etmək üçün əlimizdə vasitə yoxdur.
