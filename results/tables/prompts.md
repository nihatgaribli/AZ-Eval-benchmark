# Prompt robustluğu

Üç şablon: `default` (iki nümunə, etiketli), `zeroshot` (nümunə yox),
`plain` (nümunə var, etiket yox). Fərq struktur səviyyəsindədir.

## AZ/EN uçurumu

| Model | Şablon | AZ | EN | Uçurum | 95% CI | p |
|---|---|---|---|---|---|---|
| `CohereLabs/aya-expanse-8b` | default | 11.2% | 47.4% | 36.2pp | [33.1, 39.2] | 0.0001 |
| `GiorgiGE/Kolkha-Mini-Georgian` | default | 0.1% | 4.7% | 4.6pp | [3.4, 5.9] | 0.0001 |
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | default | 16.2% | 49.8% | 33.6pp | [30.5, 36.7] | 0.0001 |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | default | 0.0% | 24.7% | 24.7pp | [22.0, 27.7] | 0.0001 |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | default | 13.7% | 47.0% | 33.3pp | [30.1, 36.1] | 0.0001 |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | oneshot | 20.2% | 47.0% | 26.8pp | [23.9, 29.5] | 0.0001 |
| `NbAiLab/borealis-4b` | default | 22.6% | 45.3% | 22.8pp | [19.8, 25.6] | 0.0001 |
| `NbAiLab/borealis-4b` | oneshot | 21.5% | 45.1% | 23.7pp | [20.6, 26.4] | 0.0001 |
| `Qwen/Qwen3-1.7B` | default | 6.5% | 28.6% | 22.0pp | [19.1, 24.7] | 0.0001 |
| `Qwen/Qwen3-4B` | default | 20.1% | 45.4% | 25.3pp | [22.2, 28.4] | 0.0001 |
| `Qwen/Qwen3-4B` | oneshot | 23.9% | 47.2% | 23.4pp | [20.0, 26.6] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Instruct` | default | 27.1% | 54.6% | 27.6pp | [24.3, 30.4] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Instruct` | zeroshot | 28.1% | 54.7% | 26.7pp | [23.8, 29.7] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Instruct` | plain | 26.0% | 54.4% | 28.5pp | [25.3, 31.5] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Instruct` | oneshot | 25.5% | 55.3% | 29.9pp | [26.9, 32.8] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Thinking` | default | 27.9% | 55.2% | 27.4pp | [24.2, 30.3] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Thinking` | zeroshot | 8.6% | 7.1% | -1.4pp | [-3.6, 0.9] | 0.2727 |
| `Qwen/Qwen3-VL-4B-Thinking` | plain | 23.5% | 46.6% | 23.0pp | [20.1, 25.8] | 0.0001 |
| `Qwen/Qwen3-VL-4B-Thinking` | oneshot | 24.3% | 55.3% | 31.0pp | [27.9, 34.0] | 0.0001 |
| `Qwen/Qwen3.5-4B-Base` | default | 37.5% | 60.0% | 22.4pp | [19.5, 25.3] | 0.0001 |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` | default | 17.2% | 48.5% | 31.3pp | [28.2, 34.2] | 0.0001 |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` | oneshot | 15.2% | 48.7% | 33.5pp | [30.3, 36.5] | 0.0001 |
| `Trendyol/Trendyol-LLM-7b-base-v1.0` | default | 6.3% | 25.8% | 19.4pp | [16.7, 22.2] | 0.0001 |
| `Vikhrmodels/QVikhr-3-4B-Instruction` | default | 18.3% | 45.9% | 27.6pp | [24.6, 30.5] | 0.0001 |
| `Vikhrmodels/QVikhr-3-4B-Instruction` | oneshot | 16.7% | 48.0% | 31.3pp | [28.3, 34.3] | 0.0001 |
| `ai-forever/mGPT` | default | 5.6% | 14.7% | 9.1pp | [7.0, 11.1] | 0.0001 |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` | default | 28.5% | 54.8% | 26.2pp | [23.3, 29.2] | 0.0001 |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` | oneshot | 26.6% | 55.6% | 28.9pp | [25.8, 31.8] | 0.0001 |
| `bigscience/bloomz-1b7` | default | 0.0% | 3.9% | 3.9pp | [2.8, 5.1] | 0.0001 |
| `elte-nlp/Racka-4B` | default | 10.8% | 23.1% | 12.2pp | [9.3, 15.2] | 0.0001 |
| `google/gemma-3-4b-it` | default | 20.5% | 46.9% | 26.4pp | [23.2, 29.8] | 0.0001 |
| `google/gemma-3-4b-it` | oneshot | 21.4% | 48.1% | 26.7pp | [23.8, 29.8] | 0.0001 |
| `ibm-granite/granite-3.1-2b-instruct` | default | 0.3% | 32.2% | 31.9pp | [28.9, 34.5] | 0.0001 |
| `issai/Qolda-AVL-5B` | default | 4.4% | 41.5% | 37.1pp | [33.8, 40.2] | 0.0001 |
| `issai/Qolda-AVL-5B` | zeroshot | 11.7% | 41.0% | 29.4pp | [26.3, 32.4] | 0.0001 |
| `issai/Qolda-AVL-5B` | plain | 3.9% | 40.7% | 36.8pp | [33.7, 39.8] | 0.0001 |
| `issai/Qolda-AVL-5B` | oneshot | 5.2% | 45.4% | 40.1pp | [37.0, 43.2] | 0.0001 |
| `issai/Qwen3.5-4B-Base-Kazakh` | default | 17.1% | 50.2% | 33.1pp | [30.1, 36.4] | 0.0001 |
| `kurakurai/Luth-1.7B-Instruct` | default | 10.7% | 39.0% | 28.2pp | [25.4, 31.2] | 0.0001 |
| `meta-llama/Meta-Llama-3-8B` | default | 33.7% | 52.6% | 18.9pp | [16.4, 21.5] | 0.0001 |
| `microsoft/Phi-3.5-mini-instruct` | default | 3.1% | 46.6% | 43.5pp | [40.3, 46.5] | 0.0001 |
| `microsoft/Phi-4-mini-instruct` | default | 11.2% | 44.6% | 33.4pp | [30.4, 36.4] | 0.0001 |
| `mistralai/Mistral-7B-v0.1` | default | 17.2% | 52.6% | 35.4pp | [32.5, 38.3] | 0.0001 |
| `openai:anthropic/claude-sonnet-5` | default | 65.5% | 71.0% | 5.5pp | [3.0, 7.8] | 0.0001 |
| `openai:deepseek/deepseek-v3.2` | default | 64.1% | 70.0% | 5.9pp | [3.5, 8.3] | 0.0001 |
| `openai:meta-llama/llama-4-maverick` | default | 63.6% | 68.5% | 4.9pp | [2.6, 7.5] | 0.0002 |
| `openai:openai/gpt-4o` | default | 66.7% | 70.4% | 3.7pp | [1.0, 6.4] | 0.0069 |
| `openai:qwen/qwen3-235b-a22b-2507` | default | 49.8% | 64.0% | 14.2pp | [11.1, 17.1] | 0.0001 |
| `openai:qwen/qwen3-8b` | default | 28.1% | 55.7% | 27.5pp | [24.6, 30.4] | 0.0001 |
| `stabilityai/stablelm-2-1_6b-chat` | default | 0.2% | 7.6% | 7.4pp | [5.7, 9.1] | 0.0001 |
| `thelamapi/next-1b` | default | 2.7% | 16.6% | 13.9pp | [11.7, 16.2] | 0.0001 |
| `tiiuae/Falcon3-3B-Instruct` | default | 1.4% | 34.3% | 32.9pp | [29.9, 36.0] | 0.0001 |
| `utter-project/EuroLLM-1.7B-Instruct` | default | 0.1% | 17.3% | 17.2pp | [14.9, 19.6] | 0.0001 |
| `ytu-ce-cosmos/Turkish-Llama-8b-v0.1` | default | 23.5% | 44.0% | 20.4pp | [17.7, 23.3] | 0.0001 |

