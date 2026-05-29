import sqlite3
import requests
from bs4 import BeautifulSoup

def job_crawl():
    print("[+] Job Crawler starting...")
    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        
        conn = sqlite3.connect("database/search.db")
        cur = conn.cursor()
        # টেবিল নাম mega_search করা হয়েছে
        cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
        
        for item in soup.find_all("div", class_="thumbnail")[:5]:
            title = item.find("a", class_="title").text.strip() + " Developer Required"
            desc = "We are looking for an expert. Requirements: Python, Flask, Scrapy, SQLite."
            link = "https://webscraper.io" + item.find("a", class_="title")["href"] + "/apply"
            
            cur.execute("INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url) VALUES (?, ?, ?, ?, ?, ?)",
                        ("job", "webscraper.io", title, desc, "https://via.placeholder.com/150", link))
            
        conn.commit()
        conn.close()
        print("[✓] Job Crawler finished successfully.")
    except Exception as e:
        print(f"[-] Job Crawler failed: {e}")

if __name__ == "__main__":
    job_crawl()
