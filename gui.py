import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import subprocess
import os
import signal
from collections import defaultdict
from datetime import datetime

# Global variables
bot_process = None
analytics_data = {
    "total_accidents": 0,
    "accidents_per_hour": defaultdict(int),
    "most_frequent_location": defaultdict(int),
    "accidents_by_severity": defaultdict(int),
    "last_incident_time": None,
}

# Simulate updating analytics (replace with real data processing)
def update_analytics(mock_data):
    global analytics_data
    analytics_data["total_accidents"] += 1
    hour = datetime.strptime(mock_data["time"], "%Y-%m-%d %H:%M:%S").hour
    analytics_data["accidents_per_hour"][hour] += 1
    analytics_data["most_frequent_location"][mock_data["location"]] += 1
    analytics_data["accidents_by_severity"][mock_data["severity"]] += 1
    analytics_data["last_incident_time"] = mock_data["time"]

# Start the bot by running main.py
def start_bot():
    global bot_process
    if bot_process is None:
        try:
            bot_process = subprocess.Popen(
                ["python", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            update_status("Bot started")
            threading.Thread(target=monitor_bot_output, daemon=True).start()
        except Exception as e:
            update_status(f"Error starting bot: {e}")
    else:
        update_status("Bot is already running")

# Stop the bot by terminating the subprocess
def stop_bot():
    global bot_process
    if bot_process is not None:
        try:
            os.kill(bot_process.pid, signal.SIGTERM)
            bot_process = None
            update_status("Bot stopped")
        except Exception as e:
            update_status(f"Error stopping bot: {e}")
    else:
        update_status("Bot is not running")

# Monitor bot output and update the GUI
def monitor_bot_output():
    global bot_process
    if bot_process:
        for line in bot_process.stdout:
            mock_data = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "location": "Downtown",
                "severity": "High"
            }
            update_analytics(mock_data)
            update_status(f"Bot Output: {line.strip()}")
            update_analytics_display()

# Update the analytics display
def update_analytics_display():
    total_label.config(text=f"Total Accidents: {analytics_data['total_accidents']}")
    last_time_label.config(text=f"Last Incident Time: {analytics_data['last_incident_time']}")
    most_frequent_location = max(analytics_data["most_frequent_location"], key=analytics_data["most_frequent_location"].get, default="N/A")
    location_label.config(text=f"Most Frequent Location: {most_frequent_location}")
    per_hour_label.config(
        text=f"Accidents per Hour: {', '.join([f'{hour}: {count}' for hour, count in analytics_data['accidents_per_hour'].items()])}"
    )
    severity_label.config(
        text=f"Accidents by Severity: {', '.join([f'{severity}: {count}' for severity, count in analytics_data['accidents_by_severity'].items()])}"
    )

# Update the status label
def update_status(status):
    status_label.config(text=status)

# Show the latest Discord post
def show_latest_post():
    post_label.config(text="Latest Post: ⚠️ Accident near Downtown. Expect delays! 🛑")

# Show the latest generated image
def show_latest_image():
    try:
        img = Image.open("map.png")
        img = img.resize((300, 300), Image.ANTIALIAS)
        img_tk = ImageTk.PhotoImage(img)
        map_label.config(image=img_tk)
        map_label.image = img_tk
    except Exception as e:
        update_status(f"Error loading image: {e}")

root = tk.Tk()
root.title("Traffic Incident Bot")
root.geometry("800x700")
root.configure(bg="#F5F5F5")

title_label = tk.Label(root, text="Traffic Incident Bot", font=("Arial", 20, "bold"), bg="#F5F5F5", fg="#333")
title_label.pack(pady=10)

status_label = tk.Label(root, text="Status: Not running", font=("Arial", 14), bg="#F5F5F5", fg="#555")
status_label.pack(pady=5)

button_frame = tk.Frame(root, bg="#F5F5F5")
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Start Bot", command=lambda: threading.Thread(target=start_bot).start())
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(button_frame, text="Stop Bot", command=stop_bot)
stop_button.grid(row=0, column=1, padx=10)

post_button = ttk.Button(button_frame, text="Show Latest Post", command=show_latest_post)
post_button.grid(row=1, column=0, padx=10, pady=10)

image_button = ttk.Button(button_frame, text="Show Latest Image", command=show_latest_image)
image_button.grid(row=1, column=1, padx=10, pady=10)

analytics_frame = tk.Frame(root, bg="#F5F5F5")
analytics_frame.pack(pady=20)

total_label = tk.Label(analytics_frame, text="Total Accidents: 0", font=("Arial", 12), bg="#F5F5F5", fg="#555")
total_label.pack(anchor="w")

last_time_label = tk.Label(analytics_frame, text="Last Incident Time: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
last_time_label.pack(anchor="w")

location_label = tk.Label(analytics_frame, text="Most Frequent Location: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
location_label.pack(anchor="w")

per_hour_label = tk.Label(analytics_frame, text="Accidents per Hour: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
per_hour_label.pack(anchor="w")

severity_label = tk.Label(analytics_frame, text="Accidents by Severity: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
severity_label.pack(anchor="w")

post_label = tk.Label(root, text="Latest Post: None", font=("Arial", 12), bg="#F5F5F5", fg="#555", wraplength=500, justify="left")
post_label.pack(pady=10)

map_label = tk.Label(root, bg="#F5F5F5")
map_label.pack(pady=10)

root.mainloop()
