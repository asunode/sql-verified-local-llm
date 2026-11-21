# v3 tekrarlanabilirlik incelemesi (X03, X11) — 2026-11-21

Kaynak: `2026-11-21_v3_ham.jsonl` (Koşu 1 satır 3 ve 11, tekrar satır 48 ve 56). Kod değiştirilmedi.

| | X03 Koşu 1 | X03 tekrar | X11 Koşu 1 | X11 tekrar |
|---|---|---|---|---|
| Sınır isteği gitti mi (süre sn) | evet (2.133) | evet (2.169) | evet (1.956) | evet (2.003) |
| Ayar onbellek_siniri | true | true | true | true |
| Sabit önek = sistem mesajı (karakter) | 5624 | 5624 | 5624 | 5624 |
| Sistem + kullanıcı mesajı birebir aynı | evet | | evet | |
| Kullanıcı mesajı (karakter) | 220 | 220 | 93 | 93 |
| istem_token (prompt_eval_count) | 1648 | 1648 | 1620 | 1620 |
| uretilen_token | 209 | 206 | 172 | 170 |
| Model özeti | 38044be4f923 | 38044be4f923 | 38044be4f923 | 38044be4f923 |
| Önceki istek | X02 (Koşu 1) | X02 (tekrar) | X10 (Koşu 1) | X10 (tekrar) |
| Önceki isteğin ham yanıtı iki koşuda aynı | evet | | evet | |
| Ayrışma noktası (karakter / toplam) | 445 / 570 | | 47 / 428 | |
| Ayrışan dayanak | "acil durdurma butonu ayrı bir giriş" | "acil durdurma butonu" | "SPI (SD kart)" | "SD kart" |
| Arayüz çoklu kümesi | aynı | | aynı | |

Bulgular:
- Girdi tarafında fark yok: sınır isteği iki koşuda da gitti, sistem ve kullanıcı mesajları birebir aynı, model özeti aynı, hemen önceki istek de aynı ve onun yanıtı iki koşuda birebir aynı.
- İki istekte de ayrışma, dayanağın ne kadar uzun yazılacağı noktasında (olasılıkları yakın iki seçenek). Arayüzler ve adetler değişmedi; iki yanıt da kabul listesine uyuyor.
- İkisinden önceki zincir farklı: Koşu 1 X01'den soğuk başladı, tekrar X45'ten sonra başladı. Ollama'nın önbellek ara noktaları (gemma'da kayan pencere dikkati yüzünden yalnız kayıtlı noktalardan devam; `doc/cevirmen_dersleri.md` madde 2) yalnız bir önceki isteğe değil daha önceki isteklere de bağlı olabilir; sınır isteği devam noktasını sabitlemek için var ama bu izde devam noktası görünmüyor. Bu olası açıklama izden doğrulanamıyor.
- İzde önbellekten kaç token geldiği yok: `istem_token` iki koşuda da istemin tamamına yakın (1648 / 1620) ve sınır isteği ~2 sn sürüyor. Sistem istemi CPU'da yeniden işlenseydi bu süre çok daha uzun olurdu; yani bu Ollama sürümünde (0.30.7) `prompt_eval_count` önbellekten gelen tokenları da sayıyor gibi. Çekirdekteki `istem_token` açıklaması ("önbellekten gelenler sayılmaz", `asu_llmcore/ollama.py:57`) bu sürümle uyuşmuyor olabilir. Kesin hata olarak raporlanmıyor; ölçülmedi.
- Net bir yazılım hatası bulunmadı. Nedeni ayırt etmek için izde `prompt_eval_duration` (çekirdek `ollama` alanında topluyor ama `Tur` kaydına geçmiyor) ve devam noktası bilgisi gerekir.
