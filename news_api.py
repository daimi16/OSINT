import requests
from newsapi import NewsApiClient
import pandas as pd
import json
import os

class NewsAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.newsapi = NewsApiClient(api_key=api_key)
    
    def get_top_headlines(self, country='us', category=None, query=None, page_size=10):
        try:
            params = {'country': country, 'page_size': page_size}
            if category:
                params['category'] = category
            if query:
                params['q'] = query
                
            response = self.newsapi.get_top_headlines(**params)
            
            articles = response['articles']
            
            if not articles:
                return pd.DataFrame()
            
            df = pd.DataFrame(articles)
            
            if 'source' in df.columns:
                df['source_id'] = df['source'].apply(lambda x: x.get('id'))
                df['source_name'] = df['source'].apply(lambda x: x.get('name'))
                df.drop('source', axis=1, inplace=True)
                
            return df
        
        except Exception as e:
            print(f"Error fetching news: {e}")
            return pd.DataFrame()
    
    def get_everything(self, query, language='en', sort_by='publishedAt', page_size=10, from_date=None, to_date=None):
        try:
            params = {
                'q': query,
                'language': language,
                'sort_by': sort_by,
                'page_size': page_size
            }
            
            if from_date:
                params['from_param'] = from_date
            if to_date:
                params['to'] = to_date
            
            response = self.newsapi.get_everything(**params)
            
            articles = response['articles']
            
            if not articles:
                return pd.DataFrame()
            
            df = pd.DataFrame(articles)
            
            if 'source' in df.columns:
                df['source_id'] = df['source'].apply(lambda x: x.get('id'))
                df['source_name'] = df['source'].apply(lambda x: x.get('name'))
                df.drop('source', axis=1, inplace=True)
                
            return df
        
        except Exception as e:
            print(f"Error searching news: {e}")
            return pd.DataFrame()
    
    def get_everything_in_title(self, query, language='en', sort_by='publishedAt', page_size=100, from_date=None, to_date=None):
        try:
            params = {
                'q': query,
                'language': language,
                'sort_by': sort_by,
                'page_size': page_size
            }
            
            if from_date:
                params['from_param'] = from_date
            if to_date:
                params['to'] = to_date
            
            response = self.newsapi.get_everything(**params)
            
            articles = response['articles']
            
            if not articles:
                return pd.DataFrame()
            
            df = pd.DataFrame(articles)
            
            if 'title' in df.columns:
                query_terms = query.lower().split()
                filtered_df = df[df['title'].str.lower().apply(
                    lambda title: any(term in title.lower() for term in query_terms)
                )]
                
                if filtered_df.empty:
                    return pd.DataFrame()
                
                df = filtered_df
            
            if 'source' in df.columns:
                df['source_id'] = df['source'].apply(lambda x: x.get('id'))
                df['source_name'] = df['source'].apply(lambda x: x.get('name'))
                df.drop('source', axis=1, inplace=True)
                
            return df
        
        except Exception as e:
            print(f"Error searching news in titles: {e}")
            return pd.DataFrame()
    
    def get_sources(self, category=None, language='en', country=None):
        try:
            params = {'language': language}
            if category:
                params['category'] = category
            if country:
                params['country'] = country
                
            response = self.newsapi.get_sources(**params)
            
            sources = response['sources']
            
            if not sources:
                return pd.DataFrame()
            
            df = pd.DataFrame(sources)
            return df
        
        except Exception as e:
            print(f"Error fetching sources: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    API_KEY = "your-api-key-here"
    
    client = NewsAPIClient(API_KEY)
    
    headlines = client.get_top_headlines(category='technology')
    print(headlines.head()) 