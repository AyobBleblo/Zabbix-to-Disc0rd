# 🚀 Zabbix-to-Disc0rd

Welcome to **Zabbix-to-Disc0rd**! This project is a powerful, lightweight Python bridge that connects your Zabbix server directly to Discord. 

Instead of spamming your channels with individual messages, this bot uses a **Batched Alert Architecture** to group active problems by severity. It also includes a **Web Dashboard** to easily manage multiple Discord channels with advanced filtering rules!

![Batched Alerts](https://img.shields.io/badge/Alerts-Batched-success) ![Dashboard](https://img.shields.io/badge/Dashboard-Flask-blue)

## ✨ Features

- **Batched Discord Embeds:** Groups active Zabbix problems by severity (Warning, High, Disaster, etc.) into unified Discord messages.
- **True State Sync:** Old Discord messages are automatically deleted and replaced. The Discord channel perfectly reflects the exact current state of Zabbix. No more "stuck" messages!
- **Rich Metadata:** Displays the real Zabbix **Hostname** and **IP Address** for every tracked problem right inside the Discord embed.
- **Flask Web Dashboard:** A beautiful, easy-to-use web UI to configure your Discord bot settings without touching code.
- **Multi-Severity Selection:** Pick and choose exactly which severity levels get sent to which Discord channels.
- **Advanced Filtering Engine:**
  - **Include Substrings:** Only send problems matching specific keywords.
  - **Exclude Substrings:** Ignore specific spammy keywords.
  - **Host-specific Ignores:** Ignore very specific problems only when they occur on specific hosts.

## 🛠️ Prerequisites

Before you start, make sure you have:
- **Python 3.8+** installed
- A running **Zabbix server**
- A **Zabbix API URL** and **API Token**
- A **Discord Bot Token** and the Target **Channel ID**

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AyobBleblo/Zabbix-to-Disc0rd.git
   cd Zabbix-to-Disc0rd
   ```

2. **Set up a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows use: venv\Scripts\activate
   # On macOS/Linux use: source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your Zabbix credentials:**
   Create a `.env` file in `zabbix_minimal/.env` (or set environment variables) with:
   ```env
   ZABBIX_URL=http://your-zabbix-server.com/zabbix
   ZABBIX_TOKEN=your_super_secret_token_here
   HOST_GROUP_ID=22
   POLL_INTERVAL=30
   ```

## 🎮 How to Run

Zabbix-to-Disc0rd runs in two parts: the Web Dashboard (to configure your channels) and the Bridge (the actual bot).

### 1. Start the Configuration Dashboard
Run the Flask app to manage your Discord channels and filtering rules:
```bash
python dashboard/app.py
```
*Open your browser and navigate to `http://localhost:5000` to add your Discord Bot Token, Channel ID, and configure your severity/filter rules.*

### 2. Start the Discord Bot Bridge
In a separate terminal, start the main monitor loop:
```bash
python run_bridge.py
```
*This will connect to Zabbix, pull your dashboard configurations, and begin syncing batched problems strictly to your Discord channels!*

## 📂 Project Structure

- `dashboard/app.py`: The Flask web application for configuring channels.
- `dashboard/dashboard.db`: The SQLite database storing your channel rules and message tracking IDs.
- `run_bridge.py`: The main entry point that polls Zabbix and pushes updates to Discord.
- `zabbix_minimal/discord/sender.py`: Builds the batched Discord embeds and manages the Discord API.
- `zabbix_minimal/discord_bridge.py`: Orchestrates the deletion of old messages and sending of new ones per severity.
- `zabbix_minimal/discord/filters.py`: The filtering engine that enforces your dashboard rules (includes/excludes/host-ignores).
- `BATCHED_ALERTS_GUIDE.md`: A highly detailed tutorial documenting the system architecture.

## 🧪 Running Tests

To run the test suite and verify the embed logic and filtering engine:
```bash
pytest
```

## 🤝 Contributing

Got an idea to make this even better? Feel free to open an issue or submit a Pull Request. We'd love to see what you build!

---

*Built with ❤️ for simpler, beautiful Zabbix monitoring.*