# Raspberry Pi Environmental Monitor & Real-Time Web Dashboard

This project is an IoT-based environmental monitoring station that runs on a Raspberry Pi. It reads barometric pressure and temperature from a **BMP180** sensor, and temperature and humidity from a **DHT11** sensor. The readings are logged in an SQLite database, visualized on a real-time web dashboard, and can be synced directly to Microsoft Excel over Wi-Fi.

> **Internship Credit:** This project was completed during an internship under the guidance of **Mr. Chandra Shukla**, an AI Consultant in the United States.

---

## Features
*   **Averaging Filters**: Reduces sensor noise (especially for the DHT11) by calculating a 5-sample moving average over 2.5 seconds.
*   **SQLite Logging**: Stores history of temperature (BMP and DHT), pressure, and humidity.
*   **Real-Time Web Dashboard**: Built with Flask and Chart.js, showing real-time updates and deviation charts (Current value vs. Last 5-readings average).
*   **Anomalies & Bookmarks**: Scriptable logic automatically flags readings with a deviation > 0.5 in red on the charts and logs them in an "Outliers/Bookmarks" list.
*   **Microsoft Excel Web Query Sync**: Serves an HTML table route (`/table`) designed for Excel to dynamically pull data over Wi-Fi with a single click.
*   **Automation on Boot**: Configured script to start Flask and ngrok tunnels automatically when the Raspberry Pi boots.

---

## Project Structure
*   `app.py`: The Flask server, routing APIs (`/data`, `/dht11`, `/table`, `/clear`), SQLite database creation/insertion, and background recording thread.
*   `sensor.py`: Core driver logic reading from BMP180 (I2C) and DHT11 (GPIO) and calculating averages.
*   `templates/index.html`: The web dashboard frontend UI, chart layouts, and anomaly detection client logic.
*   `csv_logger.py` & `excel_logger.py`: Alternative terminal scripts to log data directly to local CSV/Excel files.

---

## Hardware Configuration (Wiring)

### BMP180 Sensor (I2C)
*   **VCC** -> **3.3V** (Pin 1)
*   **GND** -> **GND** (Pin 6)
*   **SDA** -> **GPIO 2 / SDA** (Pin 3)
*   **SCL** -> **GPIO 3 / SCL** (Pin 5)

### DHT11 Sensor (Digital)
*   **VCC** -> **3.3V**
*   **GND** -> **GND**
*   **DATA** -> **GPIO 4** (Pin 7)

---

## Software Installation & Setup

1.  **Clone the repository to your Raspberry Pi**:
    ```bash
    git clone https://github.com/YOUR_GITHUB_USERNAME/bmp180_project.git
    cd bmp180_project
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install the dependencies**:
    ```bash
    pip install Flask circuitpython-bmp180 adafruit-blinka openpyxl
    ```
4.  **Run the Flask application**:
    ```bash
    python app.py
    ```
5.  **Access the Dashboard**:
    Open your web browser and navigate to `http://<PI_IP_ADDRESS>:5000/`.

---

## Accessing Data in Microsoft Excel

1.  Make sure `app.py` is running on the Pi.
2.  Open **Excel** on your laptop.
3.  Go to the **Data** tab -> **From Web**.
4.  Enter the URL: `http://<YOUR_PI_IP>:5000/table`.
5.  Select **Table 0** and click **Load**. 
6.  Click **Refresh All** under the Data tab at any time to sync the latest readings!
