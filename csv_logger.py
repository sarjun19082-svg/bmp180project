import csv
import os
import time
from datetime import datetime

import sensor

# Name of the output CSV file (Excel can open this directly)
CSV_FILE = "sensor_data.csv"

def init_csv():
    # If the file does not exist, create it and write the headers
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Write column headers
            writer.writerow(["Timestamp", "Temperature (C)", "Pressure (hPa)"])
        print(f"Created new file: {CSV_FILE} with headers.")

def log_to_csv():
    try:
        # 1. Read data from sensor
        data = sensor.read()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = data["temperature_c"]
        press = data["pressure_hpa"]

        # 2. Append the reading to the CSV file
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temp, press])

        print(f"Logged -> Time: {timestamp} | Temp: {temp} C | Press: {press} hPa")

    except Exception as e:
        print(f"Error logging data: {e}")

if __name__ == "__main__":
    init_csv()
    print("Starting CSV logging. Press Ctrl+C to stop...")
    while True:
        log_to_csv()
        time.sleep(5)  # Log every 5 seconds (adjust as needed)
