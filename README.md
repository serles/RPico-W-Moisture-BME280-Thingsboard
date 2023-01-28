# RPico-W-Moisture-BME280-Thingsboard
Measure moisture, temperature, atmospheric pressure &amp; humidity and send data to things board with a raspberry pico W
Author: Sebastian Söll

This project is programmed in micropython on an raspberry pico W and displays the sensor values on a display and on thingsboard.

I have used the following libraries
- BME280: from Paul Cunnane 2016, Peter Dahlebrg 2016, borrowed code from Adafruit Tony DiCola
- SH1106: from Radomir Dopieralski (@deshipu), Robert Hammelrath (@robert-hh)

Used hardware:
- raspberry pico W
- BME280 sensor from berrybase
- sh1106 1.3" 128x64 OLED Display, IIC/ I2C Interface, single colored
- Analogue capacitive soil moisture sensor CAP-SHYG

Wiring:
Display via I2C:
- SDA on GP0
- SCL on GP1

BME280 via I2C:
- SDA on GP20
- SCL on GP21

moisture sensor via
- ADC on GP26

