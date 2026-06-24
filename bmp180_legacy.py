import Adafruit_BMP.BMP085 as BMP085

# Initialize the BMP180 sensor (fully register-compatible with BMP085)
# This library automatically detects the correct I2C bus and uses the default address (0x77)
bmp = BMP085.BMP085()

def read():
    """Return current sensor reading as a dictionary.
    The rest of the project depends only on this interface.
    """
    # Note: Adafruit_BMP returns pressure in Pascals, so we divide by 100 to get hPa
    return {
        "temperature_c": round(bmp.read_temperature(), 2),
        "pressure_hpa": round(bmp.read_pressure() / 100.0, 2),
    }

if __name__ == "__main__":
    import time
    print("Reading BMP180 sensor data (Legacy Adafruit_BMP). Press Ctrl+C to stop.")
    while True:
        try:
            data = read()
            print(f"Temperature: {data['temperature_c']} C | Pressure: {data['pressure_hpa']} hPa")
        except Exception as e:
            print(f"Error reading sensor: {e}")
        time.sleep(2)
