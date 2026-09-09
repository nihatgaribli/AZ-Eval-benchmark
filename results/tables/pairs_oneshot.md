# Fine-tune cütləri (`oneshot` üslubu): qohumluq, yoxsa əlifba?

| Cüt | Hədəf | Yazı | AZ baza | AZ köklənmiş | AZ itkisi | EN itkisi |
|---|---|---|---|---|---|---|
| Qazax 1 | qazax | kiril | 24.3% | 5.2% | +19.1pp | +10.0pp |
| Kiril 3 (qeyri-qazax) | ukrayna | kiril | 21.4% | 20.2% | +1.2pp | +1.1pp |
| Rus 1 (ağır) | rus | kiril | 23.9% | 15.2% | +8.6pp | -1.5pp |
| Rus 2 (yüngül) | rus | kiril | 23.9% | 16.3% | +7.6pp | -0.8pp |
| Latın 3 (qeyri-türk) | norveç | latın | 21.4% | 21.5% | -0.1pp | +3.0pp |
| SEA (qarışıq yazı) | cənub-şərqi asiya | qarışıq | 25.5% | 26.2% | -0.7pp | +0.2pp |

## Artıq zərər: AZ itkisi eksi EN itkisi

İngilis itkisi ümumi unutqanlığın ölçüsüdür. Fərq isə azərbaycancanın
ondan ƏLAVƏ nə qədər zərər gördüyünü verir. Mütləq AZ itkisinə baxmaq
kifayət etmir: hər fine-tune bir qədər unutdurur.

| Cüt | Yazı | Artıq zərər | 95% CI | Nəticə |
|---|---|---|---|---|
| Qazax 1 | kiril | +9.2pp | [+6.0, +12.5] | azərbaycanca ƏLAVƏ zərər |
| Kiril 3 (qeyri-qazax) | kiril | +0.1pp | [-2.9, +3.2] | fərq sıfırdan ayırd edilmir |
| Rus 1 (ağır) | kiril | +10.1pp | [+7.0, +13.0] | azərbaycanca ƏLAVƏ zərər |
| Rus 2 (yüngül) | kiril | +8.3pp | [+5.4, +11.4] | azərbaycanca ƏLAVƏ zərər |
| Latın 3 (qeyri-türk) | latın | -3.1pp | [-6.0, -0.5] | azərbaycanca nisbətən QORUNUB |
| SEA (qarışıq yazı) | qarışıq | -0.9pp | [-2.8, +1.1] | fərq sıfırdan ayırd edilmir |

## Transliterasiya və yazı sistemi

| Cüt | AZ itkisi (STRICT) | AZ itkisi (TRANSLIT) | Köklənmişin kiril payı |
|---|---|---|---|
| Qazax 1 | +19.1pp | +16.6pp | 84.9% |
| Kiril 3 (qeyri-qazax) | +1.2pp | +0.8pp | 0.0% |
| Rus 1 (ağır) | +8.6pp | +8.4pp | 13.8% |
| Rus 2 (yüngül) | +7.6pp | +7.6pp | 7.7% |
| Latın 3 (qeyri-türk) | -0.1pp | -0.6pp | 0.0% |
| SEA (qarışıq yazı) | -0.7pp | -1.1pp | 0.2% |

## Təsdiqləyici ailə

Aşağıdakı cədvəl Holm düzəlişini YALNIZ əvvəlcədən elan edilmiş cütlər
üzərində aparır. `analyze.py` cədvəlləri isə gördüyü hər model cütünü
sınayır; 14 model əlavə olunanda həmin ailə 474 testə çatdı və əsas
hipotezin p qiyməti 0.018-dən 0.047-yə sürüşdü. Genişlik üçün əlavə
edilmiş və hipotezi ümumiyyətlə sınamayan testlər onu cəzalandırmamalıdır.

Kəşfiyyatçı süpürgə silinmir: `analyze.py` cədvəllərində qalır və orada
öz ailəsi ilə düzəldilir.

Ailə 48 testdir: 11 elan edilmiş cüt, 4 zəncir, 2 dil.