## Cüt fərqi: baza ilə köklənmiş model

Hər iki model EYNİ promptu alır, ona görə bu fərq prompt seçimindən
daha az asılı olmalıdır.

| Şablon | Baza | Köklənmiş | Fərq | 95% CI | p |
|---|---|---|---|---|---|
| default | 27.9% | 4.4% | +23.4pp | [20.8, 26.3] | 0.0001 |
| zeroshot | 8.6% | 11.7% | -3.1pp | [-5.3, -0.6] | 0.0111 |
| plain | 23.5% | 3.9% | +19.6pp | [17.2, 22.4] | 0.0001 |
| oneshot | 24.3% | 5.2% | +19.1pp | [16.6, 21.6] | 0.0001 |

## Nəticə

Mütləq balın şablonla dəyişməsi gözləniləndir. Dəyişməməli olan
uçurumun işarəsi və mənalılığıdır.

| Yoxlama | Yararlı şablonların hamısında qalır? |
|---|---|
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` AZ/EN uçurumu | bəli |
| `NbAiLab/borealis-4b` AZ/EN uçurumu | bəli |
| `Qwen/Qwen3-4B` AZ/EN uçurumu | bəli |
| `Qwen/Qwen3-VL-4B-Instruct` AZ/EN uçurumu | bəli |
| `Qwen/Qwen3-VL-4B-Thinking` AZ/EN uçurumu | bəli |
| `RefalMachine/RuadaptQwen3-4B-Hybrid` AZ/EN uçurumu | bəli |
| `Vikhrmodels/QVikhr-3-4B-Instruction` AZ/EN uçurumu | bəli |
| `aisingapore/Qwen-SEA-LION-v4-4B-VL` AZ/EN uçurumu | bəli |
| `google/gemma-3-4b-it` AZ/EN uçurumu | bəli |
| `issai/Qolda-AVL-5B` AZ/EN uçurumu | bəli |
| cüt fərqi (baza > köklənmiş) | bəli |

### Müqayisəyə girməyən şəraitlər

Sətirlərinin 20%-dən çoxu BOŞ qalan qaçış ölçmə
sayılmır: model heç nə yazmayıbsa, qiymətləndiriləcək şey yoxdur.

- `Qwen/Qwen3-VL-4B-Thinking` [en/zeroshot]: sətirlərin 42.7%-i boş
- `bigscience/bloomz-1b7` [az/default]: sətirlərin 83.5%-i boş
- `bigscience/bloomz-1b7` [en/default]: sətirlərin 79.4%-i boş

BU, İDDİANIN UĞURSUZLUĞU DEYİL, ÖLÇMƏNİN UĞURSUZLUĞUDUR və ikisini
qarışdırmaq hesabatı yanlış oxudardı. Kənarda qalan şərait həmin
iddia barədə nə lehinə, nə əleyhinə dəlil sayılır.

MƏHDUDİYYƏT KİMİ QALIR: kənarlaşdırma möhkəmlik iddiasının
söykəndiyi şablon sayını AZALDIR. Aşağıdakı nəticə həmin azalmış
sayla oxunmalıdır.

Hər iki iddia yararlı şablonların hamısında eyni istiqamətdə və
sıfırdan fərqli qalır. **Nəticələr prompt seçiminə söykənmir.**
