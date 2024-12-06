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
import sys
import io

bot_thread = None
bot_loop = None
bot_running = False

analytics_data = {
    "total_accidents": 0,
    "accidents_per_hour": defaultdict(int),
    "most_frequent_location": defaultdict(int),
    "accidents_by_severity": defaultdict(int),
    "last_incident_time": None,
}

original_img = None  # Will hold the original loaded image
img_scale = 1.0       # Current scale factor for zooming

def parse_incident_time(time_str):
    formats = ["%Y-%m-%d %H:%M:%S", "%I:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    print(f"Skipping invalid time format: {time_str}")
    return None

def process_incident_for_analytics(incident):
    time_str = incident.get("Time")
    location = incident.get("Location")

    if time_str:
        time_obj = parse_incident_time(time_str)
        if time_obj:
            hour = time_obj.hour
            analytics_data["accidents_per_hour"][hour] += 1
            if not analytics_data["last_incident_time"] or time_str > analytics_data["last_incident_time"]:
                analytics_data["last_incident_time"] = time_str

    if location:
        analytics_data["most_frequent_location"][location] += 1

def update_analytics_from_file():
    filename = "previous_data.json"
    if not os.path.exists(filename):
        # If file doesn't exist or was just cleared, reset analytics
        analytics_data.update({
            "total_accidents": 0,
            "accidents_per_hour": defaultdict(int),
            "most_frequent_location": defaultdict(int),
            "accidents_by_severity": defaultdict(int),
            "last_incident_time": None,
        })
        update_analytics_display()
        return

    try:
        with open(filename, "r") as file:
            data = json.load(file)

        analytics_data.update({
            "total_accidents": len(data),
            "accidents_per_hour": defaultdict(int),
            "most_frequent_location": defaultdict(int),
            "accidents_by_severity": defaultdict(int),
            "last_incident_time": None,
        })

        for incident in data:
            process_incident_for_analytics(incident)

        update_analytics_display()
    except Exception as e:
        print(f"Error reading analytics: {e}")

def monitor_analytics_file():
    update_analytics_from_file()
    root.after(5000, monitor_analytics_file)

def start_bot():
    global bot_thread, bot_loop, bot_running
    if bot_running:
        update_status("Bot is already running.")
        return

    update_status("Starting bot...")
    bot_running = True
    bot_loop = asyncio.new_event_loop()
    bot_thread = threading.Thread(target=run_bot, args=(bot_loop,), daemon=True)
    bot_thread.start()
    update_status("Bot started.")

def run_bot(loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main.client.start(main.DISCORD_TOKEN))
    except Exception as e:
        print(f"Error in bot: {e}")
    finally:
        loop.run_until_complete(main.client.close())
        loop.close()

def stop_bot():
    global bot_running, bot_loop, bot_thread

    if not bot_running:
        update_status("Bot is not running.")
        return

    update_status("Stopping bot...")
    bot_running = False

    # Close the Discord client gracefully
    future = asyncio.run_coroutine_threadsafe(main.client.close(), bot_loop)
    try:
        future.result(timeout=5)
    except asyncio.TimeoutError:
        print("Timed out waiting for client to close.")

    # Stop the event loop
    bot_loop.call_soon_threadsafe(bot_loop.stop)
    
    # Join the bot thread to ensure it has finished
    bot_thread.join()

    bot_thread = None
    bot_loop = None

    update_status("Bot stopped.")
    
def update_analytics_display():
    total_label.config(text=f"Total Accidents: {analytics_data['total_accidents']}")
    last_incident = analytics_data['last_incident_time'] or "N/A"
    last_time_label.config(text=f"Last Incident Time: {last_incident}")

    freq_locations = analytics_data["most_frequent_location"]
    most_frequent_location = max(freq_locations, key=freq_locations.get, default="N/A")
    location_label.config(text=f"Most Frequent Location: {most_frequent_location}")

    total_hours = len(analytics_data["accidents_per_hour"])
    total_accidents = sum(analytics_data["accidents_per_hour"].values())
    average_per_hour = total_accidents / total_hours if total_hours > 0 else 0.0
    per_hour_label.config(text=f"Average Accidents per Hour: {average_per_hour:.2f}")

    severity_label.config(text="Accidents by Severity: None")

def update_status(message):
    status_label.config(text=message)

def zoom_image(delta):
    global img_scale, original_img
    if original_img is None:
        return
    zoom_step = 0.1
    if delta > 0:
        img_scale += zoom_step
    else:
        img_scale -= zoom_step

    if img_scale < 0.1:
        img_scale = 0.1
    if img_scale > 5.0:
        img_scale = 5.0

    scaled_width = int(original_img.width * img_scale)
    scaled_height = int(original_img.height * img_scale)
    img_resized = original_img.resize((scaled_width, scaled_height), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img_resized)
    map_label.config(image=img_tk)
    map_label.image = img_tk

def on_mousewheel(event):
    zoom_image(event.delta)

def show_latest_image():
    global original_img, img_scale
    img_path = "map.png"
    if not os.path.exists(img_path):
        update_status("No map image found.")
        map_label.config(image='')
        return

    try:
        original_img = Image.open(img_path)
        img_scale = 1.0
        img_tk = ImageTk.PhotoImage(original_img)
        map_label.config(image=img_tk)
        map_label.image = img_tk
    except Exception as e:
        update_status(f"Error loading image: {e}")
        map_label.config(image='')

def update_posted_message():
    if main.latest_posted_message:
        posted_message_label.config(text=main.latest_posted_message)
    root.after(5000, update_posted_message)

def clear_data():
    main.clear_json_file()
    update_analytics_from_file()
    main.latest_posted_message = None
    posted_message_label.config(text="")
    update_status("Data cleared and stats reset.")

class TextRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, message):
        self.buffer += message

    def flush(self):
        pass

