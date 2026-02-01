import time
from gpiozero import MCP3008

# Eğer SPI hatası alırsak, donanımsal SPI'ı zorlamak için device=0 kullanıyoruz
joy_x = MCP3008(channel=0, device=0)
joy_y = MCP3008(channel=1, device=0)

print("--- JOYSTICK DEBUG MODU ---")
print("Değerler 0.0 ile 1.0 arasında değişmeli.")
print("Çıkmak için CTRL+C bas.")

while True:
    print(f"X: {joy_x.value:.2f}  |  Y: {joy_y.value:.2f}")
    time.sleep(0.5)