import json
import requests
import sys
import time

def load_json_file(file_path: str) -> list:
    """Load and parse JSON data from file to get post IDs."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return [post['id'] for post in data if 'id' in post]
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return []

def delete_posts(post_ids: list, base_url: str = "http://localhost:8000") -> None:
    """Delete posts from the database using the FastAPI endpoint."""
    successful = 0
    failed = 0
    total = len(post_ids)

    print(f"Starting deletion of {total} posts...")

    for index, post_id in enumerate(post_ids, 1):
        try:
            response = requests.delete(f"{base_url}/delete_post/{post_id}")
            
            if response.status_code == 200:
                print(f"[{index}/{total}] Successfully deleted post with ID: {post_id}")
                successful += 1
            elif response.status_code == 404:
                print(f"[{index}/{total}] Post not found: ID {post_id}")
                failed += 1
            else:
                print(f"[{index}/{total}] Failed to delete post ID {post_id}. Status: {response.status_code}")
                print(f"Response: {response.text}")
                failed += 1
            
            time.sleep(0.5)
            
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure the FastAPI server is running.")
            sys.exit(1)
        except Exception as e:
            print(f"Error deleting post ID {post_id}: {str(e)}")
            failed += 1

def main():
    file_path = "./Posts/old_posts.json"
    
    post_ids = load_json_file(file_path)
    
    if post_ids:
        delete_posts(post_ids)
    else:
        print("No valid post IDs found in the JSON file")

if __name__ == "__main__":
    main()
