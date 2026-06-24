import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, render_template

import sensor

app = Flask(__name__)
DB_PATH = "readings.db"

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

# New route specifically for DHT11 readings
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
    
    # Reverse to chronological order (oldest first)
    rows.reverse()
    
    # We want to display the last 100 rows in the HTML table
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
        
        # Calculate moving average if we have at least 5 readings (i.e. i >= 4)
        if i >= 4:
            last_five_temps = [rows[j][1] for j in range(i-4, i+1)]
            last_five_press = [rows[j][2] for j in range(i-4, i+1)]
            avg_temp = round(sum(last_five_temps) / 5, 2)
            avg_press = round(sum(last_five_press) / 5, 2)
            avg_temp_str = str(avg_temp)
            avg_press_str = str(avg_press)
        else:
            avg_temp_str = ""  # Leave blank for starting 4 rows
            avg_press_str = ""  # Leave blank for starting 4 rows
            
        # r[3] is temperature_dht, r[4] is humidity
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
    # host="0.0.0.0" makes Flask reachable from other devices on the Wi-Fi
    app.run(host="0.0.0.0", port=5000, debug=False)
