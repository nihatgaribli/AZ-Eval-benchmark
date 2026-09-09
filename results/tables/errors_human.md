# Xəta taksonomiyası — insan hissəsi

Yalnız maşının SUSDUĞU sətirlər etiketlənib: normalizasiya zənciri
kömək etmirsə, səbəb insan tərəfindən təyin olunmalıdır.

Etiketlənən sətir: 159.

| Etiket | `issai__Qwen3.5-4B-Base-Kazakh` | `ytu-ce-cosmos__Turkish-Llama-8b-v0.1` |
|---|---|---|
| faktual | 29 (41%) | 37 (42%) |
| format | 4 (6%) | 1 (1%) |
| başqa dil | 1 (1%) | 23 (26%) |
| mənasız | 37 (52%) | 27 (31%) |
| qızıl səhv | 0 (0%) | 0 (0%) |

## Necə oxunmalıdır

Bu cədvəl MAŞININ ETİKETLƏDİYİ hissəni əvəz etmir, onu tamamlayır.
Maşın orfoqrafik xətaları tutur (yazı sistemi, diakritika,
morfologiya); burada isə onun tuta bilmədikləri var.

`başqa dil` etiketi ayrıca vacibdir: model faktı bilir, amma səhv
dildə yazır. Bu, kiril halının LATIN əlifbalı analoqudur və
transliterasiya onu tuta bilmir, çünki əlifba onsuz da düzdür.

## AÇIQLAMA: 24 sətir SONRADAN yenidən etiketləndi

Birinci keçiddə `başqa dil` etiketi heç işlədilmədi və türkcə
yazılmış cavablar `format` sayıldı. Səbəb tərifin qeyri-dəqiq
izahı idi.

MEYAR: model EYNİ ANLAYIŞI başqa dildə yazıbsa, bu, dil
səhvidir, forma səhvi deyil (`yapon dili` -> `Japonca`).
Cavabın özü yanlışdırsa, türk yer adı içində olsa belə,
etiket dəyişmir (`Şamaxı` -> `Bakü` faktual səhvdir).

Yenidən etiketləmə SONRADAN aparılıb və bu, gizlədilmir:
hər belə sətrin `qeyd` sahəsində köhnə etiket saxlanılır.
Nəticəyə baxan adam dəyişikliyi izləyə bilər.
