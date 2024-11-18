import json

with open('./data/scraped_data.json', 'r') as file:
    data = json.load(file)

input_file = "./data/scraped_data.json"
output_file = "./data/cleaned_posts.json"

limit = 2500

if isinstance(data, list):
    data = data[:limit]
else:
    raise ValueError("The JSON file does not contain a list.")

def remove_duplicates(posts):
    seen_titles = {}
    unique_posts = []

    for post in posts:
        title = post['title']
        if title not in seen_titles:
            seen_titles[title] = post
        else:
            existing_post = seen_titles[title]
            if post['upvotes'] > existing_post['upvotes'] or post['created_utc'] < existing_post['created_utc']:
                seen_titles[title] = post

    unique_posts = list(seen_titles.values())
    return unique_posts

unique_data = remove_duplicates(data)

with open(output_file, 'w') as file:
    json.dump(unique_data, file, indent=4)

print("Duplicates removed and data saved to 'cleaned_posts_1.json'.")
