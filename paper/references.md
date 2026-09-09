# §2 üçün istinadlar

**Vəziyyət:** 2026-09-08, birinci keçid.

## OXUMADAN İSTİFADƏ ETMƏ

Aşağıdakı metadata (başlıq, arXiv nömrəsi, məkan, il) axtarış nəticələrindən
təsdiqlənib. **Məqalələrin tam mətni oxunmayıb.** Ona görə:

- Başlıq, nömrə, məkan işlədilə bilər
- Onlara aid edilən KONKRET İDDİALAR mətnə düşməzdən əvvəl mənbədən
  yoxlanmalıdır

Bu fərq vacibdir: sitat gətirmək o deməkdir ki, müəlliflərin nə dediyini
bilirsən. "Axtarış xülasəsi belə deyirdi" kifayət deyil və hakim onu ilk
yoxlayan şeydir.

Bu sənəddə əvvəllər `# YOXLA:` sətirləri var idi. **2026-09-08-də hamısı
bağlandı:** hər biri ya tam mətnlə təsdiqləndi, ya da yoxlanıla bilmədiyi
üçün iddia mətndən çıxarıldı. Bağlanmış maddələr `YOXLANILDI` başlığı ilə
saxlanılır, çünki nəyin necə yoxlandığı özü qeydə alınmalıdır.

---

## 1. Benchmark boşluğu: azərbaycanca nə var, nə yoxdur

### TUMLU
Isbarov və b. (2025). *TUMLU: A Unified and Native Language Understanding
Benchmark for Turkic Languages.*

**SİTAT SƏHVİ DÜZƏLDİLDİ (2026-09-09).** Əvvəllər "İbrahimov və b." yazılırdı.
Yanlışdır: 16 müəllif arasında belə ad yoxdur, birinci müəllif **Jafar
Isbarov**-dur. Həmin şəxs "Open foundation models for Azerbaijani language"
işinin də birinci müəllifidir. arXiv metaməlumatı ilə yoxlanıldı. ACL 2025 (long). arXiv:2502.11020.
<https://aclanthology.org/2025.acl-long.1112/>

Səkkiz türk dili, orta və yuxarı sinif səviyyəsində 11 fənn. Azərbaycanca
hissəsi var. `TUMLU-mini` əl ilə yoxlanılmış balanslaşdırılmış altdəstdir və
BİZ MƏHZ ONU idxal edirik (`src/import_tumlu.py`, 735 sətir, CC BY 4.0).

**Bizim fərqimiz:** TUMLU PARALEL DEYİL və çoxvariantlıdır. Paralel olmadığı
üçün ondan AZ/EN uçurumu çıxarıla bilmir; çoxvariantlı olduğu üçün seçməni
ölçür, istehsalı yox. Bizim dəst hər iki cəhətdən fərqlidir.

**YOXLANILDI (tam mətn).**

Fənlər (11): Riyaziyyat, Fizika, Kimya, Biologiya, Coğrafiya, Ana dili və
ədəbiyyat, Tarix, Məntiq, İnsan və cəmiyyət, Fəlsəfə, Din və etika. Son
dördü yalnız bir-iki dildə var və təcrübələrə daxil edilməyib.

Ölçü: tam TUMLU 38 139 sual, 8 dil, 11 fənn. **AZƏRBAYCANCA TAM SAY
MƏTNDƏN ÇIXARILA BİLMİR:** dil üzrə bölgü Şəkil 1-dədir, şəkil isə
mətnə çevrilmir. Ona görə biz yalnız öz idxal etdiyimiz rəqəmi yazırıq:
`TUMLU-mini` azərbaycanca 735 sətir. Uydurma say yazılmır.

"Nativ" iddiasının dəqiq forması: *"TUMLU is a comprehensive,
multilingual, and natively developed language understanding benchmark
specifically designed for Turkic languages."* Onlar bunu maşın
tərcüməsinə qarşı qoyurlar: çoxdilli məhək daşlarının əksəriyyəti maşın
tərcüməsi ilə qurulub və orada mədəni qərəz və tərcümə artefaktları olur.

**BİZİM ÜÇÜN ƏLAVƏ DƏYƏRLİ FAKT.** Öz məqalələri yazır: *"In languages
such as Azerbaijani where questions were developed by the community,
around 10% of the questions were either invalid or had incorrect
answers."* Bu, bizim defekt süzgəcimizi (735 sətirdən 521-i saxladıq)
kənar mənbə ilə əsaslandırır: idxal edilən dəst süzülmədən işlədilə
bilməz və bunu dəstin öz müəllifləri deyir.

