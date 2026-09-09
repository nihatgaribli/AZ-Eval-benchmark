# Nə üçün bu qovluq var

Buradakı qaçışlar SƏHV DEYİL, amma CÜTÜN DİGƏR YARISI İLƏ MÜQAYİSƏ EDİLƏ
BİLMİR. Silinmirlər, çünki nə baş verdiyini göstərirlər.

## Problem

`run_eval` chat şablonunu yalnız modeldə varsa tətbiq edir. Fine-tune cütünün
iki yarısında şablon vəziyyəti fərqli ola bilər və o zaman iki model FƏRQLİ
şəraitdə soruşulur. Cüt müqayisəsinin bütün mənası isə şəraitin eyni
olmasıdır.

    Türk 1   Mistral-7B-v0.1 şablon YOX  ->  Trendyol şablon VAR
    Qazax 1  Qwen3-VL-4B-Thinking VAR    ->  Qolda-AVL-5B YOX
    Qazax 2  Qwen3.5-4B-Base VAR         ->  Qwen3.5-4B-Base-Kazakh YOX

Birincisində simptom kəskin idi (Trendyol ingiliscə 0.0% aldı) və dərhal
tutuldu. Qazax cütlərində isə simptom SƏSSİZ idi: ballar məqbul görünürdü,
sadəcə iki model eyni sualı fərqli formatda alırdı.

## Düzəliş

Köklənmiş modellərdə şablon olmadığına görə simmetrik şərait XAM PROMPTdur.
Baza modelləri `--no-chat-template` ilə yenidən qaçırıldı.

Ölçüldü, çünki düzəlişin nəticəyə təsiri əvvəlcədən bilinmirdi:

    Qazax 1  artıq zərər  +11.9pp -> +10.3pp
    Qazax 2  artıq zərər   +5.5pp ->  +7.8pp

İki cüt ƏKS istiqamətə hərəkət etdi və hər ikisi güclü müsbət qaldı, yəni
asimmetriya nəticəni sistematik şəkildə şişirtmirmiş.

Gözlənilməyəni: HƏR İKİ baza modeli şablonSUZ daha yaxşı bal aldı
(`Qwen3.5-4B-Base` AZ 30.2% -> 36.1%). `Qwen3.5-4B-Base` təlimat modeli
deyil, xam mətn davamı üzərində öyrədilib; ona instruksiya şablonu geydirmək
onu pisləşdirir. Deməli güzəşt yoxdur: xam variant həm simmetrikdir, həm də
daha yaxşıdır.

## Təkrarlanmasın deyə

`TransformersBackend.describe()` artıq hər sətrə yazır:
`chat_template_requested`, `chat_template_available`, `chat_template_applied`.
Əvvəl bu görünmürdü, çünki `prompt` sahəsi şablondan ƏVVƏLKİ mətni saxlayır.
`tests/test_chat_template_record.py` bunu kilidləyir.
