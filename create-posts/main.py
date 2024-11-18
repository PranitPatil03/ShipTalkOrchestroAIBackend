import praw
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import signal
import sys
import re
from openai import ChatCompletion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ChatCompletion.api_key = OPENAI_API_KEY

OUTPUT_SCRAPED_FILE = "./data/scraped_posts.json"
FILTERED_DATA_FILE = "./data/filtered_posts.json"
OUTPUT_POSTS_FILE = "./data/final_posts.json"

TARGET_UNIQUE_POSTS = 5000
SUBREDDITS = [
    "logistics",
    "shipping",
    "supplychain",
    "freight",
    "transportation",
    "operations",
    "packaging",
    "warehousing",
    "3pl",
    "supplychainlogistics",
    "logisticsmanagement",
    "supplychainmanagement",
    "trucking",
    "airfreight",
    "maritimelogistics",
    "lastmiledelivery",
    "inventorymanagement",
    "sustainablelogistics",
    "freightbrokers",
    "logisticstechnology"
]

unique_posts = []
seen_titles = set()


def save_to_file(data, file_path):
    """Save JSON data to a file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")


def load_data(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            logging.info(f"Loaded data from {file_path} with {len(data)} entries.")
            return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in file {file_path}: {e}")
        return []


def handle_exit_signal(signal_received, frame):
    """Handle script exit and save scraped posts."""
    logging.info("User requested to stop the script. Saving scraped posts...")
    save_to_file(unique_posts, OUTPUT_SCRAPED_FILE)
    logging.info(f"Saved {len(unique_posts)} unique posts.")
    sys.exit(0)


def clean_content(content):
    """Clean the content by removing unnecessary characters."""
    clean_text = re.sub(r"<[^>]*>", "", content)  
    clean_text = re.sub(r"\[.*?\]\(.*?\)", "", clean_text)  
    clean_text = re.sub(r"\*|\_", "", clean_text)  
    clean_text = re.sub(r"\s+", " ", clean_text).strip()  
    return clean_text


def paraphrase_content(content):
    """Use OpenAI to paraphrase content."""
    logging.info("Starting paraphrasing.")
    try:
        response = ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that paraphrases text concisely while preserving its original meaning."
                },
                {
                    "role": "user",
                    "content": f"Paraphrase the following content:\n\n{content}"
                }
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Paraphrasing failed: {e}")
        return content


def process_content(posts):
    """Process the content of each post."""
    for index, post in enumerate(posts):
        logging.info(f"Processing post ID: {index + 1}")
        post["content"] = paraphrase_content(clean_content(post["content"]))
    return posts



def fetch_comments(submission, max_comments=5):
    """Fetch top comments from a submission."""
    comments = []
    try:
        submission.comments.replace_more(limit=0)
        for comment in submission.comments[:max_comments]:
            comments.append({
                "author": str(comment.author) if comment.author else "Anonymous",
                "content": comment.body,
                "upvotes": comment.score,
                "created_at": datetime.fromtimestamp(comment.created_utc, timezone.utc).isoformat(),
            })
    except Exception as e:
        logging.error(f"Error fetching comments: {e}")
    return comments


def categorize_post(title):
    """Categorize a post based on keywords in the title."""
    categories = {
        "logistics": ["logistics", "supply chain", "warehouse"],
        "freight": ["freight", "shipping", "transportation"],
        "packaging": ["packaging", "sustainable", "eco-friendly"],
        "inventory": ["inventory", "management", "stock"],
        "last-mile": ["last mile", "delivery", "final mile"],
    }
    for category, keywords in categories.items():
        if any(keyword in title for keyword in keywords):
            return category
    return "general"


def scrape_subreddit(subreddit, limit=200):
    """Scrape posts from a subreddit."""
    results = []
    try:
        posts = reddit.subreddit(subreddit).new(limit=limit)
        for submission in posts:
            post = {
                "id": submission.id,
                "title": submission.title.strip().lower(),
                "content": submission.selftext or "",
                "subreddit": subreddit,
                "author": str(submission.author) if submission.author else "Anonymous",
                "upvotes": submission.score,
                "created_at": datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                "url": submission.url,
                "comments": fetch_comments(submission),
                "category": categorize_post(submission.title.lower()),
            }
            results.append(post)
    except Exception as e:
        logging.error(f"Error fetching posts from subreddit {subreddit}: {e}")
    return results


def scrape_unique_posts():
    """Scrape unique posts across subreddits."""
    global unique_posts, seen_titles
    post_limit = 200

    while len(unique_posts) < TARGET_UNIQUE_POSTS:
        for subreddit in SUBREDDITS:
            if len(unique_posts) >= TARGET_UNIQUE_POSTS:
                break

            logging.info(f"Scraping subreddit: {subreddit} with limit {post_limit}")
            subreddit_results = scrape_subreddit(subreddit, limit=post_limit)

            for post in subreddit_results:
                title = post["title"]
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_posts.append(post)

                    if len(unique_posts) >= TARGET_UNIQUE_POSTS:
                        break

            logging.info(f"Unique posts collected so far: {len(unique_posts)}")

    logging.info(f"Total unique posts collected: {len(unique_posts)}")
    return unique_posts


def main():
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    logging.info("Starting Reddit scraper...")

    scrape_unique_posts()
    save_to_file(unique_posts, OUTPUT_SCRAPED_FILE)

    filtered_data = load_data(OUTPUT_SCRAPED_FILE)
    processed_posts = process_content(filtered_data)
    save_to_file(processed_posts, OUTPUT_POSTS_FILE)

    logging.info("Scraping and processing completed.")


if __name__ == "__main__":
    main()