### KazMMLU
Toğmanov və b. (2025). *KazMMLU: Evaluating Language Models on Kazakh,
Russian, and Regional Knowledge of Kazakhstan.* ACL 2025 (long).
arXiv:2502.12829. <https://aclanthology.org/2025.acl-long.701/>

10 969 qazax + 12 031 rus sualı. Layihəmiz üçün ikiqat əhəmiyyətlidir:
qazax dili üçün resurs VAR, azərbaycanca üçün yox idi, və məhz bu
asimmetriya "qazax modelini azərbaycancaya köçürək" fikrini doğurur.

**YOXLANILDI (tam mətn), sitat birbaşadır:** *"All questions are written
in Cyrillic script, which remains the prevailing standard in Kazakhstan's
formal education system."*

Bu, bizim mexanizm arqumentimizin daşıyıcı həlqəsidir: qazax dilinə
uyğunlaşdırma praktikada KİRİL mətnə uyğunlaşdırmadır.

### INCLUDE
Romanou və b. (2025). *INCLUDE: Evaluating Multilingual Language
Understanding with Regional Knowledge.* ICLR 2025. arXiv:2411.19799.

44 dil, 197 243 sual, yerli imtahan mənbələrindən. Çoxvariantlıdır.

**YOXLANILDI (tam mətn, Cədvəl 8):** azərbaycanca DAXİLDİR:
`"Azerbaijani | latin | Turkic | Azerbaijani North | Mid | 6937"`.
Yəni 6937 sual, latın yazı, orta resurs səviyyəsi.

Deməli "azərbaycanca üçün məhək daşı yoxdur" cümləsi YANLIŞDIR və
mətndə işlədilə bilməz. Bizim fərqimiz sayda deyil, quruluşdadır:
INCLUDE paralel deyil və çoxvariantlıdır.

---

## 2. Yazı sistemi maneəsi: BİZİM TAPINTIMIZIN ƏDƏBİYYATDAKI YERİ

Bu qrup ən vacibidir, çünki bizim nəticəmiz onlara ZİDD deyil, onları
FİNE-TUNE tərəfinə uzadır.

### Moosa və b. (2022)
*Does Transliteration Help Multilingual Language Modeling?* arXiv:2201.12501.

### Liu və b. (2024)
*Breaking the Script Barrier in Multilingual Pre-Trained Language Models with
Transliteration-Based Post-Training Alignment.* arXiv:2406.19759.

### *How Transliterations Improve Crosslingual Alignment* (2024)
arXiv:2409.17326.

### RomanSetu (2024)
*RomanSetu: Efficiently unlocking multilingual capabilities of Large Language
Models via Romanization.* arXiv:2401.14280.

**Ortaq xətt:** yazı sistemi fərqi qohum dillər arasında leksik üst-üstə
düşməni azaldır və transferi pozur; transliterasiya onu bərpa edir.

**BİZİM ƏLAVƏMİZ və məqalənin yerləşdiyi boşluq.** Yuxarıdakı işlərin hamısı
PRE-TRAINING və ya alignment mərhələsinə baxır və sualı belə qoyur: "ortaq
yazıya gətirsək transfer YAXŞILAŞIRMI?" Cavab: bəli.

Biz tərs tərəfdən yanaşırıq: "fərqli yazılı qohum dilə KÖKLƏNMƏK nə edir?"
Cavab: PİSLƏŞDİRİR, özü də ümumi unutqanlıqdan artıq. Bu, həmin ədəbiyyatın
gözlədiyi istiqamətdədir, amma bildiyimizə görə fine-tune cütləri üzərində
ölçülməyib.

Üstəlik bizim transliterasiya nəticəsi onların mexanizmini DƏSTƏKLƏYİR:
`Qolda-AVL-5B` cavabların 86%-ni kirillə yazır və transliterasiyadan sonra
itkinin bir hissəsi qayıdır, yəni bilik yerindədir, forma yanlışdır.

### YOXLANILDI (2026-09-08): yenilik iddiası sağ qalır

`arXiv:2406.19759` tam oxundu (abstrakt + səhifə). O, **post-pretraining
alignment** metodudur və yalnız transferin YAXŞILAŞMASINI ölçür; üçüncü dilə
zərər ölçülmür, mənfi transferdən söz getmir.

Yəni "fərqli yazılı qohum dilə köklənmək ÜÇÜNCÜ dilə nə edir" sualı bu
ədəbiyyatda qoyulmayıb. İddia zəiflədilməli deyil.

