# Ship Talk 🚢💬

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/PranitPatil03/ShipTalkOrchestroAIBackend.git
   cd ShipTalk
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## API Documentation

### 🏠 Health Check
- **`GET /healthcheck`**
  - **Response**: 
    ```json
    {
      "message": "Server is up and running",
      "domain": "server_hostname"
    }
    ```

### 📝 Posts Endpoints

#### 1. Get Posts
- **`GET /get_posts/`**
  - **Query Params**: 
    - `search`: Optional search term
    - `sort_by`: Sort options (created_at, upvotes, title)
    - `limit`: Number of posts to return
    - `offset`: Pagination offset
  - **Response**: 
    ```json
    {
      "posts": [
        {
          "id": "1gu32g2",
          "title": "shipping 200kg from malaga to niamey",
          "content": "Detailed post content...",
          "subreddit": "logistics",
          "author": "Obvious_Law6783",
          "upvotes": 1,
          "created_at": "2024-11-18T11:57:41+00:00",
          "url": "full_post_url",
          "category": "freight"
        }
      ],
      "total_posts": 1,
      "limit": 10,
      "offset": 0
    }
    ```

#### 2. Upload Post
- **`POST /upload_post/`**
  - **Request Body**: 
    ```json
    {
      "title": "Shipping 200kg from Malaga to Niamey",
      "content": "Detailed shipping inquiry text",
      "subreddit": "logistics",
      "author": "Username",
      "category": "freight"
    }
    ```
  - **Response**: Created post object with assigned ID

#### 3. Get Specific Post
- **`GET /get_post/{post_id}`**
  - **Response**: 
    ```json
    {
      "id": "1gu32g2",
      "title": "shipping 200kg from malaga to niamey",
      "content": "Full post content",
      "subreddit": "logistics",
      "author": "Obvious_Law6783",
      "upvotes": 1,
      "created_at": "2024-11-18T11:57:41+00:00",
      "url": "full_post_url",
      "comments": [
        {
          "author": "PJ-time",
          "content": "Detailed comment text",
          "upvotes": 1,
          "created_at": "2024-11-18T12:26:36+00:00"
        }
      ],
      "category": "freight"
    }
    ```

#### 4. Like Post
- **`GET /like_post/{post_id}`**
  - **Response**: 
    ```json
    {
      "message": "Post liked successfully",
      "upvotes": 2
    }
    ```

#### 5. Delete Post
- **`DELETE /delete_post/{post_id}`**
  - **Response**: 
    ```json
    {
      "message": "Post deleted successfully"
    }
    ```

### 💬 Comments Endpoints

#### 1. Upload Comment
- **`POST /upload_comment/{post_id}`**
  - **Request Body**: 
    ```json
    {
      "author": "PJ-time",
      "content": "Detailed logistics advice...",
      "upvotes": 0
    }
    ```
  - **Response**: Created comment object

#### 2. Like Comment
- **`GET /like_comment/{post_id}/{comment_id}`**
  - **Response**: 
    ```json
    {
      "message": "Comment liked successfully",
      "upvotes": 1
    }
    ```

#### 3. Delete Comment
- **`DELETE /delete_comment/{post_id}/{comment_id}`**
  - **Response**: 
    ```json
    {
      "message": "Comment deleted successfully"
    }
    ```

### 🤖 AI Chatbot
- **`POST /AI_bot/`**
  - **Request Body**: 
    ```json
    {
      "question": "How to ship heavy equipment internationally?"
    }
    ```
  - **Response**: 
    ```json
    {
      "answer": "Detailed AI-generated response about international shipping",
      "related_posts": [
        {
          "id": "1gu32g2",
          "title": "shipping 200kg from malaga to niamey",
          "url": "full_post_url"
        }
      ]
    }
    ```

### 📋 Get All Posts Endpoint

#### Get All Posts
- **`GET /get_all_posts/`**
  - **Query Parameters**:
    - `search`: Optional string to filter posts by title
    - `sort_by`: Optional sorting field (default: `created_at`)
      - Valid options: 
        - `created_at` (default)
        - `upvotes`
        - `title`

  - **Response**:
    ```json
    {
      "posts": [
        {
          "id": "1gu32g2",
          "title": "shipping 200kg from malaga to niamey",
          "content": "Full post content",
          "subreddit": "logistics",
          "author": "Obvious_Law6783",
          "upvotes": 1,
          "created_at": "2024-11-18T11:57:41+00:00",
          "category": "freight"
        }
        // More posts...
      ],
      "total_posts": 10
    }
    ```

### Post Creation and Database Population

#### Generating Posts
```bash
python create-post/main.py
```
This script generates `final_posts.json` in the `data` folder containing posts.

#### Adding Posts to Database
```bash
python Script/add_all_posts.py
```
Adds all posts from `final_posts.json` to the application's database.

