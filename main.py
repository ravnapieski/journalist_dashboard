import time
import re
from src.database import init_db, upgrade_db_schema, save_articles, get_articles_missing_metadata, update_article_full_data, create_journalist
from src.scraper import scrape_profile_feed_generator, fetch_yle_article_details, scrape_journalist_name

def run_scraper_pipeline(target_profile_id, max_articles=10):
    """
    Runs the full scraping pipeline for a specific journalist ID.
    Returns the name of the journalist scraped.
    """
    
    # Database Setup
    init_db()
    upgrade_db_schema()
    
    # Identify Journalist
    print(f"Resolving journalist name for ID: {target_profile_id}...")
    journalist_name = scrape_journalist_name(target_profile_id)
    print(f" -> Found: {journalist_name}")
    
    create_journalist(target_profile_id, journalist_name)
    
    # Fetch Links
    print(f"--- Fetching max {max_articles} links ---")
    for article_batch in scrape_profile_feed_generator(target_profile_id, max_articles=max_articles):
        save_articles(target_profile_id, article_batch)
    
    # Fetch Content & Metadata
    print("\n--- Updating Article Details ---")
    
    # Only get articles that are missing data 
    pending_articles = get_articles_missing_metadata()
    
    # Filter pending articles to only match the current journalist 
    pending_for_this_journalist = [a for a in pending_articles if target_profile_id in a['url']]
    
    count_updated = 0
    for i, article in enumerate(pending_articles):
        url = article['url']
        print(f"[{i+1}/{len(pending_articles)}] Processing: {url}")
        
        data = fetch_yle_article_details(url)
        
        if data:
            update_article_full_data(
                article['id'], 
                data['content'], 
                data['description'], 
                data['keywords'],
                data['published_date']
            )
            count_updated += 1
        
        time.sleep(0.5) 

    return journalist_name, count_updated

if __name__ == "__main__":
    run_scraper_pipeline("56-74-1533", max_articles=10)