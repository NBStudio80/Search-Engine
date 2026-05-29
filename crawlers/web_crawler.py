import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# আমরা যে লিংকগুলো অলরেডি ভিজিট করেছি তা মনে রাখার জন্য
visited_urls = set()

def is_valid_url(url):
    """লিংকটি সঠিক এবং ক্রল করার যোগ্য কিনা পরীক্ষা করা"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def google_style_crawl(start_url, max_pages=10):
    """Google-এর মতো লিংক ফলো করে করে ক্রল করার ফাংশন"""
    urls_to_crawl = [start_url]
    pages_crawled = 0
    
    # ডাটাবেজ কানেকশন
    conn = sqlite3.connect("database/search.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, content TEXT, url TEXT UNIQUE)")
    
    print(f"[+] Google-style Crawler Started for: {start_url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    while urls_to_crawl and pages_crawled < max_pages:
        url = urls_to_crawl.pop(0)
        
        if url in visited_urls:
            continue
            
        print(f"[{pages_crawled + 1}] Crawling: {url}")
        visited_urls.add(url)
        
        try:
            # পেজ ডাউনলোড করা
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            pages_crawled += 1
            
            # ১. ডেটা এক্সট্রাক্ট করা (Title, Text content)
            title = soup.title.string.strip() if soup.title else "No Title"
            
            # পেজের মেইন টেক্সট বডি থেকে প্যারাগ্রাফ নেওয়া
            paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
            content = " ".join(paragraphs[:3]) # প্রথম ৩টি প্যারাগ্রাফ টেক্সট হিসেবে জমা রাখা
            
            if not content:
                content = f"Web page content from {urlparse(url).netloc}"

            # ২. ডাটাবেজে সেভ করা
            cur.execute("INSERT OR IGNORE INTO data (type, title, content, url) VALUES (?, ?, ?, ?)",
                        ("web", title, content, url))
            conn.commit()
            
            # ৩. Google-এর মতো নতুন লিংক খুঁজে বের করা (Link Extraction)
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                # রিলেটিভ লিংকগুলোকে (যেমন: /about) ফুল লিংকে রূপান্তর করা
                full_url = urljoin(url, href)
                
                if is_valid_url(full_url) and full_url not in visited_urls:
                    urls_to_crawl.append(full_url)
                    
            # সার্ভারে যেন লোড না পড়ে তাই একটু বিরতি (Google-এর নিয়ম)
            time.sleep(1)
            
        except Exception as e:
            print(f"[-] Failed to crawl {url}: {e}")
            continue
            
    conn.close()
    print(f"[✓] Successfully crawled {pages_crawled} pages and saved to database.")

if __name__ == "__main__":
    # আপনি যেকোনো সচল লাইভ ওয়েবসাইট এখানে দিতে পারেন টেস্ট করার জন্য
    # উদাহরণ হিসেবে একটি উইকিপিডিয়া পেজ দেওয়া হলো যা ক্রল করা সহজ
    target_site = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    google_style_crawl(target_site, max_pages=15)

