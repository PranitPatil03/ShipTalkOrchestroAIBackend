import praw
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import signal
import sys


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


load_dotenv()

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)


OUTPUT_SCRAPED_FILE = "./data/scraped_posts.json"
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
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save data to file {file_path}: {e}")


def handle_exit_signal(signal_received, frame):
    """Handle script exit and save scraped posts."""
    logging.info("User requested to stop the script. Saving scraped posts...")
    save_to_file(unique_posts, OUTPUT_SCRAPED_FILE)
    logging.info(f"Saved {len(unique_posts)} unique posts.")
    sys.exit(0)


def fetch_comments(submission, max_comments=5):
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
            logging.info(f"Scraped post ID: {submission.id}")
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

            if len(subreddit_results) < post_limit and len(unique_posts) < TARGET_UNIQUE_POSTS:
                logging.info(f"Subreddit {subreddit} exhausted. Increasing post limit.")
                post_limit += 50  

    logging.info(f"Total unique posts collected: {len(unique_posts)}")
    return unique_posts


def main():
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    logging.info("Starting Reddit scraper...")

    scrape_unique_posts()

    save_to_file(unique_posts, OUTPUT_SCRAPED_FILE)

    logging.info("Scraping completed.")


if __name__ == "__main__":
    main()
