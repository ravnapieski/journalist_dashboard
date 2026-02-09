import time
from src.database import init_db, upgrade_db_schema, save_articles, get_articles_missing_metadata, update_article_full_data
from src.scraper import scrape_profile_feed_generator, fetch_yle_article_details # note: new function name

def main():
    TARGET_PROFILE_ID = "56-74-1051" 
    MAX_ARTICLES_TO_FETCH = 41 
    
    # initialization and migration
    init_db()
    upgrade_db_schema()
    
    print(f"--- Phase 1: Fetching links ({MAX_ARTICLES_TO_FETCH} items) ---")
    for article_batch in scrape_profile_feed_generator(TARGET_PROFILE_ID, max_articles=MAX_ARTICLES_TO_FETCH):
        save_articles(TARGET_PROFILE_ID, article_batch)
    
    print("\n--- Phase 2: Fetching content and metadata ---")
    
    # now fetching articles missing metadata or content
    pending_articles = get_articles_missing_metadata()
    
    print(f"Found {len(pending_articles)} articles to update.")
    
    for i, article in enumerate(pending_articles):
        url = article['url']
        print(f"[{i+1}/{len(pending_articles)}] Processing: {url}")
        
        data = fetch_yle_article_details(url)
        
        if data:
            update_article_full_data(
                article['id'], 
                data['content'], 
                data['description'], 
                data['keywords']
            )
            print(f"   -> OK. Metadata + {len(data['content'])} characters of text.")
        else:
            print("   -> Failed.")
        
        time.sleep(1.0)

    print("\nDone.")

if __name__ == "__main__":
    main()