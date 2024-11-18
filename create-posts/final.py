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

# Limit to 10 posts for testing
TARGET_UNIQUE_POSTS = 10

# Subreddits and topic keywords
SUBREDDITS = ["logistics"]  # Use a single subreddit for testing
TOPICS_KEYWORDS = {
    "Parcel Shipping": ["parcel shipping", "package shipping", "parcel delivery", "package transit"],
    "Sustainable Packaging": ["eco-friendly packaging", "sustainable packaging", "green packaging"],
    "Last Mile Innovation": ["last mile delivery", "last mile solutions", "final delivery stage"],
    # Add more topics as needed
}

# Initialize Reddit
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# Functions
def save_data(data, file_path):
    """Save JSON data to a file."""
    logging.info(f"Saving data to {file_path}...")
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save data: {e}")

def clean_content(content):
    """Clean HTML tags and unnecessary formatting."""
    if not content:
        return ""
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
                {"role": "system", "content": "Paraphrase text concisely while preserving its meaning."},
                {"role": "user", "content": f"Paraphrase:\n{content}"}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error paraphrasing content: {e}")
        return content

def matches_keywords(text):
    """Check if text contains topic keywords."""
    if not text:
        return False
    for keywords in TOPICS_KEYWORDS.values():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return True
    return False

def filter_posts(posts):
    """Filter relevant posts based on keywords."""
    filtered = sorted(
        [post for post in posts if matches_keywords(post['title']) or matches_keywords(post['content'])],
        key=lambda x: (x['upvotes'], len(x['comments'])),
        reverse=True
    )
    return filtered[:TARGET_UNIQUE_POSTS]  # Limit to 10 filtered posts

def scrape_subreddit(subreddit, limit=100):
    """Scrape subreddit posts."""
    results = []
    try:
        posts = reddit.subreddit(subreddit).new(limit=limit)
        for submission in posts:
            post = {
                "id": submission.id,
                "title": submission.title.strip(),
                "content": submission.selftext or "",
                "subreddit": subreddit,
                "author": str(submission.author) if submission.author else "Anonymous",
                "upvotes": submission.score,
                "created_at": datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                "url": submission.url,
                "comments": fetch_comments(submission),
            }
            results.append(post)
        logging.info(f"Scraped {len(results)} posts from {subreddit}.")
    except Exception as e:
        logging.error(f"Error scraping subreddit {subreddit}: {e}")
    return results[:TARGET_UNIQUE_POSTS]  # Limit to 10 posts

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

def main():
    logging.info("Starting Reddit scraper...")
    scraped_posts = []
    for subreddit in SUBREDDITS:
        scraped_posts.extend(scrape_subreddit(subreddit, limit=TARGET_UNIQUE_POSTS))
    save_data(scraped_posts, OUTPUT_SCRAPED_FILE)

    filtered_posts = filter_posts(scraped_posts)
    save_data(filtered_posts, FILTERED_DATA_FILE)

    cleaned_posts = [
        {**post, "content": paraphrase_content(clean_content(post["content"]))}
        for post in filtered_posts
    ]
    save_data(cleaned_posts, FINAL_CLEANED_FILE)
    logging.info("Scraping and processing completed.")

if __name__ == "__main__":
    main()
