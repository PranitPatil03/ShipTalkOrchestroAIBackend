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

TARGET_UNIQUE_POSTS = 5

SUBREDDITS = [
    "logistics", "shipping", "supplychain", "freight", "transportation", "operations",
    "packaging", "warehousing", "3pl", "supplychainlogistics", "logisticsmanagement",
    "supplychainmanagement", "trucking", "airfreight", "maritimelogistics",
    "lastmiledelivery", "inventorymanagement", "sustainablelogistics",
    "freightbrokers", "logisticstechnology"
]

TOPICS_KEYWORDS = {
    "Parcel Shipping": ["parcel shipping", "package shipping", "parcel delivery", "package transit"],
    "Sustainable Packaging": ["eco-friendly packaging", "sustainable packaging", "green packaging"],
    "Last Mile Innovation": ["last mile delivery", "last mile solutions", "final delivery stage"],
    "Integration": ["system integration", "platform integration", "integration with"],
    "Carrier Solutions": ["carrier options", "carrier comparison", "shipping carriers", "freight carriers"],
    "Eco-Friendly": ["eco-friendly", "environmentally friendly", "sustainable", "green"],
    "3-2-1 Shipping": ["3-2-1 shipping", "3-2-1 logistics"],
    "Just-In-Time Inventory": ["just-in-time inventory", "JIT inventory", "inventory management"],
    "Cross-Docking": ["cross-docking", "dock transfer", "direct unloading"],
    "Distributed Inventory": ["distributed inventory", "inventory distribution", "regional inventory"],
    "Last-Mile Delivery Solutions": ["last-mile solutions", "last-mile logistics", "final mile delivery"],
    "Freight Consolidation": ["freight consolidation", "shipment consolidation", "consolidated freight"],
    "Dynamic Routing": ["dynamic routing", "adaptive routing", "route optimization"],
    "Third-Party Logistics (3PL)": ["third-party logistics", "3PL", "outsourced logistics"],
    "Seasonal Planning": ["seasonal planning", "holiday planning", "peak season planning"],
    "Cycle Counting": ["cycle counting", "inventory counting", "inventory auditing"],
    "Sales and Operations Planning (S&OP)": ["sales and operations planning", "S&OP", "sales planning"],
    "Cost-to-Serve Analysis": ["cost-to-serve", "cost analysis", "serve cost analysis"],
}

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
            model="gpt-4o-mini",
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

def matches_keywords(text):
    """Check if a text matches any of the keywords in the TOPICS_KEYWORDS."""
    for keywords in TOPICS_KEYWORDS.values():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return True
    return False

def filter_posts(posts):
    """Filter posts based on relevance to TOPICS_KEYWORDS."""
    filtered_posts = [post for post in posts if matches_keywords(post['title']) or matches_keywords(post['content'])]
    return sorted(filtered_posts, key=lambda x: (x['upvotes'], len(x['comments'])), reverse=True)

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
            logging.info(f"Scraped post ID: {submission.id}")
    except Exception as e:
        logging.error(f"Error fetching posts from subreddit {subreddit}: {e}")
    return results

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

def process_content(posts):
    """Clean and paraphrase content of posts."""
    for post in posts[:10]: 
        post["content"] = paraphrase_content(clean_content(post["content"]))
    return posts

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

    filtered_posts = filter_posts(scraped_posts)
    save_data(filtered_posts, FILTERED_DATA_FILE)

    cleaned_posts = process_content(filtered_posts)
    save_data(cleaned_posts, FINAL_CLEANED_FILE)

    final_posts = remove_id_fields(cleaned_posts)
    save_data(final_posts, './data/final_posts.json')

    logging.info("Scraping and processing completed.")

if __name__ == "__main__":
    main()
