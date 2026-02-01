import time
import random
import threading
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from gpiozero import MCP3008, Button, TonalBuzzer, RGBLED
from gpiozero.tones import Tone

# --- DONANIM AYARLARI ---
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)

joy_x = MCP3008(channel=0, device=0)
joy_y = MCP3008(channel=1, device=0)
buton = Button(17)

buzzer = TonalBuzzer(27, mid_tone=Tone("A4"), octaves=3) 
led = RGBLED(red=22, green=23, blue=25)

# --- OYUN DEĞİŞKENLERİ ---
GENISLIK = 128
YUKSEKLIK = 64
KUTU_BOYUT = 8

oyuncu_x = 10
oyuncu_y = 15 # Yazı için biraz aşağı aldık
hiz = 3

bomba_aktif = False
bomba_x = 0
bomba_y = 0
bomba_zaman = 0
PATLAMA_SURESI = 2.0

dusman_x = 100
dusman_y = 50
dusman_hiz_x = 2
dusman_hiz_y = 2

# YENİ: Skor ve Süre
skor = 0
TOPLAM_SURE = 60 # Saniye
baslangic_zamani = time.time()
oyun_bitti = False

# Ses ve Thread Kontrolleri
ses_efekti_caliyor = False
oyun_devam_ediyor = True

# Yazı Fontu (Varsayılan basit font)
font = ImageFont.load_default()

# --- MÜZİK NOTALARI (Hızlandırılmış Gerilim) ---
MUZIK_LISTESI = [
    ("E5", 0.15), (None, 0.05), ("E5", 0.15), (None, 0.2), 
    ("E5", 0.15), (None, 0.2), ("C5", 0.15), ("E5", 0.3), 
    ("G5", 0.3), (None, 0.3), ("G4", 0.3), (None, 0.3)
]

def muzik_cal():
    """Arka plan müziği"""
    while oyun_devam_ediyor and not oyun_bitti:
        for nota, sure in MUZIK_LISTESI:
            if not oyun_devam_ediyor or oyun_bitti: break
            
            if ses_efekti_caliyor:
                buzzer.stop()
                time.sleep(0.1)
                continue
            
            try:
                if nota: buzzer.play(Tone(nota))
                else: buzzer.stop()
            except: pass
            
            # Süre azalınca müzik hızlansın (Heyecan!)
            kalan = TOPLAM_SURE - (time.time() - baslangic_zamani)
            if kalan < 15:
                time.sleep(sure * 0.7) # Hızlı mod
            else:
                time.sleep(sure)

def efekt_patlama():
    global ses_efekti_caliyor
    ses_efekti_caliyor = True
    led.color = (1, 1, 1)
    try:
        buzzer.play(Tone(600))
        time.sleep(0.05)
        buzzer.play(Tone(300))
        time.sleep(0.05)
        buzzer.play(Tone(100))
        time.sleep(0.1)
        buzzer.stop()
    except: pass
    led.color = (0, 0, 0)
    time.sleep(0.1)
    ses_efekti_caliyor = False

def efekt_skor():
    # Puan alınca kısa, mutlu bir ses
    global ses_efekti_caliyor
    ses_efekti_caliyor = True
    led.color = (0, 0, 1) # Mavi yanıp sönsün
    try:
        buzzer.play(Tone("C6"))
        time.sleep(0.1)
        buzzer.play(Tone("E6"))
        time.sleep(0.1)
        buzzer.stop()
    except: pass
    led.off()
    ses_efekti_caliyor = False

def bitis_ekrani_goster():
    """Oyun bitince skoru göster"""
    buzzer.stop()
    led.color = (1, 0, 0) # Kırmızı ışık
    oled.fill(0)
    
    # Ekrana Yazdır
    yazi1 = "SURE BITTI!"
    yazi2 = f"SKOR: {skor}"
    
    # Yazıları ortalamak için basit matematik (Pixel genişliği tahmini)
    draw.rectangle((0, 0, GENISLIK, YUKSEKLIK), outline=0, fill=0)
    draw.text((30, 20), yazi1, font=font, fill=255)
    draw.text((35, 35), yazi2, font=font, fill=255)
    
    oled.image(image)
    oled.show()
    
    # Bitiş melodisi
    try:
        notalar = ["C5", "G4", "E4", "A3"]
        for n in notalar:
            buzzer.play(Tone(n))
            time.sleep(0.2)
        buzzer.stop()
    except: pass
    
    time.sleep(1)
    led.off()

