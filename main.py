import requests
import json
import os
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Function to scrape top 10 clans from territorial.io
def scrape_top_clans():
    try:
        response = requests.get('https://territorial.io/clans')
        content = response.text
        lines = content.split('\n')
        top_10_clans = []
        count = 0
        for line in lines:
            parts = line.split(',')
            if len(parts) == 3 and parts[0].strip().isdigit():
                rank = parts[0].strip()
                name = parts[1].strip()
                points = parts[2].strip()
                if name and points.replace('.', '').replace('-', '').isdigit():
                    clan_info = {'rank': rank, 'name': name, 'points': points}
                    top_10_clans.append(clan_info)
                    count += 1
                    if count == 10:  # Limit to top 10 clans
                        break
        return top_10_clans
    except Exception as e:
        print(f"Error scraping top clans: {e}")
        return None

# Function to save data to JSON file
def save_data(data):
    try:
        with open('clan_data.json', 'w') as file:
            json.dump(data, file, indent=4)
        print("Data saved successfully.")
    except Exception as e:
        print(f"Error saving data: {e}")

# Function to load data from JSON file
def load_data():
    try:
        with open('clan_data.json', 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("No data file found.")
        return None
    except Exception as e:
        print(f"Error loading data: {e}")

# Function to delete old data (older than 30 days)
def delete_old_data():
    try:
        if os.path.exists('clan_data.json'):
            creation_time = os.path.getctime('clan_data.json')
            file_age = time.time() - creation_time
            if file_age > 30 * 24 * 60 * 60:  # 30 days in seconds
                os.remove('clan_data.json')
                print("Old data deleted.")
    except Exception as e:
        print(f"Error deleting old data: {e}")

# Function to create graph from data over the past day
def create_graph(data, filename):
    try:
        # Extract relevant data for the past day
        past_day_data = [entry for entry in data if datetime.now() - datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') <= timedelta(days=1)]
        
        # Get unique clan names
        clan_names = set(entry['name'] for entry in past_day_data)
        
        # Plotting
        plt.figure(figsize=(10, 6))
        for clan_name in clan_names:
            clan_data = [entry for entry in past_day_data if entry['name'] == clan_name]
            points = [float(entry['points']) for entry in clan_data]
            timestamps = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in clan_data]
            plt.plot(timestamps, points, marker='o', label=clan_name)
        
        plt.xlabel('Time')
        plt.ylabel('Points')
        plt.title('Top Clans Points over Past Day')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.grid(True)
        plt.legend(loc='upper right')  # Position legend in the top right corner
        plt.savefig(filename)  # Save the plot as an image
        plt.close()
        print("Graph created successfully.")
        return True
    except Exception as e:
        print(f"Error creating graph: {e}")
        return False


# Function to send graph via Discord webhook
import os

# Function to send graph via Discord webhook
def send_graph_to_discord(filename):
    try:
        # Read image file
        with open(filename, 'rb') as file:
            image_data = file.read()

        # Discord webhook URL from environment variable
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

        # Payload
        payload = {
            'content': 'Top Clans Rankings over Past Day',
            'file': (filename, image_data, 'image/png')
        }

        # Send POST request to Discord webhook
        response = requests.post(webhook_url, files=payload)
        if response.status_code == 200:
            print("Graph sent successfully.")
        else:
            print("Failed to send graph:", response.text)
    except Exception as e:
        print(f"Error sending graph to Discord: {e}")


# Main function
def main():
    # Scrape top clans
    top_clans = scrape_top_clans()
    
    # Load existing data or create new if not found
    existing_data = load_data() or []
    
    # Update timestamp for new data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for entry in top_clans:
        entry['timestamp'] = timestamp
    
    # Combine new data with existing data
    combined_data = existing_data + top_clans
    
    # Save combined data
    save_data(combined_data)
    
    # Delete old data
    delete_old_data()
    
    # Create graph for top 5 clans
    top_5_data = [entry for entry in combined_data if int(entry['rank']) <= 5]
    top_5_graph_created = create_graph(top_5_data, 'top_5_clans_rankings.png')
    if top_5_graph_created:
        send_graph_to_discord('top_5_clans_rankings.png')
    
    # Create graph for top 6-10 clans
    top_6_to_10_data = [entry for entry in combined_data if 6 <= int(entry['rank']) <= 10]
    top_6_to_10_graph_created = create_graph(top_6_to_10_data, 'top_6_to_10_clans_rankings.png')
    if top_6_to_10_graph_created:
        send_graph_to_discord('top_6_to_10_clans_rankings.png')

if __name__ == "__main__":
    main()
