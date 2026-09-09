# Əlifba fərziyyəsi: tapıntılar

Tarix: 2026-08-24 | dataset: `data/az_eval_v0.jsonl`, 484 sual |
seed 0, bootstrap 1000 təkrar | rəqəmlərin mənbəyi: `tables.md`

## Qısa cavab

Qolda ilə onun baza modeli arasındakı azərbaycanca fərq **əsasən ölçmə
artefaktıdır, bilik fərqi deyil**. STRICT rejimdə fərq 7.2 bənddir və
statistik mənalıdır; transliterasiya tətbiq olunanda fərqin **91%-i itir**,
qalan 0.6 bənd isə sıfırdan ayırd edilmir (p = 0.76, Holm).

Amma ikinci sınaq gözlənilən nəticəni VERMƏDİ və bu, müstəqil bir tapıntıdır:
promptla latın əlifbası tələb etmək balı qaldırmır, çünki **model tələbə əməl
etmir**. Yəni problemin həlli prompt qatında deyil, qiymətləndirmə qatındadır.

## Analiz 1: normalizasiya nərdivanı

| Zəncir | Baza | Qolda | Fərq | 95% CI | Bağlanan pay | p (Holm) |
|---|---|---|---|---|---|---|
| strict | 10.5% | 3.3% | +7.2 bənd | [4.8, 9.7] | 0% | 0.0008 |
| morph | 11.0% | 3.3% | +7.6 bənd | [5.2, 10.1] | -6% | 0.0008 |
| lenient | 11.2% | 3.3% | +7.9 bənd | [5.4, 10.5] | -9% | 0.0008 |
| translit | 11.2% | 10.5% | +0.6 bənd | [-1.9, 3.1] | **91%** | 0.7569 |

Zəncirlər iç-içədir və hər addım əvvəlkinə **bir** çevirmə əlavə edir. Bu
quruluş sayəsində payı konkret çevirməyə aid etmək olur: LENIENT (şəkilçi
kəsimi + diakritik yumşaltması, transliterasiyasız) fərqi bağlamır, hətta
genişləndirir. Deməli 91%-i tək başına **transliterasiya** verir.

Fərqin MORPH və LENIENT-də genişlənməsi səhv deyil, real haldır: həmin iki
çevirmə bazaya +0.7 bənd qazandırır, Qoldaya isə 0.0. Bir çevirmə iki modelə
eyni fayda vermir.

### Nəzarət: transliterasiya balı süni qaldırmır

Ən açıq etiraz budur: "transliterasiya hər modelin balını qaldırır, ona görə
fərqin bağlanması mənasızdır". Rəqəm bu etirazı rədd edir.

| Model | STRICT-də səhv, TRANSLIT-də düz sayılan cavab |
|---|---|
| Baza (latın yazır) | 3 |
| Qolda (kiril yazır) | 35 |

Çevirmə ümumi bal artırıcısı olsaydı, iki rəqəm yaxın olardı. Onlar 12 dəfə
fərqlənir: çevirmə yalnız kirillə yazılmış cavabları xilas edir.

## Analiz 2: latın əlifbasının məcbur edilməsi

Bu sınaq yeni inference tələb edirdi: eyni 484 sual, "latın əlifbası ilə cavab
ver" promptu ilə. 2x2-nin çatışmayan xanası (baza + latın tələbi) bu iş üçün
qaçırıldı.

| Model | Zəncir | Adi prompt | Latın tələbi | Fərq | p (Holm) |
|---|---|---|---|---|---|
| Baza | strict | 10.5% | 11.4% | +0.8 bənd | 1.0000 |
| Qolda | strict | 3.3% | 3.5% | +0.2 bənd | 1.0000 |
| Qolda | translit | 10.5% | 10.5% | +0.0 bənd | 1.0000 |

Səkkiz müqayisənin heç biri mənalı deyil. Səbəbi yazı sistemi saylarında
görünür:

| Qaçış | Kiril | Latın | Kiril payı |
|---|---|---|---|
| Qolda, adi prompt | 444 | 40 | 91.7% |
| Qolda, latın tələbi | 430 | 54 | 88.8% |

Prompt kiril payını cəmi 2.9 bənd azaldır. Sətir səviyyəsində: 17 cavab kirildən
latına keçib, 3 cavab əks istiqamətdə hərəkət edib. **Model təlimatı oxuyur və
təxminən görməzdən gəlir.**

Üstəlik latına keçən 17 cavabdan yalnız **1-i** STRICT-də düz oldu. Yəni
əlifbanı dəyişmək öz-özünə cavabı düzəltmir.

## Nə iddia edə bilərik, nə edə bilmərik

**Edə bilərik.** Qolda ilə bazası arasındakı STRICT fərqi əsasən yazı
sisteminin ölçülməsindən doğur. Kiril cavablar transliterasiya olunanda fərq
statistik olaraq yox olur. Bu, "qazax fine-tune-u Azərbaycan bilikini məhv
edir" oxunuşunu **zəiflədir**.

**Edə bilmərik.** "Qolda azərbaycanca yaxşıdır" demək olmaz. TRANSLIT-də
Qolda 10.5%, baza 11.2%-dir: ikisi də zəifdir. Aradan qalxan şey fərqdir, aşağı
bal deyil.

Bir daha ehtiyat: Qoldanın latınla yazdığı 40 cavabın STRICT balı 40%-dir,
ümumi 3.3% deyil. Yazı sisteminin seçimi sualın növü ilə əlaqəlidir (rəqəm və
xüsusi adlarda latın yazır), ona görə "model bilir, sadəcə kirillə yazır"
cümləsi tam doğru deyil. Kiril altqrupunun TRANSLIT balı cəmi 7.9%-dir.

## Praktik nəticə

1. Kiril yazan modelləri qiymətləndirən hər kəs üçün **transliterasiya
   qatı məcburidir**. Onsuz ölçü modelin bilikini deyil, yazı sistemini ölçür.
2. Prompt mühəndisliyi bu problemi həll etmir. Sınadıq, işləmədi, rəqəm
   yuxarıdadır.
3. Hesabat tək rejimdə verilməməlidir. Yalnız STRICT dərc etsəydik, 7.2 bəndlik
   "mənfi transfer" iddiası çap olunardı və o, yanlış olardı.

## Bir provenans qeydi

`config.json` faylında baza modelinin adi qaçışı üçün 485 cavab görünür, ortaq
sual sayı isə 484-dür. Fərq `az-546` sualıdır: o, promptdakı few-shot nümunəsi
ilə üst-üstə düşdüyü üçün datasetdən çıxarılıb, xam cavab faylında isə köhnə
sətir qalıb. Analizə düşmür, çünki ortaq dəst dataset ilə kəsişmədən qurulur.
Bu, `build_dataset.py`-dakı çirklənmə qapısının işlədiyinin sübutudur.

## Təkrar istehsal

```
python -m src.script_hypothesis
```

Xam cavablar `generations/` altındadır, konfiqurasiya və fayl SHA-ları
`config.json` içindədir. Bu analiz `results/raw_outputs/` qovluğuna toxunmur,
ona görə əsas cədvəllərin Holm ailəsi və p qiymətləri dəyişmir.
