import os
import sys
import io
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from collections import defaultdict
from datetime import datetime
import threading
import asyncio
import main  # Import the main.py module

# --- Global Variables ---
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

# --- Functions for Parsing and Processing Incidents ---
def parse_incident_time(time_str):
    """
    Attempts to parse the given time string into a datetime object using multiple formats.
    Returns a datetime object if successful, otherwise None.
    """
    formats = ["%Y-%m-%d %H:%M:%S", "%I:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    print(f"Skipping invalid time format: {time_str}")
    return None

def process_incident_for_analytics(incident):
    """
    Updates analytics_data based on a single incident.
    Extracts time and location information and increments corresponding counts.
    """
    time_str = incident.get("Time")
    location = incident.get("Location")

    if time_str:
        time_obj = parse_incident_time(time_str)
        if time_obj:
            hour = time_obj.hour
            analytics_data["accidents_per_hour"][hour] += 1

            # Update last incident time if this one is newer
            if not analytics_data["last_incident_time"] or time_str > analytics_data["last_incident_time"]:
                analytics_data["last_incident_time"] = time_str

    if location:
        analytics_data["most_frequent_location"][location] += 1

# --- Analytics Handling ---
def update_analytics_from_file():
    """
    Reads previous_data.json file and updates the analytics data.
    If file doesn't exist or is empty, it resets the analytics.
    """
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

        # Reset analytics and re-calculate
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
    """
    Periodically updates analytics data from the file.
    """
    update_analytics_from_file()
    root.after(5000, monitor_analytics_file)

def update_analytics_display():
    """
    Updates the labels in the GUI to reflect the current analytics data.
    """
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

# --- Bot Control Functions ---
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
    """
    Runs the Discord bot in a separate thread.
    """
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

def update_status(message):
    """
    Updates the status label with the given message.
    """
    status_label.config(text=message)

# --- Image Display ---
def show_latest_image():
    """
    Displays the latest map image (map.png) in the map_label widget.
    Automatically resizes the image to fit the current widget size.
    """
    img_path = "map.png"
    if not os.path.exists(img_path):
        update_status("No map image found.")
        map_label.config(image='')
        return

    try:
        img = Image.open(img_path)
        window_width = map_label.winfo_width()
        window_height = map_label.winfo_height()

        if window_width > 0 and window_height > 0:
            img_aspect = img.width / img.height
            window_aspect = window_width / window_height

            if window_aspect > img_aspect:
                new_height = window_height
                new_width = int(new_height * img_aspect)
            else:
                new_width = window_width
                new_height = int(new_width / img_aspect)

            img = img.resize((new_width, new_height), Image.LANCZOS)

        img_tk = ImageTk.PhotoImage(img)
        map_label.config(image=img_tk)
        map_label.image = img_tk
    except Exception as e:
        update_status(f"Error loading image: {e}")
        map_label.config(image='')

# --- Posted Message Update ---
def update_posted_message():
    """
    Periodically checks the main.latest_posted_message and updates the label.
    """
    if main.latest_posted_message:
        posted_message_label.config(text=main.latest_posted_message)
    root.after(5000, update_posted_message)

# --- Clear Data ---
def clear_data():
    """
    Clears the previous_data.json file, resets analytics and clears the posted message.
    """
    main.clear_json_file()  # Clears the file content in main
    # Reset analytics
    update_analytics_from_file()
    # Clear posted message
    main.latest_posted_message = None
    posted_message_label.config(text="")
    update_status("Data cleared and stats reset.")

# --- Terminal Output Redirection ---
class TextRedirector(io.StringIO):
    """
    Redirects stdout to a text widget. Buffers output and flushes periodically.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, message):
        self.buffer += message

    def flush(self):
        pass

def update_terminal():
    """
    Periodically checks if there's new output in our StringIO buffer
    and writes it into the Text widget.
    """
    new_content = stdout_redirector.buffer
    if new_content:
        terminal_text.configure(state='normal')
        terminal_text.insert(tk.END, new_content)
        terminal_text.configure(state='disabled')
        terminal_text.see(tk.END)
        stdout_redirector.buffer = ""
    root.after(1000, update_terminal)

# --- GUI Setup ---
root = tk.Tk()
root.title("Traffic Incident Bot")
root.geometry("800x700")
root.configure(bg="#F5F5F5")

# Title Label
title_label = tk.Label(
    root, text="Traffic Incident Bot",
    font=("Arial", 20, "bold"),
    bg="#F5F5F5", fg="#333"
)
title_label.pack(pady=10)

# Status Label
status_label = tk.Label(
    root, text="Status: Not running",
    font=("Arial", 14),
    bg="#F5F5F5", fg="#555"
)
status_label.pack(pady=5)

# Button Frame
button_frame = tk.Frame(root, bg="#F5F5F5")
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Start Bot", command=start_bot)
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(button_frame, text="Stop Bot", command=stop_bot)
stop_button.grid(row=0, column=1, padx=10)

image_button = ttk.Button(button_frame, text="Show Latest Image", command=show_latest_image)
image_button.grid(row=1, column=0, padx=0, pady=0)

clear_button = ttk.Button(button_frame, text="Clear Data", command=clear_data)
clear_button.grid(row=1, column=1, padx=10, pady=10)

# Analytics Frame
analytics_frame = tk.Frame(root, bg="#F5F5F5")
analytics_frame.pack(pady=20)

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

# Posted Message Label
posted_message_label = tk.Message(
    root,
    text="",
    font=("Arial", 14),
    bg="#F5F5F5",
    fg="#333",
    width=700,
    justify="left"
)
posted_message_label.pack(pady=5, fill='x', padx=10)

# Map Label
map_label = tk.Label(root, bg="#F5F5F5", width=800, height=200)
map_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Terminal Frame
terminal_frame = tk.Frame(root, bg="#F5F5F5")
terminal_frame.pack(fill='both', expand=True, padx=10, pady=10)

terminal_label = tk.Label(
    terminal_frame, text="Terminal Output:",
    font=("Arial", 14),
    bg="#F5F5F5", fg="#333"
)
terminal_label.pack(anchor='w')

terminal_text = tk.Text(terminal_frame, wrap='word', state='disabled', font=("Consolas", 10))
terminal_text.pack(fill='both', expand=True)

# Redirect stdout
stdout_redirector = TextRedirector(terminal_text)
sys.stdout = stdout_redirector

# Bind events and start periodic updates
root.bind("<Configure>", lambda event: show_latest_image())

update_analytics_from_file()
monitor_analytics_file()
update_posted_message()
update_terminal()

root.mainloop()
