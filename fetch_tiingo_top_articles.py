#!/usr/bin/env python3
"""
Script to fetch top financial news articles from Tiingo's news API.
Focuses on collecting popular financial news articles based on relevance.
"""
import os
import urllib.request
import urllib.error
import urllib.parse
import json
from datetime import datetime, timedelta

def get_api_key():
    """Load TIINGO_API_KEY from environment or .env file."""
    api_key = os.getenv("TIINGO_API_KEY")
    if not api_key:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.strip().split("=", 1)
                    if k == "TIINGO_API_KEY":
                        api_key = v
                        break
    if not api_key:
        raise RuntimeError("TIINGO_API_KEY not found in environment or .env")
    
    # Remove any quotes around the key
    api_key = api_key.strip('"\'')
    return api_key

def fetch_tiingo_top_articles(days_back=7, limit=100):
    """
    Fetch top financial news articles from the Tiingo news API.
    
    Args:
        days_back (int): How many days to look back from today. Default is 7 days.
        limit (int): Maximum number of articles to fetch. Default is 100.
    
    Returns:
        list: List of top financial news articles.
    """
    api_key = get_api_key()
    
    # Set up date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Build query parameters
    # Sort by relevance which should give us the most important articles
    params = {
        "token": api_key,
        "startDate": start_date,
        "endDate": end_date,
        "limit": limit,
        "sortBy": "relevance",  # Sort by relevance to get top articles
        "sortOrder": "desc"
    }
    
    url = "https://api.tiingo.com/tiingo/news"
    
    print(f"Fetching top financial news articles from {start_date} to {end_date}")
    
    headers = {"Authorization": f"Token {api_key}"}
    query_string = urllib.parse.urlencode(params)
    request_url = f"{url}?{query_string}"
    
    try:
        req = urllib.request.Request(request_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            status = resp.getcode()
            if status != 200:
                raise RuntimeError(f"Tiingo API returned status {status}")
            articles = json.load(resp)
            print(f"Found {len(articles)} top financial news articles")
            return articles
    except urllib.error.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
        if hasattr(http_err, 'read'):
            print(f"Error content: {http_err.read().decode('utf-8')}")
        raise RuntimeError(f"HTTP error fetching Tiingo Top articles: {http_err.code} {http_err.reason}")
    except urllib.error.URLError as url_err:
        raise RuntimeError(f"URL error fetching Tiingo Top articles: {url_err.reason}")
    except Exception as err:
        raise RuntimeError(f"Unexpected error fetching Tiingo Top articles: {err}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch top financial news articles from Tiingo news API")
    parser.add_argument('-d', '--days', type=int, default=7,
                        help='Number of days to look back (default: 7)')
    parser.add_argument('-l', '--limit', type=int, default=100,
                        help='Maximum number of articles to fetch (default: 100)')
    parser.add_argument('-o', '--output', type=str, default="/Users/David/git/agents-prediction/data/tiingo_top_articles.json",
                        help='Output JSON file to save the results (default: ./data/tiingo_top_articles.json)')
    args = parser.parse_args()
    
    try:
        # Fetch top financial news articles
        articles = fetch_tiingo_top_articles(days_back=args.days, limit=args.limit)
        
        if not articles:
            print("No top financial news articles found.")
            return
            
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # Save results to JSON
        try:
            with open(args.output, 'w') as f:
                json.dump(articles, f, indent=2)
            print(f"Saved {len(articles)} articles to {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}")
        
        # Print results
        print(f"\nTop financial news articles:")
        for idx, article in enumerate(articles[:10], start=1):  # Show top 10
            print(f"\nArticle {idx}:")
            print(f"  Title: {article.get('title')}")
            print(f"  Source: {article.get('source')}")
            print(f"  Published: {article.get('publishedDate')}")
            print(f"  URL: {article.get('url')}")
            description = article.get('description', '')
            if description:
                # Truncate long descriptions
                if len(description) > 150:
                    description = description[:147] + "..."
                print(f"  Description: {description}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()