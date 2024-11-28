import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from collections import defaultdict
from datetime import datetime
import threading
import asyncio
import main  # Import the main.py module

# Global variables
bot_task = None
bot_loop = None
bot_running = False
analytics_data = {
    "total_accidents": 0,
    "accidents_per_hour": defaultdict(int),
    "most_frequent_location": defaultdict(int),
    "accidents_by_severity": defaultdict(int),
    "last_incident_time": None,
}

# Simulate updating analytics by reading from previous_data.json
def update_analytics_from_file():
    global analytics_data
    try:
        filename = "previous_data.json"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
                
                # Reset analytics data
                analytics_data = {
                    "total_accidents": len(data),
                    "accidents_per_hour": defaultdict(int),
                    "most_frequent_location": defaultdict(int),
                    "accidents_by_severity": defaultdict(int),
                    "last_incident_time": None,
                }
                
                # Process each incident
                for incident in data:
                    if incident.get("Time"):
                        try:
                            # Attempt to parse time in the expected format
                            time_obj = datetime.strptime(incident["Time"], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                # Handle alternative format (e.g., '8:45 PM')
                                time_obj = datetime.strptime(incident["Time"], "%I:%M %p")
                            except ValueError:
                                # Skip if the time format is invalid
                                print(f"Skipping invalid time format: {incident['Time']}")
                                continue
                        hour = time_obj.hour
                        analytics_data["accidents_per_hour"][hour] += 1

                    if incident.get("Location"):
                        analytics_data["most_frequent_location"][incident["Location"]] += 1
                    if not analytics_data["last_incident_time"] or \
                       (incident.get("Time") and incident["Time"] > analytics_data["last_incident_time"]):
                        analytics_data["last_incident_time"] = incident.get("Time")

                # Update GUI labels
                update_analytics_display()
    except Exception as e:
        print(f"Error reading analytics: {e}")

# Periodically monitor updates to previous_data.json
def monitor_analytics_file():
    update_analytics_from_file()  # Update analytics from the file
    root.after(5000, monitor_analytics_file)  # Check every 5 seconds

# Start the bot by running main.py logic
def start_bot():
    global bot_task, bot_loop, bot_running
    if not bot_running:
        try:
            bot_running = True
            update_status("Starting bot...")
            # Create a new event loop and run the bot inside it
            bot_loop = asyncio.new_event_loop()
            bot_task = threading.Thread(target=run_bot, args=(bot_loop,), daemon=True)
            bot_task.start()
            update_status("Bot Started")
        except Exception as e:
            update_status(f"Error starting bot: {e}")
    else:
        update_status("Bot is already running")

def run_bot(loop):
    """Run the bot using asyncio."""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main.client.start(main.DISCORD_TOKEN))
    except Exception as e:
        print(f"Error in bot: {e}")
    finally:
        loop.run_until_complete(main.client.close())
        loop.close()

def stop_bot():
    global bot_task, bot_loop, bot_running
    if bot_running and bot_loop:
        update_status("Stopping bot...")
        bot_running = False
        asyncio.run_coroutine_threadsafe(main.client.close(), bot_loop)
        bot_task.join()
        update_status("Bot stopped")
    else:
        update_status("Bot is not running.")

# Update the analytics display
def update_analytics_display():
    total_label.config(text=f"Total Accidents: {analytics_data['total_accidents']}")
    last_time_label.config(text=f"Last Incident Time: {analytics_data['last_incident_time'] or 'N/A'}")
    most_frequent_location = max(
        analytics_data["most_frequent_location"], 
        key=analytics_data["most_frequent_location"].get, 
        default="N/A"
    )
    location_label.config(text=f"Most Frequent Location: {most_frequent_location}")
    per_hour_text = ", ".join([f'{hour}: {count}' for hour, count in analytics_data['accidents_per_hour'].items()]) or "None"
    per_hour_label.config(text=f"Accidents per Hour: {per_hour_text}")
    severity_label.config(text=f"Accidents by Severity: None")  # Can be updated if severity data is available

# Update the status label
def update_status(status):
    status_label.config(text=status)

# Show the latest generated image and maintain aspect ratio
def show_latest_image():
    try:
        img_path = "map.png"
        img = Image.open(img_path)
        # Get the size of the window to resize the image
        window_width = map_label.winfo_width()
        window_height = map_label.winfo_height()
        if window_width > 0 and window_height > 0:
            # Calculate aspect ratio
            img_aspect = img.width / img.height
            window_aspect = window_width / window_height

            if window_aspect > img_aspect:
                # Window is wider than the image
                new_height = window_height
                new_width = int(new_height * img_aspect)
            else:
                # Window is taller than the image
                new_width = window_width
                new_height = int(new_width / img_aspect)

            img = img.resize((new_width, new_height), Image.LANCZOS)

        img_tk = ImageTk.PhotoImage(img)
        map_label.config(image=img_tk)
        map_label.image = img_tk
    except Exception as e:
        update_status(f"Error loading image: {e}")
        map_label.config(image='')

# Create the main window
root = tk.Tk()
root.title("Traffic Incident Bot")
root.geometry("800x700")
root.configure(bg="#F5F5F5")

# Title
title_label = tk.Label(root, text="Traffic Incident Bot", font=("Arial", 20, "bold"), bg="#F5F5F5", fg="#333")
title_label.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Status: Not running", font=("Arial", 14), bg="#F5F5F5", fg="#555")
status_label.pack(pady=5)

# Button Frame
button_frame = tk.Frame(root, bg="#F5F5F5")
button_frame.pack(pady=20)

# Buttons
start_button = ttk.Button(button_frame, text="Start Bot", command=start_bot)
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(button_frame, text="Stop Bot", command=stop_bot)
stop_button.grid(row=0, column=1, padx=10)

image_button = ttk.Button(button_frame, text="Show Latest Image", command=show_latest_image)
image_button.grid(row=1, column=0, padx=10, pady=10)

# Analytics Frame
analytics_frame = tk.Frame(root, bg="#F5F5F5")
analytics_frame.pack(pady=20)

# Analytics Labels
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

# Map Label (with stretch and aspect ratio lock)
map_label = tk.Label(root, bg="#F5F5F5", width=800, height=400)
map_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Bind the resizing event to reload the stretched image
root.bind("<Configure>", lambda event: show_latest_image())

# Initial population of analytics and start periodic monitoring
update_analytics_from_file()
monitor_analytics_file()  # Periodically monitor updates to the file

# Start the GUI
root.mainloop()
