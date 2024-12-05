# 🚦 Traffic Incident Bot 🛑

## Overview

The **Traffic Incident Bot** is an intelligent system that monitors traffic incidents in real-time, generates detailed summaries with engaging emojis, and posts updates to a Discord channel. Designed with automation and user interaction in mind, it includes a **Graphical User Interface (GUI)** for managing the bot and visualizing traffic data.

---

## 🧰 Features

### 🎮 **Interactive GUI**
- **Start/Stop Bot**: Easily manage the bot's operations with intuitive buttons.
- **Analytics Dashboard**: View real-time statistics, including:
  - Total accidents 🚗
  - Accidents per hour ⏰
  - Most frequent locations 📍
  - Accident severity (future feature)
- **Live Map View**: See a dynamically updated map of accident locations.

### 🤖 **Automated Traffic Monitoring**
- Fetches traffic incident data using a custom scraper.
- Summarizes incidents using **OpenAI GPT** for concise, engaging updates.
- Generates map images for incidents and posts them alongside the summary.

### 📝 **Discord Integration**
- Posts real-time traffic updates to a specified Discord channel.
- Includes an optional map image for better visualization.

### 🔄 **Data Persistence**
- Tracks previously posted incidents to avoid duplicates.
- Stores and processes historical data for analytics.

---

## 💻 How to Use

1. **Run the Bot**:
   - Launch the GUI with `python gui.py`.
   - Use the **Start Bot** button to initiate traffic monitoring.
   
2. **View Analytics**:
   - Check the GUI for live analytics on traffic incidents.
   - View the map of recent accidents by clicking the **Show Latest Image** button.

3. **Post Updates to Discord**:
   - Connect to a Discord channel with the configured token.
   - Summaries and map images are posted automatically.

4. **Stop the Bot**:
   - Gracefully stop the bot using the **Stop Bot** button.

---

## 🛠️ Requirements

- **Python 3.8+**
- Libraries:
  - `discord`
  - `Pillow`
  - `openai`
  - `dotenv`
- A Discord bot token.
- OpenAI API key for generating summaries.
- Traffic scraper and map generator modules (`traffic_scraper.py`, `map_generator.py`).

---

## 🚀 Future Enhancements
- Add **accident severity classification** to analytics.
- Implement **dynamic Discord channel configuration** from the GUI.
- Provide **detailed graphs and charts** for better data visualization.
- Add support for email notifications with incident summaries.

---

## 🗺️ Project Structure

```plaintext
.
├── gui.py                # GUI application for managing the bot
├── main.py               # Bot logic and Discord integration
├── traffic_scraper.py    # Scraper for fetching traffic incident data
├── map_generator.py      # Generates map images for accident locations
├── previous_data.json    # Stores historical traffic data
├── requirements.txt      # Dependencies
💡 Inspiration
This project combines automation, real-time data processing, and AI-powered text generation to deliver a seamless traffic monitoring solution. With its engaging Discord posts and visual analytics, the bot is perfect for keeping communities informed about road conditions.

📜 License
Feel free to use and enhance the project for personal or educational purposes. Contributions are welcome! 😊

Made with ❤️ by Duffy Adams, leveraging Python, OpenAI, and Discord APIs. 🚀
