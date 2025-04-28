#!/usr/bin/env python3
"""
Simple script to fetch recent news articles from Tiingo using API key in .env.
"""
import os
import urllib.request
import urllib.error
import urllib.parse
import json

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

def fetch_news_articles(count=1, tickers=None, tags=None):
    """Fetch the most recent news articles.
    Args:
        count (int): number of articles to return (slice after fetch).
        tickers (str): comma-separated list of ticker symbols to filter (optional).
        tags (str): comma-separated list of tags to filter (optional).
    """
    api_key = get_api_key()
    base_url = "https://api.tiingo.com/tiingo/news"
    # Build query parameters
    params = {}
    if tickers:
        params['tickers'] = tickers
    if tags:
        params['tags'] = tags
    url = base_url
    if params:
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
    headers = {"Authorization": f"Token {api_key}"}
    # Send HTTP request
    print(f"Requesting URL: {url}")
    print(f"Headers: {headers}")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.getcode()
            print(f"Response status: {status}")
            if status != 200:
                raise RuntimeError(f"Tiingo API returned status {status}")
            data = json.load(resp)
    except urllib.error.HTTPError as http_err:
        print(f"Full HTTP error: {http_err}")
        if hasattr(http_err, 'read'):
            print(f"Error content: {http_err.read().decode('utf-8')}")
        raise RuntimeError(f"HTTP error fetching news: {http_err.code} {http_err.reason}")
    except urllib.error.URLError as url_err:
        raise RuntimeError(f"URL error fetching news: {url_err.reason}")
    except Exception as err:
        raise RuntimeError(f"Unexpected error fetching news: {err}")
    return data[:count]

def main():
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Fetch recent news articles from Tiingo.")
    parser.add_argument('-n', '--count', type=int, default=1,
                        help='Number of articles to fetch (default: 1)')
    parser.add_argument('-t', '--tickers', type=str,
                        help='Comma-separated tickers to filter (e.g., aapl,googl)')
    parser.add_argument('-g', '--tags', type=str,
                        help='Comma-separated tags/topics to filter (e.g., election,argentina)')
    parser.add_argument('-o', '--output', type=str,
                        help='Output JSON file to save the results')
    args = parser.parse_args()
    try:
        articles = fetch_news_articles(count=args.count,
                                       tickers=args.tickers,
                                       tags=args.tags)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return
    
    if not articles:
        print("No recent news articles found.")
        return
    
    # Save to JSON file if output is specified
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(articles, f, indent=2)
            print(f"Saved {len(articles)} articles to {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    # Print to console
    for idx, article in enumerate(articles, start=1):
        print(f"Article {idx}:")
        print(f"  Title: {article.get('title')}")
        print(f"  Published Date: {article.get('publishedDate')}")
        print(f"  Url: {article.get('url')}")
        print(f"  Description: {article.get('description')}")
        print()

if __name__ == "__main__":
    main()