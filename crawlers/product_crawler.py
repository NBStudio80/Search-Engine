import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

DB_PATH = "database/search.db"
visited_urls = set()

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def global_mega_crawl(start_urls, max_pages=100):
    urls_to_crawl = start_urls
    pages_crawled = 0
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    conn.text_factory = str 
    
    cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
    
    headers = {'User-Agent': 'Mozilla/5.0'}

    while urls_to_crawl and pages_crawled < max_pages:
        url = urls_to_crawl.pop(0)
        if url in visited_urls: continue
        visited_urls.add(url)
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code != 200: continue
            soup = BeautifulSoup(res.text, "html.parser")
            pages_crawled += 1
            
            title = soup.title.string.strip() if soup.title else "No Title"
            paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
            content = " ".join(paragraphs[:4])
            
            domain = urlparse(url).netloc
            category = "news" if "news" in domain else "product"
            source = domain.replace("www.", "")
            img_tag = soup.find("img")
            img_url = urljoin(url, img_tag["src"]) if (img_tag and img_tag.get("src")) else "https://via.placeholder.com/150"

            cur.execute("INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url) VALUES (?, ?, ?, ?, ?, ?)", 
                        (category, source, title, content, img_url, url))
            conn.commit()
            
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"])
                if is_valid_url(full_url) and full_url not in visited_urls:
                    urls_to_crawl.append(full_url)
            time.sleep(0.5)
        except:
            continue
    conn.close()
    print(f"[✓] Mega Crawl Finished!")

if __name__ == "__main__":
    seed_sites = ["https://bn.wikipedia.org/wiki/প্রধান_পাতা", "https://webscraper.io/test-sites/e-commerce/allinone"]
    global_mega_crawl(seed_sites, max_pages=100)
