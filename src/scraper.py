import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

def get_driver():
    """Initializes and returns a Chrome driver."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Keep commented out for debugging
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_profile_feed_generator(profile_id, max_articles=10):
    """
    Yields batches of articles from the profile.
    Stops when max_articles is reached or no more buttons exist.
    """
    url = f"https://yle.fi/p/{profile_id}/fi"
    driver = get_driver()
    
    # We use a set to keep track of IDs we have already yielded
    # to avoid duplicates when we re-parse the page after clicking.
    processed_ids = set()
    total_yielded = 0
    
    try:
        print(f"Opening profile: {url}")
        driver.get(url)

        # handle Cookies (One time setup)
        try:
            cookie_btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Hyväksy') or contains(text(), 'Vain välttämättömät')]"))
            )
            cookie_btn.click()
            time.sleep(1) 
        except:
            pass

        # Main Scraping Loop
        while total_yielded < max_articles:
            # A. Parse the current state of the page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = soup.find_all('a', attrs={"data-card-heading-content-id": True})
            
            new_articles = []
            for link in links:
                a_id = link['data-card-heading-content-id']
                
                # If we haven't seen this article yet, let's process it
                if a_id not in processed_ids:
                    # Parse article details
                    a_name = link.get_text().strip()
                    a_url = f"https://yle.fi/a/{a_id}"
                    
                    # Store to avoid re-yielding later
                    processed_ids.add(a_id)
                    
                    # Add to our batch
                    new_articles.append({
                        "name": a_name,
                        "id": a_id,
                        "url": a_url
                    })
                    
                    # Increment counter
                    total_yielded += 1
                    
                    # Check if we hit the limit
                    if total_yielded >= max_articles:
                        break
            
            # yield the batch to the main program immediately
            if new_articles:
                print(f"Scraper: Found {len(new_articles)} new articles.")
                yield new_articles
            
            # check if we need to click "Show More"
            if total_yielded < max_articles:
                print("Scraper: Need more articles. Looking for button...")
                try:
                    load_more = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Näytä lisää"]'))
                    )
                    
                    if load_more.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", load_more)
                        time.sleep(0.5) # Give it a moment to load
                    else:
                        print("Scraper: Button found but not visible. End of list.")
                        break
                except Exception:
                    print("Scraper: No more buttons found. End of list.")
                    break
            else:
                print("Scraper: Reached max article limit.")
                break

    finally:
        driver.quit()

def fetch_yle_article_details(url):
    """
    Fetches article body text and meta data (description, keywords).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # meta data
        description = ""
        keywords = ""
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]
            
        meta_keys = soup.find("meta", attrs={"name": "keywords"})
        if meta_keys and meta_keys.get("content"):
            keywords = meta_keys["content"]

        # body text
        content_text = ""
        content_div = soup.find('section', class_='yle__article__content')
        if not content_div:
            content_div = soup.find('div', class_='yle__article__content')
        if not content_div:
            content_div = soup.find('main')

        if content_div:
            text_blocks = []
            for element in content_div.find_all(['p', 'h2', 'h3']):
                txt = element.get_text().strip()
                if txt:
                    text_blocks.append(txt)
            content_text = "\n\n".join(text_blocks)
        
        if content_text:
            return {
                "content": content_text,
                "description": description,
                "keywords": keywords
            }
        else:
            return None

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None