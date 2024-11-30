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
def clear_json_file(filename="previous_data.json"):
    """
    Clears the contents of the specified JSON file.
    """
    with open(filename, "w") as file:
        json.dump([], file, indent=4)
        
def load_data_from_file(filename="previous_data.json"):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return []

def save_data_to_file(data, filename="previous_data.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


async def summarize_data(data):
    global latest_gpt_description
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
    latest_gpt_description = response.choices[0].message.content
    return latest_gpt_description

def get_latest_description():
    return latest_gpt_description

async def post_to_discord(channel_id, message, image_path=None):

    channel = client.get_channel(int(channel_id))
    if channel:
        if image_path and os.path.exists(image_path):
            # Attach the image
            with open(image_path, 'rb') as image_file:
                file = discord.File(image_file)
                await channel.send(content=message, file=file)
        else:
            # Post only the message if no image is available
            await channel.send(message)
    else:
        print(f"Could not find the specified channel with ID {channel_id}.")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    asyncio.create_task(traffic_monitor())

async def traffic_monitor():
    global posted_incidents
    all_previous_data = load_data_from_file()  # Load existing data from file

    # Build a set of existing incident numbers for quick duplicate checking
    existing_incident_numbers = {entry.get("No.") for entry in all_previous_data if "No." in entry}

    while True:
        try:
            print("Fetching merged data...")
            current_data = get_merged_data()
            print(f"Current data: {current_data}")

            # Generate a unique identifier for the incident
            incident_id = (
                current_data.get("Incident No.") or
                f"{current_data.get('Time')}-{current_data.get('Location')}"
            )

            # Check if the incident is a duplicate using the "No." field
            current_incident_no = current_data.get("No.")
            if current_incident_no in existing_incident_numbers:
                print("Duplicate incident detected. Skipping...")
                continue

            if current_data and incident_id not in posted_incidents:
                print("New incident detected. Preparing to post...")

                # Generate the map image
                lon = current_data.get("Longitude")
                lat = current_data.get("Latitude")
                image_path = 'map.png'
                save_map_image(lon, lat, MAP_ACCESS_TOKEN, image_path)

                # Summarize the data
                summary = await summarize_data(current_data)
                print(f"Summary: {summary}")

                # Post to Discord
                await post_to_discord(DISCORD_CHANNEL_ID, summary, image_path)

                # Mark as posted and update the file
                posted_incidents.add(incident_id)
                existing_incident_numbers.add(current_incident_no)  # Add new incident to the set
                all_previous_data.append(current_data)  # Add new incident to the list
                save_data_to_file(all_previous_data)  # Save updated data to file
                print(f"Data saved to previous_data.json: {current_data}")
            else:
                print("No new data or duplicate incident.")
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(30)


if __name__ == "__main__":
    clear_json_file()
    client.run(DISCORD_TOKEN)
