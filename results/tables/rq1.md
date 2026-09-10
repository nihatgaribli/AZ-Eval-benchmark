# RQ1 — AZ vs EN

| Model                                                 | Rejim    | N    | AZ EM | EN EM | Fərq   | 95% CI       | p      | p (Holm) | Mənalı |
|-------------------------------------------------------|----------|------|-------|-------|--------|--------------|--------|----------|--------|
| CohereLabs/aya-expanse-8b                             | strict   | 994  | 11.2% | 47.4% | 36.2pp | [33.1, 39.2] | 0.0001 | 0.0216   | bəli   |
| CohereLabs/aya-expanse-8b                             | morph    | 994  | 11.8% | 47.4% | 35.6pp | [32.5, 38.7] | 0.0001 | 0.0216   | bəli   |
| CohereLabs/aya-expanse-8b                             | lenient  | 994  | 12.0% | 47.4% | 35.4pp | [32.2, 38.5] | 0.0001 | 0.0216   | bəli   |
| CohereLabs/aya-expanse-8b                             | translit | 994  | 12.0% | 47.4% | 35.4pp | [32.2, 38.5] | 0.0001 | 0.0216   | bəli   |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | strict   | 1006 | 16.2% | 49.8% | 33.6pp | [30.5, 36.7] | 0.0001 | 0.0216   | bəli   |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | morph    | 1006 | 16.6% | 49.8% | 33.2pp | [30.2, 36.4] | 0.0001 | 0.0216   | bəli   |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | lenient  | 1006 | 16.9% | 49.8% | 32.9pp | [29.8, 36.2] | 0.0001 | 0.0216   | bəli   |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | translit | 1006 | 16.9% | 49.8% | 32.9pp | [29.8, 36.2] | 0.0001 | 0.0216   | bəli   |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | strict   | 994  | 0.0%  | 24.7% | 24.7pp | [22.0, 27.7] | 0.0001 | 0.0216   | bəli   |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | morph    | 994  | 0.0%  | 24.7% | 24.7pp | [22.0, 27.7] | 0.0001 | 0.0216   | bəli   |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | lenient  | 994  | 0.0%  | 24.7% | 24.7pp | [22.0, 27.7] | 0.0001 | 0.0216   | bəli   |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | translit | 994  | 0.0%  | 24.7% | 24.7pp | [22.0, 27.7] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | strict   | 1006 | 13.7% | 47.0% | 33.3pp | [30.1, 36.1] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | morph    | 1006 | 14.5% | 47.0% | 32.5pp | [29.3, 35.4] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | lenient  | 1006 | 14.6% | 47.1% | 32.5pp | [29.3, 35.5] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | translit | 1006 | 14.6% | 47.1% | 32.5pp | [29.3, 35.5] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | strict   | 1006 | 20.2% | 47.0% | 26.8pp | [23.9, 29.5] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | morph    | 1006 | 21.6% | 47.0% | 25.4pp | [22.5, 28.1] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | lenient  | 1006 | 21.9% | 47.1% | 25.2pp | [22.3, 28.0] | 0.0001 | 0.0216   | bəli   |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | translit | 1006 | 21.9% | 47.1% | 25.2pp | [22.3, 28.0] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b                                   | strict   | 1006 | 22.6% | 45.3% | 22.8pp | [19.8, 25.6] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b                                   | morph    | 1006 | 24.1% | 45.3% | 21.3pp | [18.2, 24.3] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b                                   | lenient  | 1006 | 24.4% | 45.3% | 21.0pp | [17.8, 24.1] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b                                   | translit | 1006 | 24.4% | 45.3% | 21.0pp | [17.8, 24.1] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b (oneshot)                         | strict   | 1006 | 21.5% | 45.1% | 23.7pp | [20.6, 26.4] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b (oneshot)                         | morph    | 1006 | 23.0% | 45.1% | 22.2pp | [19.1, 25.0] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b (oneshot)                         | lenient  | 1006 | 23.3% | 45.1% | 21.9pp | [18.8, 24.7] | 0.0001 | 0.0216   | bəli   |
| NbAiLab/borealis-4b (oneshot)                         | translit | 1006 | 23.3% | 45.1% | 21.9pp | [18.8, 24.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-1.7B                                       | strict   | 994  | 6.5%  | 28.6% | 22.0pp | [19.1, 24.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-1.7B                                       | morph    | 994  | 6.7%  | 28.6% | 21.8pp | [18.9, 24.5] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-1.7B                                       | lenient  | 994  | 7.0%  | 28.7% | 21.6pp | [18.6, 24.4] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-1.7B                                       | translit | 994  | 7.0%  | 28.7% | 21.6pp | [18.6, 24.4] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B                                         | strict   | 1006 | 20.1% | 45.4% | 25.3pp | [22.2, 28.4] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B                                         | morph    | 1006 | 21.0% | 45.5% | 24.6pp | [21.4, 27.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B                                         | lenient  | 1006 | 21.4% | 45.5% | 24.2pp | [21.0, 27.2] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B                                         | translit | 1006 | 21.5% | 45.5% | 24.1pp | [21.0, 27.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B (oneshot)                               | strict   | 1006 | 23.9% | 47.2% | 23.4pp | [20.0, 26.6] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B (oneshot)                               | morph    | 1006 | 24.8% | 47.2% | 22.5pp | [19.2, 25.5] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B (oneshot)                               | lenient  | 1006 | 25.2% | 47.2% | 22.0pp | [18.7, 25.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-4B (oneshot)                               | translit | 1006 | 25.4% | 47.2% | 21.8pp | [18.5, 25.0] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct                             | strict   | 994  | 27.1% | 54.6% | 27.6pp | [24.3, 30.4] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct                             | morph    | 994  | 27.6% | 54.6% | 27.1pp | [23.8, 29.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct                             | lenient  | 994  | 27.8% | 54.6% | 26.9pp | [23.7, 29.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct                             | translit | 994  | 27.8% | 54.6% | 26.9pp | [23.7, 29.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | strict   | 994  | 25.5% | 55.3% | 29.9pp | [26.9, 32.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | morph    | 994  | 26.0% | 55.3% | 29.4pp | [26.5, 32.4] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | lenient  | 994  | 26.3% | 55.3% | 29.1pp | [26.2, 32.0] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | translit | 994  | 26.3% | 55.3% | 29.1pp | [26.2, 32.0] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | strict   | 994  | 26.0% | 54.4% | 28.5pp | [25.3, 31.5] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | morph    | 994  | 26.5% | 54.4% | 28.0pp | [24.7, 31.0] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | lenient  | 994  | 26.7% | 54.4% | 27.8pp | [24.5, 30.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | translit | 994  | 26.7% | 54.4% | 27.8pp | [24.5, 30.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | strict   | 994  | 28.1% | 54.7% | 26.7pp | [23.8, 29.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | morph    | 994  | 28.7% | 54.7% | 26.1pp | [23.2, 29.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | lenient  | 994  | 29.0% | 54.7% | 25.8pp | [22.9, 28.9] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | translit | 994  | 29.0% | 54.7% | 25.8pp | [22.9, 28.9] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking                             | strict   | 994  | 27.9% | 55.2% | 27.4pp | [24.2, 30.3] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking                             | morph    | 994  | 29.1% | 55.2% | 26.2pp | [23.1, 29.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking                             | lenient  | 994  | 29.6% | 55.2% | 25.7pp | [22.6, 28.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking                             | translit | 994  | 29.6% | 55.2% | 25.7pp | [22.6, 28.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | strict   | 994  | 24.3% | 55.3% | 31.0pp | [27.9, 34.0] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | morph    | 994  | 25.7% | 55.3% | 29.7pp | [26.5, 32.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | lenient  | 994  | 26.3% | 55.3% | 29.1pp | [26.0, 32.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | translit | 994  | 26.3% | 55.3% | 29.1pp | [26.0, 32.1] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | strict   | 994  | 23.5% | 46.6% | 23.0pp | [20.1, 25.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | morph    | 994  | 24.4% | 46.6% | 22.1pp | [19.2, 24.8] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | lenient  | 994  | 24.6% | 46.6% | 21.9pp | [19.0, 24.6] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | translit | 994  | 24.6% | 46.6% | 21.9pp | [19.0, 24.6] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | strict   | 994  | 8.6%  | 7.1%  | -1.4pp | [-3.6, 0.9]  | 0.2727 | 0.8333   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | morph    | 994  | 8.8%  | 7.2%  | -1.5pp | [-3.8, 0.9]  | 0.2365 | 0.8333   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | lenient  | 994  | 8.9%  | 7.2%  | -1.6pp | [-3.9, 0.9]  | 0.2044 | 0.8333   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | translit | 994  | 8.9%  | 7.2%  | -1.6pp | [-3.9, 0.9]  | 0.2044 | 0.8333   | xeyr   |
| Qwen/Qwen3.5-4B-Base                                  | strict   | 994  | 37.5% | 60.0% | 22.4pp | [19.5, 25.3] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3.5-4B-Base                                  | morph    | 994  | 38.7% | 60.0% | 21.2pp | [18.3, 23.9] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3.5-4B-Base                                  | lenient  | 994  | 39.0% | 60.0% | 20.9pp | [18.1, 23.7] | 0.0001 | 0.0216   | bəli   |
| Qwen/Qwen3.5-4B-Base                                  | translit | 994  | 39.0% | 60.0% | 20.9pp | [18.1, 23.7] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | strict   | 1006 | 17.2% | 48.5% | 31.3pp | [28.2, 34.2] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | morph    | 1006 | 17.8% | 48.5% | 30.7pp | [27.7, 33.6] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | lenient  | 1006 | 18.0% | 48.5% | 30.5pp | [27.5, 33.3] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | translit | 1006 | 18.7% | 48.5% | 29.8pp | [26.7, 32.7] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | strict   | 1006 | 15.2% | 48.7% | 33.5pp | [30.3, 36.5] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | morph    | 1006 | 15.7% | 48.7% | 33.0pp | [29.7, 35.9] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | lenient  | 1006 | 16.1% | 48.7% | 32.6pp | [29.4, 35.4] | 0.0001 | 0.0216   | bəli   |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | translit | 1006 | 17.0% | 48.7% | 31.7pp | [28.6, 34.6] | 0.0001 | 0.0216   | bəli   |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | strict   | 994  | 6.3%  | 25.8% | 19.4pp | [16.7, 22.2] | 0.0001 | 0.0216   | bəli   |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | morph    | 994  | 6.6%  | 26.3% | 19.6pp | [16.9, 22.4] | 0.0001 | 0.0216   | bəli   |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | lenient  | 994  | 6.8%  | 26.4% | 19.5pp | [16.8, 22.4] | 0.0001 | 0.0216   | bəli   |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | translit | 994  | 6.8%  | 26.4% | 19.5pp | [16.8, 22.4] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | strict   | 1006 | 18.3% | 45.9% | 27.6pp | [24.6, 30.5] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | morph    | 1006 | 18.7% | 46.0% | 27.3pp | [24.3, 30.3] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | lenient  | 1006 | 18.8% | 46.0% | 27.2pp | [24.1, 30.2] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | translit | 1006 | 19.5% | 46.0% | 26.5pp | [23.5, 29.5] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | strict   | 1006 | 16.7% | 48.0% | 31.3pp | [28.3, 34.3] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | morph    | 1006 | 17.7% | 48.1% | 30.4pp | [27.4, 33.4] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | lenient  | 1006 | 17.8% | 48.1% | 30.3pp | [27.3, 33.3] | 0.0001 | 0.0216   | bəli   |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | translit | 1006 | 18.5% | 48.1% | 29.6pp | [26.5, 32.6] | 0.0001 | 0.0216   | bəli   |
| ai-forever/mGPT                                       | strict   | 994  | 5.6%  | 14.7% | 9.1pp  | [7.0, 11.1]  | 0.0001 | 0.0216   | bəli   |
| ai-forever/mGPT                                       | morph    | 994  | 6.5%  | 14.7% | 8.1pp  | [6.2, 10.3]  | 0.0001 | 0.0216   | bəli   |
| ai-forever/mGPT                                       | lenient  | 994  | 6.5%  | 15.0% | 8.5pp  | [6.5, 10.6]  | 0.0001 | 0.0216   | bəli   |
| ai-forever/mGPT                                       | translit | 994  | 6.5%  | 15.0% | 8.5pp  | [6.5, 10.6]  | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | strict   | 1006 | 28.5% | 54.8% | 26.2pp | [23.3, 29.2] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | morph    | 1006 | 29.1% | 54.8% | 25.6pp | [22.8, 28.6] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | lenient  | 1006 | 29.3% | 54.8% | 25.4pp | [22.5, 28.4] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | translit | 1006 | 29.3% | 54.8% | 25.4pp | [22.5, 28.4] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | strict   | 1006 | 26.6% | 55.6% | 28.9pp | [25.8, 31.8] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | morph    | 1006 | 27.3% | 55.6% | 28.2pp | [25.2, 31.2] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | lenient  | 1006 | 27.8% | 55.6% | 27.7pp | [24.7, 30.7] | 0.0001 | 0.0216   | bəli   |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | translit | 1006 | 27.8% | 55.6% | 27.7pp | [24.7, 30.7] | 0.0001 | 0.0216   | bəli   |
| bigscience/bloomz-1b7                                 | strict   | 994  | 0.0%  | 3.9%  | 3.9pp  | [2.8, 5.1]   | 0.0001 | 0.0216   | bəli   |
| bigscience/bloomz-1b7                                 | morph    | 994  | 0.0%  | 3.9%  | 3.9pp  | [2.8, 5.1]   | 0.0001 | 0.0216   | bəli   |
| bigscience/bloomz-1b7                                 | lenient  | 994  | 0.0%  | 3.9%  | 3.9pp  | [2.8, 5.1]   | 0.0001 | 0.0216   | bəli   |
| bigscience/bloomz-1b7                                 | translit | 994  | 0.0%  | 3.9%  | 3.9pp  | [2.8, 5.1]   | 0.0001 | 0.0216   | bəli   |
| elte-nlp/Racka-4B                                     | strict   | 1006 | 10.8% | 23.1% | 12.2pp | [9.3, 15.2]  | 0.0001 | 0.0216   | bəli   |
| elte-nlp/Racka-4B                                     | morph    | 1006 | 11.0% | 23.1% | 12.0pp | [9.1, 15.1]  | 0.0001 | 0.0216   | bəli   |
| elte-nlp/Racka-4B                                     | lenient  | 1006 | 11.2% | 23.3% | 12.0pp | [9.3, 15.1]  | 0.0001 | 0.0216   | bəli   |
| elte-nlp/Racka-4B                                     | translit | 1006 | 11.2% | 23.3% | 12.0pp | [9.3, 15.1]  | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it                                  | strict   | 994  | 20.5% | 46.9% | 26.4pp | [23.2, 29.8] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it                                  | morph    | 994  | 21.5% | 46.9% | 25.4pp | [22.0, 28.7] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it                                  | lenient  | 994  | 21.9% | 46.9% | 24.9pp | [21.7, 28.4] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it                                  | translit | 994  | 21.9% | 46.9% | 24.9pp | [21.7, 28.4] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it (oneshot)                        | strict   | 1006 | 21.4% | 48.1% | 26.7pp | [23.8, 29.8] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it (oneshot)                        | morph    | 1006 | 22.5% | 48.1% | 25.6pp | [22.6, 28.7] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it (oneshot)                        | lenient  | 1006 | 22.7% | 48.1% | 25.4pp | [22.3, 28.5] | 0.0001 | 0.0216   | bəli   |
| google/gemma-3-4b-it (oneshot)                        | translit | 1006 | 22.7% | 48.1% | 25.4pp | [22.3, 28.5] | 0.0001 | 0.0216   | bəli   |
| ibm-granite/granite-3.1-2b-instruct                   | strict   | 994  | 0.3%  | 32.2% | 31.9pp | [28.9, 34.5] | 0.0001 | 0.0216   | bəli   |
| ibm-granite/granite-3.1-2b-instruct                   | morph    | 994  | 0.3%  | 32.2% | 31.9pp | [28.9, 34.5] | 0.0001 | 0.0216   | bəli   |
| ibm-granite/granite-3.1-2b-instruct                   | lenient  | 994  | 0.3%  | 32.2% | 31.9pp | [28.9, 34.5] | 0.0001 | 0.0216   | bəli   |
| ibm-granite/granite-3.1-2b-instruct                   | translit | 994  | 0.3%  | 32.2% | 31.9pp | [28.9, 34.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B                                    | strict   | 994  | 4.4%  | 41.5% | 37.1pp | [33.8, 40.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B                                    | morph    | 994  | 4.4%  | 41.5% | 37.1pp | [33.8, 40.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B                                    | lenient  | 994  | 4.4%  | 41.5% | 37.1pp | [33.8, 40.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B                                    | translit | 994  | 9.2%  | 41.5% | 32.4pp | [29.4, 35.4] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (oneshot)                          | strict   | 994  | 5.2%  | 45.4% | 40.1pp | [37.0, 43.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (oneshot)                          | morph    | 994  | 5.2%  | 45.4% | 40.1pp | [37.0, 43.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (oneshot)                          | lenient  | 994  | 5.2%  | 45.4% | 40.1pp | [37.0, 43.2] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (oneshot)                          | translit | 994  | 9.7%  | 45.4% | 35.7pp | [32.7, 38.7] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (plain)                            | strict   | 994  | 3.9%  | 40.7% | 36.8pp | [33.7, 39.8] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (plain)                            | morph    | 994  | 4.1%  | 40.7% | 36.6pp | [33.5, 39.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (plain)                            | lenient  | 994  | 4.1%  | 40.7% | 36.6pp | [33.5, 39.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (plain)                            | translit | 994  | 8.1%  | 40.7% | 32.6pp | [29.7, 35.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (script)                           | strict   | 994  | 5.0%  | 41.4% | 36.4pp | [33.4, 39.4] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (script)                           | morph    | 994  | 5.2%  | 41.4% | 36.2pp | [33.1, 39.1] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (script)                           | lenient  | 994  | 5.2%  | 41.4% | 36.2pp | [33.1, 39.1] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (script)                           | translit | 994  | 9.9%  | 41.4% | 31.6pp | [28.7, 34.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (zeroshot)                         | strict   | 994  | 11.7% | 41.0% | 29.4pp | [26.3, 32.4] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (zeroshot)                         | morph    | 994  | 11.8% | 41.0% | 29.3pp | [26.2, 32.3] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (zeroshot)                         | lenient  | 994  | 11.8% | 41.0% | 29.3pp | [26.2, 32.3] | 0.0001 | 0.0216   | bəli   |
| issai/Qolda-AVL-5B (zeroshot)                         | translit | 994  | 15.6% | 41.0% | 25.5pp | [22.5, 28.5] | 0.0001 | 0.0216   | bəli   |
| issai/Qwen3.5-4B-Base-Kazakh                          | strict   | 994  | 17.1% | 50.2% | 33.1pp | [30.1, 36.4] | 0.0001 | 0.0216   | bəli   |
| issai/Qwen3.5-4B-Base-Kazakh                          | morph    | 994  | 17.7% | 50.2% | 32.5pp | [29.4, 35.7] | 0.0001 | 0.0216   | bəli   |
| issai/Qwen3.5-4B-Base-Kazakh                          | lenient  | 994  | 17.9% | 50.2% | 32.3pp | [29.2, 35.4] | 0.0001 | 0.0216   | bəli   |
| issai/Qwen3.5-4B-Base-Kazakh                          | translit | 994  | 19.2% | 50.2% | 31.0pp | [28.0, 34.0] | 0.0001 | 0.0216   | bəli   |
| kurakurai/Luth-1.7B-Instruct                          | strict   | 1006 | 10.7% | 39.0% | 28.2pp | [25.4, 31.2] | 0.0001 | 0.0216   | bəli   |
| kurakurai/Luth-1.7B-Instruct                          | morph    | 1006 | 10.7% | 39.0% | 28.2pp | [25.4, 31.2] | 0.0001 | 0.0216   | bəli   |
| kurakurai/Luth-1.7B-Instruct                          | lenient  | 1006 | 11.1% | 39.0% | 27.8pp | [25.1, 30.8] | 0.0001 | 0.0216   | bəli   |
| kurakurai/Luth-1.7B-Instruct                          | translit | 1006 | 11.1% | 39.0% | 27.8pp | [25.1, 30.8] | 0.0001 | 0.0216   | bəli   |
| meta-llama/Meta-Llama-3-8B                            | strict   | 994  | 33.7% | 52.6% | 18.9pp | [16.4, 21.5] | 0.0001 | 0.0216   | bəli   |
| meta-llama/Meta-Llama-3-8B                            | morph    | 994  | 34.9% | 52.6% | 17.7pp | [15.1, 20.3] | 0.0001 | 0.0216   | bəli   |
| meta-llama/Meta-Llama-3-8B                            | lenient  | 994  | 35.1% | 52.6% | 17.5pp | [14.8, 20.1] | 0.0001 | 0.0216   | bəli   |
| meta-llama/Meta-Llama-3-8B                            | translit | 994  | 35.1% | 52.6% | 17.5pp | [14.8, 20.1] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-3.5-mini-instruct                       | strict   | 994  | 3.1%  | 46.6% | 43.5pp | [40.3, 46.5] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-3.5-mini-instruct                       | morph    | 994  | 3.3%  | 46.6% | 43.3pp | [40.1, 46.4] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-3.5-mini-instruct                       | lenient  | 994  | 3.3%  | 46.6% | 43.3pp | [40.1, 46.4] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-3.5-mini-instruct                       | translit | 994  | 3.3%  | 46.6% | 43.3pp | [40.1, 46.4] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-4-mini-instruct                         | strict   | 994  | 11.2% | 44.6% | 33.4pp | [30.4, 36.4] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-4-mini-instruct                         | morph    | 994  | 12.0% | 44.6% | 32.6pp | [29.5, 35.6] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-4-mini-instruct                         | lenient  | 994  | 12.2% | 44.6% | 32.4pp | [29.3, 35.4] | 0.0001 | 0.0216   | bəli   |
| microsoft/Phi-4-mini-instruct                         | translit | 994  | 12.2% | 44.6% | 32.4pp | [29.3, 35.4] | 0.0001 | 0.0216   | bəli   |
| mistralai/Mistral-7B-v0.1                             | strict   | 994  | 17.2% | 52.6% | 35.4pp | [32.5, 38.3] | 0.0001 | 0.0216   | bəli   |
| mistralai/Mistral-7B-v0.1                             | morph    | 994  | 17.8% | 52.6% | 34.8pp | [31.8, 37.8] | 0.0001 | 0.0216   | bəli   |
| mistralai/Mistral-7B-v0.1                             | lenient  | 994  | 18.2% | 52.7% | 34.5pp | [31.5, 37.5] | 0.0001 | 0.0216   | bəli   |
| mistralai/Mistral-7B-v0.1                             | translit | 994  | 18.2% | 52.7% | 34.5pp | [31.5, 37.5] | 0.0001 | 0.0216   | bəli   |
| openai:anthropic/claude-sonnet-5                      | strict   | 1006 | 65.5% | 71.0% | 5.5pp  | [3.0, 7.8]   | 0.0001 | 0.0216   | bəli   |
| openai:anthropic/claude-sonnet-5                      | morph    | 1006 | 67.6% | 71.0% | 3.4pp  | [1.0, 5.6]   | 0.0076 | 0.1064   | xeyr   |
| openai:anthropic/claude-sonnet-5                      | lenient  | 1006 | 67.9% | 71.1% | 3.2pp  | [0.9, 5.4]   | 0.0107 | 0.1177   | xeyr   |
| openai:anthropic/claude-sonnet-5                      | translit | 1006 | 67.9% | 71.1% | 3.2pp  | [0.9, 5.4]   | 0.0107 | 0.1177   | xeyr   |
| openai:deepseek/deepseek-v3.2                         | strict   | 1006 | 64.1% | 70.0% | 5.9pp  | [3.5, 8.3]   | 0.0001 | 0.0216   | bəli   |
| openai:deepseek/deepseek-v3.2                         | morph    | 1006 | 65.9% | 70.0% | 4.1pp  | [1.7, 6.6]   | 0.0018 | 0.0306   | bəli   |
| openai:deepseek/deepseek-v3.2                         | lenient  | 1006 | 66.6% | 70.1% | 3.5pp  | [1.2, 6.0]   | 0.0079 | 0.1064   | xeyr   |
| openai:deepseek/deepseek-v3.2                         | translit | 1006 | 66.6% | 70.1% | 3.5pp  | [1.2, 6.0]   | 0.0079 | 0.1064   | xeyr   |
| openai:meta-llama/llama-4-maverick                    | strict   | 1006 | 63.6% | 68.5% | 4.9pp  | [2.6, 7.5]   | 0.0002 | 0.0216   | bəli   |
| openai:meta-llama/llama-4-maverick                    | morph    | 1006 | 65.0% | 68.5% | 3.5pp  | [1.1, 6.1]   | 0.0062 | 0.0992   | xeyr   |
| openai:meta-llama/llama-4-maverick                    | lenient  | 1006 | 65.6% | 68.6% | 3.0pp  | [0.8, 5.5]   | 0.0181 | 0.1629   | xeyr   |
| openai:meta-llama/llama-4-maverick                    | translit | 1006 | 65.7% | 68.6% | 2.9pp  | [0.8, 5.4]   | 0.0231 | 0.1848   | xeyr   |
| openai:openai/gpt-4o                                  | strict   | 1006 | 66.7% | 70.4% | 3.7pp  | [1.0, 6.4]   | 0.0069 | 0.1035   | xeyr   |
| openai:openai/gpt-4o                                  | morph    | 1006 | 68.0% | 70.4% | 2.4pp  | [-0.2, 5.0]  | 0.0730 | 0.5109   | xeyr   |
| openai:openai/gpt-4o                                  | lenient  | 1006 | 68.4% | 70.4% | 2.0pp  | [-0.6, 4.6]  | 0.1389 | 0.8333   | xeyr   |
| openai:openai/gpt-4o                                  | translit | 1006 | 68.4% | 70.4% | 2.0pp  | [-0.6, 4.6]  | 0.1389 | 0.8333   | xeyr   |
| openai:qwen/qwen3-235b-a22b-2507                      | strict   | 1006 | 49.8% | 64.0% | 14.2pp | [11.1, 17.1] | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-235b-a22b-2507                      | morph    | 1006 | 50.9% | 64.0% | 13.1pp | [10.0, 16.0] | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-235b-a22b-2507                      | lenient  | 1006 | 51.4% | 64.0% | 12.6pp | [9.4, 15.5]  | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-235b-a22b-2507                      | translit | 1006 | 51.5% | 64.0% | 12.5pp | [9.3, 15.3]  | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-8b                                  | strict   | 1006 | 28.1% | 55.7% | 27.5pp | [24.6, 30.4] | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-8b                                  | morph    | 1006 | 29.2% | 55.7% | 26.4pp | [23.6, 29.3] | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-8b                                  | lenient  | 1006 | 29.2% | 55.7% | 26.4pp | [23.6, 29.3] | 0.0001 | 0.0216   | bəli   |
| openai:qwen/qwen3-8b                                  | translit | 1006 | 29.2% | 55.7% | 26.4pp | [23.6, 29.3] | 0.0001 | 0.0216   | bəli   |
| stabilityai/stablelm-2-1_6b-chat                      | strict   | 994  | 0.2%  | 7.6%  | 7.4pp  | [5.7, 9.1]   | 0.0001 | 0.0216   | bəli   |
| stabilityai/stablelm-2-1_6b-chat                      | morph    | 994  | 0.2%  | 7.6%  | 7.4pp  | [5.7, 9.1]   | 0.0001 | 0.0216   | bəli   |
| stabilityai/stablelm-2-1_6b-chat                      | lenient  | 994  | 0.2%  | 7.6%  | 7.4pp  | [5.7, 9.1]   | 0.0001 | 0.0216   | bəli   |
| stabilityai/stablelm-2-1_6b-chat                      | translit | 994  | 0.2%  | 7.6%  | 7.4pp  | [5.7, 9.1]   | 0.0001 | 0.0216   | bəli   |
| thelamapi/next-1b                                     | strict   | 994  | 2.7%  | 16.6% | 13.9pp | [11.7, 16.2] | 0.0001 | 0.0216   | bəli   |
| thelamapi/next-1b                                     | morph    | 994  | 2.7%  | 16.6% | 13.9pp | [11.7, 16.2] | 0.0001 | 0.0216   | bəli   |
| thelamapi/next-1b                                     | lenient  | 994  | 2.8%  | 16.7% | 13.9pp | [11.8, 16.2] | 0.0001 | 0.0216   | bəli   |
| thelamapi/next-1b                                     | translit | 994  | 2.8%  | 16.7% | 13.9pp | [11.8, 16.2] | 0.0001 | 0.0216   | bəli   |
| tiiuae/Falcon3-3B-Instruct                            | strict   | 994  | 1.4%  | 34.3% | 32.9pp | [29.9, 36.0] | 0.0001 | 0.0216   | bəli   |
| tiiuae/Falcon3-3B-Instruct                            | morph    | 994  | 1.4%  | 34.3% | 32.9pp | [29.9, 36.0] | 0.0001 | 0.0216   | bəli   |
| tiiuae/Falcon3-3B-Instruct                            | lenient  | 994  | 1.4%  | 34.3% | 32.9pp | [29.9, 36.0] | 0.0001 | 0.0216   | bəli   |
| tiiuae/Falcon3-3B-Instruct                            | translit | 994  | 1.4%  | 34.3% | 32.9pp | [29.9, 36.0] | 0.0001 | 0.0216   | bəli   |
| utter-project/EuroLLM-1.7B-Instruct                   | strict   | 994  | 0.1%  | 17.3% | 17.2pp | [14.9, 19.6] | 0.0001 | 0.0216   | bəli   |
| utter-project/EuroLLM-1.7B-Instruct                   | morph    | 994  | 0.1%  | 17.4% | 17.3pp | [15.0, 19.6] | 0.0001 | 0.0216   | bəli   |
| utter-project/EuroLLM-1.7B-Instruct                   | lenient  | 994  | 0.1%  | 17.4% | 17.3pp | [15.0, 19.6] | 0.0001 | 0.0216   | bəli   |
| utter-project/EuroLLM-1.7B-Instruct                   | translit | 994  | 0.1%  | 17.4% | 17.3pp | [15.0, 19.6] | 0.0001 | 0.0216   | bəli   |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | strict   | 994  | 23.5% | 44.0% | 20.4pp | [17.7, 23.3] | 0.0001 | 0.0216   | bəli   |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | morph    | 994  | 25.2% | 44.0% | 18.8pp | [16.2, 21.7] | 0.0001 | 0.0216   | bəli   |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | lenient  | 994  | 26.4% | 44.1% | 17.7pp | [15.0, 20.5] | 0.0001 | 0.0216   | bəli   |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | translit | 994  | 26.4% | 44.1% | 17.7pp | [15.0, 20.5] | 0.0001 | 0.0216   | bəli   |