| Cüt | Dil | Zəncir | Baza | Köklənmiş | Fərq | p | p (Holm) | Mənalı |
|---|---|---|---|---|---|---|---|---|
| Qazax 1 | AZ | strict | 24.3% | 5.2% | +19.1pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | AZ | morph | 25.7% | 5.2% | +20.4pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | AZ | lenient | 26.3% | 5.2% | +21.0pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | AZ | translit | 26.3% | 9.7% | +16.6pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | EN | strict | 55.3% | 45.4% | +10.0pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | EN | morph | 55.3% | 45.4% | +10.0pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | EN | lenient | 55.3% | 45.4% | +10.0pp | 0.0001 | 0.0048 | bəli |
| Qazax 1 | EN | translit | 55.3% | 45.4% | +10.0pp | 0.0001 | 0.0048 | bəli |
| Kiril 3 (qeyri-qazax) | AZ | strict | 21.4% | 20.2% | +1.2pp | 0.3261 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | AZ | morph | 22.5% | 21.6% | +0.9pp | 0.4855 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | AZ | lenient | 22.7% | 21.9% | +0.8pp | 0.5432 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | AZ | translit | 22.7% | 21.9% | +0.8pp | 0.5432 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | strict | 48.1% | 47.0% | +1.1pp | 0.3459 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | morph | 48.1% | 47.0% | +1.1pp | 0.3459 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | lenient | 48.1% | 47.1% | +1.0pp | 0.4001 | 1.0000 | xeyr |
| Kiril 3 (qeyri-qazax) | EN | translit | 48.1% | 47.1% | +1.0pp | 0.4001 | 1.0000 | xeyr |
| Rus 1 (ağır) | AZ | strict | 23.9% | 15.2% | +8.6pp | 0.0001 | 0.0048 | bəli |
| Rus 1 (ağır) | AZ | morph | 24.8% | 15.7% | +9.0pp | 0.0001 | 0.0048 | bəli |
| Rus 1 (ağır) | AZ | lenient | 25.2% | 16.1% | +9.1pp | 0.0001 | 0.0048 | bəli |
| Rus 1 (ağır) | AZ | translit | 25.4% | 17.0% | +8.4pp | 0.0001 | 0.0048 | bəli |
| Rus 1 (ağır) | EN | strict | 47.2% | 48.7% | -1.5pp | 0.2074 | 1.0000 | xeyr |
| Rus 1 (ağır) | EN | morph | 47.2% | 48.7% | -1.5pp | 0.2074 | 1.0000 | xeyr |
| Rus 1 (ağır) | EN | lenient | 47.2% | 48.7% | -1.5pp | 0.2074 | 1.0000 | xeyr |
| Rus 1 (ağır) | EN | translit | 47.2% | 48.7% | -1.5pp | 0.2074 | 1.0000 | xeyr |
| Rus 2 (yüngül) | AZ | strict | 23.9% | 16.3% | +7.6pp | 0.0001 | 0.0048 | bəli |
| Rus 2 (yüngül) | AZ | morph | 24.8% | 17.1% | +7.7pp | 0.0001 | 0.0048 | bəli |
| Rus 2 (yüngül) | AZ | lenient | 25.2% | 17.2% | +8.1pp | 0.0001 | 0.0048 | bəli |
| Rus 2 (yüngül) | AZ | translit | 25.4% | 17.9% | +7.6pp | 0.0001 | 0.0048 | bəli |
| Rus 2 (yüngül) | EN | strict | 47.2% | 48.0% | -0.8pp | 0.4705 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | morph | 47.2% | 48.1% | -0.9pp | 0.4061 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | lenient | 47.2% | 48.1% | -0.9pp | 0.4061 | 1.0000 | xeyr |
| Rus 2 (yüngül) | EN | translit | 47.2% | 48.1% | -0.9pp | 0.4061 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | strict | 21.4% | 21.5% | -0.1pp | 1.0000 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | morph | 22.5% | 23.0% | -0.5pp | 0.6931 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | lenient | 22.7% | 23.3% | -0.6pp | 0.6279 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | AZ | translit | 22.7% | 23.3% | -0.6pp | 0.6279 | 1.0000 | xeyr |
| Latın 3 (qeyri-türk) | EN | strict | 48.1% | 45.1% | +3.0pp | 0.0048 | 0.1536 | xeyr |
| Latın 3 (qeyri-türk) | EN | morph | 48.1% | 45.1% | +3.0pp | 0.0048 | 0.1536 | xeyr |
| Latın 3 (qeyri-türk) | EN | lenient | 48.1% | 45.1% | +3.0pp | 0.0048 | 0.1536 | xeyr |
| Latın 3 (qeyri-türk) | EN | translit | 48.1% | 45.1% | +3.0pp | 0.0048 | 0.1536 | xeyr |
| SEA (qarışıq yazı) | AZ | strict | 25.5% | 26.2% | -0.7pp | 0.4245 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | morph | 26.0% | 26.9% | -0.9pp | 0.3073 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | lenient | 26.3% | 27.4% | -1.1pp | 0.2049 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | AZ | translit | 26.3% | 27.4% | -1.1pp | 0.2049 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | strict | 55.3% | 55.1% | +0.2pp | 0.8885 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | morph | 55.3% | 55.1% | +0.2pp | 0.8885 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | lenient | 55.3% | 55.1% | +0.2pp | 0.8885 | 1.0000 | xeyr |
| SEA (qarışıq yazı) | EN | translit | 55.3% | 55.1% | +0.2pp | 0.8885 | 1.0000 | xeyr |

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
