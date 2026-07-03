import board
import busio
import bmp180
import time
import adafruit_dht

# Initialize the I2C bus for BMP180
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    bmp = bmp180.BMP180(i2c, address=0x77)
    # Set the reference sea level pressure (in hPa)
    bmp.sea_level_pressure = 1013.25
except Exception as e:
    print(f"Warning: Failed to initialize BMP180 sensor: {e}")
    bmp = None

# Initialize DHT11 on GPIO 4 (board.D4)
try:
    dht_sensor = adafruit_dht.DHT11(board.D4)
except Exception as e:
    print(f"Warning: Failed to initialize DHT11 sensor: {e}")
    dht_sensor = None

def read():
    """Return current sensor reading as a dictionary.
    Takes 5 readings with a sleep time of 0.5s between each,
    and returns the average of those 5 readings to smooth out noise.
    """
    temps_bmp = []
    pressures_bmp = []
    temps_dht = []
    humidities_dht = []

    for _ in range(5):
        # Read BMP180
        if bmp is not None:
            try:
                temps_bmp.append(bmp.temperature)
            except Exception:
                pass
            try:
                pressures_bmp.append(bmp.pressure)
            except Exception:
                pass
            
        # Read DHT11 (adafruit_dht raises RuntimeError on failed checksums/timeouts, which is normal)
        if dht_sensor is not None:
            try:
                t = dht_sensor.temperature
                if t is not None:
                    temps_dht.append(t)
            except Exception:
                pass
            try:
                h = dht_sensor.humidity
                if h is not None:
                    humidities_dht.append(h)
            except Exception:
                pass
            
        time.sleep(0.5)

    # Calculate averages
    avg_temp_bmp = sum(temps_bmp) / len(temps_bmp) if temps_bmp else 0.0
    avg_press_bmp = sum(pressures_bmp) / len(pressures_bmp) if pressures_bmp else 0.0
    avg_temp_dht = sum(temps_dht) / len(temps_dht) if temps_dht else 0.0
    avg_hum_dht = sum(humidities_dht) / len(humidities_dht) if humidities_dht else 0.0

    return {
        "temperature_c": round(avg_temp_bmp, 2),
        "pressure_hpa": round(avg_press_bmp, 2),
        "temperatureDHT": round(avg_temp_dht, 2),
        "humidity": round(avg_hum_dht, 2),
    }

if __name__ == "__main__":
    print("Reading sensor data (5-sample average). Press Ctrl+C to stop.")
    while True:
        try:
            print(read())
        except Exception as e:
            print(f"Error reading sensors: {e}")
        time.sleep(2)
