#!/usr/bin/env python
"""
Script to fetch morning market summaries from financial news sources.
Focuses on articles published before market open (9:30 AM EST) that discuss
the broader market outlook, futures, or pre-market activity.
"""
import os
import urllib.request
import urllib.error
import urllib.parse
import json
from datetime import datetime, timedelta, time
import pytz

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

def fetch_morning_market_summaries(date=None, days_back=14):
    """
    Fetch morning market summaries from financial news sources.
    
    Args:
        date (str): The specific date to fetch in YYYY-MM-DD format. Defaults to today.
        days_back (int): How many days to look back if no specific date provided
    """
    api_key = get_api_key()
    
    # Set up date range
    if date:
        start_date = date
        end_date = date
    else:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Sources for market news
    sources = [
        "cnbc.com",           # Before the Bell
        "finance.yahoo.com",  # Morning Brief
        "marketwatch.com",    # Need to Know
        "reuters.com",        # Morning Bid
        "bloomberg.com",      
        "wsj.com",            # Markets Morning Briefing
        "barrons.com",        
        "investing.com",      # Pre-Market report
        "thestreet.com"       # Morning Bell
    ]
    
    # Market-related tickers that might give us broad market summaries
    market_tickers = ["SPY", "QQQ", "DIA", "IWM", "VIX"]
    
    # Run searches for each ticker with a high limit
    all_articles = []
    
    for ticker in market_tickers:
        # Build query parameters
        params = {
            "token": api_key,
            "startDate": start_date,
            "endDate": end_date,
            "source": ",".join(sources),
            "tickers": ticker,
            "limit": 500,  # Get many results to filter by time
            "sortBy": "publishedDate"  # Sort by published date
        }
        
        url = "https://api.tiingo.com/tiingo/news"
        
        print(f"Fetching {ticker} market news from {start_date} to {end_date}")
        
        headers = {"Authorization": f"Token {api_key}"}
        query_string = urllib.parse.urlencode(params)
        request_url = f"{url}?{query_string}"
        
        try:
            req = urllib.request.Request(request_url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                status = resp.getcode()
                if status != 200:
                    raise RuntimeError(f"Tiingo API returned status {status}")
                data = json.load(resp)
                all_articles.extend(data)
        except urllib.error.HTTPError as http_err:
            print(f"HTTP error for {ticker}: {http_err}")
            continue
        except Exception as err:
            print(f"Error fetching {ticker} news: {err}")
            continue
    
    # Remove duplicates by ID
    unique_articles = {article['id']: article for article in all_articles}
    print(f"Found {len(unique_articles)} unique articles across all market tickers")
    
    # Filter articles published before 9:30 AM EST (market open)
    eastern = pytz.timezone('US/Eastern')
    market_open_time = time(9, 30, 0)  # 9:30 AM
    
    morning_articles = []
    
    for article in unique_articles.values():
        # Parse the published date
        published_str = article.get("publishedDate", "")
        if not published_str:
            continue
        
        try:
            # Parse ISO format datetime with timezone
            if published_str.endswith('Z'):
                # If UTC time (Z), convert to datetime and localize to Eastern
                published_dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                published_eastern = published_dt.astimezone(eastern)
            else:
                # If already has timezone info
                published_dt = datetime.fromisoformat(published_str)
                published_eastern = published_dt.astimezone(eastern)
            
            # Check if it's before market open
            article_time = published_eastern.time()
            if article_time < market_open_time:
                # Add market-related fields to help analyze the article
                article['_market_relevance'] = {
                    'published_time_eastern': published_eastern.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'is_pre_market': True
                }
                morning_articles.append(article)
        except (ValueError, TypeError) as e:
            print(f"Error parsing date {published_str}: {e}")
            continue
    
    print(f"Found {len(morning_articles)} articles published before 9:30 AM EST")
    
    # Further filter for articles that are likely market summaries
    # These usually contain specific keywords in the title or description
    market_summary_keywords = [
        "morning brief", "before the bell", "pre-market", "premarket",
        "futures", "market preview", "stocks to watch", "morning update",
        "morning briefing", "need to know", "trading day ahead", "morning bid",
        "market outlook", "today's market", "what to watch", "morning markets",
        "opening bell", "stock futures", "dow futures", "nasdaq futures",
        "s&p futures", "markets today", "5 things to know", "top stories"
    ]
    
    summary_articles = []
    
    for article in morning_articles:
        title = article.get("title", "") or ""
        description = article.get("description", "") or ""
        
        # Convert to lowercase for comparison
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Check if any keyword is in the title or description
        if any(keyword in title_lower or keyword in description_lower for keyword in market_summary_keywords):
            article['_market_relevance']['is_likely_summary'] = True
            summary_articles.append(article)
    
    print(f"Found {len(summary_articles)} likely market summary articles")
    
    # Sort by relevance score and then by date (newest first)
    # This prioritizes articles that are explicitly morning market summaries
    summary_articles.sort(key=lambda x: (
        1 if "before the bell" in (x.get("title", "") or "").lower() else 0,
        1 if "morning brief" in (x.get("title", "") or "").lower() else 0,
        1 if "market preview" in (x.get("title", "") or "").lower() else 0,
        1 if "futures" in (x.get("title", "") or "").lower() else 0,
        datetime.fromisoformat(x.get("publishedDate", "").replace('Z', '+00:00'))
    ), reverse=True)
    
    return summary_articles if summary_articles else morning_articles

def main():
    try:
        # If a date argument is provided, use that specific date
        import sys
        date = None
        if len(sys.argv) > 1:
            date = sys.argv[1]
        
        # Fetch morning market summaries
        articles = fetch_morning_market_summaries(date=date)
        
        if not articles:
            print("No morning market summaries found.")
            return
            
        # Save results to JSON
        output_file = "/Users/David/git/agents-prediction/data/morning_market_summaries.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(articles, f, indent=2)
            print(f"Saved {len(articles)} articles to {output_file}")
        except Exception as e:
            print(f"Error saving to file: {e}")
        
        # Print results
        print(f"Morning market summary articles:")
        for idx, article in enumerate(articles[:10], start=1):  # Show top 10
            print(f"\nArticle {idx}:")
            print(f"  Title: {article.get('title')}")
            print(f"  Source: {article.get('source')}")
            print(f"  Published (ET): {article.get('_market_relevance', {}).get('published_time_eastern')}")
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