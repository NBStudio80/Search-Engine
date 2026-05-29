import sqlite3
import requests
from bs4 import BeautifulSoup

def news_crawl():
    print("[+] News Crawler starting...")
    url = "https://quotes.toscrape.com/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        
        conn = sqlite3.connect("database/search.db")
        cur = conn.cursor()
        
        cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
        
        for quotes in soup.find_all("div", class_="quote"):
            text = quotes.find("span", class_="text").text
            author = quotes.find("small", class_="author").text
            title = f"Quote by {author}"
            link = f"https://quotes.toscrape.com/author/{author.replace(' ', '-')}"
            
            cur.execute("INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url) VALUES (?, ?, ?, ?, ?, ?)",
                        ("news", "quotes.toscrape.com", title, text, "https://via.placeholder.com/150", link))
            
        conn.commit()
        conn.close()
        print("[✓] News Crawler finished successfully.")
    except Exception as e:
        print(f"[-] News Crawler failed: {e}")

if __name__ == "__main__":
    news_crawl()
