# Annotatorlararası razılıq

Nümunə: 200 sətir, mənşəyə görə təbəqələndirilib (seed=0).

| İkinci annotatorun qərarı | n | pay |
|---|---|---|
| düzgün | 187 | 93.5% |
| səhv | 13 | 6.5% |
| qeyri-səlis | 0 | 0.0% |

**Razılıq: 93.5%.** Cohen kappa: 0.000 (cüzi).

## Bu rəqəmi necə oxumaq lazımdır

Birinci annotatorun etiketi HƏMİŞƏ `düzgün`-dür, çünki datasetdə olan
sətir onun tərəfindən artıq qəbul edilib. Bu, ölçünün zəif nöqtəsidir
və gizlədilmir: kappa yalnız ikinci annotatorun nə qədər `səhv`
dediyindən asılı olur, iki müstəqil qərar paylanmasından yox.

Buna baxmayaraq rəqəm mənalıdır, çünki əsl sual budur: **müstəqil adam
eyni sətirlərə baxıb nə qədərini rədd edir?** Yüksək rədd nisbəti
datasetin keyfiyyət iddiasını birbaşa zəiflədir; aşağı rədd nisbəti isə
onu müstəqil şəkildə dəstəkləyir.

TAM SİMMETRİK ÖLÇÜ üçün hər iki annotator eyni sətirləri SIFIRDAN,
bir-birindən xəbərsiz yoxlamalı idi. Bu, gələcək iş üçün qeyd edilir.

## Rədd edilən və ya şübhəli sətirlər

- `az-091` [səhv]  ->  — _Fici hind dili həm devanagari, həm də latın qrafikası ilə yazıla bildiyindən sual tək cavablı deyil._
- `az-1045` [səhv]  ->  — _Vəzifə/titul “Şirvanşah” olmalıdır; “Şirvanşahlar” sülalə adıdır._
- `az-1258` [səhv]  ->  — _Siborgium 1974-cü ildə Q. N. Flerovun qrupu və ABŞ-də G. T. Seaborgun qrupu tərəfindən sintez olunub; Yuri Oqanesyan deyil._
- `az-1424` [səhv] Üçbucağın üçüncü bucağını tap: 47 dərəcə və 63 dərəcə. -> 70 — _Sualda bucaqların üçbucağa aid olduğu göstərilmədiyi üçün üçüncü bucaq müəyyən edilmir._
- `az-530` [səhv]  ->  — _Cavab yarımçıqdır və cənub nöqtəsini tam adlandırmır._
- `az-560` [səhv]  ->  — _Sualda ciddi yazı səhvləri var: “aqirliqdad ir” ifadəsi qüsurludur._
- `az-582` [səhv]  ->  — _Füzulinin tanınmış əsəri “Hədiqətüs-süəda”dır; verilən əsər adı uyğun deyil._
- `az-585` [səhv]  ->  — _Sualdakı bəstəkarın adı yazı səhvi ilə verilib: “Üıyeyir” əvəzinə “Üzeyir”._
- `az-631` [səhv]  ->  — _Cavabda düzgün hal adı əvəzinə “#NAME?” xətası verilib._
- `az-636` [səhv]  ->  — _Xəbər şəkilçisinin variantları natamam verilib; “-dir” iki dəfə təkrarlanıb._
- `az-647` [səhv] Azərbaycan dilində aidlik şəkilçisi hansıdır? -> -ki — _Cavabda düzgün şəkilçi əvəzinə “#NAME?” xətası verilib._
- `az-652` [səhv]  ->  — _Xəbər adətən mübtəda haqqında hökmü, hərəkəti və ya halı bildirir; təkcə təsdiqi bildirmir._
- `az-716` [səhv]  ->  — _Asiyada ölkələrin sayı qəbul edilən coğrafi-siyasi təsnifatdan asılı olaraq dəyişir._

Bu sətirlər AVTOMATİK silinmir. Hər biri əl ilə baxılmalı və
ya düzəldilməli, ya da `verified_by: rejected` edilməlidir.

## Mənşəyə görə

| Mənşə | n | düzgün |
|---|---|---|
| `?` | 11 | 0.0% |
| `computed-template` | 47 | 97.9% |
| `manual` | 43 | 97.7% |
| `wikidata-template` | 99 | 100.0% |
