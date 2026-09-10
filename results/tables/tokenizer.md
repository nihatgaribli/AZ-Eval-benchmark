# Tokenizator məhsuldarlığı

Bir sözə düşən token sayı, datasetin sual mətnləri üzərində.

| Model | AZ | EN | AZ / EN |
|---|---|---|---|
| `issai/Qwen3.5-4B-Base-Kazakh` | 3.00 | 1.40 | **2.14x** |
| `Qwen/Qwen3.5-4B-Base` | 3.00 | 1.40 | **2.14x** |
| `Qwen/Qwen3-1.7B` | 3.51 | 1.41 | **2.49x** |
| `Qwen/Qwen3-VL-4B-Instruct` | 3.51 | 1.41 | **2.49x** |
| `Qwen/Qwen3-VL-4B-Thinking` | 3.51 | 1.41 | **2.49x** |
| `issai/Qolda-AVL-5B` | 3.51 | 1.41 | **2.49x** |
| `microsoft/Phi-3.5-mini-instruct` | 4.06 | 1.52 | **2.66x** |
| `tiiuae/Falcon3-3B-Instruct` | 3.91 | 1.37 | **2.86x** |

Azərbaycan dili hər tokenizatorda ingiliscədən bahadır: ən yaxşı halda 2.14x (`issai/Qwen3.5-4B-Base-Kazakh`), ən pisdə 2.86x (`tiiuae/Falcon3-3B-Instruct`).

Bu, modelin bilikindən asılı olmayan struktur dezavantajdır: eyni mənanı
daha çox və daha xırda fraqmentdə emal etmək lazım gəlir. Səbəb-nəticə
iddiası DEYİL, izahedici kontekstdir.

## Cüt daxilində tokenizator eynidirmi (ÖLÇÜLÜR)

Əlavə olunan tokenlər İKİ növə ayrılır. Xüsusi tokenlər
(`<|audio_start|>` kimi) idarəetmə nişanlarıdır və mətnin necə
parçalandığını dəyişmir. Adi SÖZ əlavə etmək isə tokenizasiyanın
özünü dəyişir və nəzarəti pozur.

| Cüt | Əlavə söz | Əlavə xüsusi token | Nəzarət qurulur? |
|---|---|---|---|
| Qazax 1 | 0 | 3 | bəli |
| Qazax 2 | 16000 | 0 | **XEYR** |
| Türk 1 | 12312 | 0 | **XEYR** |
| Türk 2 | 0 | 0 | bəli |
| Kiril 3 (qeyri-qazax) | 0 | 0 | bəli |
| Rus 1 (ağır) | 43047 | 21 | **XEYR** |
| Rus 2 (yüngül) | 0 | 0 | bəli |
| Latın 3 (qeyri-türk) | 0 | 0 | bəli |
| Gürcü (qeyri-latın, qeyri-kiril) | 0 | 0 | bəli |
| SEA (qarışıq yazı) | 0 | 0 | bəli |
| Macar (latın, eyni baza) | 32768 | 0 | **XEYR** |
| Latın 4 (Qwen bazası) | 0 | 0 | bəli |
| Latın 5 (Qwen bazası) | 0 | 0 | bəli |

NƏZARƏT QURULAN CÜTLƏR: **Qazax 1**, **Türk 2**, **Kiril 3 (qeyri-qazax)**, **Rus 2 (yüngül)**, **Latın 3 (qeyri-türk)**, **Gürcü (qeyri-latın, qeyri-kiril)**, **SEA (qarışıq yazı)**, **Latın 4 (Qwen bazası)**, **Latın 5 (Qwen bazası)**.
Burada hər iki model mətni eyni parçalara bölür, yəni **cüt
daxilindəki fərq tokenizasiya ilə izah edilə bilməz**. Fərq
çəkilərdədir, girişdə deyil.

NƏZARƏT QURULMAYAN CÜTLƏR: **Qazax 2**, **Türk 1**, **Rus 1 (ağır)**, **Macar (latın, eyni baza)**.
Burada lüğətə minlərlə söz əlavə edilib, yəni tokenizasiya
alternativ izah olaraq QALIR və həmin cütlərdən çıxarılan nəticə
bu şərtlə oxunmalıdır.

Lüğətin genişlədilməsi adi fine-tune-dan qat-qat böyük
müdaxilədir: model yeni tokenlər üçün embeddinq öyrənməli və
köhnə paylanmanı yenidən qurmalıdır.

ƏSAS NƏTİCƏYƏ TƏSİRİ. Xoşbəxtlikdən nəzarət qurulan cütlər hər
İKİ tərəfdə var: biri kiril, biri latın. Deməli əsas müqayisə
onların üzərində qurula bilir və genişlədilmiş lüğətli cütlər
təsdiqləyici rol oynayır, daşıyıcı yox.
