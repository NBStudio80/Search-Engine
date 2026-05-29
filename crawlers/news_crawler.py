import sqlite3
import requests
from bs4 import BeautifulSoup

def news_crawl():
    print("[+] News Crawler starting...")
    url = "https://quotes.toscrape.com/" # স্ক্র্যাপিং ফ্রেন্ডলি সাইট
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        
        conn = sqlite3.connect("database/search.db")
        cur = conn.cursor()
        
        # টেবিল না থাকলে তৈরি করবে
        cur.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, content TEXT, url TEXT UNIQUE)")
        
        for quotes in soup.find_all("div", class_="quote"):
            text = quotes.find("span", class_="text").text
            author = quotes.find("small", class_="author").text
            title = f"Quote by {author}"
            link = f"https://quotes.toscrape.com/author/{author.replace(' ', '-')}"
            
            cur.execute("INSERT OR IGNORE INTO data (type, title, content, url) VALUES (?, ?, ?, ?)",
                        ("news", title, text, link))
            
        conn.commit()
        conn.close()
        print("[✓] News Crawler finished successfully.")
    except Exception as e:
        print(f"[-] News Crawler failed: {e}")

if __name__ == "__main__":
    news_crawl()


