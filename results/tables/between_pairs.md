# Cütlər arası: yazı, yoxsa başqa nə?

`analyze.py`-nin təsdiqləyici ailəsi cüt DAXİLİNDƏ ölçür. Bu cədvəl
cütlər ARASINDAKI iddianı sınayır və rəqib izahları eyni testdən
keçirir.

Test dəqiq permutasiyadır: qrup etiketləri bütün mümkün yollarla
paylanır, təxmin yoxdur.

Ölçülən cüt sayı: **10**.

| Cüt | Üslub | Artıq zərər | 95% CI | Zərər? | Yazı | Baza ailəsi |
|---|---|---|---|---|---|---|
| Kazakh 2 | `default` | +10.7pp | [+7.0, +14.3] | **bəli** | Cyrillic | Qwen |
| Kazakh 1 | `default` | +9.8pp | [+6.2, +13.4] | **bəli** | Cyrillic | Qwen |
| Latin 5 | `default` | +6.1pp | [+3.2, +9.2] | xeyr | Latin | Qwen |
| Russian 1 | `default` | +6.0pp | [+3.0, +8.9] | **bəli** | Cyrillic | Qwen |
| Russian 2 | `default` | +2.3pp | [-0.6, +5.2] | xeyr | Cyrillic | Qwen |
| Turkish 2 | `default` | +1.5pp | [-1.0, +4.5] | xeyr | Latin | Llama |
| Cyrillic 3 | `oneshot` | +0.1pp | [-2.9, +3.2] | xeyr | Cyrillic | Gemma |
| SEA | `default` | -1.2pp | [-3.3, +0.7] | xeyr | mixed | Qwen |
| Latin 3 | `default` | -3.1pp | [-6.1, -0.2] | xeyr | Latin | Gemma |
| Turkish 1 | `default` | -16.0pp | [-19.2, -12.8] | xeyr | Latin | Mistral |

## Rəqib izahlar, eyni testdə

Hər sətir bir izahı yoxlayır: həmin izahın zərər gözlədiyi cütlərin
artıq zərəri qalanlardan fərqlənirmi?

| İzah | Doğru proqnoz | Orta fərq | p (orta) | p (sıra) |
|---|---|---|---|---|
| hədəfin yazısı kirildir | 8/10 | +8.29pp | 0.0714 | 0.0952 |
| bazanın ailəsi Qwen-dir | 7/10 | +9.98pp | 0.0238 | 0.0381 |
| adaptasiya güclüdür (|AZ|+|EN| > 3.5) | 7/10 | +3.49pp | 0.5667 | 0.1714 |
| hədəf dil azərbaycancaya qohumdur | 7/10 | -0.21pp | 0.9667 | 0.6095 |

Bu bölgüdə iki tərəfli p-nin ala biləcəyi ƏN KİÇİK qiymət
**0.0040**-dir (252 düzülüş). Effekt nə qədər güclü olsa da,
bu dizayn ondan aşağı heç nə göstərə bilməz.

## Baza modeli konfaundu

Yazı izahı 8/10, baza ailəsi izahı 7/10 doğru proqnoz verir; p qiymətləri 0.0714 və 0.0238.

**Zərər verən cütlərin HAMISININ bazası Qwen-dir.** Bu, p
qiymətlərinin nə qədər yaxın olmasından asılı olmayan struktur
faktdır: dizayn yazı ilə baza ailəsini tam ayıra bilmir.

Ayırıcı təcrübə **Qwen bazası + latın hədəf**dir. Yazı izahı
orada zərər GÖZLƏMİR, baza izahı GÖZLƏYİR. Macar cütü
(`Racka-4B`, Qwen3-4B üzərində, latın hədəf) məhz bu idi və
sual-təkrarı qapısından keçmədi, yəni məsələni həll edəcək cüt
artıq tapılmışdı, sadəcə ölçülə bilmədi.

İkinci yol: Qwen olmayan bazada zərər VERƏN kiril cütü. Hazırda
yeganə Qwen olmayan kiril cütü (gemma + ukraynaca) zərər vermir,
yəni o, baza izahının proqnozuna da uyğun gəlir.

## Üslub seçiminə həssaslıq

Bir cüt hər iki üslubda ölçülə bilər. Hansının götürülməsi
NƏTİCƏNİ DƏYİŞİR, ona görə hər iki qayda hesablanır.

| Qayda | Cüt | Yazı izahı doğru | p (orta) | Qwen izahı doğru | p (orta) |
|---|---|---|---|---|---|
| `default` üstün | 10 | 8/10 | 0.0714 | 7/10 | 0.0238 |
| `oneshot` üstün | 10 | 9/10 | 0.0238 | 8/10 | 0.0143 |

Sayım qayda ilə dəyişir, İŞARƏ dəyişmir. Məqalə iddianı ona görə
istiqamət və əhəmiyyət səviyyəsində saxlayır, kəmiyyət səviyyəsində
yox.

