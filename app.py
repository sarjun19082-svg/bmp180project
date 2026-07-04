import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, render_template

import sensor

app = Flask(__name__)
DB_PATH = "readings.db"

# Initialize GPIO Pin for Anomaly Signal (GPIO 17 / Pin 11 on header)
# Wrapped in try/except so it doesn't crash if run on Windows for testing
try:
    import board
    import digitalio
    anomaly_pin = digitalio.DigitalInOut(board.D17)
    anomaly_pin.direction = digitalio.Direction.OUTPUT
    anomaly_pin.value = False
    print("GPIO Anomaly Pin (GPIO 17) successfully initialized.")
except Exception as e:
    print(f"Warning: Could not initialize GPIO Anomaly Pin (this is normal on Windows): {e}")
    anomaly_pin = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # Create the basic table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            temperature_c REAL,
            pressure_hpa REAL
        )
    """)
    # Alter table to add DHT11 columns if they aren't already there (for backward compatibility)
    try:
        conn.execute("ALTER TABLE readings ADD COLUMN temperature_dht REAL")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        conn.execute("ALTER TABLE readings ADD COLUMN humidity REAL")
    except sqlite3.OperationalError:
        pass # Column already exists
    conn.commit()
    conn.close()

init_db()

_recording = False
_thread = None
_lock = threading.Lock()

def _record_loop():
    global _recording
    while _recording:
        try:
            data = sensor.read()
            conn = sqlite3.connect(DB_PATH)
            
            # Fetch the last 4 readings to calculate the moving average
            last_readings = conn.execute(
                "SELECT temperature_c, pressure_hpa, temperature_dht, humidity FROM readings ORDER BY id DESC LIMIT 4"
            ).fetchall()
            
            # Insert the new reading
            conn.execute(
                "INSERT INTO readings (ts, temperature_c, pressure_hpa, temperature_dht, humidity) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.utcnow().isoformat(), 
                    data["temperature_c"], 
                    data["pressure_hpa"], 
                    data["temperatureDHT"], 
                    data["humidity"]
                ),
            )
            conn.commit()
            conn.close()
            
            # --- Server-Side Anomaly Detection & GPIO Signal Trigger ---
            # 1. BMP Temperature Deviation
            bmp_temps = [r[0] for r in last_readings if r[0] is not None] + [data["temperature_c"]]
            bmp_temp_avg = sum(bmp_temps) / len(bmp_temps)
            bmp_temp_dev = abs(data["temperature_c"] - bmp_temp_avg)
            
            # 2. BMP Pressure Deviation
            pressures = [r[1] for r in last_readings if r[1] is not None] + [data["pressure_hpa"]]
            pressure_avg = sum(pressures) / len(pressures)
            pressure_dev = abs(data["pressure_hpa"] - pressure_avg)

            # 3. DHT Temperature Deviation
            dht_temps = [r[2] for r in last_readings if r[2] is not None] + [data["temperatureDHT"]]
            dht_temp_avg = sum(dht_temps) / len(dht_temps)
            dht_temp_dev = abs(data["temperatureDHT"] - dht_temp_avg)

            # 4. DHT Humidity Deviation
            humidities = [r[3] for r in last_readings if r[3] is not None] + [data["humidity"]]
            humidity_avg = sum(humidities) / len(humidities)
            humidity_dev = abs(data["humidity"] - humidity_avg)
            
            # Trigger signal if any deviation > 0.5 (requires at least 5 baseline readings)
            has_anomaly = (
                (len(bmp_temps) >= 5 and bmp_temp_dev > 0.5) or
                (len(pressures) >= 5 and pressure_dev > 0.5) or
                (len(dht_temps) >= 5 and dht_temp_dev > 0.5) or
                (len(humidities) >= 5 and humidity_dev > 0.5)
            )
            
            # Output to GPIO physical pin
            if anomaly_pin is not None:
                anomaly_pin.value = has_anomaly
                if has_anomaly:
                    print("GPIO Alert: Anomaly detected! GPIO 17 set to HIGH.")
                else:
                    anomaly_pin.value = False
                    
        except Exception as e:
            print("Record error:", e)
        time.sleep(2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global _recording, _thread
    with _lock:
        if _recording:
            return jsonify({"status": "already_recording"})
        _recording = True
        _thread = threading.Thread(target=_record_loop, daemon=True)
        _thread.start()
    return jsonify({"status": "started"})

@app.route("/stop", methods=["POST"])
def stop():
    global _recording
    with _lock:
        _recording = False
        # Make sure pin turns off if logging is stopped
        if anomaly_pin is not None:
            anomaly_pin.value = False
    return jsonify({"status": "stopped"})

@app.route("/status")
def status():
    return jsonify({"recording": _recording})

@app.route("/data")
def data():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts, temperature_c, pressure_hpa, temperature_dht, humidity FROM readings ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    rows.reverse()
    return jsonify([
        {
            "ts": r[0], 
            "temperature_c": r[1], 
            "pressure_hpa": r[2], 
            "temperature_dht": r[3], 
            "humidity": r[4]
        } for r in rows
    ])

# Route for DHT11 readings
@app.route("/dht11")
def dht11():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT ts, temperature_dht, humidity FROM readings ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    rows.reverse()
    return jsonify([
        {
            "ts": r[0], 
            "temperature_dht": r[1], 
            "humidity": r[2]
        } for r in rows
    ])

@app.route("/table")
def table():
    conn = sqlite3.connect(DB_PATH)
    # Fetch 104 rows to calculate 5-point average for the oldest displayed row
    rows = conn.execute(
        "SELECT ts, temperature_c, pressure_hpa, temperature_dht, humidity FROM readings ORDER BY id DESC LIMIT 104"
    ).fetchall()
    conn.close()
    
    rows.reverse()
    display_start = max(0, len(rows) - 100)
    
    html = """
    <html>
    <head>
        <title>Sensor Data Table</title>
        <style>
            table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>Sensor Readings Log (Last 100 records)</h2>
        <table border="1">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Temperature BMP (C)</th>
                    <th>Avg Temp BMP (Last 5)</th>
                    <th>Pressure BMP (hPa)</th>
                    <th>Avg Press BMP (Last 5)</th>
                    <th>Temperature DHT (C)</th>
                    <th>Humidity (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for i in range(display_start, len(rows)):
        r = rows[i]
        
        if i >= 4:
            last_five_temps = [rows[j][1] for j in range(i-4, i+1)]
            last_five_press = [rows[j][2] for j in range(i-4, i+1)]
            avg_temp = round(sum(last_five_temps) / 5, 2)
            avg_press = round(sum(last_five_press) / 5, 2)
            avg_temp_str = str(avg_temp)
            avg_press_str = str(avg_press)
        else:
            avg_temp_str = ""
            avg_press_str = ""
            
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{avg_temp_str}</td><td>{r[2]}</td><td>{avg_press_str}</td><td>{r[3]}</td><td>{r[4]}</td></tr>"
        
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

@app.route("/clear", methods=["POST"])
def clear():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM readings")
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
