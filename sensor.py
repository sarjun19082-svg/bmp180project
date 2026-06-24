import board
import busio
import bmp180

# Initialize the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the BMP180 sensor
bmp = bmp180.BMP180(i2c, address=0x77)

# Set the reference sea level pressure (in hPa)
bmp.sea_level_pressure = 1013.25

def read():
    """Return current sensor reading as a dictionary.
    The rest of the project depends only on this interface.
    """
    return {
        "temperature_c": round(bmp.temperature, 2),
        "pressure_hpa": round(bmp.pressure, 2),
    }
