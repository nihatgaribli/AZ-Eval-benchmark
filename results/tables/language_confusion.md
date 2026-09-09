# Səhv dil: hazır metriklər onu tuturmu?

Marchisio et al. (EMNLP 2024) latın əlifbalı dillər üçün söz
səviyyəli dil qarışıqlığını dilin Unicode diapazonundan kənar
simvolla təyin edir. Həmin qayda bizim insan etiketli sətirlərə
tətbiq olunur.

Türk əlifbası azərbaycan əlifbasının alt-çoxluğudur: **BƏLİ** (azərbaycanca yalnız `q`, `x`, `ə` əlavə edir).

| | n |
|---|---|
| İnsan etiketli xəta | 159 |
| Bunlardan `başqa dil` | 24 |
| Söz səviyyəli detektor tutur | 2 |
| Detektor buraxır | 22 |

Detektor səhv dil xətalarının **92%-ni buraxır.**

Tutulanlar qaydanı təsdiqləyir: hamısı azərbaycan əlifbasında
olmayan hərf daşıyır.

| id | cavab | kənar hərf |
|---|---|---|
| az-553 | Sir Isaac Newton | `w` |
| az-681 | Washington, D.C | `W` |

## Buraxılanlar

| id | qızıl | modelin cavabı |
|---|---|---|
| az-079 | Putonqhua | Çin dili (Mandarin) |
| az-022 | funt sterlinq | Sterlin |
| az-067 | güləşçi | Güreş |
| az-076 | yapon dili | Japonca |
| az-079 | Putonqhua | Mandarin |
| az-080 | ingilis dili | İngilizce |
| az-081 | ispan dili | İspanyolca |
| az-135 | kamança | Keman |
| az-1443 | Ulan-Bator | Ulaanbaatar |
| az-1453 | Qaborone | Gaborone |
| az-1480 | Aşqabad | Aşgabat |
| az-1532 | Filipsburq | Philipsburg |
| az-574 | Yupiter | Jüpiter |
| az-682 | Tokio | Tokyo |
| az-687 | Tbilisi | Tiflis |
| az-689 | Kiyev | Kiev |
| az-701 | Funt sterlinq | Sterlin |
| az-713 | Sakit okean | Pasifik Okyanusu |
| az-900 | Triqonometriya | Trigonometri |
| az-985 | ərəb dili | Arapça |
| az-989 | yunan dili | Yunanca |
| az-991 | fars dili | Farsça |

Səbəb konstruksiyadadır, təsadüf deyil: türk orfoqrafiyası ilə
yazılmış söz azərbaycan diapazonundan kənara çıxa bilmir.

SƏTİR SƏVİYYƏLİ qayda burada ölçülmür: o, fastText ilə sətir-sətir
işləyir, bizim cavab isə orta hesabla 1.34 sözdür. Mühitdə fastText
yoxdur, ona görə onun bu cütdə davranışı barədə iddia edilmir.
