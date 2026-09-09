# data/raw/

Qaralama sətirlər buraya. `build` əmri bu qovluqdakı bütün `*.jsonl` fayllarını
birləşdirir, amma yekun datasetə **yalnız `verified_by: "human"` olan sətirləri** buraxır.

## `verified_by` dəyərləri

| Dəyər | Mənası |
|---|---|
| `llm-draft` | LLM tərəfindən tərcümə/qaralama edilib, hələ oxunmayıb |
| `pending` | əl ilə yazılıb, amma mənbə yoxlanılmayıb |
| `human` | sual, cavab və mənbə əl ilə yoxlanılıb — yekun datasetə keçir |

Sətri `human` etməzdən əvvəl:

1. Cavabın doğruluğu `source`-dakı mənbə ilə yoxlanılıb
2. `question_az` təbii Azərbaycan dilidir, hərfi tərcümə deyil (brief 4-cü bölmə:
   **tərcümə + lokallaşdırma**, sadəcə tərcümə yox)
3. Cavabın hallanmış formaları `answer_aliases`-ə əlavə olunub
   (məs. `answer: "Bakı"`, `answer_aliases: ["Bakıda", "Bakı şəhəri"]`)
4. `question_en` eyni faktı soruşur — cütləşdirilmiş AZ/EN müqayisəsi buna söykənir

## Etika

LLM-dən tərcümə və ya qaralama üçün istifadə edilibsə, bunu README-də və tezisdə
açıq yaz (brief 4-cü bölmə). `verified_by: "llm-draft"` izi məhz bunun üçün saxlanılır —
datasetin neçə faizinin LLM qaralamasından başladığını sonradan göstərə biləsən.
