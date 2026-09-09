# Əlifba fərziyyəsi

Dataset: `data\az_eval_v0.jsonl` | ortaq sual: 484 | seed: 0 | bootstrap: 1000

Bütün müqayisələr cütləşdirilib və eyni sual dəsti üzərində aparılıb.

## 2x2 bir baxışda

| Model (STRICT / TRANSLIT) | Adi prompt    | Latın tələbi  |
|---------------------------|---------------|---------------|
| Qwen/Qwen3-VL-4B-Thinking | 10.5% / 11.2% | 11.4% / 12.2% |
| issai/Qolda-AVL-5B        | 3.3% / 10.5%  | 3.5% / 10.5%  |

## Analiz 1: normalizasiya nərdivanı

| Model                              | Prompt  | Zəncir   | EM    | 95% CI      |
|------------------------------------|---------|----------|-------|-------------|
| Qwen/Qwen3-VL-4B-Thinking          | default | strict   | 10.5% | [7.6, 13.6] |
| Qwen/Qwen3-VL-4B-Thinking          | default | morph    | 11.0% | [8.1, 14.0] |
| Qwen/Qwen3-VL-4B-Thinking          | default | lenient  | 11.2% | [8.3, 14.0] |
| Qwen/Qwen3-VL-4B-Thinking          | default | translit | 11.2% | [8.3, 14.0] |
| Qwen/Qwen3-VL-4B-Thinking (script) | script  | strict   | 11.4% | [8.5, 14.5] |
| Qwen/Qwen3-VL-4B-Thinking (script) | script  | morph    | 11.8% | [8.9, 14.9] |
| Qwen/Qwen3-VL-4B-Thinking (script) | script  | lenient  | 12.2% | [9.3, 15.3] |
| Qwen/Qwen3-VL-4B-Thinking (script) | script  | translit | 12.2% | [9.3, 15.3] |
| issai/Qolda-AVL-5B                 | default | strict   | 3.3%  | [1.9, 5.0]  |
| issai/Qolda-AVL-5B                 | default | morph    | 3.3%  | [1.9, 5.0]  |
| issai/Qolda-AVL-5B                 | default | lenient  | 3.3%  | [1.9, 5.0]  |
| issai/Qolda-AVL-5B                 | default | translit | 10.5% | [7.9, 13.2] |
| issai/Qolda-AVL-5B (script)        | script  | strict   | 3.5%  | [1.9, 5.2]  |
| issai/Qolda-AVL-5B (script)        | script  | morph    | 3.9%  | [2.3, 5.8]  |
| issai/Qolda-AVL-5B (script)        | script  | lenient  | 3.9%  | [2.3, 5.8]  |
| issai/Qolda-AVL-5B (script)        | script  | translit | 10.5% | [8.1, 13.4] |

## Analiz 1: fərq və bağlanan pay

| Prompt  | Zəncir   | Baza EM | Qolda EM | Fərq   | 95% CI      | Bağlanan pay | p      | p (Holm) | Mənalı |
|---------|----------|---------|----------|--------|-------------|--------------|--------|----------|--------|
| default | strict   | 10.5%   | 3.3%     | +7.2pp | [4.8, 9.7]  | 0%           | 0.0001 | 0.0008   | bəli   |
| default | morph    | 11.0%   | 3.3%     | +7.6pp | [5.2, 10.1] | -6%          | 0.0001 | 0.0008   | bəli   |
| default | lenient  | 11.2%   | 3.3%     | +7.9pp | [5.4, 10.5] | -9%          | 0.0001 | 0.0008   | bəli   |
| default | translit | 11.2%   | 10.5%    | +0.6pp | [-1.9, 3.1] | 91%          | 0.7569 | 0.7569   | xeyr   |
| script  | strict   | 11.4%   | 3.5%     | +7.9pp | [5.2, 10.5] | 0%           | 0.0001 | 0.0008   | bəli   |
| script  | morph    | 11.8%   | 3.9%     | +7.9pp | [5.2, 10.5] | 0%           | 0.0001 | 0.0008   | bəli   |
| script  | lenient  | 12.2%   | 3.9%     | +8.3pp | [5.6, 11.0] | -5%          | 0.0001 | 0.0008   | bəli   |
| script  | translit | 12.2%   | 10.5%    | +1.7pp | [-1.0, 4.3] | 79%          | 0.2825 | 0.5649   | xeyr   |

_Holm ailəsi: 8 test._

## Analiz 2: latın tələbinin təsiri

| Model                     | Zəncir   | Adi prompt | Latın tələbi | Fərq   | 95% CI      | p      | p (Holm) | Mənalı |
|---------------------------|----------|------------|--------------|--------|-------------|--------|----------|--------|
| Qwen/Qwen3-VL-4B-Thinking | strict   | 10.5%      | 11.4%        | +0.8pp | [-0.6, 2.3] | 0.3955 | 1.0000   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking | morph    | 11.0%      | 11.8%        | +0.8pp | [-0.6, 2.3] | 0.3955 | 1.0000   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking | lenient  | 11.2%      | 12.2%        | +1.0pp | [-0.4, 2.5] | 0.2751 | 1.0000   | xeyr   |
| Qwen/Qwen3-VL-4B-Thinking | translit | 11.2%      | 12.2%        | +1.0pp | [-0.4, 2.5] | 0.2751 | 1.0000   | xeyr   |
| issai/Qolda-AVL-5B        | strict   | 3.3%       | 3.5%         | +0.2pp | [0.0, 0.6]  | 1.0000 | 1.0000   | xeyr   |
| issai/Qolda-AVL-5B        | morph    | 3.3%       | 3.9%         | +0.6pp | [0.0, 1.4]  | 0.2577 | 1.0000   | xeyr   |
| issai/Qolda-AVL-5B        | lenient  | 3.3%       | 3.9%         | +0.6pp | [0.0, 1.4]  | 0.2577 | 1.0000   | xeyr   |
| issai/Qolda-AVL-5B        | translit | 10.5%      | 10.5%        | +0.0pp | [-1.2, 1.4] | 1.0000 | 1.0000   | xeyr   |

_Holm ailəsi: 8 test._

## Yazı sistemi (zəncirdən asılı deyil)

| Model                     | Prompt  | Kiril | Latın | Kiril payı |
|---------------------------|---------|-------|-------|------------|
| Qwen/Qwen3-VL-4B-Thinking | default | 2     | 482   | 0.4%       |
| Qwen/Qwen3-VL-4B-Thinking | script  | 2     | 482   | 0.4%       |
| issai/Qolda-AVL-5B        | default | 444   | 40    | 91.7%      |
| issai/Qolda-AVL-5B        | script  | 430   | 54    | 88.8%      |
