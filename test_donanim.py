import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from gpiozero import MCP3008, Button

# --- 1. DONANIM AYARLARI ---

# OLED Ekran Ayarları (I2C)
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)

# Joystick ve MCP3008 Ayarları
# MCP3008'in 0. kanalına VRx (Yatay), 1. kanalına VRy (Dikey) bağlamıştık.
joy_x = MCP3008(channel=0)
joy_y = MCP3008(channel=1)

# Joystick Butonu (GPIO 17'ye bağlamıştık)
joy_buton = Button(17)

# --- 2. EKRANI TEMİZLE ---
oled.fill(0)
oled.show()

# Çizim yapmak için boş bir tuval oluştur
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

print("Test Başlıyor... Joystick'i oynat! Çıkış için CTRL+C")

try:
    while True:
        # --- 3. VERİ OKUMA ---
        # MCP3008 0 ile 1 arasında değer verir. (Örn: 0.5 tam orta)
        x_deger = joy_x.value  
        y_deger = joy_y.value
        buton_basili = joy_buton.is_pressed

        # --- 4. HESAPLAMA (Joystick -> Ekran Koordinatı) ---
        # Joystick verisini (0.0 - 1.0) ekran boyutuna (0 - 128) uyarla
        # Not: Joystick bazen ters çalışabilir, duruma göre 128 - ... yaparız.
        imlec_x = int(x_deger * 128)
        imlec_y = int(y_deger * 64)

        # Sınırların dışına çıkmasın
        if imlec_x > 120: imlec_x = 120
        if imlec_y > 56: imlec_y = 56

        # --- 5. ÇİZİM ---
        # Her karede ekranı temizle (Siyah dikdörtgen çiz)
        draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

        # Bilgileri Yaz
        draw.text((0, 0), f"X: {x_deger:.2f}", fill=255)
        draw.text((60, 0), f"Y: {y_deger:.2f}", fill=255)

        # İmleci Çiz (Küçük bir kutu)
        draw.rectangle((imlec_x, imlec_y, imlec_x+5, imlec_y+5), outline=255, fill=255)

        # Butona basılınca mesaj yaz
        if buton_basili:
             draw.text((30, 30), "BUTON BASILDI!", fill=255)

        # --- 6. EKRANA GÖNDER ---
        oled.image(image)
        oled.show()
        
        # Çok hızlı olursa yavaşlatmak için
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nTest durduruldu.")
    oled.fill(0)
    oled.show()