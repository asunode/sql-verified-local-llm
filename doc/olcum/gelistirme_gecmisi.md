# Geliştirme geçmişi (istem revizyonları)

Kural: en çok 3 istem revizyonu; her revizyondan sonra geliştirme seti (20 istek) yeniden çalıştırılır ve buraya bir satır yazılır. İstem sürümü = dosyanın SHA-256 ilk 12 hanesi.

| Sürüm | Tarih | Değişiklik | Sonuç |
|---|---|---|---|
| v0 öncesi | 2026-11-20 | `atama_sistem.txt`: kural 5 eklendi ("atandi" tanımı). Bulgu geliştirme seti dışından, kendi yazdığım bir cümleyle: Çağrı B, gerekçede atamayı anlatıp her seferinde `mumkun_degil` + boş liste dönüyordu. | O cümle 1. turda geçti. Set henüz çalıştırılmamıştı. |
| v0 | 2026-11-20 | Taban. atama_sistem.txt f09040e1f110, ihtiyac_sistem.txt a091cdfe0aa4. | A 20/20; B 18/18 1. turda; model–atayıcı kararı 18/18 aynı; ort. 66.7 sn, en uzun 173.2 sn. (`2026-11-20_gelistirme_v0.md`) |
| — | 2026-11-20 | Revizyon yapılmadı: tabanda düzeltilecek hata kalmadı, bu sette ölçülebilir bir iyileşme mümkün değil. | 0/3 revizyon kullanıldı. |

## Adım 6 — gerileme (geliştirme seti 20 + doğrulama seti v1 30)

Kural: en çok 2 istem revizyonu; her revizyondan sonra iki set de uçtan uca (model + atayıcı) yeniden çalıştırılır. v1 görülmüş settir (T-26). Tablosuz koşu tekrarlanmaz.

| Sürüm | Tarih | Değişiklik | Sonuç |
|---|---|---|---|
| r0 | 2026-11-20 | F1–F4: şemada `adet` ve `baglam_ifadeleri`; SAYI_UYUSMAZ ve BAGLAM_CELISKI denetimi (sözlük veritabanında); `tamam` + boş liste geçerli; WAKE/GPIO/PWM tanımları. ihtiyac_sistem.txt 9d73663cf149 (yeniden yazıldı), atama_sistem.txt f09040e1f110 (değişmedi). | Geliştirme: A 19/20, B 19/19 1. turda, karar hakemle 18/18. v1 (görülmüş): A 28/30, B 22/1/2 (1./2./3. tur) + 1 KULLANICIYA, karar hakemle 25/26. SAYI_UYUSMAZ 1 + 3 istek, BAGLAM_CELISKI 0. Yanlışlar: G09 (RMII Ethernet → GPIO_OUT), V01 (dayanakta "de" atlandı, 3 tur DAYANAK_YOK), V04 (SAYI_UYUSMAZ "bir" yüzünden doğru adet 2'yi 1'e zorladı). (`2026-11-20_gerileme_r0.md`) |
| r1 | 2026-11-20 | ihtiyac_sistem.txt fa82cd182666: kural 2'ye tek cihazın birden çok hattı (dayanakta sayı sözcüğü olmadan, adet = hat sayısı); kural 5'e "sürekli parça, içinden sözcük atlanmaz"; kural 7'ye "desteklenmeyen arayüz GPIO ya da başka arayüzle karşılanmaz". Kural 2 ve 1. örnekteki tırnaklı parçalar v1'de geçtiği için değiştirildi (test genişletildi). Çağrı A denetleyicisinin DAYANAK_YOK ve SAYI_UYUSMAZ geri bildirim metinleri aynı yönde genişletildi. | Geliştirme: A 19/20, B 19/19 1. turda, karar hakemle 18/18, SAYI_UYUSMAZ 0. v1 (görülmüş): A 30/30, B 22/1/2 + 1 KULLANICIYA (V23), karar hakemle 25/26, SAYI_UYUSMAZ 2 istek (V23, V24; 2. turda düzeldi), BAGLAM_CELISKI 0. V04 ve V01 düzeldi; V28 (DS18B20) `tamam [GPIO_OUT]` yerine `desteklenmiyor` verdi (kabul seçeneklerinde var). G09 yine yanlış: "RMII üzerinden" dayanağı ile GPIO_OUT ×5 (yeni çok hatlı kuralı kullandı). (`2026-11-20_gerileme_r1.md`) |
| r2 | 2026-11-20 | ihtiyac_sistem.txt 164fa748b37b: kural 2'deki çok hatlı cihaz yalnız "plain input or output lines" için; kural 7'ye "listede olmayan bir veri yolu ya da bağlantı üzerinden konuşan cihaz, sinyalleri GPIO ile taklit edilebilse de desteklenmiyor". Kod değişmedi. | Geliştirme: A 19/20 (A turları 17/3/0, fazla turlar DAYANAK_YOK), B 18/18 1. turda, karar hakemle 18/18, SAYI_UYUSMAZ 0. v1 (görülmüş): A 30/30 (25/5/0), B 23/1/2 + 1 KULLANICIYA (V23, Çağrı B), karar hakemle 26/27, SAYI_UYUSMAZ 2 istek (V23, V24), BAGLAM_CELISKI 0. G09 artık `desteklenmiyor` ("Ethernet PHY"), pin atanmıyor; ihtiyaç listesi dolu olduğu için geliştirme setinin katı puanlamasında yine yanlış (T-35). V28 yeniden `tamam [GPIO_OUT]`. (`2026-11-20_gerileme_r2.md`) |
| — | 2026-11-20 | Son sürüm r2 (ihtiyac_sistem.txt 164fa748b37b). 2/2 revizyon kullanıldı. v2 dondurma: `2026-11-20_v2_dondurma.md`. | |
