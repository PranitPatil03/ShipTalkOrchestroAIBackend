import json
import os
import logging
from datetime import datetime
from collections import Counter
from openai import ChatCompletion
from dotenv import load_dotenv
import re
import openai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ChatCompletion.api_key = OPENAI_API_KEY

FILTERED_DATA_FILE = "./data/filtered_posts.json"
OUTPUT_POSTS_FILE = "./data/final_posts.json"

def load_data(file_path):
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

def save_data(data, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Data saved to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")


def clean_content(content):
    clean_text = re.sub(r"<[^>]*>", "", content)  
    clean_text = re.sub(r"\[.*?\]\(.*?\)", "", clean_text)  
    clean_text = re.sub(r"\*|\_", "", clean_text)  
    clean_text = re.sub(r"\s+", " ", clean_text).strip()  
    return clean_text

def paraphrase_content(content):
    logging.info("Starting paraphrasing.")
    logging.debug(f"Content to paraphrase: {content}")  
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that paraphrases text concisely while preserving its original meaning and avoiding length increase."
                },
                {
                    "role": "user",
                    "content": f"Paraphrase the following content without changing its meaning or increasing its length:\n\n{content}"
                }
            ],
            max_tokens=500,
            temperature=0.7,
        )
        logging.info("Paraphrasing completed successfully.")
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Paraphrasing failed: {e}")
        return content

def process_content(posts):
    for index, post in enumerate(posts):  
        logging.info(f"Processing post ID: {index + 1}")  
        post["content"] = paraphrase_content(clean_content(post["content"]))
    return posts

def generate_test_posts(num_posts=10):
    """Generate a list of test posts."""
    return [{"content": f"This is test post number {i + 1}."} for i in range(num_posts)]

def main():
    filtered_data = load_data(FILTERED_DATA_FILE)

    if not filtered_data:
        logging.info("No data found. Generating test posts.")
        filtered_data = generate_test_posts(10)  

    created_posts = process_content(filtered_data)

    save_data(created_posts, OUTPUT_POSTS_FILE)


if __name__ == "__main__":
    main()