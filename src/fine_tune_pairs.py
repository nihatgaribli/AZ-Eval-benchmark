"""Qohum dilə köklənmək azərbaycancanı pozurmu, yoxsa məsələ əlifbadadır?

    python -m src.fine_tune_pairs

SUAL. İki qazax fine-tune-u azərbaycancanı pozur. Amma qazax dili
azərbaycancadan İKİ cəhətdən fərqlənir və hər ikisi eyni anda dəyişir:

    qohum türk dilidir      (leksika, qrammatika yaxındır)
    KİRİLLƏ yazılır         (azərbaycanca latındır)

Bu iki amili ayırmadan səbəb deyilə bilməz.

TÜRK CÜTLƏRİ ONLARI AYIRIR. Türk dili də türk dilidir, azərbaycancaya daha da
yaxındır, amma LATIN yazır. Zəncirlər model kartlarından izlənilib:

    mistralai/Mistral-7B-v0.1    ->  Trendyol/Trendyol-LLM-7b-base-v1.0
    meta-llama/Meta-Llama-3-8B   ->  ytu-ce-cosmos/Turkish-Llama-8b-v0.1

İKİ TÜRK CÜTÜ, ÇÜNKİ BİRİ AZDIR. Tək cütlə "latın əlifbalı köklənmə zərər
vermir" iddiası bir ölçmədən asılı olardı, üstəlik `Trendyol`-un mütləq balı
aşağıdır (AZ 7.4%) və aşağı baldan çıxarılan fərq kövrəkdir. İkinci cüt ayrı
baza ailəsindən (Llama-3) və ayrı komandadandır, yəni müstəqil təkrardır.

NİYƏ MÜTLƏQ AZ İTKİSİ KİFAYƏT ETMİR. Hər hansı dilə köklənmə digər dilləri
bir qədər unutdurur. `Trendyol` azərbaycancada 11.5 bənd itirir, amma
İNGİLİSCƏDƏ 24.8 bənd itirir. Onun azərbaycanca itkisi ümumi unutqanlığın
bir hissəsidir, hətta ondan KİÇİKDİR.

ÖLÇÜ: AZ itkisi EKSİ EN itkisi. İngilis tərəfi ümumi deqradasiyanın
göstəricisidir, ona görə fərq "azərbaycanca xüsusi olaraq nə qədər əlavə
zərər gördü" sualına cavab verir. Sətir-sətir cütləşdirilir və bootstrap ilə
interval qurulur.

    müsbət  -> azərbaycanca ümumi deqradasiyadan ARTIQ zərər görüb
    mənfi   -> azərbaycanca nisbətən QORUNUB

ŞƏRAİT SİMMETRİK OLMALIDIR. Cütün iki yarısı EYNİ formatda soruşulmalıdır,
yoxsa fərq modelin özündən yox, sualın verilişindən gələ bilər. Köklənmiş
modellərin heç birində chat şablonu yoxdur, ona görə simmetrik şərait XAM
promptdur və baza modelləri də `--no-chat-template` ilə qaçırılır.

Bu, sonradan tutulmuş səhvdir: əvvəl `Qwen3-VL-4B-Thinking` və
`Qwen3.5-4B-Base` şablonla soruşulurdu. Detallar və ölçülmüş təsir
`results/raw_outputs/invalid_chat_template/README.md` faylındadır.

ÖLÇÜNÜN ZƏİF NÖQTƏSİ, AÇIQ YAZILIR. Fərq olduğuna görə, ingilis itkisi
partlayanda rəqəm mənfiyə düşür, halbuki azərbaycanca vəziyyət yaxşılaşmır.
`Trendyol` məhz belədir: -13.3 bənd alır, amma azərbaycanca mütləq itkisi
digər cütlərlə eyni sıradadır. Ona görə mənfi rəqəm "qorundu" kimi TƏK
BAŞINA oxunmamalıdır; mütləq itkilər həmişə yanında verilir.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from src.analyze import _column, load_runs, score_run
from src.echo_gate import MAX_ECHO, MAX_QUESTION_ECHO, echo_rate, question_echo_rate
from src.extraction_gate import degenerate as extraction_degenerate
from src.build_dataset import load_jsonl
from src.metrics import (
    MODES,
    STRICT,
    TRANSLIT,
    bootstrap_ci,
    compare_paired,
    holm_correction,
)

_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


@dataclass(frozen=True)
class Pair:
    """Bir baza modeli və ondan köklənmiş variant."""

    label: str
    base: str
    tuned: str
    target: str
    script: str

    #: MƏQALƏ İNGİLİSCƏDİR, ona görə şəkil və göndəriş üçün ingiliscə adlar
    #: burada saxlanılır. Ayrı tərcümə cədvəli yaratsaydıq, cüt əlavə
    #: ediləndə səssizcə köhnələrdi.
    label_en: str = ""
    target_en: str = ""
    script_en: str = ""

    @property
    def base_family(self) -> str:
        """Baza modelinin ailəsi, məsələn `Qwen3-VL-4B-Thinking` -> `Qwen`.

        NİYƏ LAZIMDIR. Zərər verən dörd cütün hamısının bazası Qwen-dir və
        zərər verməyən dörd cütün heç birininki deyil, yəni "hədəf kirildir"
        ilə "bazası Qwen-dir" bu dizaynda demək olar ki, eyni proqnozu verir.
        Bu, iddiaya qarşı ən güclü konfaunddur və `between_pairs.py` onu
        ölçmək üçün bu sahəni işlədir.

        Ailə HF təşkilatından yox, model adından çıxarılır: `issai/Qolda-AVL-5B`
        Qwen3-VL üzərində qurulub, amma başqa laboratoriyadan gəlir. Bizi
        maraqlandıran çəkilərin haradan gəldiyidir, kimin yüklədiyi deyil.
        """
        name = self.base.split("/")[-1].lower()
        for family in ("qwen", "gemma", "llama", "mistral", "phi", "falcon"):
            if family in name:
                return family.capitalize() if family != "phi" else "Phi"
        return "digər"


PAIRS = (
    Pair(
        "Qazax 1",
        "Qwen/Qwen3-VL-4B-Thinking",
        "issai/Qolda-AVL-5B",
        "qazax",
        "kiril",
        "Kazakh 1",
        "Kazakh",
        "Cyrillic",
    ),
    Pair(
        "Qazax 2",
        "Qwen/Qwen3.5-4B-Base",
        "issai/Qwen3.5-4B-Base-Kazakh",
        "qazax",
        "kiril",
        "Kazakh 2",
        "Kazakh",
        "Cyrillic",
    ),
    Pair(
        "Türk 1",
        "mistralai/Mistral-7B-v0.1",
        "Trendyol/Trendyol-LLM-7b-base-v1.0",
        "türk",
        "latın",
        "Turkish 1",
        "Turkish",
        "Latin",
    ),
    #: İKİNCİ TÜRK CÜTÜ. Birinci türk cütü tək qalsaydı, "latın əlifbalı
    #: köklənmə zərər vermir" iddiası BİR ölçmədən asılı olardı və o ölçmə
    #: `Trendyol`-un aşağı mütləq balı ilə (AZ 7.4%) yüklüdür. Bu cüt fərqli
    #: baza ailəsindən (Llama-3, Mistral deyil) və fərqli komandadandır, yəni
    #: təkrar müstəqildir.
    #:
    #: Hər iki həlqədə chat template YOXDUR; üçüncü cütdə nəticəni sıfıra
    #: endirən asimmetriya (baza şablonsuz, fine-tune şablonla) burada
    #: quruluşca mümkün deyil.
    Pair(
        "Türk 2",
        "meta-llama/Meta-Llama-3-8B",
        "ytu-ce-cosmos/Turkish-Llama-8b-v0.1",
        "türk",
        "latın",
        "Turkish 2",
        "Turkish",
        "Latin",
    ),
    #: BEŞİNCİ CÜT, 2026-09-08-də ƏLAVƏ EDİLDİ. Bunu gizlətmək olmaz: cüt
    #: əsas nəticələr məlum olandan SONRA seçilib. Səbəbi §10-un birinci
    #: məhdudiyyətidir: hər iki kiril cütü qazaxcaya və hər ikisi ISSAI-dandır,
    #: yəni "kiril" dəyişəni bir hədəf dil və bir laboratoriya ilə təmsil
    #: olunurdu. Rəyçi haqlı olaraq "siz kirili yox, qazaxcanı ölçmüsünüz"
    #: deyə bilərdi.
    #:
    #: UKRAYNACA BU ETİRAZI QAPADIR, çünki kirildir, amma SLAVYANDIR: azərbaycanca
    #: ilə qohumluğu yoxdur. Qazaxcada yazı və qohumluq eyni istiqamətə işarə
    #: edir və ayrıla bilmir; burada yalnız yazı qalır.
    #:
    #: Cüt seçilərkən nəticəyə BAXILMAYIB, yalnız quruluş yoxlanılıb:
    #:   - davamlı ilkin öyrətmə (Qolda ilə eyni mexanizm, təkcə instruksiya yox)
    #:   - tokenizator tam eyni (0 əlavə söz parçası, ölçülüb)
    #:   - hər iki tərəf instruct, yəni şablon asimmetriyası quruluşca yoxdur
    #:   - fərqli laboratoriya (INSAIT, Sofiya) və fərqli ölkə
    #:
    #: Ailə 32 -> 40 testə böyüyür, yəni Holm SƏRTLƏŞİR. Əlavə etmək
    #: mənalılıq qazandıra bilməz, yalnız itirə bilər.
    #:
    #: TEST HƏR İKİ TƏRƏFƏ İŞLƏYƏ BİLƏR. Artıq zərər çıxmasa, bu, yazı
    #: izahının ƏLEYHİNƏ dəlildir və səbəbin qazaxcaya və ya ISSAI reseptinə
    #: xas olduğunu göstərir. Nəticə nə olursa olsun yazılır.
    Pair(
        "Kiril 3 (qeyri-qazax)",
        "google/gemma-3-4b-it",
        "INSAIT-Institute/MamayLM-Gemma-3-4B-IT-v1.0",
        "ukrayna",
        "kiril",
        "Cyrillic 3",
        "Ukrainian",
        "Cyrillic",
    ),
    #: ALTINCI VƏ YEDDİNCİ CÜT, 2026-09-09. Kiril 3 bir etirazı açıq qoydu:
    #: `MamayLM` ingiliscədə cəmi 1.1 bənd itirir, yəni ÇOX YÜNGÜL
    #: uyğunlaşdırmadır. Sıfır nəticəsi "qohum deyil"dən yox, "model demək
    #: olar dəyişməyib"dən gələ bilər. Bu iki cüt həmin etirazı hədəfləyir.
    #:
    #: Hər ikisi rus dilinədir (kiril, slavyan, azərbaycanca ilə qohum deyil)
    #: və EYNİ bazadan çıxır, ona görə uyğunlaşdırmanın GÜCÜ dəyişən, hədəf
    #: dil isə sabitdir:
    #:
    #:   Rus 1  davamlı ilkin öyrətmə + lüğət əvəzlənməsi -> AĞIR
    #:   Rus 2  yalnız instruksiya kökləməsi              -> YÜNGÜL
    #:
    #: Rus 1 ağır olduğu halda zərər verməsə, "yüngüllük" izahı düşür və
    #: qarşılıqlı təsir möhkəmlənir. Zərər versə, qarşılıqlı təsir düşür və
    #: yazı təkbaşına izahı qayıdır. Hər iki nəticə yazılır.
    #:
    #: TOKENİZATOR: Rus 1-də lüğət ƏVƏZLƏNİB (151669 -> 146260), Rus 2-də
    #: eynidir. Rus 1 üçün bu, testi MÜHAFİZƏKAR edir: dəyişmiş tokenizator
    #: zərəri artırmalıdır, ona görə "zərər yoxdur" nəticəsi daha güclüdür.
    #:
    #: Revizyonlar (Ruadapt kartı "çəkilər yenilənə bilər" deyir):
    #:   Qwen/Qwen3-4B                        1cfa9a720891
    #:   RefalMachine/RuadaptQwen3-4B-Hybrid  bb890732923b
    #:   Vikhrmodels/QVikhr-3-4B-Instruction  b2a4232a1f3e
    #:
    #: Ailə 40 -> 56 testə böyüyür, yəni Holm yenə sərtləşir.
    Pair(
        "Rus 1 (ağır)",
        "Qwen/Qwen3-4B",
        "RefalMachine/RuadaptQwen3-4B-Hybrid",
        "rus",
        "kiril",
        "Russian 1",
        "Russian",
        "Cyrillic",
    ),
    Pair(
        "Rus 2 (yüngül)",
        "Qwen/Qwen3-4B",
        "Vikhrmodels/QVikhr-3-4B-Instruction",
        "rus",
        "kiril",
        "Russian 2",
        "Russian",
        "Cyrillic",
    ),
    #: SƏKKİZİNCİ CÜT, 2026-09-09. 2x2 dizaynın SON BOŞ XANASI:
    #: qohum DEYİL + eyni əlifba.
    #:
    #:                      eyni əlifba (latın)   fərqli əlifba (kiril)
    #:   qohum (türk)       Türk 1, Türk 2        Qazax 1, Qazax 2
    #:   qohum deyil        BU CÜT                Kiril 3, Rus 1, Rus 2
    #:
    #: DİQQƏT: bu xana iki hipotezi AYIRD ETMİR. Həm "qarşılıqlı təsir", həm
    #: "yazı təkbaşına" izahı burada zərər GÖZLƏMİR. Onda niyə ölçülür?
    #:
    #: Çünki metrikanın özünü yoxlayır. Norveç dilinə kökləmək azərbaycancaya
    #: zərər versəydi, bu, "hər hansı fine-tune azərbaycancanı pozur" demək
    #: olardı və bütün çərçivə çökərdi. Yəni bu, hipotez testi yox, ALƏTİN
    #: sağlamlıq yoxlamasıdır və nəticəsi gözlənilən olsa da yazılmalıdır.
    #:
    #: Norveç dili german qrupundandır, azərbaycanca ilə heç bir qohumluğu
    #: yoxdur və latın əlifbası işlədir. Baza MamayLM ilə EYNİDİR
    #: (`gemma-3-4b-it`), ona görə eyni bazadan kiril/latın müqayisəsi çıxır.
    #:
    #: Tokenizator ölçüldü: 0 əlavə söz parçası, 0 idarə tokeni. Şablon hər
    #: iki tərəfdə var, yəni asimmetriya quruluşca mümkün deyil.
    #:
    #: Ailə 56 -> 64 testə böyüyür.
    Pair(
        "Latın 3 (qeyri-türk)",
        "google/gemma-3-4b-it",
        "NbAiLab/borealis-4b",
        "norveç",
        "latın",
        "Latin 3",
        "Norwegian",
        "Latin",
    ),
    #: DOQQUZUNCU CÜT. Yazı iddiasının KİRİLDƏN KƏNARA yayılıb-yayılmadığını
    #: yoxlayır: gürcü əlifbası (mxedruli) nə latındır, nə kiril.
    #:
    #: MƏHDUDİYYƏT ƏVVƏLCƏDƏN BİLİNİR VƏ YAZILIR: bazanın azərbaycancası
    #: cəmi 6.5%-dir, yəni itirməyə çox az yer var. MÜSBƏT nəticə mənalı
    #: olar (döşəməyə baxmayaraq zərər görünür), MƏNFİ nəticə isə zəif
    #: dəlildir, çünki 6.5%-dən 8-10 bənd itirmək mümkün deyil.
    #:
    #: Sınaqda model bəzən cavab əvəzinə SUALI təkrarlayırdı; buna görə
    #: `echo_gate` genişləndirildi. Qapıdan keçib-keçmədiyi ölçüləcək.
    Pair(
        "Gürcü (qeyri-latın, qeyri-kiril)",
        "Qwen/Qwen3-1.7B",
        "GiorgiGE/Kolkha-Mini-Georgian",
        "gürcü",
        "mxedruli",
        "Georgian",
        "Georgian",
        "Mkhedruli",
    ),
    #: ONUNCU CÜT. Bazası QOLDA İLƏ EYNİDİR (`Qwen3-VL-4B-Instruct`), yəni
    #: ən böyük zərəri verən cütün bazası. Eyni bazadan fərqli hədəf.
    #:
    #: HƏDƏF YAZISI QARIŞIQDIR və bu, qəsdən belə yazılır: SEA-LION
    #: vyetnam/indonez/malay/filippin (latın) ilə yanaşı tay, birma və
    #: tamil (qeyri-latın) dillərinə uyğunlaşdırılıb. Ona görə nə təmiz
    #: latın, nə təmiz qeyri-latın cütü sayılır.
    #:
    #: Buna baxmayaraq dəyərlidir: zərər verməsə, "qeyri-latın hədəf zərər
    #: verir" iddiası zəifləyir, çünki tay/birma/tamil qeyri-latındır.
    #: Zərər versə, iddia genişlənir. Hər iki nəticə məlumat verir.
    Pair(
        "SEA (qarışıq yazı)",
        "Qwen/Qwen3-VL-4B-Instruct",
        "aisingapore/Qwen-SEA-LION-v4-4B-VL",
        "cənub-şərqi asiya",
        "qarışıq",
        "SEA",
        "SE Asian",
        "mixed",
    ),
    #: ON BİRİNCİ CÜT. Rus cütləri ilə EYNİ BAZADAN (`Qwen3-4B`) latın hədəf:
    #: eyni bazadan kiril/latın müqayisəsi verir, bu isə hazırda yoxdur.
    #: Model qapalı repodur, istifadəçi 2026-09-09-da giriş aldı.
    #:
    #: TOKENİZATOR ÖLÇÜLDÜ VƏ NƏTİCƏ MARAQLIDIR: lüğətin ÖLÇÜSÜ eynidir
    #: (151669), amma 32768 token FƏRQLİDİR. Yəni lüğət böyüdülməyib,
    #: məzmunu qismən əvəz edilib. Ölçüyə baxsaydıq "eynidir" deyərdik;
    #: `added_tokens` çoxluq müqayisəsi apardığı üçün tutuldu.
    #:
    #: SINAQDA DEGENERATİV ÇIXDI: model cavab vermək əvəzinə yeni sual-cavab
    #: cütləri uydurur: sual sətri, sonra cavab sətri, sonra yenə sual.
    #: Dörd üslubun heç birində düzəlmir. Qapılar qərar verəcək; nəticə nə
    #: olursa olsun yazılır.
    Pair(
        "Macar (latın, eyni baza)",
        "Qwen/Qwen3-4B",
        "elte-nlp/Racka-4B",
        "macar",
        "latın",
        "Hungarian",
        "Hungarian",
        "Latin",
    ),
    #: BAZA KONFAUNDUNU QIRMAQ ÜÇÜN ELAN EDİLİR, nəticə hesablanmamışdan
    #: əvvəl. Zərər verən dörd cütün hamısının bazası Qwen-dir, ona görə
    #: "hədəf kirildir" ilə "bazası Qwen-dir" indiyə qədər demək olar ki,
    #: eyni proqnozu verirdi. Qwen bazası + LATIN hədəf ikisini ayırır:
    #: yazı izahı zərər GÖZLƏMİR, baza izahı GÖZLƏYİR.
    #:
    #: Macar cütü məhz bu idi və sual-təkrarı qapısından keçmədi. Bu ikisi
    #: onun əvəzidir və hər ikisinin bazası ARTIQ ölçülüb, yəni cütün baza
    #: yarısı yenidən qaçırılmır.
    #:
    #: Bask/qalisiya/kataloniya (Latxa) və fransız (Luth) hədəfləri
    #: bütünlüklə latındır. Nəticə nə olursa olsun yazılır: zərər çıxsa,
    #: yazı izahı zəifləyir və konfaund baza tərəfinə keçir.
    Pair(
        "Latın 4 (Qwen bazası)",
        "Qwen/Qwen3-VL-4B-Instruct",
        "HiTZ/Latxa-Qwen3-VL-4B-Instruct",
        "bask",
        "latın",
        "Latin 4",
        "Basque",
        "Latin",
    ),
    Pair(
        "Latın 5 (Qwen bazası)",
        "Qwen/Qwen3-1.7B",
        "kurakurai/Luth-1.7B-Instruct",
        "fransız",
        "latın",
        "Latin 5",
        "French",
        "Latin",
    ),
)


def _common(runs, pair: Pair, dataset) -> list[str]:
    keys = [
        (pair.base, "az"),
        (pair.tuned, "az"),
        (pair.base, "en"),
        (pair.tuned, "en"),
    ]
    if any(k not in runs for k in keys):
        return []
    ids = set(dataset)
    for key in keys:
        ids &= runs[key].ids
    return sorted(ids)


def confirmatory_table(dataset, runs, seed: int = 0) -> str:
    """TƏSDİQLƏYİCİ ailə: yalnız əvvəlcədən elan edilmiş cütlər.

    NİYƏ AYRICA AİLƏ. `analyze.py` cədvəlləri gördüyü hər model cütünü
    müqayisə edir və Holm düzəlişini həmin siyahıya görə aparır. 14 model
    əlavə olunanda ailə 474 testə çatdı və layihənin ƏSAS hipotezinin p
    qiyməti 0.018-dən 0.047-yə sürüşdü. Halbuki həmin 14 model bu hipotezi
    ÜMUMİYYƏTLƏ sınamır: onlar genişlik üçün əlavə edilib.

    Əvvəlcədən elan edilmiş hipotezi sonradan əlavə edilmiş kəşfiyyatçı
    testlərə görə cəzalandırmaq səhvdir. Ona görə burada ailə hipotezin öz
    ölçüsündədir: `PAIRS` × zəncir × dil.

    BU, AİLƏNİ NƏTİCƏ ALINANA QƏDƏR DARALTMAQ DEYİL. `PAIRS` siyahısı
    modullarda və commit tarixində əvvəlcədən yazılıb; 14 modelli süpürgə
    bu gün əlavə olunub. Kəşfiyyatçı süpürgə silinmir, `analyze.py`
    cədvəllərində olduğu kimi qalır və orada öz ailəsi ilə düzəldilir.

    AİLƏ BÖYÜYƏNDƏ NƏ OLUR. Dördüncü cüt əlavə olunanda ailə 24-dən 32 testə
    çıxdı. Holm düzəlişi ailə böyüdükcə SƏRTLƏŞİR, yəni bu dəyişiklik əsas
    nəticəni asanlaşdırmır, çətinləşdirir. İstiqamət mühümdür: ailəni
    böyüdərək nəticə "qazanmaq" mümkün deyil, yalnız itirmək mümkündür.
    """
    entries: list[tuple[str, str, str, Any]] = []
    for pair in PAIRS:
        ids = _common(runs, pair, dataset)
        if not ids:
            continue
        for language in ("az", "en"):
            for mode in MODES:
                a = _column(
                    score_run(runs[(pair.base, language)], dataset, mode, ids), "em", ids
                )
                b = _column(
                    score_run(runs[(pair.tuned, language)], dataset, mode, ids), "em", ids
                )
                entries.append((pair.label, language, mode.name, compare_paired(a, b, seed=seed)))

    if not entries:
        return "_Elan edilmiş cüt tapılmadı._"

    adjusted = holm_correction([e[3].p_value for e in entries])
    lines = [
        f"Ailə {len(entries)} testdir: {len(PAIRS)} elan edilmiş cüt, "
        f"{len(MODES)} zəncir, 2 dil.",
        "",
        "| Cüt | Dil | Zəncir | Baza | Köklənmiş | Fərq | p | p (Holm) | Mənalı |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for (label, language, mode, result), p_adj in zip(entries, adjusted, strict=True):
        lines.append(
            f"| {label} | {language.upper()} | {mode} | {100 * result.mean_a:.1f}% | "
            f"{100 * result.mean_b:.1f}% | {100 * result.diff:+.1f}pp | "
            f"{result.p_value:.4f} | {p_adj:.4f} | "
            f"{'bəli' if p_adj < 0.05 else 'xeyr'} |"
        )
    return "\n".join(lines)


def _gate_failure(runs, pair, dataset) -> str | None:
    """Cütün hansısa yarısı hansısa qapıdan keçmirsə, səbəbi qaytarır.

    NİYƏ BURADA. Qapıdan keçməyən qaçışın rəqəmi cədvəldə olduğu kimi
    görünsə, oxucu onu ölçmə sayır. İki nümunə:

      `Kolkha-Mini-Georgian` ingiliscədə səhvlərinin 42.4%-ində cavabı XAM
      MƏTNDƏ saxlayır; cədvələ -17.8pp kimi girərdi.

      `Racka-4B` azərbaycanca sualların 68.4%-ini geri yazır (ingiliscədə
      1.6%), yəni ölçmə ikitərəfli müqayisənin BİR tərəfində sınıb.

    BÜTÜN qapılar yoxlanılır, yalnız çıxarış deyil. Racka çıxarış qapısından
    KEÇİR (12.0%), ona görə tək qapıya baxsaydıq onu ölçmə sayardıq.
    """
    checks = (
        ("nümunə təkrarı", lambda run: echo_rate(run), MAX_ECHO),
        ("sual təkrarı", lambda run: question_echo_rate(run, dataset), MAX_QUESTION_ECHO),
    )
    for model in (pair.base, pair.tuned):
        for language in ("az", "en"):
            run = runs.get((model, language))
            if run is None:
                continue
            for name, measure, limit in checks:
                share = measure(run)
                if share > limit:
                    return (
                        f"`{model}` [{language}] {name} qapısından keçmir: "
                        f"{100 * share:.1f}%"
                    )
            share = extraction_degenerate(run, dataset)
            if share is not None:
                return (
                    f"`{model}` [{language}] çıxarış qapısından keçmir: "
                    f"səhvlərin {100 * share:.1f}%-ində cavab xam mətndədir"
                )
    return None


def build_report(dataset, runs, seed: int = 0) -> str:
    lines = [
        "# Fine-tune cütləri: qohumluq, yoxsa əlifba?",
        "",
        "| Cüt | Hədəf | Yazı | AZ baza | AZ köklənmiş | AZ itkisi | EN itkisi |",
        "|---|---|---|---|---|---|---|",
    ]
    detail = []
    excluded: list[tuple[str, str]] = []
    for pair in PAIRS:
        ids = _common(runs, pair, dataset)
        if not ids:
            continue

        failure = _gate_failure(runs, pair, dataset)
        if failure is not None:
            excluded.append((pair.label, failure))
            continue

        def column(model, language, mode=STRICT):
            return _column(score_run(runs[(model, language)], dataset, mode, ids), "em", ids)

        az = compare_paired(column(pair.base, "az"), column(pair.tuned, "az"), seed=seed)
        en = compare_paired(column(pair.base, "en"), column(pair.tuned, "en"), seed=seed)
        lines.append(
            f"| {pair.label} | {pair.target} | {pair.script} | "
            f"{100 * az.mean_a:.1f}% | {100 * az.mean_b:.1f}% | "
            f"{100 * az.diff:+.1f}pp | {100 * en.diff:+.1f}pp |"
        )

        # Sətir-sətir: (AZ itkisi) - (EN itkisi).
        base_az, tuned_az = column(pair.base, "az"), column(pair.tuned, "az")
        base_en, tuned_en = column(pair.base, "en"), column(pair.tuned, "en")
        excess = [
            (base_az[i] - tuned_az[i]) - (base_en[i] - tuned_en[i])
            for i in range(len(ids))
        ]
        ci = bootstrap_ci(excess, seed=seed)
        # VERDİKT ÜÇÜN İNTERVAL TƏK BAŞINA BƏS ETMİR.
        #
        # Artıq zərər FƏRQ metrikidir və hər iki dil YÜKSƏLƏNDƏ də müsbət
        # çıxa bilər. `Latın 5` (fransız) belədir: azərbaycanca 6.5%-dən
        # 10.7%-ə qalxır, ingiliscə 28.6%-dən 38.8%-ə. İnterval sıfırı
        # kəsmir, amma azərbaycancaya dəyən zərər YOXDUR.
        #
        # Simmetrik hal `Türk 1`-dir: mənfi artıq zərər "qorunub" kimi
        # oxunurdu, halbuki azərbaycanca 10.9 bənd itirmişdi və rəqəm
        # yalnız ingiliscənin 26.9 bənd çökməsindən mənfi idi.
        #
        # Ona görə hər iki verdikt öz dilinin FAKTİKİ istiqamətini tələb
        # edir. `between_pairs.is_damaged` eyni şərti işlədir; ikisi
        # ayrılsaydı, layihənin iki cədvəli eyni cüt haqqında bir-birinə
        # zidd danışardı.
        # HƏR İKİ İSTİQAMƏTDƏ AYIRICI ŞƏRT AZƏRBAYCANCANIN ÖZ İSTİQAMƏTİDİR,
        # ingiliscənin yox. İddia azərbaycancaya nə olduğu barədədir.
        az_fell = az.diff > 0
        if ci.low > 0:
            verdict = (
                "azərbaycanca ƏLAVƏ zərər" if az_fell
                else "hər iki dil yaxşılaşıb, ingiliscə daha çox"
            )
        elif ci.high < 0:
            verdict = (
                "ingiliscə daha çox itirib, azərbaycanca da düşüb" if az_fell
                else "azərbaycanca nisbətən QORUNUB"
            )
        else:
            verdict = "fərq sıfırdan ayırd edilmir"
        translit = compare_paired(
            column(pair.base, "az", TRANSLIT), column(pair.tuned, "az", TRANSLIT), seed=seed
        )
        cyrillic = sum(
            1 for i in ids if _CYRILLIC.search(runs[(pair.tuned, "az")].predictions[i])
        )
        detail.append(
            (pair, ci, verdict, translit, 100 * cyrillic / len(ids), len(ids))
        )

    if excluded:
        lines += [
            "",
            "## Qapıdan keçməyən cütlər",
            "",
            "Bu cütlər ELAN EDİLİB, amma ölçmə etibarlı olmadığı üçün",
            "cədvəllərə girmir. Rəqəmləri gizlətmək yox, onları ölçmə kimi",
            "təqdim etməmək üçün.",
            "",
            "| Cüt | Səbəb |",
            "|---|---|",
        ]
        for label, reason in excluded:
            lines.append(f"| {label} | {reason} |")

    lines += [
        "",
        "## Artıq zərər: AZ itkisi eksi EN itkisi",
        "",
        "İngilis itkisi ümumi unutqanlığın ölçüsüdür. Fərq isə azərbaycancanın",
        "ondan ƏLAVƏ nə qədər zərər gördüyünü verir. Mütləq AZ itkisinə baxmaq",
        "kifayət etmir: hər fine-tune bir qədər unutdurur.",
        "",
        "| Cüt | Yazı | Artıq zərər | 95% CI | Nəticə |",
        "|---|---|---|---|---|",
    ]
    for pair, ci, verdict, _translit, _cyr, _n in detail:
        lines.append(
            f"| {pair.label} | {pair.script} | {100 * ci.mean:+.1f}pp | "
            f"[{100 * ci.low:+.1f}, {100 * ci.high:+.1f}] | {verdict} |"
        )

    lines += [
        "",
        "## Transliterasiya və yazı sistemi",
        "",
        "| Cüt | AZ itkisi (STRICT) | AZ itkisi (TRANSLIT) | Köklənmişin kiril payı |",
        "|---|---|---|---|",
    ]
    for pair, _ci, _v, translit, cyr, _n in detail:
        ids = _common(runs, pair, dataset)
        strict = compare_paired(
            _column(score_run(runs[(pair.base, "az")], dataset, STRICT, ids), "em", ids),
            _column(score_run(runs[(pair.tuned, "az")], dataset, STRICT, ids), "em", ids),
            seed=seed,
        )
        lines.append(
            f"| {pair.label} | {100 * strict.diff:+.1f}pp | "
            f"{100 * translit.diff:+.1f}pp | {cyr:.1f}% |"
        )

    lines += [
        "",
        "## Təsdiqləyici ailə",
        "",
        "Aşağıdakı cədvəl Holm düzəlişini YALNIZ əvvəlcədən elan edilmiş cütlər",
        "üzərində aparır. `analyze.py` cədvəlləri isə gördüyü hər model cütünü",
        "sınayır; 14 model əlavə olunanda həmin ailə 474 testə çatdı və əsas",
        "hipotezin p qiyməti 0.018-dən 0.047-yə sürüşdü. Genişlik üçün əlavə",
        "edilmiş və hipotezi ümumiyyətlə sınamayan testlər onu cəzalandırmamalıdır.",
        "",
        "Kəşfiyyatçı süpürgə silinmir: `analyze.py` cədvəllərində qalır və orada",
        "öz ailəsi ilə düzəldilir.",
        "",
        confirmatory_table(dataset, runs, seed),
        "",
        "## Oxunuş",
        "",
        "Qohumluq tək başına zərəri PROQNOZLAŞDIRMIR. Türk dili azərbaycancaya",
        "qazax dilindən daha yaxındır, yəni qohumluq izahı doğru olsaydı, türk",
        "cütləri DAHA çox artıq zərər verməli idi. Vermir.",
        "",
        "Dörd cüt iki qrupa TƏMİZ ayrılır:",
        "",
        "  kiril hədəf   hər ikisində artıq zərər MÜSBƏT, interval sıfırı kənarda",
        "  latın hədəf   heç birində artıq zərər müsbət deyil",
        "",
        "İDDİA BUDUR: kiril əlifbalı hədəfə köklənmə azərbaycancaya ÜMUMİ",
        "unutqanlıqdan ARTIQ zərər verir; latın əlifbalı hədəfə köklənmə vermir.",
        "",
        "İDDİA BU DEYİL: 'latın əlifbaya köklənmə azərbaycancanı QORUYUR.'",
        "Bir cüt bunu göstərsə də, ikincisi göstərmir və birincinin mənfi",
        "rəqəmi aldadıcıdır. Aşağıya bax.",
        "",
        "### İKİ LATIN CÜTÜ NİYƏ FƏRQLƏNİR",
        "",
        "Türk 1-in artıq zərəri güclü MƏNFİDİR, amma bu, azərbaycancanın yaxşı",
        "qorunmasından deyil: onun MÜTLƏQ azərbaycanca itkisi (11.5 bənd) digər",
        "cütlərlə eyni sıradadır. Fərqi yaradan İNGİLİS itkisinin nəhəngliyidir",
        "(24.8 bənd). Artıq zərər fərq olduğuna görə, məxrəc partlayanda kəsr",
        "mənfiyə düşür.",
        "",
        "Türk 2-nin ingilis itkisi daha mötədildir (8.8 bənd) və artıq zərəri",
        "sıfıra yaxın çıxır. Ölçmə baxımından TƏMİZ olan budur.",
        "",
        "DƏRS: tək cütlə qurulan iddia kövrək idi və ikinci cüt onu düzəltdi.",
        "Əvvəlki hesabatda yazılmış 'latın köklənmə azərbaycancanı qoruyur'",
        "cümləsi bir ölçmənin artefaktı imiş. İddia daraldılıb, silinməyib:",
        "kiril və latın arasındakı fərq qalır, çünki latın cütlərinin heç biri",
        "artıq zərər göstərmir, kiril cütlərinin isə hər ikisi göstərir.",
        "",
        "MƏHDUDİYYƏT: hər istiqamətdə iki cüt var və modellər ölçü, ailə,",
        "təlim resepti ilə də fərqlənir. Nəticə istiqaməti göstərir, kəmiyyəti",
        "yox.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="fine_tune_pairs")
    parser.add_argument("--dataset", type=Path, default=Path("data/az_eval_v0.jsonl"))
    parser.add_argument("--raw-dir", type=Path, default=Path("results/raw_outputs"))
    parser.add_argument("--out", type=Path, default=Path("results/tables/pairs.md"))
    parser.add_argument("--seed", type=int, default=0)
    #: Cütün HƏR İKİ yarısı eyni üslubda ölçülməlidir. Bu bayraq üslubu
    #: dəyişməyə imkan verir, amma dəyişiklik həmişə cütün İKİSİNƏ birdən
    #: tətbiq olunur: asimmetriya buraxmaq ölçmə səhvidir.
    parser.add_argument("--prompt-style", default="default")
    args = parser.parse_args(argv)

    dataset: dict[str, dict[str, Any]] = {
        r["id"]: r
        for _, r in load_jsonl(args.dataset)
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }
    runs = {
        (r.key.model, r.key.language): r
        for r in load_runs(args.raw_dir)
        if r.key.prompt_style == args.prompt_style
    }
    report = build_report(dataset, runs, args.seed)
    if args.prompt_style != "default":
        report = report.replace(
            "# Fine-tune cütləri",
            f"# Fine-tune cütləri (`{args.prompt_style}` üslubu)",
            1,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
