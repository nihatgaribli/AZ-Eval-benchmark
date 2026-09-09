# Qərarlar jurnalı

Layihənin gedişində verilən və geri qayıtmağa dəyən qərarlar. Hər yazı
tarixlidir və üç sualı cavablandırır: nə qərara alındı, niyə, nəyi rədd etdik.

Kod dəyişikliyinin özü git tarixindədir. Bura yalnız **git tarixindən
çıxarıla bilməyən** şeylər yazılır: alternativlər, səbəblər, sınanıb işləməyən
yanaşmalar.

---

## 2026-08-24: əlifba fərziyyəsi ayrı qovluqda ölçülür

**Qərar.** Əlifba analizi `results/script_hypothesis/` altında, öz xam
cavabları və öz Holm ailəsi ilə aparılır. Yeni qaçış `results/raw_outputs/`
qovluğuna YAZILMIR.

**Səbəb.** `analyze.py` gördüyü hər qaçışı müqayisə ailəsinə salır. Ailə
böyüyəndə Holm düzəlişi sərtləşir və ƏSAS cədvəllərin bütün p qiymətləri
sürüşür. Ayrı sual ayrı ailədə ölçülməlidir, yoxsa bir analizin əlavəsi
başqasının nəticəsini səssizcə dəyişir.

**Rədd edilən alternativ.** Qaçışı `raw_outputs/` altına atıb cədvəlləri
yenidən qurmaq. Sadə idi, amma konfrans üçün dondurulmuş rəqəmləri
dəyişdirərdi.

**Nəticə.** `results/script_hypothesis/FINDINGS.md`.

---

## 2026-08-24: STRICT fərqi əsasən artefaktdır, prompt onu düzəltmir

**Qərar.** "Mənfi transfer" iddiası tək STRICT rejimlə dərc edilmir. Hesabat
dörd zəncirin hamısını verir və transliterasiya qatını məcburi sayır.

**Səbəb.** Qolda ilə bazası arasındakı 7.2 bəndlik STRICT fərqinin 91%-i
transliterasiya ilə bağlanır, qalanı sıfırdan ayırd edilmir (p = 0.76).
Nəzarət yoxlaması çevirmənin ümumi bal artırıcısı olmadığını göstərir: bazada
3 cavab xilas olur, Qoldada 35.

**Sınandı, işləmədi.** Promptla latın əlifbası tələb etmək. Model əməl etmir:
kiril payı 91.7%-dən yalnız 88.8%-ə düşür və latına keçən 17 cavabdan cəmi 1-i
düzəlir. Prompt mühəndisliyi bu problemin həlli deyil; həll qiymətləndirmə
qatındadır.

**Diqqət.** Bu, "Qolda azərbaycanca yaxşıdır" demək deyil. TRANSLIT-də Qolda
10.5%, baza 11.2%-dir. Aradan qalxan fərqdir, zəiflik deyil.

---

## 2026-08-24: bütün fərq sütunlarına bootstrap CI

**Qərar.** `rq2.md` və nəzarət cədvəlinə 95% CI sütunu əlavə edildi;
əvvəllər yalnız `rq1.md`-də vardı.

**Səbəb.** p qiyməti effektin ÖLÇÜSÜNÜ göstərmir. CI-siz cədvəldə "mənalı"
sütunu 0.3 bəndlik fərqi 9 bəndlik fərqlə eyni çəkidə göstərir.
