# Fine-tune cütləri: qohumluq, yoxsa əlifba?

| Cüt | Hədəf | Yazı | AZ baza | AZ köklənmiş | AZ itkisi | EN itkisi |
|---|---|---|---|---|---|---|
| Qazax 1 | qazax | kiril | 27.9% | 4.4% | +23.4pp | +13.7pp |
| Qazax 2 | qazax | kiril | 37.5% | 17.1% | +20.4pp | +9.9pp |
| Türk 1 | türk | latın | 17.2% | 6.3% | +10.9pp | +26.9pp |
| Türk 2 | türk | latın | 33.7% | 23.5% | +10.2pp | +8.7pp |
| Rus 1 (ağır) | rus | kiril | 20.0% | 17.2% | +2.8pp | -3.1pp |
| Rus 2 (yüngül) | rus | kiril | 20.0% | 18.3% | +1.7pp | -0.5pp |
| Latın 3 (qeyri-türk) | norveç | latın | 20.5% | 21.6% | -1.1pp | +2.0pp |
| SEA (qarışıq yazı) | cənub-şərqi asiya | qarışıq | 27.1% | 28.2% | -1.1pp | +0.1pp |

## Qapıdan keçməyən cütlər

Bu cütlər ELAN EDİLİB, amma ölçmə etibarlı olmadığı üçün
cədvəllərə girmir. Rəqəmləri gizlətmək yox, onları ölçmə kimi
təqdim etməmək üçün.

| Cüt | Səbəb |
|---|---|
| Kiril 3 (qeyri-qazax) | `INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0` [az] nümunə təkrarı qapısından keçmir: 68.2% |
| Gürcü (qeyri-latın, qeyri-kiril) | `GiorgiGE/Kolkha-Mini-Georgian` [en] çıxarış qapısından keçmir: səhvlərin 42.4%-ində cavab xam mətndədir |
| Macar (latın, eyni baza) | `elte-nlp/Racka-4B` [az] sual təkrarı qapısından keçmir: 68.4% |

## Artıq zərər: AZ itkisi eksi EN itkisi

İngilis itkisi ümumi unutqanlığın ölçüsüdür. Fərq isə azərbaycancanın
ondan ƏLAVƏ nə qədər zərər gördüyünü verir. Mütləq AZ itkisinə baxmaq
kifayət etmir: hər fine-tune bir qədər unutdurur.

| Cüt | Yazı | Artıq zərər | 95% CI | Nəticə |
|---|---|---|---|---|
| Qazax 1 | kiril | +9.8pp | [+6.2, +13.4] | azərbaycanca ƏLAVƏ zərər |
| Qazax 2 | kiril | +10.6pp | [+7.0, +14.2] | azərbaycanca ƏLAVƏ zərər |
| Türk 1 | latın | -16.0pp | [-19.2, -12.8] | azərbaycanca nisbətən QORUNUB |
| Türk 2 | latın | +1.5pp | [-1.0, +4.5] | fərq sıfırdan ayırd edilmir |
| Rus 1 (ağır) | kiril | +5.9pp | [+2.9, +8.8] | azərbaycanca ƏLAVƏ zərər |
| Rus 2 (yüngül) | kiril | +2.2pp | [-0.7, +5.1] | fərq sıfırdan ayırd edilmir |
| Latın 3 (qeyri-türk) | latın | -3.1pp | [-6.1, -0.2] | azərbaycanca nisbətən QORUNUB |
| SEA (qarışıq yazı) | qarışıq | -1.2pp | [-3.3, +0.7] | fərq sıfırdan ayırd edilmir |

## Transliterasiya və yazı sistemi

| Cüt | AZ itkisi (STRICT) | AZ itkisi (TRANSLIT) | Köklənmişin kiril payı |
|---|---|---|---|
| Qazax 1 | +23.4pp | +20.4pp | 85.9% |
| Qazax 2 | +20.4pp | +19.8pp | 18.9% |
| Türk 1 | +10.9pp | +11.4pp | 0.0% |
| Türk 2 | +10.2pp | +8.8pp | 0.0% |
| Rus 1 (ağır) | +2.8pp | +2.7pp | 8.6% |
| Rus 2 (yüngül) | +1.7pp | +1.9pp | 7.4% |
| Latın 3 (qeyri-türk) | -1.1pp | -1.5pp | 0.0% |
| SEA (qarışıq yazı) | -1.1pp | -1.2pp | 0.2% |

