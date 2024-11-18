# import json

# # File paths
# FILE_CURRENT = "./temp/new.json"  # Path to the current data file
# FILE_OLD = "./temp/old.json"  # Path to the old data file
# OUTPUT_FILE = "./temp/final.json"  # Path for the final output file

# def load_json(file_path):
#     """Load JSON data from a file."""
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             data = json.load(file)
#             print(f"Loaded {len(data)} records from {file_path}")
#             return data
#     except FileNotFoundError:
#         print(f"File not found: {file_path}")
#         return []
#     except json.JSONDecodeError as e:
#         print(f"Invalid JSON format in file {file_path}: {e}")
#         return []

# def save_json(data, file_path):
#     """Save JSON data to a file."""
#     try:
#         with open(file_path, 'w', encoding='utf-8') as file:
#             json.dump(data, file, indent=4)
#         print(f"Data saved to {file_path}. Total records: {len(data)}")
#     except Exception as e:
#         print(f"Error saving file {file_path}: {e}")

# def merge_unique_posts(current_data, old_data):
#     """Merge two datasets, retaining only one post per title."""
#     seen_titles = set()
#     unique_posts = []

#     # Add posts from the current data first
#     for post in current_data:
#         title = post.get("title", "").strip().lower()
#         if title not in seen_titles:
#             seen_titles.add(title)
#             unique_posts.append(post)

#     # Add posts from the old data only if the title is not already seen
#     for post in old_data:
#         title = post.get("title", "").strip().lower()
#         if title not in seen_titles:
#             seen_titles.add(title)
#             unique_posts.append(post)

#     return unique_posts

# def main():
#     # Load data from both files
#     current_data = load_json(FILE_CURRENT)
#     old_data = load_json(FILE_OLD)

#     if not current_data and not old_data:
#         print("No data to process. Exiting.")
#         return

#     # Merge unique posts
#     final_data = merge_unique_posts(current_data, old_data)

#     # Save the final data to a new file
#     save_json(final_data, OUTPUT_FILE)

# if __name__ == "__main__":
#     main()


import json

# File paths
FILE_CURRENT = "./temp/new.json"  # Path to the current data file
FILE_OLD = "./temp/old.json"  # Path to the old data file
OUTPUT_FILE = "./temp/final_posts.json"  # Path for the final output file

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Loaded {len(data)} records from {file_path}")
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format in file {file_path}: {e}")
        return []

def save_json(data, file_path):
    """Save JSON data to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}. Total records: {len(data)}")
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")

def filter_new_posts(current_data, old_data):
    """Filter out posts from current_data if their title exists in old_data."""
    old_titles = {post.get("title", "").strip().lower() for post in old_data}
    filtered_posts = [post for post in current_data if post.get("title", "").strip().lower() not in old_titles]
    return filtered_posts

def remove_id_fields(data):
    """Remove 'id' and '_id' fields from each post."""
    for post in data:
        if 'id' in post:
            del post['id']
        if '_id' in post:
            del post['_id']
    return data

def main():
    # Load data from both files
    current_data = load_json(FILE_CURRENT)
    old_data = load_json(FILE_OLD)

    if not current_data:
        print("No new data to process. Exiting.")
        return

    if not old_data:
        print("No old data found. All new data will be saved.")
        save_json(current_data, OUTPUT_FILE)
        return

    # Filter out old titles from the new data
    filtered_data = filter_new_posts(current_data, old_data)

    # Save the final data to a new file

    final_Posts= remove_id_fields(filtered_data)

    save_json(final_Posts, OUTPUT_FILE)

if __name__ == "__main__":
    main()
