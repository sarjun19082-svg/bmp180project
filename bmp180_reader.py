import board
import busio
import bmp180

# Initialize the I2C bus
# SCL and SDA are standard I2C pins defined by the board
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the BMP180 sensor
# Note: BMP180 default address is 0x77. If it fails, try 0x75 or 0x76.
bmp = bmp180.BMP180(i2c, address=0x77)

# Set the reference sea level pressure (in hPa) to calculate altitude
bmp.sea_level_pressure = 1013.25

def read():
    """Return current sensor reading as a dictionary.
    The rest of the project depends only on this interface.
    """
    return {
        "temperature_c": round(bmp.temperature, 2),
        "pressure_hpa": round(bmp.pressure, 2),
    }

if __name__ == "__main__":
    import time
    print("Reading BMP180 sensor data. Press Ctrl+C to stop.")
    while True:
        try:
            data = read()
            print(f"Temperature: {data['temperature_c']} C | Pressure: {data['pressure_hpa']} hPa")
        except Exception as e:
            print(f"Error reading sensor: {e}")
        time.sleep(2)
