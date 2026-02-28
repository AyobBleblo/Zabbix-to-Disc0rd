# 🚀 Zabbix-to-Disc0rd

Welcome to **Zabbix-to-Disc0rd**! This project is a lightweight, easy-to-use Python monitoring service that connects to your Zabbix server, tracks active problems in real-time, and is perfectly suited for extending with notifications (like Discord webhooks!).

If you're tired of checking your Zabbix dashboard manually and want an automated way to keep an eye on your servers, you're in the right place.

## ✨ Features

- **Real-Time Polling:** Automatically checks your Zabbix server for new, resolved, or ongoing problems.
- **Smart Change Detection:** Only alerts you when there's an actual change (a new issue pops up, or an old one gets resolved).
- **Rich Context:** Fetches not just the problem name, but also severity, hostnames, and IP addresses.
- **Clean Architecture:** Built using modern Python dataclasses for robust error handling and easy readability.
- **Easy to Extend:** Specifically designed so you can plug in Discord notifications (or any other messaging platforms) effortlessly!

## 🛠️ Prerequisites

Before you start, make sure you have:
- **Python 3.8+** installed
- A running **Zabbix server**
- Your Zabbix API **URL** and an **API Token**

## 🚀 Getting Started

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/AyobBleblo/Zabbix-to-Disc0rd.git
   cd Zabbix-to-Disc0rd
   ```

2. **Set up a virtual environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   # On Windows use: venv\Scripts\activate
   # On macOS/Linux use: source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your credentials:**
   Set up your `ZABBIX_URL` and `ZABBIX_TOKEN` in `zabbix_minimal/config.py` or as environment variables.

   *Example in `zabbix_minimal/config.py`:*
   ```python
   ZABBIX_URL = "http://your-zabbix-server.com/zabbix"
   ZABBIX_TOKEN = "your_super_secret_token_here"
   ```

5. **Run the Monitor:**
   ```bash
   python main_zabbix.py
   # OR
   python zabbix_minimal/main.py
   ```
   *Watch your terminal light up with your Zabbix stats! It updates every 10 seconds.*

## 🧪 Running Tests

We love stable code! To run the test suite, just use `pytest`:
```bash
pytest
```

## 📂 Project Structure

- `zabbix_minimal/client.py`: The core API client handling authentication and data fetching securely from Zabbix.
- `zabbix_minimal/monitor.py`: The stateful engine that continuously watches for changes.
- `zabbix_minimal/models.py`: Python dataclasses to represent Zabbix data cleanly.
- `zabbix_minimal/main.py` & `main_zabbix.py`: Entry point scripts to run the monitoring loop.
- `tests/`: Because testing is awesome.

## 🤝 Contributing

Got an idea to make this even better? Maybe adding that Discord webhook integration directly? 
Feel free to open an issue or submit a Pull Request. We'd love to see what you build!

---

*Built with ❤️ for simpler, better monitoring.*