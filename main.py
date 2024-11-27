import asyncio
import discord
from traffic_scraper import get_merged_data
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
import json
from map_generator import save_map_image

# Initialize Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Load environment variables
load_dotenv(find_dotenv())
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
MAP_ACCESS_TOKEN = os.getenv("MAP_ACCESS_TOKEN")

# Track posted incidents to avoid duplicates
posted_incidents = set()

def load_data_from_file(filename="TrafficIncidentBot/previous_data.json"):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return []

def save_data_to_file(data, filename="TrafficIncidentBot/previous_data.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

async def summarize_data(data):
    client_gpt = OpenAI(api_key=os.getenv("GPT_KEY"))
    prompt = (
        "Write a one-sentence summary with emojis for a traffic incident using the following details:\n"
        f"- Type: {data.get('Type')}\n"
        f"- Report No.: {data.get('Incident No.', 'N/A')}\n"
        f"- Time: {data.get('Time')}\n"
        f"- Location: {data.get('Location')}\n"
        f"- Details: {data.get('Details', 'No additional details available')}\n"
        "Make it concise, engaging, and include related emojis."
    )
    response = client_gpt.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a traffic reporter creating engaging one-sentence summaries for traffic incidents."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.7
    )
    return response.choices[0].message.content

async def post_to_discord(channel_id, message, image_path=None):
    channel = client.get_channel(int(channel_id))
    if channel:
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                file = discord.File(image_file)
                await channel.send(content=message, file=file)
        else:
            await channel.send(message)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    asyncio.create_task(traffic_monitor())

async def traffic_monitor():
    global posted_incidents
    previous_data = {}
    all_previous_data = load_data_from_file()

    while True:
        try:
            current_data = get_merged_data()
            if current_data:
                incident_id = (
                    current_data.get("Incident No.") or
                    f"{current_data.get('Time')}-{current_data.get('Location')}"
                )
                if incident_id not in posted_incidents:
                    lon = current_data.get("Longitude")
                    lat = current_data.get("Latitude")
                    image_path = 'TrafficIncidentBot/map.png'
                    save_map_image(lon, lat, MAP_ACCESS_TOKEN, image_path)

                    summary = await summarize_data(current_data)
                    await post_to_discord(DISCORD_CHANNEL_ID, summary, image_path)

                    posted_incidents.add(incident_id)
                    previous_data = current_data
                    save_data_to_file(all_previous_data)
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
