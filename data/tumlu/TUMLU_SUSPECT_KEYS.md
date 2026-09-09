# Şübhəli cavab açarları

Dəst: 521 sual. Modellər: 4.

- `Qwen/Qwen3-1.7B` (485 cavab)
- `Qwen/Qwen3-VL-4B-Instruct` (521 cavab)
- `Qwen/Qwen3-VL-4B-Thinking` (460 cavab)
- `issai/Qolda-AVL-5B` (521 cavab)

**36 sətirdə bütün modellər eyni variantda birləşir, amma açar başqasını göstərir** (6.9%).

Kobud düstura görə təsadüfi gözlənti: 6.1.

Permutasiya ilə qurulmuş EMPİRİK sıfır fərziyyəsi: orta 7.8, 95-ci persentil 12. Bu hədd modellərin hərf meylini də nəzərə alır, ona görə düsturdan etibarlıdır. Tapılan 36 rəqəmi həmin həddi keçmirsə, razılıq təsadüfdən ayırd edilmir və siyahı məlumat daşımır.

DİQQƏT: bu, hökm deyil, şübhə siyahısıdır. Modellərin hamısı Qwen ailəsindəndir (Qolda məhz Qwen3-VL-dən köklənib), yəni eyni səhvi etməyə meyllidirlər. Hər sətir insan tərəfindən yoxlanmalıdır.

**ƏL İLƏ YOXLANDI VƏ SİYAHI ETİBARSIZ ÇIXDI.** Yoxlana bilən hər şübhəlidə açar DOĞRU, modellər isə səhv oldu (adrenalin, Daymler, dəqiqə əqrəbi, paraleloqram). Razılıq təsadüfi deyil, amma açarın səhvindən yox, modellərin ORTAQ səhvindən doğur: permutasiya testi təsadüfi razılığı nəzarətə alır, korrelyasiyalı səhvi yox. Metodun işləməsi üçün fərqli ailədən model lazımdır.

## Fənn üzrə

| Fənn | Şübhəli |
|---|---|
| Chemistry | 10 |
| History | 6 |
| Maths | 6 |
| Native L&L | 5 |
| Geography | 4 |
| Physics | 3 |
| Biology | 2 |

## Sətirlər

### `tumlu-az-372` (Biology)

Adrenalin hormonunu hansı vəzi ifraz edir?

- açar: **D** = Böyrəküstü vəzi
- 4 modelin hamısı: **B** = Epifiz vəzi

### `tumlu-az-429` (Biology)

Tumurcuqlanma yolu ilə çoxalan göbələk hansıdır?

- açar: **A** = Maya
- 4 modelin hamısı: **B** = Penisil

### `tumlu-az-106` (Chemistry)

Həllolma əmsalı hansı vahidlə ifadə olunur?

- açar: **B** = q/l
- 4 modelin hamısı: **C** = mol/l

### `tumlu-az-140` (Chemistry)

Avaqadro qanunu maddənin hansı aqreqat halı üçün ödənilir?

- açar: **D** = qaz
- 4 modelin hamısı: **C** = qaz və bərk

### `tumlu-az-504` (Chemistry)

Benzolun 16 hidrogen atomu olan homoloqunun tərkibində neçə karbon atomu var?

- açar: **D** = 11
- 3 modelin hamısı: **C** = 7

### `tumlu-az-66` (Chemistry)

Bir elementin beş atomunun kütləsi 1 a.K.V.-dən 160 dəfə ağırdır. Bu elementin bir molunun kütləsi neçə qramdır?

- açar: **B** = 32q
- 3 modelin hamısı: **C** = 40q

### `tumlu-az-71` (Chemistry)

Valentlik anlayışı ilk dəfə elmə neçənci ildə gətirilib?

- açar: **C** = 1852-ci
- 4 modelin hamısı: **A** = 1842-ci

### `tumlu-az-75` (Chemistry)

200 qr 10%-li məhluldan 40%-li məhlul almaq üçün ona nə qədər 50 %-li məhlul əlavə edilməlidir?

- açar: **C** = 600
- 4 modelin hamısı: **B** = 100

### `tumlu-az-81` (Chemistry)

8M NaOH məhlulu almaq üçün 400 ml 2M NaOH məhlulundan neçə qram su buxarlandırmaq lazımdır?

- açar: **A** = 300
- 2 modelin hamısı: **B** = 200

### `tumlu-az-89` (Chemistry)

Molyar kütləsi 54 qram olan alkin molekulunda neytron sayını müəyyən edin

- açar: **A** = 24
- 3 modelin hamısı: **B** = 30

### `tumlu-az-93` (Chemistry)

Havanın orta molekul kütləsi neçə qram/mol-dur?

- açar: **A** = 29
- 3 modelin hamısı: **C** = 28

### `tumlu-az-98` (Chemistry)

1 mol aren molekulu yanan zaman ayrılan suyu mol sayı n-3-ə bərabər olarsa aren molekulunda karbon atomlarının sayının müəyyən edin

- açar: **B** = n
- 4 modelin hamısı: **C** = n-2

### `tumlu-az-200` (Geography)

Yer kürəsində su nə qədər hissəni tutur?

- açar: **D** = 361 mln.km2
- 3 modelin hamısı: **C** = 133 mln.km2

### `tumlu-az-229` (Geography)

Yaz gecə-gündüz bərabərliyi Nə vaxtdır?

- açar: **A** = Martın 21-də
- 3 modelin hamısı: **B** = Aprelin 21-də

### `tumlu-az-252` (Geography)

