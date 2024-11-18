import json
import requests
from typing import List, Dict
import time
import sys
from datetime import datetime

def load_json_file(file_path: str) -> List[Dict]:
    """Load and parse JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return []

def upload_posts(posts: List[Dict], base_url: str = "http://localhost:8000") -> None:
    """Upload posts to the database using the FastAPI endpoint."""
    successful = 0
    failed = 0
    total = len(posts)

    print(f"Starting upload of {total} posts...")

    for index, post in enumerate(posts, 1):
        try:
            post_data = {
                "title": post["title"],
                "content": post["content"],
                "author": post.get("author", "Anonymous"),
                "category": post.get("category", "Carrier Comparison"),
                "upvotes": post.get("upvotes", 0),
                "created_at": post.get("created_utc", datetime.utcnow().isoformat())
            }

            response = requests.post(f"{base_url}/upload_post/", json=post_data)

            if response.status_code == 201:
                print(f"[{index}/{total}] Successfully uploaded post: {post['title'][:50]}...")
                successful += 1

                post_id = response.json()["id"]
                if post.get("comments"):
                    for comment in post["comments"]:
                        comment_data = {
                            "content": comment["body"],
                            "author": comment.get("author", "Anonymous"),
                            "created_at": comment.get("created_utc", datetime.utcnow().isoformat())
                        }
                        comment_response = requests.post(
                            f"{base_url}/upload_comment/{post_id}",
                            json=comment_data
                        )
                        if comment_response.status_code != 201:
                            print(f"Failed to upload comment for post {post_id}: {comment_response.text}")
            else:
                print(f"[{index}/{total}] Failed to upload post: {post['title'][:50]}... Status: {response.status_code}")
                print(f"Response: {response.text}")
                failed += 1

            time.sleep(0.5)

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure the FastAPI server is running.")
            sys.exit(1)
        except KeyError as e:
            print(f"Missing key in post: {e}")
            failed += 1
        except Exception as e:
            print(f"Error uploading post: {str(e)}")
            failed += 1

def main():
    file_path = "./Posts/final_posts.json"

    posts = load_json_file(file_path)

    if posts:
        upload_posts(posts)
    else:
        print("No valid posts found in the JSON file")

if __name__ == "__main__":
    main()
