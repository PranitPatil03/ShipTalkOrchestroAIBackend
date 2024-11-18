import json


with open('./data/scraped_posts.json', 'r') as file:
    data = json.load(file)

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

with open('./data/cleaned_posts.json', 'w') as file:
    json.dump(unique_data, file, indent=4)

print("Duplicates removed and data saved to 'cleaned_posts.json'.")