## Təsdiqləyici ailə

Aşağıdakı cədvəl Holm düzəlişini YALNIZ əvvəlcədən elan edilmiş cütlər
üzərində aparır. `analyze.py` cədvəlləri isə gördüyü hər model cütünü
sınayır; 14 model əlavə olunanda həmin ailə 474 testə çatdı və əsas
hipotezin p qiyməti 0.018-dən 0.047-yə sürüşdü. Genişlik üçün əlavə
edilmiş və hipotezi ümumiyyətlə sınamayan testlər onu cəzalandırmamalıdır.

Kəşfiyyatçı süpürgə silinmir: `analyze.py` cədvəllərində qalır və orada
öz ailəsi ilə düzəldilir.

Ailə 88 testdir: 11 elan edilmiş cüt, 4 zəncir, 2 dil.

| Cüt | Dil | Zəncir | Baza | Köklənmiş | Fərq | p | p (Holm) | Mənalı |
|---|---|---|---|---|---|---|---|---|
| Qazax 1 | AZ | strict | 27.9% | 4.4% | +23.4pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | AZ | morph | 29.1% | 4.4% | +24.6pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | AZ | lenient | 29.6% | 4.4% | +25.2pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | AZ | translit | 29.6% | 9.2% | +20.4pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | EN | strict | 55.2% | 41.5% | +13.7pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | EN | morph | 55.2% | 41.5% | +13.7pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | EN | lenient | 55.2% | 41.5% | +13.7pp | 0.0001 | 0.0088 | bəli |
| Qazax 1 | EN | translit | 55.2% | 41.5% | +13.7pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | AZ | strict | 37.5% | 17.1% | +20.4pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | AZ | morph | 38.7% | 17.7% | +21.0pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | AZ | lenient | 39.0% | 17.9% | +21.1pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | AZ | translit | 39.0% | 19.2% | +19.8pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | EN | strict | 60.0% | 50.1% | +9.9pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | EN | morph | 60.0% | 50.1% | +9.9pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | EN | lenient | 60.0% | 50.1% | +9.9pp | 0.0001 | 0.0088 | bəli |
| Qazax 2 | EN | translit | 60.0% | 50.1% | +9.9pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | AZ | strict | 17.2% | 6.3% | +10.9pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | AZ | morph | 17.8% | 6.6% | +11.2pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | AZ | lenient | 18.2% | 6.8% | +11.4pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | AZ | translit | 18.2% | 6.8% | +11.4pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | EN | strict | 52.6% | 25.8% | +26.9pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | EN | morph | 52.6% | 26.3% | +26.4pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | EN | lenient | 52.7% | 26.4% | +26.4pp | 0.0001 | 0.0088 | bəli |
| Türk 1 | EN | translit | 52.7% | 26.4% | +26.4pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | AZ | strict | 33.7% | 23.5% | +10.2pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | AZ | morph | 34.9% | 25.2% | +9.8pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | AZ | lenient | 35.1% | 26.4% | +8.8pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | AZ | translit | 35.1% | 26.4% | +8.8pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | EN | strict | 52.6% | 44.0% | +8.7pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | EN | morph | 52.6% | 44.0% | +8.7pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | EN | lenient | 52.6% | 44.1% | +8.6pp | 0.0001 | 0.0088 | bəli |
| Türk 2 | EN | translit | 52.6% | 44.1% | +8.6pp | 0.0001 | 0.0088 | bəli |
| Kiril 3 (qeyri-qazax) | AZ | strict | 20.5% | 13.1% | +7.4pp | 0.0001 | 0.0088 | bəli |
| Kiril 3 (qeyri-qazax) | AZ | morph | 21.5% | 13.9% | +7.6pp | 0.0001 | 0.0088 | bəli |
| Kiril 3 (qeyri-qazax) | AZ | lenient | 21.9% | 14.0% | +7.9pp | 0.0001 | 0.0088 | bəli |
| Kiril 3 (qeyri-qazax) | AZ | translit | 21.9% | 14.0% | +7.9pp | 0.0001 | 0.0088 | bəli |
| Kiril 3 (qeyri-qazax) | EN | strict | 46.9% | 46.5% | +0.4pp | 0.7777 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | morph | 46.9% | 46.5% | +0.4pp | 0.7777 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | lenient | 46.9% | 46.6% | +0.3pp | 0.8490 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | translit | 46.9% | 46.6% | +0.3pp | 0.8490 | 1.0000 | xeyr |
| Rus 1 (ağır) | AZ | strict | 20.0% | 17.2% | +2.8pp | 0.0114 | 0.3420 | xeyr |
| Rus 1 (ağır) | AZ | morph | 20.9% | 17.8% | +3.1pp | 0.0067 | 0.2278 | xeyr |
| Rus 1 (ağır) | AZ | lenient | 21.3% | 18.0% | +3.3pp | 0.0041 | 0.1476 | xeyr |
| Rus 1 (ağır) | AZ | translit | 21.4% | 18.7% | +2.7pp | 0.0190 | 0.5509 | xeyr |
| Rus 1 (ağır) | EN | strict | 45.4% | 48.5% | -3.1pp | 0.0058 | 0.2030 | xeyr |
| Rus 1 (ağır) | EN | morph | 45.5% | 48.5% | -3.0pp | 0.0078 | 0.2574 | xeyr |
| Rus 1 (ağır) | EN | lenient | 45.5% | 48.5% | -3.0pp | 0.0078 | 0.2574 | xeyr |
| Rus 1 (ağır) | EN | translit | 45.5% | 48.5% | -3.0pp | 0.0078 | 0.2574 | xeyr |
| Rus 2 (yüngül) | AZ | strict | 20.0% | 18.3% | +1.7pp | 0.1252 | 1.0000 | xeyr |
| Rus 2 (yüngül) | AZ | morph | 20.9% | 18.7% | +2.2pp | 0.0526 | 1.0000 | xeyr |
| Rus 2 (yüngül) | AZ | lenient | 21.3% | 18.8% | +2.5pp | 0.0274 | 0.7671 | xeyr |
| Rus 2 (yüngül) | AZ | translit | 21.4% | 19.5% | +1.9pp | 0.1027 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | strict | 45.4% | 45.9% | -0.5pp | 0.6737 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | morph | 45.5% | 46.0% | -0.5pp | 0.6737 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | lenient | 45.5% | 46.0% | -0.5pp | 0.6737 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | translit | 45.5% | 46.0% | -0.5pp | 0.6737 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | strict | 20.5% | 21.6% | -1.1pp | 0.3295 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | morph | 21.5% | 23.1% | -1.6pp | 0.1544 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | lenient | 21.9% | 23.4% | -1.5pp | 0.1896 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | translit | 21.9% | 23.4% | -1.5pp | 0.1896 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | EN | strict | 46.9% | 44.9% | +2.0pp | 0.0681 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | EN | morph | 46.9% | 44.9% | +2.0pp | 0.0681 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | EN | lenient | 46.9% | 44.9% | +2.0pp | 0.0681 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | EN | translit | 46.9% | 44.9% | +2.0pp | 0.0681 | 1.0000 | xeyr |
| Gürcü (qeyri-latın, qeyri-kiril) | AZ | strict | 6.5% | 0.1% | +6.4pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | AZ | morph | 6.7% | 0.1% | +6.6pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | AZ | lenient | 7.0% | 0.1% | +6.9pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | AZ | translit | 7.0% | 0.1% | +6.9pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | EN | strict | 28.6% | 4.3% | +24.2pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | EN | morph | 28.6% | 4.3% | +24.2pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | EN | lenient | 28.7% | 4.3% | +24.3pp | 0.0001 | 0.0088 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | EN | translit | 28.7% | 4.3% | +24.3pp | 0.0001 | 0.0088 | bəli |
| SEA (qarışıq yazı) | AZ | strict | 27.1% | 28.2% | -1.1pp | 0.1824 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | morph | 27.6% | 28.8% | -1.2pp | 0.1452 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | lenient | 27.8% | 29.0% | -1.2pp | 0.1452 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | translit | 27.8% | 29.0% | -1.2pp | 0.1452 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | strict | 54.6% | 54.5% | +0.1pp | 1.0000 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | morph | 54.6% | 54.5% | +0.1pp | 1.0000 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | lenient | 54.6% | 54.5% | +0.1pp | 1.0000 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | translit | 54.6% | 54.5% | +0.1pp | 1.0000 | 1.0000 | xeyr |
| Macar (latın, eyni baza) | AZ | strict | 20.0% | 0.6% | +19.4pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | AZ | morph | 20.9% | 0.6% | +20.3pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | AZ | lenient | 21.3% | 0.6% | +20.7pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | AZ | translit | 21.4% | 0.6% | +20.8pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | EN | strict | 45.4% | 22.5% | +23.0pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | EN | morph | 45.5% | 22.5% | +23.1pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | EN | lenient | 45.5% | 22.7% | +22.9pp | 0.0001 | 0.0088 | bəli |
| Macar (latın, eyni baza) | EN | translit | 45.5% | 22.7% | +22.9pp | 0.0001 | 0.0088 | bəli |

