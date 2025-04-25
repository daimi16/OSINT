import praw
import pandas as pd
from datetime import datetime

class RedditClient:
    def __init__(self, client_id, client_secret, user_agent):
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"Error initializing Reddit client: {e}")
            raise
    
    def search_posts(self, query="", subreddit=None, limit=25, sort='hot'):
        try:
            if subreddit:
                search_source = self.reddit.subreddit(subreddit)
            else:
                search_source = self.reddit.subreddit('all')
            
            if sort == 'hot':
                posts = search_source.hot(limit=limit)
            elif sort == 'new':
                posts = search_source.new(limit=limit)
            elif sort == 'top':
                posts = search_source.top(limit=limit)
            elif sort == 'rising':
                posts = search_source.rising(limit=limit)
            elif sort == 'search' and query:
                posts = search_source.search(query, limit=limit)
            else:
                posts = search_source.hot(limit=limit)
            
            post_data = []
            for post in posts:
                try:
                    created_time = datetime.fromtimestamp(post.created_utc)
                    
                    upvote_ratio = post.upvote_ratio if hasattr(post, 'upvote_ratio') else 0
                    
                    data = {
                        'id': post.id,
                        'title': post.title,
                        'text': post.selftext[:500] + ('...' if len(post.selftext) > 500 else ''),
                        'score': post.score,
                        'upvote_ratio': upvote_ratio,
                        'created_at': created_time,
                        'author': str(post.author),
                        'num_comments': post.num_comments,
                        'subreddit': post.subreddit.display_name,
                        'url': post.url,
                        'is_self': post.is_self,
                        'is_video': post.is_video if hasattr(post, 'is_video') else False
                    }
                    
                    post_data.append(data)
                except Exception as e:
                    print(f"Error processing post {post.id}: {e}")
                    continue
            
            df = pd.DataFrame(post_data)
            return df
        
        except Exception as e:
            print(f"Error searching Reddit: {e}")
            return pd.DataFrame()
    
    def get_subreddit_info(self, subreddit_name):
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            subreddit_data = {
                'display_name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.public_description,
                'subscribers': subreddit.subscribers,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc),
                'url': subreddit.url,
                'over18': subreddit.over18,
                'public': subreddit.subreddit_type == 'public'
            }
            
            return subreddit_data
        
        except Exception as e:
            print(f"Error getting subreddit info: {e}")
            return {}
    
    def get_trending_subreddits(self):
        try:
            trending = self.reddit.random_subreddit()
            return [trending.display_name]
        except Exception as e:
            print(f"Error getting trending subreddits: {e}")
            return []
    
if __name__ == "__main__":
    REDDIT_CLIENT_ID = "your-client-id"
    REDDIT_CLIENT_SECRET = "your-client-secret"
    REDDIT_USER_AGENT = "python:data-dashboard:v1.0 (by /u/your_username)"
    
    client = RedditClient(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)
    
    posts = client.search_posts(subreddit="python", limit=10, sort="hot")
    print(posts.head()) 