# --- OYUNU BAŞLAT ---
print(f"BOMBERPI V4.0 - SÜRE: {TOPLAM_SURE}sn")
baslangic_zamani = time.time() # Süreyi şimdi başlat

muzik_thread = threading.Thread(target=muzik_cal)
muzik_thread.start()

# Tuval
image = Image.new("1", (GENISLIK, YUKSEKLIK))
draw = ImageDraw.Draw(image)

try:
    while True:
        draw.rectangle((0, 0, GENISLIK, YUKSEKLIK), outline=0, fill=0)

        # --- SÜRE KONTROLÜ ---
        gecen_zaman = time.time() - baslangic_zamani
        kalan_sure = int(TOPLAM_SURE - gecen_zaman)

        if kalan_sure <= 0:
            oyun_bitti = True
            bitis_ekrani_goster()
            break # Döngüden çık, oyun bitti.

        # 1. HAREKET KONTROLLERİ
        jx = joy_x.value
        jy = joy_y.value
        if jx > 0.60: oyuncu_x += hiz
        if jx < 0.40: oyuncu_x -= hiz
        if jy > 0.60: oyuncu_y += hiz
        if jy < 0.40: oyuncu_y -= hiz
        
        # Üst kısımda skor barı var (0-10 piksel), oraya girmesin
        oyuncu_x = max(0, min(oyuncu_x, GENISLIK-KUTU_BOYUT))
        oyuncu_y = max(10, min(oyuncu_y, YUKSEKLIK-KUTU_BOYUT))

        # 2. BOMBA MEKANİĞİ
        if buton.is_pressed and not bomba_aktif:
            bomba_aktif = True
            bomba_x, bomba_y = oyuncu_x, oyuncu_y
            bomba_zaman = time.time()
            
            # Bomba kurma sesi (Thread içinde basit bip)
            def bip():
                global ses_efekti_caliyor
                ses_efekti_caliyor = True
                led.color = (1, 0, 0)
                buzzer.play(Tone("G5"))
                time.sleep(0.1)
                buzzer.stop()
                led.off()
                ses_efekti_caliyor = False
            threading.Thread(target=bip).start()

        if bomba_aktif:
            sure_farki = time.time() - bomba_zaman
            if sure_farki < PATLAMA_SURESI:
                if int(sure_farki * 10) % 2 == 0:
                    draw.rectangle((bomba_x, bomba_y, bomba_x+6, bomba_y+6), outline=255, fill=255)
            elif sure_farki < PATLAMA_SURESI + 0.5:
                # PATLAMA
                patlama_alani = 25
                draw.ellipse((bomba_x-patlama_alani, bomba_y-patlama_alani, 
                              bomba_x+patlama_alani, bomba_y+patlama_alani), outline=255, fill=255)
                
                if sure_farki < PATLAMA_SURESI + 0.1:
                    threading.Thread(target=efekt_patlama).start()

                # VURULMA KONTROLÜ
                if (abs(bomba_x - dusman_x) < patlama_alani) and (abs(bomba_y - dusman_y) < patlama_alani):
                    skor += 1 # PUAN VER!
                    threading.Thread(target=efekt_skor).start() # Mutlu ses
                    dusman_x = random.randint(0, 100)
                    dusman_y = random.randint(15, 50) # Üst bara çarpmasın
            else:
                bomba_aktif = False

        # 3. DÜŞMAN VE ÇİZİM
        dusman_x += dusman_hiz_x
        dusman_y += dusman_hiz_y
        if dusman_x <= 0 or dusman_x >= GENISLIK-8: dusman_hiz_x *= -1
        if dusman_y <= 10 or dusman_y >= YUKSEKLIK-8: dusman_hiz_y *= -1

        draw.rectangle((oyuncu_x, oyuncu_y, oyuncu_x+8, oyuncu_y+8), outline=255, fill=0)
        draw.rectangle((dusman_x, dusman_y, dusman_x+8, dusman_y+8), outline=255, fill=255)

        # --- ÜST BİLGİ ÇUBUĞU ---
        # Üst kısma bir çizgi çek
        draw.line((0, 10, GENISLIK, 10), fill=255)
        # Yazıları yaz
        bilgi_metni = f"SKOR: {skor}   SURE: {kalan_sure}"
        draw.text((2, 0), bilgi_metni, font=font, fill=255)

        oled.image(image)
        oled.show()

except KeyboardInterrupt:
    oyun_devam_ediyor = False
    muzik_thread.join()
    oled.fill(0)
    oled.show()
    buzzer.stop()
    led.off()
    print(f"\nOyun Kapatıldı. SKORUNUZ: {skor}")