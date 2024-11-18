import praw
import json
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import re
import openai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

OUTPUT_SCRAPED_FILE = "./data/scraped_posts.json"
FILTERED_DATA_FILE = "./data/filtered_posts.json"
FINAL_CLEANED_FILE = "./data/ready_posts.json"

TARGET_UNIQUE_POSTS = 20
SUBREDDITS = [
    "logistics", "shipping", "supplychain", "freight", "transportation", "operations",
    "packaging", "warehousing", "3pl", "supplychainlogistics", "logisticsmanagement",
    "supplychainmanagement", "trucking", "airfreight", "maritimelogistics",
    "lastmiledelivery", "inventorymanagement", "sustainablelogistics",
    "freightbrokers", "logisticstechnology"
]

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

unique_posts = []
seen_titles = set()

def save_data(data, file_path):
    """Save data to a file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")

def clean_content(content):
    """Clean content text."""
    clean_text = re.sub(r"<[^>]*>", "", content)
    clean_text = re.sub(r"\[.*?\]\(.*?\)", "", clean_text)
    clean_text = re.sub(r"\*|\_", "", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text

def paraphrase_content(content):
    """Paraphrase content using OpenAI."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that paraphrases text concisely while preserving its original meaning."},
                {"role": "user", "content": f"Paraphrase the following text:\n\n{content}"}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error during paraphrasing: {e}")
        return content

def fetch_comments(submission, max_comments=5):
    """Fetch comments from a submission."""
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

def scrape_subreddit(subreddit, limit=100):
    """Scrape subreddit posts."""
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
            }
            results.append(post)
            logging.info(f"Scraped post ID: {submission.id}")
    except Exception as e:
        logging.error(f"Error fetching posts from subreddit {subreddit}: {e}")
    return results

def remove_duplicates(posts):
    """Remove duplicate posts based on title."""
    seen_titles = {}
    for post in posts:
        title = post['title']
        if title not in seen_titles:
            seen_titles[title] = post
        else:
            existing_post = seen_titles[title]
            if post['upvotes'] > existing_post['upvotes']:
                seen_titles[title] = post
    return list(seen_titles.values())

def process_content(posts):
    """Clean and paraphrase content of posts."""
    for post in posts[:10]: 
        post["content"] = paraphrase_content(clean_content(post["content"]))
    return posts

def scrape_unique_posts():
    """Scrape unique posts across subreddits."""
    global unique_posts, seen_titles
    while len(unique_posts) < TARGET_UNIQUE_POSTS:
        for subreddit in SUBREDDITS:
            if len(unique_posts) >= TARGET_UNIQUE_POSTS:
                break
            logging.info(f"Scraping subreddit: {subreddit}")
            subreddit_posts = scrape_subreddit(subreddit, limit=100)
            for post in subreddit_posts:
                if post['title'] not in seen_titles:
                    seen_titles.add(post['title'])
                    unique_posts.append(post)
    return unique_posts

def remove_id_fields(data):
    """Remove 'id' and '_id' fields from each post."""
    for post in data:
        if 'id' in post:
            del post['id']
        if '_id' in post:
            del post['_id']
    return data

def main():
    logging.info("Starting Reddit scraper...")
    
    scraped_posts = scrape_unique_posts()
    save_data(scraped_posts, OUTPUT_SCRAPED_FILE)

    unique_posts = remove_duplicates(scraped_posts)
    save_data(unique_posts, FILTERED_DATA_FILE)

    cleaned_posts = process_content(unique_posts)
    save_data(cleaned_posts, FINAL_CLEANED_FILE)

    final_posts = remove_id_fields(cleaned_posts)
    save_data(final_posts, './data/final_posts.json')

    logging.info("Scraping and processing completed.")

if __name__ == "__main__":
    main()