---

## 2b. ƏN CİDDİ RƏQİB İZAH: mütləq cavablanmalıdır

### Tufa, Markov və Vossen (2024)
*Unknown Script: Impact of Script on Cross-Lingual Transfer.*
arXiv:2404.18810. Vrije Universiteit Amsterdam.

**SİTAT SƏHVİ DÜZƏLDİLDİ.** Əvvəlki qaralamalarda bu iş "Purkayastha və b."
kimi göstərilirdi. Yanlışdır: "Purkayastha" adı həmin məqalənin ÖZ istinad
siyahısındadır, müəllifləri deyil. arXiv metaməlumatı ilə yoxlanıldı.
Səhv sitat rəyçi üçün ucuz və ağrılı tapıntıdır, ona görə burada açıq
qeyd edilir.

**Bu iş bizim çərçivəmizə birbaşa toxunur və nəticəsi ilk baxışdan bizə
ZİDDİR:** onlar "tokenizator yazı sistemindən, dil oxşarlığından və model
ölçüsündən GÜCLÜ amildir" deyirlər.

Tam mətn yoxlanıldı, quruluş belədir:

    modellər    enkoder (BERT, RoBERTa, mBERT, CANINE), generativ LLM YOX
    tapşırıq    NER və POS, hədəf dil amhar (yazısı modelə tanış deyil)
    ölçü        yalnız HƏDƏF dildəki performans

**İKİ MÜHÜM FƏRQ VAR və hər ikisi mətndə yazılmalıdır.**

1. Onlar yalnız hədəf dildəki performansı ölçürlər. Bir dilə köklənib
   BAŞQA dildəki deqradasiyanı ölçmürlər. Bizim sualımız məhz odur.

2. Onların "tokenizator daha güclüdür" nəticəsi MODELLƏRARASI müqayisədən
   çıxır: fərqli modellərin fərqli tokenizatorları var (BPE vs WordPiece) və
   fərq oradan gəlir. Bizim dizayn isə tokenizatoru CÜT DAXİLİNDƏ sabit
   saxlayır.

**BİZİM CAVABIMIZ HAZIRDIR VƏ GÜCLÜDÜR.** Ölçdük: iki cütdə tokenizator
tam eynidir (`Qazax 1`: yalnız 3 xüsusi token, `Türk 2`: 0 fərq). Həmin iki
cütdə tokenizator amili quruluşca sıfırlanır, buna baxmayaraq:

    Qazax 1 (kiril, tokenizator eyni)   artıq zərər  +9.7pp [+6.2, +13.1]
    Türk 2  (latın, tokenizator eyni)   artıq zərər  +1.8pp [-1.0,  +4.8]

Yəni tokenizator bərabər olanda da kiril/latın fərqi qalır. Bu, onların
irəli sürdüyü ən güclü rəqib izahı bizim əsas cütlərimizdə İSTİSNA EDİR.

**MƏTNDƏ NECƏ YERLƏŞMƏLİDİR.** Bu işə istinad etmək məcburidir və onu
zəiflətmək cəhdi səhv olardı. Düzgün forma: "Tufa və b. tokenizatorun
yazı sistemindən güclü amil olduğunu göstərir; biz həmin amili cüt daxilində
sabit saxlayır və yazı sistemi effektinin ondan asılı olmadan qaldığını
göstəririk." Onların nəticəsi bizim dizaynımızın SƏBƏBİDİR, əleyhinə dəlil
yox.

**YOXLANILDI: eyni şeyi ölçmürük.** Onların Cədvəl 1-i tokenizatoru
ALQORİTM TİPİ kimi dəyişir: WordPiece (BERT, m-BERT, BERT-arabic), BPE
(RoBERTa), SentencePiece (ALBERT), simvol səviyyəli (CANINE-c). Yəni
dəyişən altı MODEL arasındadır. Nə "lüğət ölçüsü", nə "fertillik" sözü
mətndə keçmir.

Bizim ölçümüz isə bir CÜT DAXİLİNDƏ lüğət fərqidir; orada alqoritm
konstruksiyaya görə eynidir, çünki tuned model bazanın tokenizatorunu
miras alır.

Deməli müqayisə belə yazılmalıdır: onlar alqoritm sinfinin modellər
arasında əhəmiyyətli olduğunu göstərir; biz isə lüğətin də dəyişmədiyi
cütdə yazı sistemi fərqinin qaldığını göstəririk. İki iddia bir-birinə
ZİDD DEYİL və heç biri o birinin əleyhinə dəlil sayıla bilməz.