## Oxunuş

Qohumluq tək başına zərəri PROQNOZLAŞDIRMIR. Türk dili azərbaycancaya
qazax dilindən daha yaxındır, yəni qohumluq izahı doğru olsaydı, türk
cütləri DAHA çox artıq zərər verməli idi. Vermir.

Dörd cüt iki qrupa TƏMİZ ayrılır:

  kiril hədəf   hər ikisində artıq zərər MÜSBƏT, interval sıfırı kənarda
  latın hədəf   heç birində artıq zərər müsbət deyil

İDDİA BUDUR: kiril əlifbalı hədəfə köklənmə azərbaycancaya ÜMUMİ
unutqanlıqdan ARTIQ zərər verir; latın əlifbalı hədəfə köklənmə vermir.

İDDİA BU DEYİL: 'latın əlifbaya köklənmə azərbaycancanı QORUYUR.'
Bir cüt bunu göstərsə də, ikincisi göstərmir və birincinin mənfi
rəqəmi aldadıcıdır. Aşağıya bax.

### İKİ LATIN CÜTÜ NİYƏ FƏRQLƏNİR

Türk 1-in artıq zərəri güclü MƏNFİDİR, amma bu, azərbaycancanın yaxşı
qorunmasından deyil: onun MÜTLƏQ azərbaycanca itkisi (11.5 bənd) digər
cütlərlə eyni sıradadır. Fərqi yaradan İNGİLİS itkisinin nəhəngliyidir
(24.8 bənd). Artıq zərər fərq olduğuna görə, məxrəc partlayanda kəsr
mənfiyə düşür.

Türk 2-nin ingilis itkisi daha mötədildir (8.8 bənd) və artıq zərəri
sıfıra yaxın çıxır. Ölçmə baxımından TƏMİZ olan budur.

DƏRS: tək cütlə qurulan iddia kövrək idi və ikinci cüt onu düzəltdi.
Əvvəlki hesabatda yazılmış 'latın köklənmə azərbaycancanı qoruyur'
cümləsi bir ölçmənin artefaktı imiş. İddia daraldılıb, silinməyib:
kiril və latın arasındakı fərq qalır, çünki latın cütlərinin heç biri
artıq zərər göstərmir, kiril cütlərinin isə hər ikisi göstərir.

MƏHDUDİYYƏT: hər istiqamətdə iki cüt var və modellər ölçü, ailə,
təlim resepti ilə də fərqlənir. Nəticə istiqaməti göstərir, kəmiyyəti
yox.