def update_terminal():
    new_content = stdout_redirector.buffer
    if new_content:
        terminal_text.configure(state='normal')
        terminal_text.insert(tk.END, new_content)
        terminal_text.configure(state='disabled')
        terminal_text.see(tk.END)
        stdout_redirector.buffer = ""
    root.after(1000, update_terminal)

root = tk.Tk()
root.title("Traffic Incident Bot")
root.geometry("1000x700")
root.configure(bg="#F5F5F5")

title_label = tk.Label(root, text="Traffic Incident Bot", font=("Arial", 20, "bold"), bg="#F5F5F5", fg="#333")
title_label.pack(pady=10)

status_label = tk.Label(root, text="Status: Not running", font=("Arial", 14), bg="#F5F5F5", fg="#555")
status_label.pack(pady=5)

button_frame = tk.Frame(root, bg="#F5F5F5")
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Start Bot", command=start_bot)
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(button_frame, text="Stop Bot", command=stop_bot)
stop_button.grid(row=0, column=1, padx=10)

image_button = ttk.Button(button_frame, text="Show Latest Image", command=show_latest_image)
image_button.grid(row=1, column=0, padx=0, pady=10)

clear_button = ttk.Button(button_frame, text="Clear Data", command=clear_data)
clear_button.grid(row=1, column=1, padx=10, pady=10)

# Create a top_frame to hold analytics on the left and image on the right
top_frame = tk.Frame(root, bg="#F5F5F5")
top_frame.pack(fill='both', expand=True, padx=10, pady=10)

# Analytics Frame on the left
analytics_frame = tk.Frame(top_frame, bg="#F5F5F5")
analytics_frame.pack(side='left', fill='y', padx=(0,10))

total_label = tk.Label(analytics_frame, text="Total Accidents: 0", font=("Arial", 12), bg="#F5F5F5", fg="#555")
total_label.pack(anchor="w")

last_time_label = tk.Label(analytics_frame, text="Last Incident Time: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
last_time_label.pack(anchor="w")

location_label = tk.Label(analytics_frame, text="Most Frequent Location: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
location_label.pack(anchor="w")

per_hour_label = tk.Label(analytics_frame, text="Average Accidents per Hour: 0.00", font=("Arial", 12), bg="#F5F5F5", fg="#555")
per_hour_label.pack(anchor="w")

severity_label = tk.Label(analytics_frame, text="Accidents by Severity: None", font=("Arial", 12), bg="#F5F5F5", fg="#555")
severity_label.pack(anchor="w")

posted_message_label = tk.Message(
    top_frame,
    text="",
    font=("Roboto", 14),
    bg="#F5F5F5",
    fg="#333",
    width=400,
    justify="left"
)
posted_message_label.pack(side='left', fill='y', padx=(0,10))

# Image Frame on the right
image_frame = tk.Frame(top_frame, bg="#F5F5F5")
image_frame.pack(side='right', fill='both', expand=True)

map_label = tk.Label(image_frame, bg="#F5F5F5")
map_label.pack(fill=tk.BOTH, expand=True)

# Bind mouse wheel event for zooming on the image
map_label.bind("<MouseWheel>", on_mousewheel)

terminal_frame = tk.Frame(root, bg="#F5F5F5")
terminal_frame.pack(fill='both', expand=True, padx=10, pady=10)

terminal_label = tk.Label(terminal_frame, text="Terminal Output:", font=("Arial", 14), bg="#F5F5F5", fg="#333")
terminal_label.pack(anchor='w')

terminal_text = tk.Text(terminal_frame, wrap='word', state='disabled', font=("Consolas", 10))
terminal_text.pack(fill='both', expand=True)

stdout_redirector = TextRedirector(terminal_text)
sys.stdout = stdout_redirector

root.bind("<Configure>", lambda event: show_latest_image())

update_analytics_from_file()
monitor_analytics_file()
update_posted_message()
update_terminal()

root.mainloop()