---

## 3. Katastrofik unutma: ölçümüzün əsaslandırılması

### *Conditions for Catastrophic Forgetting in Multilingual Translation* (2025)
MRL 2025. arXiv:2510.19546. <https://aclanthology.org/2025.mrl-main.23.pdf>

### Luo və b. (2023)
*An Empirical Study of Catastrophic Forgetting in Large Language Models
During Continual Fine-tuning.* arXiv:2308.08747.

### *Revisiting Catastrophic Forgetting in Large Language Model Tuning* (2024)
Findings of EMNLP 2024. <https://aclanthology.org/2024.findings-emnlp.249/>

**Niyə lazımdır.** Bunlar "hər fine-tune nəyisə unutdurur" faktını qurur və
bizim ƏSAS ÖLÇÜMÜZÜN əsaslandırılmasıdır: mütləq AZ itkisi kifayət etmir,
çünki onun bir hissəsi ümumi unutqanlıqdır. Ona görə biz AZ itkisi EKSİ EN
itkisi ölçürük.

Bu bölmə həm də TÜRK 1 CÜTÜNÜ izah edir: `Trendyol` ingiliscədə 26.6 bənd
itirir, yəni klassik katastrofik unutma nümunəsidir, azərbaycanca xüsusi
zərər deyil.

**YOXLANILDI: normallaşdırılmış ölçü VAR, amma dil-asimmetrik deyil.**

Koloski və b. (arXiv:2309.06089, 2023; "Accepted to IEEE Access") Kemker və b.
(2018) ailəsini işlədir:

BAŞLIQ DÜZƏLİŞİ (2026-09-10): əvvəlki qeyd başlığı "Measuring Catastrophic
Forgetting in Cross-Lingual Classification: Transfer Paradigms and Tuning
Strategies" yazırdı. Doğrusu "Measuring Catastrophic Forgetting in
Cross-Lingual Transfer Paradigms: Exploring Tuning Strategies"-dir. İl də
2025 yox, 2023-dür: arXiv qeydində nə DOI, nə də jurnal istinadı var, ona
görə preprint kimi sitat gətirilir.

    Omega_base = orta( alpha_base,i / alpha_ideal )

burada `alpha_ideal` modelin ÖZ oflayn nəticəsidir. Bu, dilin ÖZ idealına
nisbətidir. Liu və Niehues (MRL 2025) isə cüt üzrə MÜTLƏQ dəyişmə verir
(fine-tune-dan əvvəl/sonra qrafiki).

Bizim `artıq zərər` iki DİL ARASINDAKI FƏRQDİR:

    artıq zərər = (EN əvvəl - EN sonra) - (AZ əvvəl - AZ sonra)

Fərq mahiyyətlidir: Kemker/Koloski-də istinad dili MƏNBƏ dilidir, yəni
model onun üzərində öyrədilib. Bizdə isə NƏ AZ, NƏ EN fine-tune hədəfi
deyil: hər ikisi kənar müşahidəçidir və biri o birini kalibrləyir.

**MƏTNDƏ NECƏ YAZILMALIDIR.** "Yeni ölçü təklif edirik" yazmaq olmaz;
normallaşdırılmış unutma ölçüləri artıq var və onlara istinad edilməlidir.
Düzgün forma: bizim konstruksiya kənar dili kalibrləyici kimi işlədir,
bunu bu ədəbiyyatda tapmadıq, iddia məhz bu dəqiqlikdə səslənməlidir.

---

## Hələ axtarılmayıb

- Türk dilləri arasında transfer üzrə işlər (azərbaycanca-türkcə cütü)
- Azərbaycan dili üçün NLP resursları icmalı
- Qısa cavab vs çoxvariantlı format müqayisəsi üzrə metodiki işlər
  (bizim `format_contrast.py` tapıntısı üçün)
- Tokenizator fertilliyi və az resurslu dillərdə qiymət

---

## 4. TÜRK DİLLƏRİ ÜZRƏ ƏN YAXIN İŞLƏR (2026, yenilik yoxlanışında tapıldı)

Bunlar 2026-09-08 yenilik axtarışında üzə çıxdı və məqalənin ilk qaralamasında
YOX İDİ. Ən yaxın qonşularımızdır, ona görə istinad MƏCBURİDİR: rəyçi bunları
bilirsə və biz yazmamışıqsa, işi oxumamış görünərik.

