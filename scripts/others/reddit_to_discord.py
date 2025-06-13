import praw
import time
import os
import requests

# --- Configuration ---
# Store sensitive information like client_id and client_secret in environment variables.
# The Discord Webhook URL is directly set as requested.
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# Replace "u/YourRedditUsername" with your actual Reddit username.
REDDIT_USER_AGENT = "OmniscientReaderDiscordBot/1.0 by u/YourRedditUsername"
SUBREDDIT_NAME = "OmniscientReader"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383081509287886898/yvNw5rxgq3gfMm7wJzP7XKCbJbdFyLiyFM_UjISFfiP3BMGw4IvKKbcFJNjIqTVXLU"

# To prevent duplicate posts, store fetched post IDs in a set.
# For a persistent bot, you'd save this to a database or file.
fetched_post_ids = set()

def send_to_discord(title, url):
    """Sends a message to the configured Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set. Cannot send message.")
        return

    payload = {
        "content": f"New post on r/{SUBREDDIT_NAME}!\n**{title}**\n{url}"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Successfully sent message to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Discord: {e}")

def fetch_reddit_posts_praw():
    global fetched_post_ids
    print("Starting Reddit to Discord Bot...")

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        print(f"Fetching new posts from r/{SUBREDDIT_NAME}...")
        subreddit = reddit.subreddit(SUBREDDIT_NAME)

        new_posts_found = False
        posts_to_process = []

        # Check the 10 newest posts.
        for submission in subreddit.new(limit=10):
            if submission.id not in fetched_post_ids:
                print(f"Found new post: {submission.title} (ID: {submission.id})")
                posts_to_process.append(submission)
                fetched_post_ids.add(submission.id)
                new_posts_found = True
            else:
                # Stop if an already processed post is found, assuming older posts have been handled.
                print(f"Post {submission.id} already processed. Stopping check for older posts.")
                break

        if not new_posts_found:
            print("No new Reddit posts found.")
        else:
            # Process new posts by sending them to Discord, starting with the oldest.
            for post in reversed(posts_to_process):
                print(f"Sending post to Discord: {post.title} (URL: {post.url})")
                send_to_discord(post.title, post.url)
                time.sleep(1) # Add a small delay to avoid Discord rate limits

    except praw.exceptions.APIException as e:
        print(f"Error fetching Reddit posts (PRAW API Exception): {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Reddit to Discord Bot finished.")

if __name__ == "__main__":
    # --- How to set environment variables (Crucial for Client ID/Secret) ---
    # For Linux/macOS:
    # export REDDIT_CLIENT_ID="your_client_id_here"
    # export REDDIT_CLIENT_SECRET="your_client_secret_here"
    #
    # For Windows (Command Prompt):
    # set REDDIT_CLIENT_ID="your_client_id_here"
    # set REDDIT_CLIENT_SECRET="your_client_secret_here"

    fetch_reddit_posts_praw()

    # Uncomment the loop below to run the bot periodically.
    # while True:
    #     fetch_reddit_posts_praw()
    #     print("Waiting for 5 minutes before next check...")
    #     time.sleep(300)
