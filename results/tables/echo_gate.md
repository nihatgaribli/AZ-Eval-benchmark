# Nümunə təkrarı qapısı

Model few-shot nümunələrinin cavablarını təkrarlayıb sonra əsl cavabı
yazırsa, çıxarıcı birinci sətri götürür və model düzgün cavabladığı
sualda səhv sayılır. Belə qaçış ölçmə deyil.

Hədd: nümunə təkrarı **20%**, sual təkrarı **20%**.

**4 qaçış qapıdan keçmir:**

| Qaçış | Dil | Nümunə təkrarı | Sual təkrarı | n |
|---|---|---|---|---|
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | az | **5.3%** | **82.3%** | 1006 |
| `elte-nlp/Racka-4B` | az | **16.9%** | **68.4%** | 1006 |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | az | **68.2%** | **0.0%** | 1006 |
| `Qwen/Qwen3-VL-4B-Thinking (zeroshot)` | az | **0.0%** | **31.4%** | 1005 |

## Ən yüksək on qaçış

| Qaçış | Dil | Nümunə təkrarı | Sual təkrarı | n |
|---|---|---|---|---|
| `HiTZ/Latxa-Qwen3-VL-4B-Instruct` | az | 5.3% | 82.3% | 1006 |
| `elte-nlp/Racka-4B` | az | 16.9% | 68.4% | 1006 |
| `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` | az | 68.2% | 0.0% | 1006 |
| `Qwen/Qwen3-VL-4B-Thinking (zeroshot)` | az | 0.0% | 31.4% | 1005 |
| `utter-project/EuroLLM-1.7B-Instruct` | az | 6.0% | 19.6% | 1005 |
| `elte-nlp/Racka-4B` | en | 10.4% | 1.6% | 1006 |
| `GiorgiGE/Kolkha-Mini-Georgian` | az | 0.0% | 9.5% | 1006 |
| `ai-forever/mGPT` | az | 8.7% | 0.2% | 1005 |
| `ai-forever/mGPT` | en | 7.7% | 0.0% | 1005 |
| `stabilityai/stablelm-2-1_6b-chat` | en | 6.5% | 0.0% | 1005 |
