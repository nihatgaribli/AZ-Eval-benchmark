# Normalizasiya rejimləri — RQ3 dekompozisiyası

| Model                                                 | Dil | STRICT | MORPH | LENIENT | TRANSLIT | morfologiya | diakritika | yazı sistemi |
|-------------------------------------------------------|-----|--------|-------|---------|----------|-------------|------------|--------------|
| CohereLabs/aya-expanse-8b                             | AZ  | 11.2%  | 11.8% | 12.0%   | 12.0%    | +0.6pp      | +0.2pp     | +0.0pp       |
| CohereLabs/aya-expanse-8b                             | EN  | 47.4%  | 47.4% | 47.4%   | 47.4%    | +0.0pp      | +0.0pp     | +0.0pp       |
| GiorgiGE/Kolkha-Mini-Georgian                         | AZ  | 0.1%   | 0.1%  | 0.1%    | 0.1%     | +0.0pp      | +0.0pp     | +0.0pp       |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | AZ  | 16.2%  | 16.6% | 16.9%   | 16.9%    | +0.4pp      | +0.3pp     | +0.0pp       |
| HiTZ/Latxa-Qwen3-VL-4B-Instruct                       | EN  | 49.8%  | 49.8% | 49.8%   | 49.8%    | +0.0pp      | +0.0pp     | +0.0pp       |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | AZ  | 0.0%   | 0.0%  | 0.0%    | 0.0%     | +0.0pp      | +0.0pp     | +0.0pp       |
| HuggingFaceTB/SmolLM2-1.7B-Instruct                   | EN  | 24.7%  | 24.7% | 24.7%   | 24.7%    | +0.0pp      | +0.0pp     | +0.0pp       |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | AZ  | 20.2%  | 21.6% | 21.9%   | 21.9%    | +1.4pp      | +0.3pp     | +0.0pp       |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0 (oneshot) | EN  | 47.0%  | 47.0% | 47.1%   | 47.1%    | +0.0pp      | +0.1pp     | +0.0pp       |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | AZ  | 13.7%  | 14.5% | 14.6%   | 14.6%    | +0.8pp      | +0.1pp     | +0.0pp       |
| INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0           | EN  | 47.0%  | 47.0% | 47.1%   | 47.1%    | +0.0pp      | +0.1pp     | +0.0pp       |
| NbAiLab/borealis-4b (oneshot)                         | AZ  | 21.5%  | 23.0% | 23.3%   | 23.3%    | +1.5pp      | +0.3pp     | +0.0pp       |
| NbAiLab/borealis-4b (oneshot)                         | EN  | 45.1%  | 45.1% | 45.1%   | 45.1%    | +0.0pp      | +0.0pp     | +0.0pp       |
| NbAiLab/borealis-4b                                   | AZ  | 22.6%  | 24.1% | 24.4%   | 24.4%    | +1.5pp      | +0.3pp     | +0.0pp       |
| NbAiLab/borealis-4b                                   | EN  | 45.3%  | 45.3% | 45.3%   | 45.3%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-1.7B                                       | AZ  | 6.5%   | 6.7%  | 7.0%    | 7.0%     | +0.2pp      | +0.3pp     | +0.0pp       |
| Qwen/Qwen3-1.7B                                       | EN  | 28.6%  | 28.6% | 28.7%   | 28.7%    | +0.0pp      | +0.1pp     | +0.0pp       |
| Qwen/Qwen3-4B (oneshot)                               | AZ  | 23.9%  | 24.8% | 25.2%   | 25.4%    | +0.9pp      | +0.5pp     | +0.2pp       |
| Qwen/Qwen3-4B (oneshot)                               | EN  | 47.2%  | 47.2% | 47.2%   | 47.2%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-4B                                         | AZ  | 20.1%  | 21.0% | 21.4%   | 21.5%    | +0.9pp      | +0.4pp     | +0.1pp       |
| Qwen/Qwen3-4B                                         | EN  | 45.4%  | 45.5% | 45.5%   | 45.5%    | +0.1pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | AZ  | 25.5%  | 26.0% | 26.3%   | 26.3%    | +0.5pp      | +0.3pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (oneshot)                   | EN  | 55.3%  | 55.3% | 55.3%   | 55.3%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | AZ  | 26.0%  | 26.5% | 26.7%   | 26.7%    | +0.5pp      | +0.2pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (plain)                     | EN  | 54.4%  | 54.4% | 54.4%   | 54.4%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | AZ  | 28.1%  | 28.7% | 29.0%   | 29.0%    | +0.6pp      | +0.3pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct (zeroshot)                  | EN  | 54.7%  | 54.7% | 54.7%   | 54.7%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct                             | AZ  | 27.1%  | 27.6% | 27.8%   | 27.8%    | +0.5pp      | +0.2pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Instruct                             | EN  | 54.6%  | 54.6% | 54.6%   | 54.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | AZ  | 24.3%  | 25.7% | 26.3%   | 26.3%    | +1.3pp      | +0.6pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (oneshot)                   | EN  | 55.3%  | 55.3% | 55.3%   | 55.3%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | AZ  | 23.5%  | 24.4% | 24.6%   | 24.6%    | +0.9pp      | +0.2pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (plain)                     | EN  | 46.6%  | 46.6% | 46.6%   | 46.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | AZ  | 8.6%   | 8.8%  | 8.9%    | 8.9%     | +0.2pp      | +0.1pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking (zeroshot)                  | EN  | 7.1%   | 7.2%  | 7.2%    | 7.2%     | +0.1pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking                             | AZ  | 27.9%  | 29.1% | 29.6%   | 29.6%    | +1.2pp      | +0.5pp     | +0.0pp       |
| Qwen/Qwen3-VL-4B-Thinking                             | EN  | 55.2%  | 55.2% | 55.2%   | 55.2%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Qwen/Qwen3.5-4B-Base                                  | AZ  | 37.5%  | 38.7% | 39.0%   | 39.0%    | +1.2pp      | +0.3pp     | +0.0pp       |
| Qwen/Qwen3.5-4B-Base                                  | EN  | 60.0%  | 60.0% | 60.0%   | 60.0%    | +0.0pp      | +0.0pp     | +0.0pp       |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | AZ  | 15.2%  | 15.7% | 16.1%   | 17.0%    | +0.5pp      | +0.4pp     | +0.9pp       |
| RefalMachine/RuadaptQwen3-4B-Hybrid (oneshot)         | EN  | 48.7%  | 48.7% | 48.7%   | 48.7%    | +0.0pp      | +0.0pp     | +0.0pp       |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | AZ  | 17.2%  | 17.8% | 18.0%   | 18.7%    | +0.6pp      | +0.2pp     | +0.7pp       |
| RefalMachine/RuadaptQwen3-4B-Hybrid                   | EN  | 48.5%  | 48.5% | 48.5%   | 48.5%    | +0.0pp      | +0.0pp     | +0.0pp       |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | AZ  | 6.3%   | 6.6%  | 6.8%    | 6.8%     | +0.3pp      | +0.2pp     | +0.0pp       |
| Trendyol/Trendyol-LLM-7b-base-v1.0                    | EN  | 25.8%  | 26.3% | 26.4%   | 26.4%    | +0.5pp      | +0.1pp     | +0.0pp       |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | AZ  | 16.7%  | 17.7% | 17.8%   | 18.5%    | +1.0pp      | +0.1pp     | +0.7pp       |
| Vikhrmodels/QVikhr-3-4B-Instruction (oneshot)         | EN  | 48.0%  | 48.1% | 48.1%   | 48.1%    | +0.1pp      | +0.0pp     | +0.0pp       |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | AZ  | 18.3%  | 18.7% | 18.8%   | 19.5%    | +0.4pp      | +0.1pp     | +0.7pp       |
| Vikhrmodels/QVikhr-3-4B-Instruction                   | EN  | 45.9%  | 46.0% | 46.0%   | 46.0%    | +0.1pp      | +0.0pp     | +0.0pp       |
| ai-forever/mGPT                                       | AZ  | 5.6%   | 6.5%  | 6.5%    | 6.5%     | +0.9pp      | +0.0pp     | +0.0pp       |
| ai-forever/mGPT                                       | EN  | 14.7%  | 14.7% | 15.0%   | 15.0%    | +0.0pp      | +0.3pp     | +0.0pp       |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | AZ  | 26.6%  | 27.3% | 27.8%   | 27.8%    | +0.7pp      | +0.5pp     | +0.0pp       |
| aisingapore/Qwen-SEA-LION-v4-4B-VL (oneshot)          | EN  | 55.6%  | 55.6% | 55.6%   | 55.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | AZ  | 28.5%  | 29.1% | 29.3%   | 29.3%    | +0.6pp      | +0.2pp     | +0.0pp       |
| aisingapore/Qwen-SEA-LION-v4-4B-VL                    | EN  | 54.8%  | 54.8% | 54.8%   | 54.8%    | +0.0pp      | +0.0pp     | +0.0pp       |
| bigscience/bloomz-1b7                                 | AZ  | 0.0%   | 0.0%  | 0.0%    | 0.0%     | +0.0pp      | +0.0pp     | +0.0pp       |
| bigscience/bloomz-1b7                                 | EN  | 3.9%   | 3.9%  | 3.9%    | 3.9%     | +0.0pp      | +0.0pp     | +0.0pp       |
| elte-nlp/Racka-4B                                     | AZ  | 10.8%  | 11.0% | 11.2%   | 11.2%    | +0.2pp      | +0.2pp     | +0.0pp       |
| elte-nlp/Racka-4B                                     | EN  | 23.1%  | 23.1% | 23.3%   | 23.3%    | +0.0pp      | +0.2pp     | +0.0pp       |
| google/gemma-3-4b-it (oneshot)                        | AZ  | 21.4%  | 22.5% | 22.7%   | 22.7%    | +1.1pp      | +0.2pp     | +0.0pp       |
| google/gemma-3-4b-it (oneshot)                        | EN  | 48.1%  | 48.1% | 48.1%   | 48.1%    | +0.0pp      | +0.0pp     | +0.0pp       |
| google/gemma-3-4b-it                                  | AZ  | 20.5%  | 21.5% | 21.9%   | 21.9%    | +1.0pp      | +0.4pp     | +0.0pp       |
| google/gemma-3-4b-it                                  | EN  | 46.9%  | 46.9% | 46.9%   | 46.9%    | +0.0pp      | +0.0pp     | +0.0pp       |
| ibm-granite/granite-3.1-2b-instruct                   | AZ  | 0.3%   | 0.3%  | 0.3%    | 0.3%     | +0.0pp      | +0.0pp     | +0.0pp       |
| ibm-granite/granite-3.1-2b-instruct                   | EN  | 32.2%  | 32.2% | 32.2%   | 32.2%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qolda-AVL-5B (oneshot)                          | AZ  | 5.2%   | 5.2%  | 5.2%    | 9.7%     | +0.0pp      | +0.0pp     | +4.4pp       |
| issai/Qolda-AVL-5B (oneshot)                          | EN  | 45.4%  | 45.4% | 45.4%   | 45.4%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qolda-AVL-5B (plain)                            | AZ  | 3.9%   | 4.1%  | 4.1%    | 8.1%     | +0.2pp      | +0.0pp     | +4.0pp       |
| issai/Qolda-AVL-5B (plain)                            | EN  | 40.7%  | 40.7% | 40.7%   | 40.7%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qolda-AVL-5B (script)                           | AZ  | 5.0%   | 5.2%  | 5.2%    | 9.9%     | +0.2pp      | +0.0pp     | +4.6pp       |
| issai/Qolda-AVL-5B (script)                           | EN  | 41.4%  | 41.4% | 41.4%   | 41.4%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qolda-AVL-5B (zeroshot)                         | AZ  | 11.7%  | 11.8% | 11.8%   | 15.6%    | +0.1pp      | +0.0pp     | +3.8pp       |
| issai/Qolda-AVL-5B (zeroshot)                         | EN  | 41.0%  | 41.0% | 41.0%   | 41.0%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qolda-AVL-5B                                    | AZ  | 4.4%   | 4.4%  | 4.4%    | 9.2%     | +0.0pp      | +0.0pp     | +4.7pp       |
| issai/Qolda-AVL-5B                                    | EN  | 41.5%  | 41.5% | 41.5%   | 41.5%    | +0.0pp      | +0.0pp     | +0.0pp       |
| issai/Qwen3.5-4B-Base-Kazakh                          | AZ  | 17.1%  | 17.7% | 17.9%   | 19.2%    | +0.6pp      | +0.2pp     | +1.3pp       |
| issai/Qwen3.5-4B-Base-Kazakh                          | EN  | 50.2%  | 50.2% | 50.2%   | 50.2%    | +0.0pp      | +0.0pp     | +0.0pp       |
| kurakurai/Luth-1.7B-Instruct                          | AZ  | 10.7%  | 10.7% | 11.1%   | 11.1%    | +0.0pp      | +0.4pp     | +0.0pp       |
| kurakurai/Luth-1.7B-Instruct                          | EN  | 39.0%  | 39.0% | 39.0%   | 39.0%    | +0.0pp      | +0.0pp     | +0.0pp       |
| meta-llama/Meta-Llama-3-8B                            | AZ  | 33.7%  | 34.9% | 35.1%   | 35.1%    | +1.2pp      | +0.2pp     | +0.0pp       |
| meta-llama/Meta-Llama-3-8B                            | EN  | 52.6%  | 52.6% | 52.6%   | 52.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| microsoft/Phi-3.5-mini-instruct                       | AZ  | 3.1%   | 3.3%  | 3.3%    | 3.3%     | +0.2pp      | +0.0pp     | +0.0pp       |
| microsoft/Phi-3.5-mini-instruct                       | EN  | 46.6%  | 46.6% | 46.6%   | 46.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| microsoft/Phi-4-mini-instruct                         | AZ  | 11.2%  | 12.0% | 12.2%   | 12.2%    | +0.8pp      | +0.2pp     | +0.0pp       |
| microsoft/Phi-4-mini-instruct                         | EN  | 44.6%  | 44.6% | 44.6%   | 44.6%    | +0.0pp      | +0.0pp     | +0.0pp       |
| mistralai/Mistral-7B-v0.1                             | AZ  | 17.2%  | 17.8% | 18.2%   | 18.2%    | +0.6pp      | +0.4pp     | +0.0pp       |
| mistralai/Mistral-7B-v0.1                             | EN  | 52.6%  | 52.6% | 52.7%   | 52.7%    | +0.0pp      | +0.1pp     | +0.0pp       |
| openai:anthropic/claude-sonnet-5                      | AZ  | 65.5%  | 67.6% | 67.9%   | 67.9%    | +2.1pp      | +0.3pp     | +0.0pp       |
| openai:anthropic/claude-sonnet-5                      | EN  | 71.0%  | 71.0% | 71.1%   | 71.1%    | +0.0pp      | +0.1pp     | +0.0pp       |
| openai:deepseek/deepseek-v3.2                         | AZ  | 64.1%  | 65.9% | 66.6%   | 66.6%    | +1.8pp      | +0.7pp     | +0.0pp       |
| openai:deepseek/deepseek-v3.2                         | EN  | 70.0%  | 70.0% | 70.1%   | 70.1%    | +0.0pp      | +0.1pp     | +0.0pp       |
| openai:meta-llama/llama-4-maverick                    | AZ  | 63.6%  | 65.0% | 65.6%   | 65.7%    | +1.4pp      | +0.6pp     | +0.1pp       |
| openai:meta-llama/llama-4-maverick                    | EN  | 68.5%  | 68.5% | 68.6%   | 68.6%    | +0.0pp      | +0.1pp     | +0.0pp       |
| openai:openai/gpt-4o                                  | AZ  | 66.7%  | 68.0% | 68.4%   | 68.4%    | +1.3pp      | +0.4pp     | +0.0pp       |
| openai:openai/gpt-4o                                  | EN  | 70.4%  | 70.4% | 70.4%   | 70.4%    | +0.0pp      | +0.0pp     | +0.0pp       |
| openai:qwen/qwen3-235b-a22b-2507                      | AZ  | 49.8%  | 50.9% | 51.4%   | 51.5%    | +1.1pp      | +0.5pp     | +0.1pp       |
| openai:qwen/qwen3-235b-a22b-2507                      | EN  | 64.0%  | 64.0% | 64.0%   | 64.0%    | +0.0pp      | +0.0pp     | +0.0pp       |
| openai:qwen/qwen3-8b                                  | AZ  | 28.1%  | 29.2% | 29.2%   | 29.2%    | +1.1pp      | +0.0pp     | +0.0pp       |
| openai:qwen/qwen3-8b                                  | EN  | 55.7%  | 55.7% | 55.7%   | 55.7%    | +0.0pp      | +0.0pp     | +0.0pp       |
| stabilityai/stablelm-2-1_6b-chat                      | AZ  | 0.2%   | 0.2%  | 0.2%    | 0.2%     | +0.0pp      | +0.0pp     | +0.0pp       |
| stabilityai/stablelm-2-1_6b-chat                      | EN  | 7.6%   | 7.6%  | 7.6%    | 7.6%     | +0.0pp      | +0.0pp     | +0.0pp       |
| thelamapi/next-1b                                     | AZ  | 2.7%   | 2.7%  | 2.8%    | 2.8%     | +0.0pp      | +0.1pp     | +0.0pp       |
| thelamapi/next-1b                                     | EN  | 16.6%  | 16.6% | 16.7%   | 16.7%    | +0.0pp      | +0.1pp     | +0.0pp       |
| tiiuae/Falcon3-3B-Instruct                            | AZ  | 1.4%   | 1.4%  | 1.4%    | 1.4%     | +0.0pp      | +0.0pp     | +0.0pp       |
| tiiuae/Falcon3-3B-Instruct                            | EN  | 34.3%  | 34.3% | 34.3%   | 34.3%    | +0.0pp      | +0.0pp     | +0.0pp       |
| utter-project/EuroLLM-1.7B-Instruct                   | AZ  | 0.1%   | 0.1%  | 0.1%    | 0.1%     | +0.0pp      | +0.0pp     | +0.0pp       |
| utter-project/EuroLLM-1.7B-Instruct                   | EN  | 17.3%  | 17.4% | 17.4%   | 17.4%    | +0.1pp      | +0.0pp     | +0.0pp       |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | AZ  | 23.5%  | 25.2% | 26.4%   | 26.4%    | +1.6pp      | +1.2pp     | +0.0pp       |
| ytu-ce-cosmos/Turkish-Llama-8b-v0.1                   | EN  | 44.0%  | 44.0% | 44.1%   | 44.1%    | +0.0pp      | +0.1pp     | +0.0pp       |