### Ibrahimzade, O. və Tabasaransky, K. (2026)
*Cross-Lingual Transfer and Parameter-Efficient Adaptation in the Turkic
Language Family: A Theoretical Framework for Low-Resource Language Models.*
arXiv:2604.06202, mart 2026.

**BİZİM HİPOTEZİMİZİ ALTI AY ƏVVƏL YAZIBLAR, AMMA SINAMAYIBLAR.** Azərbaycan,
qazax, özbək, türkmən, qaqauz dilləri. "Turkic Transfer Coefficient" təklif
edirlər və ora YAZI UYĞUNLUĞUNU daxil edirlər. Birbaşa sitatlar:

  "Kazakh demonstrates somewhat lower TTC values with the Latin-script
   languages due to the continued use of Cyrillic orthography in much of
   its digital text"

  "orthographic divergence, particularly the coexistence of Latin and
   Cyrillic scripts, may partially reduce effective transfer despite high
   morphological similarity"

Təcrübə YOXDUR, özləri yazır: "The goal is not to report experimental
outcomes, but rather to establish a conceptual model".

**MÖVQEYİMİZ:** bunu gizlətmək olmaz və gizlətməyə ehtiyac da yoxdur. Əksinə,
GÜCLƏNDİRİR: dərc olunmuş bir proqnozun empirik yoxlanışıyıq, təsadüfi fikir
deyil. Sualın əhəmiyyətli olduğunu müstəqil mənbə təsdiqləyir.

### Cinar, O. B., Dalkilic, M. M. və Toraman, C. (2026)
*Cross-Lingual Transfer for Machine Translation in Turkic Languages.*
arXiv:2607.29355, METU, iyul 2026.

mT5, beş türk dili (tr, az, uz, kk, ky), cüt-cüt transfer matrisləri.
Latınlaşdırma kiril hədəflərdə BLEU-nu yaxşılaşdırır (az->ky üçün +63.64%).
Həm də: transfer ən güclü türkcə-azərbaycanca cütündədir, bu bizim dizaynı
dəstəkləyir (türkcə daha yaxın qohumdur).

**FƏRQ:** onlarda translit tərcümə sisteminin GİRİŞİNƏ tətbiq olunur, bizdə
uyğunlaşdırılmış generativ modelin ÇIXIŞINA.

### Zhang, Z. (2026)
*Universal or Language-Family-Specific Script Unification for Cross-Lingual
Transfer? A Case Study on Turkic Languages.* arXiv:2608.09356, CUHK-Shenzhen.

fastText, 11 türk dili, WikiANN NER + UD POS. uroman ilə Common Turkic Script
müqayisəsi. Yenə də məqsəd transferi YAXŞILAŞDIRMAQDIR, zərəri ölçmək yox.

### Khelli, M., Cahyawijaya, S., Purwarianti, A. və Winata, G. I. (2025)
*What Causes Knowledge Loss in Multilingual Language Models?*
arXiv:2504.20356.

**NƏTİCƏSİ İLK BAXIŞDAN BİZİM ƏKSİMİZDİR.** 52 dil, XLM-R, MASSIVE slot
filling, LoRA. Tapıntı: latın yazılı dillər daha az unudulur və daha yaxşı
donordur.

Sadəlövh oxunuşda bu, azərbaycancanın (latın) qorunmalı olduğunu deyir.

**HƏLL:** eyni dəyişəni dəyişmirik. Onlarda dəyişən UNUDULAN dilin yazısıdır,
bizdə UYĞUNLAŞDIRILAN hədəfin yazısı. Latın kənar dil qorunmur, çünki zərər
modelin nə saxlamalı olduğundan yox, nə yazmağı ÖYRƏNDİYİNDƏN gəlir.
Azərbaycanca onların 52 dili arasında yoxdur, modellər enkoderdir.

Bu gərginlik MƏTNDƏ AÇIQ YAZILMALIDIR (§2.7), çünki həmin işi bilən rəyçi
bizim bilmədiyimizi düşünəcək.

### Yenilik yoxlanışının nəticəsi (2026-09-08)

`alexeyev/awesome-azerbaijani-nlp` siyahısının "Benchmarks / Evaluation"
bölməsində YEGANƏ giriş bizim v1-dir. arXiv-də azərbaycanca üzrə bütün işlər
nəzərdən keçirildi: işarə dili, orfoqrafiya düzəlişi, MT, TTS, enkoder
modelləri. Paralel və sərbəst formalı dəst yoxdur.

Heç bir iş uyğunlaşdırmanın HƏDƏFİ OLMAYAN üçüncü dilə vurduğu zərəri
generativ şəraitdə ölçmür.