Dağın ətəyində atmosfer təzyiqi 760mm.C.S, zirvəsində isə 560mm.C.S olduğunu nəzərə alaraq dağın hündürlüyünü tapın

- açar: **D** = 2km
- 4 modelin hamısı: **B** = 4000m

### `tumlu-az-273` (Geography)

Böyük Qafqazın Azərbaycandan başlayan silsiləsi necə adlanır?

- açar: **A** = Sudur
- 4 modelin hamısı: **B** = Bazardüzü

### `tumlu-az-279` (History)

Səlcuq imperatorluğu neçənci illərdə mövcud olub?

- açar: **C** = 1038-1157
- 4 modelin hamısı: **B** = 1038-1587

### `tumlu-az-284` (History)

Yevlax – Bərdə - Ağdam dəmiryolu neçənci ildə işə salındı?

- açar: **D** = 1967-ci ildə
- 3 modelin hamısı: **B** = 1969-cu ildə

### `tumlu-az-293` (History)

Benzinlə işləyən ilk mühərriki düzəltmişdi

- açar: **A** = Q.Daymler
- 4 modelin hamısı: **C** = R.Dizel

### `tumlu-az-300` (History)

3-cu Vasili 1510-cu ildə Azad etdi:

- açar: **D** = Pskov
- 4 modelin hamısı: **C** = Smolensk

### `tumlu-az-304` (History)

XX əsrin əvvəllərində Yaponiyanın xarici bazarlarda rəqabət apara bilmədiyi ölkələri doğru göstərən variantı müəyyən edin. - <br>a)Rusiya. <br>B)Fransa. <br>C)ABŞ. <br>D)İngiltərə. - -<br>e)Almaniya

- açar: **D** = c. d. e
- 3 modelin hamısı: **B** = b. c. d

### `tumlu-az-316` (History)

Bu milli Azərbaycan diviziyası mayın 2-də Berlinin Brandenburq darvazası üzərinə qələbə bayrağı sancdı

- açar: **D** = 416-cı
- 4 modelin hamısı: **B** = 402-ci

### `tumlu-az-444` (Maths)

xı=x-3, yı=y+1, zı=z-2 paralel köçürməsi  A(5;-1;3) nöqtəsini hansı nöqtəyə çevirir?

- açar: **D** = (2;0;1)
- 2 modelin hamısı: **C** = (1;1;2)

### `tumlu-az-448` (Maths)

Cəmi 119 olan üç fərqli ədədin ikisi 26-dan kiçik olarsa, ən böyüyünün ən kiçik qiymətini tapın

- açar: **D** = 70
- 3 modelin hamısı: **C** = 60

### `tumlu-az-455` (Maths)

Ən böyüyü 2n-3 olan 4 ardıcıl tək ədədin cəmini tapın

- açar: **C** = 8n-24
- 3 modelin hamısı: **B** = 6n-15

### `tumlu-az-491` (Maths)

7/13 kəsrinin surət və məxrəcindən hansı ədədi çıxmaq lazımdır ki, 1/4 alınsın.

- açar: **C** = 5
- 3 modelin hamısı: **B** = 2

### `tumlu-az-492` (Maths)

(ab):b=4 (qalıq 3) isə, a+b=? ( (ab) 2 rəqəmli ədəddir)

- açar: **D** = 12
- 2 modelin hamısı: **C** = 10

### `tumlu-az-519` (Maths)

Paraleloqramın perimetri 60 sm, iki tərəfin fərqi 14 sm-dir. Bu tərəfləri tapın.

- açar: **C** = 8;22
- 3 modelin hamısı: **A** = 9;11

### `tumlu-az-160` (Native L&L)

Mürəkkəb fellər neçə yollarla yaranır?

- açar: **D** = 5
- 4 modelin hamısı: **C** = 4

### `tumlu-az-168` (Native L&L)

Hansı nümunədə isim mənsubiyyətə görə dəyişmişdir

- açar: **D** = hissim
- 4 modelin hamısı: **C** = oğulam

### `tumlu-az-173` (Native L&L)

Məlum növün neçə əlaməti olur?

- açar: **A** = 3
- 4 modelin hamısı: **C** = 7

### `tumlu-az-184` (Native L&L)

Felin lazım şəklinin şəkilçisi hansıdır?

- açar: **D** = -ası, -əsi
- 4 modelin hamısı: **C** = -malı, -məli

### `tumlu-az-196` (Native L&L)

Fel hansı cümlə üzvü ilə ifadə olunur?

- açar: **D** = Xəbər
- 4 modelin hamısı: **C** = Təyin

### `tumlu-az-21` (Physics)

Bir sutka ərzində saatın dəqiqə əqrəbi necə tam dövr edər?

- açar: **A** = 24
- 4 modelin hamısı: **C** = 1440

### `tumlu-az-5` (Physics)

Hidravlik presdə porşenlər bərabər səviyyədə tarazladıqda, porşenlərin yerdəyişmələri nisbəti H2/H1=2 olarsa, porşenlərin altında mayelərin təzyiqləri nisbətini P2/P1 hesablayın

- açar: **A** = 4
- 4 modelin hamısı: **C** = 2

### `tumlu-az-61` (Physics)

Kütləsi 80 kq olan idmançı xizəyin xəttində durmuşdur. Hər bir xizəyin uzunluğu 2m eni 10sm olarsa idmançının xizəyinin təzyiqi nə qədərdir?

- açar: **A** = 2.10 Pa
- 4 modelin hamısı: **C** = 56 Pa

