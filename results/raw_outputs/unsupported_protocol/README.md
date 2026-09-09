# Protokolu dəstəkləməyən endpoint-lər

Buradakı fayllar BOŞDUR və bu, modelin uğursuzluğu deyil, endpoint-in
məhdudiyyətidir.

## Nə baş verdi

`openai/gpt-5` çağırışları 400 xətası ilə rədd olundu:

    Reasoning is mandatory for this endpoint and cannot be disabled.

Yəni model düşünməni söndürməyə icazə vermir. Parametr göndərilməsə, çağırış
qəbul edilir, amma bütün token büdcəsi daxili mühakiməyə gedir və cavab boş
qayıdır (64 token sınandı, məzmun boş).

Eyni davranış `openai/gpt-5-mini` və `google/gemini-3.1-pro-preview`
modellərində də ölçüldü.

## Niyə büdcə artırılmadı

Layihənin bütün qaçışları 32 token limiti ilə aparılır. Bir modelə fərqli
büdcə vermək onu qalan 28 modellə müqayisə edilməz edərdi. Şərait ya hamı
üçün eynidir, ya da müqayisə yoxdur.

## Nəticə

`gpt-5` əvəzinə `openai/gpt-4o` işlədildi: OpenAI-ı təmsil edir, düşünməyən
modeldir və protokola uyğundur.

BU, ÖZÜ DƏ QEYD EDİLMƏYƏ DƏYƏR TAPINTIDIR. Bir sıra yeni frontier
endpoint-lər qısa cavab protokolunu dəstəkləmir, çünki düşünmə məcburidir.
Bu, benchmark qaçırmaq istəyən hər kəsə aid praktik məhdudiyyətdir.
