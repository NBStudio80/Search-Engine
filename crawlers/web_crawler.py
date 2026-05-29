import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

visited_urls = set()

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def google_style_crawl(start_url, max_pages=10):
    urls_to_crawl = [start_url]
    pages_crawled = 0
    
    conn = sqlite3.connect("database/search.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
    
    print(f"[+] Google-style Crawler Started for: {start_url}")
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
            content = " ".join(paragraphs[:3])
            
            cur.execute("INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url) VALUES (?, ?, ?, ?, ?, ?)",
                        ("web", urlparse(url).netloc, title, content, "https://via.placeholder.com/150", url))
            conn.commit()
            
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"])
                if is_valid_url(full_url) and full_url not in visited_urls:
                    urls_to_crawl.append(full_url)
            time.sleep(1)
        except:
            continue
    conn.close()
    print(f"[✓] Successfully crawled {pages_crawled} pages.")

if __name__ == "__main__":
    google_style_crawl("https://en.wikipedia.org/wiki/Python_(programming_language)", max_pages=15)
