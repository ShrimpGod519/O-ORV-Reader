import praw
import time
import os
import requests
import re # For regular expressions to handle spoiler tags

# --- Configuration ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# Updated Reddit username
REDDIT_USER_AGENT = "OmniscientReaderDiscordBot/1.0 by u/RealNPC_"
SUBREDDIT_NAME = "OmniscientReader"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1383081509287886898/yvNw5rxgq3gfMm7wJzP7XKCgbbdyLiyFM_UjISFfiP3BMGw4IvKKbcFJNjIqTVwXVXLU"

fetched_post_ids = set()

def convert_reddit_spoiler_to_discord(text):
    """Converts Reddit's >!spoiler!< tag to Discord's ||spoiler|| tag."""
    # Regex to find >!any text here!<
    # The (?:.|\n) non-capturing group allows for newlines within the spoiler tag
    return re.sub(r'>!(.*?)!<', r'|| \1 ||', text, flags=re.DOTALL)

def get_submission_image_url(submission):
    """
    Attempts to get the best image URL for a submission thumbnail.
    Prioritizes preview image for image posts.
    """
    if submission.is_reddit_media_domain: # e.g., i.redd.it, v.redd.it
        # For direct image/video links from Reddit
        if hasattr(submission, 'url') and submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return submission.url
        elif hasattr(submission, 'preview') and 'images' in submission.preview and len(submission.preview['images']) > 0:
            # Get the source URL of the highest quality preview image
            return submission.preview['images'][0]['source']['url']
    elif hasattr(submission, 'thumbnail') and submission.thumbnail not in ("self", "default", "nsfw") and submission.thumbnail.startswith(('http', 'https')):
        # Fallback to general thumbnail if available and not a placeholder
        return submission.thumbnail
    return None # No suitable image found

def send_to_discord(submission):
    """Sends a rich embed message to the configured Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set. Cannot send message.")
        return

    embed_color = 3447003 # A pleasant blue (Hex #3498DB)

    # Convert Reddit spoiler tags in title and selftext
    embed_title = convert_reddit_spoiler_to_discord(submission.title)

    # Determine description and apply spoiler conversion
    description_text = ""
    if submission.is_self:
        description_text = convert_reddit_spoiler_to_discord(submission.selftext)
    elif submission.link_flair_text: # Sometimes a link flair can describe content
        description_text = f"Link Flair: {submission.link_flair_text}"
    else:
        description_text = "Click the title to view the post!"

    if len(description_text) > 4000:
        description_text = description_text[:4000] + "..."

    # Check for content warning (can be customized based on flair/keywords)
    content_warning = "None"
    if submission.over_18:
        content_warning = "NSFW"
    # You could add more sophisticated logic here, e.g.:
    # if "spoiler" in submission.link_flair_text.lower():
    #     content_warning = "Contains Spoilers"

    # Construct the embed
    embed = {
        "title": embed_title,
        "url": submission.url,
        "color": embed_color,
        "description": description_text,
        "fields": [
            {
                "name": "Post Author",
                "value": f"u/{submission.author.name}" if submission.author else "Deleted/Unknown",
                "inline": False
            },
            {
                "name": "Content Warning",
                "value": content_warning,
                "inline": False
            }
        ]
    }

    # Get thumbnail URL using the refined function
    thumbnail_url = get_submission_image_url(submission)
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Successfully sent embed message to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send embed message to Discord: {e}")

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

        for submission in subreddit.new(limit=10):
            if submission.id not in fetched_post_ids:
                print(f"Found new post: {submission.title} (ID: {submission.id})")
                posts_to_process.append(submission)
                fetched_post_ids.add(submission.id)
                new_posts_found = True
            else:
                print(f"Post {submission.id} already processed. Stopping check for older posts.")
                break

        if not new_posts_found:
            print("No new Reddit posts found.")
        else:
            for post in reversed(posts_to_process):
                print(f"Sending post to Discord: {post.title}")
                send_to_discord(post)
                time.sleep(1)

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
