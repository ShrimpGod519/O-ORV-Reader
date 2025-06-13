import requests
import json
import time
import os

# --- Configuration ---
REDDIT_URL = "https://www.reddit.com/r/OmniscientReader/new.json"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383081509287886898/yvNw5rxgq3gfMm7wJzP7XKCgbbdyLiyFM_UjISFfiP3BMGw4IvKKbcFJNjIqTVwXVXLU"  # Replace with your actual Discord webhook URL
DATA_FILE = "reddit_posts.json"
HEADERS = {
    "User-Agent": "PythonRedditToDiscordBot/1.0"  # Always use a User-Agent for Reddit API requests
}

def load_existing_posts(filename):
    """Loads existing post IDs from a JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {filename}. Starting with empty data.")
                return []
    return []

def save_posts(filename, posts):
    """Saves post data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)

def fetch_reddit_posts(url, headers):
    """Fetches new posts from Reddit."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Reddit posts: {e}")
        return None

def create_discord_embed(post):
    """Creates a Discord embed dictionary from a Reddit post."""
    title = post['data'].get('title', 'No Title')
    url = post['data'].get('url', 'No URL')
    author = post['data'].get('author', 'Unknown Author')
    permalink = f"https://www.reddit.com{post['data'].get('permalink', '')}"
    thumbnail = post['data'].get('thumbnail')
    score = post['data'].get('score')
    num_comments = post['data'].get('num_comments')

    embed = {
        "title": title,
        "url": permalink,
        "description": f"Posted by u/{author}",
        "color": 16729344,  # A nice Reddit orange color (decimal)
        "fields": [],
        "footer": {
            "text": f"Score: {score} | Comments: {num_comments}"
        }
    }

    if thumbnail and thumbnail.startswith(('http', 'https')):
        embed["thumbnail"] = {"url": thumbnail}

    # Add URL as a field if it's different from permalink (e.g., direct image/article link)
    if url != permalink and url.startswith(('http', 'https')):
        embed["fields"].append({
            "name": "Link",
            "value": url,
            "inline": False
        })
      
    return embed

def send_discord_webhook(webhook_url, embeds):
    """Sends a Discord webhook message with embeds."""
    if not embeds:
        return

    payload = {
        "embeds": embeds
    }
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Successfully sent {len(embeds)} post(s) to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord webhook: {e}")

def main():
    print("Starting Reddit to Discord Bot...")
    existing_posts_data = load_existing_posts(DATA_FILE)
    existing_post_ids = {post['id'] for post in existing_posts_data}

    new_posts_to_save = []
    embeds_to_send = []

    reddit_data = fetch_reddit_posts(REDDIT_URL, HEADERS)

    if reddit_data and 'data' in reddit_data and 'children' in reddit_data['data']:
        new_posts_found = 0
        for post in reddit_data['data']['children']:
            post_id = post['data']['id']
            if post_id not in existing_post_ids:
                print(f"New post found: {post['data']['title']}")
                new_posts_to_save.append(post['data'])
                embeds_to_send.append(create_discord_embed(post))
                existing_post_ids.add(post_id) # Add to set to avoid duplicates within the same run
                new_posts_found += 1
            else:
                # Optionally, you can print that a post is already known
                # print(f"Post already known: {post['data']['title']}")
                pass
        print(f"Found {new_posts_found} new posts.")

        # Append new posts to the existing data before saving
        existing_posts_data.extend(new_posts_to_save)
        save_posts(DATA_FILE, existing_posts_data)
        print(f"Saved {len(new_posts_to_save)} new posts to {DATA_FILE}.")

        # Send embeds in batches if there are many to avoid Discord rate limits
        batch_size = 10  # Discord allows up to 10 embeds per message
        for i in range(0, len(embeds_to_send), batch_size):
            batch = embeds_to_send[i:i + batch_size]
            send_discord_webhook(DISCORD_WEBHOOK_URL, batch)
            time.sleep(1) # Small delay between batches to be safe

    else:
        print("No new Reddit posts found or an error occurred during fetch.")

    print("Reddit to Discord Bot finished.")

if __name__ == "__main__":
    main()
