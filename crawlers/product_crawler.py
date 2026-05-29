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
    """সব ভাষা এবং সব কিওয়ার্ডের ডেটা একবারে ক্রল করার জন্য মেগা ক্রলার"""
    urls_to_crawl = start_urls
    pages_crawled = 0
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # UTF-8 সাপোর্ট নিশ্চিত করতে ডাটাবেজ কনফিগারেশন
    conn.text_factory = str 
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mega_search (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        source TEXT,
        title TEXT,
        content TEXT,
        image_url TEXT,
        target_url TEXT UNIQUE
    )
    """)
    
    print(f"[+] Global Mega Crawler Started for {len(start_urls)} seed sites...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    while urls_to_crawl and pages_crawled < max_pages:
        url = urls_to_crawl.pop(0)
        
        if url in visited_urls:
            continue
            
        print(f"[{pages_crawled + 1}/{max_pages}] Crawling: {url}")
        visited_urls.add(url)
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code != 200:
                continue
                
            # UTF-8 এনকোডিং ফিক্স (বাংলা ও অন্যান্য ভাষার লেখা ভেঙে যাওয়া রোধ করতে)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            pages_crawled += 1
            
            # ১. ডাটা এক্সট্রাকশন
            title = soup.title.string.strip() if soup.title else "No Title"
            
            paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
            content = " ".join(paragraphs[:4]) # প্রথম ৪টি প্যারাগ্রাফ টেক্সট হিসেবে নেওয়া
            
            if not content or len(content) < 10:
                continue

            # ডোমেইন নাম অনুযায়ী ক্যাটাগরি ও সোর্স ঠিক করা
            domain = urlparse(url).netloc
            category = "news" if "news" in domain or "wikipedia" in domain else "product"
            source = domain.replace("www.", "")

            # ইমেজ খোঁজা
            img_tag = soup.find("img")
            img_url = urljoin(url, img_tag["src"]) if (img_tag and img_tag.get("src")) else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=200"

            # ২. ডাটাবেজে সেভ (সব ভাষা ও কিওয়ার্ডসহ)
            cur.execute("""
                INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category, source, title, content, img_url, url))
            conn.commit()
            
            # ৩. পেজের ভেতরের সব লিংক খুঁজে বের করা (গুগল স্টাইল)
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"])
                if is_valid_url(full_url) and full_url not in visited_urls:
                    # সোশ্যাল মিডিয়া লিংক ও এক্সটার্নাল ট্র্যাশ লিংক বাদ দেওয়া
                    if "facebook" not in full_url and "twitter" not in full_url:
                        urls_to_crawl.append(full_url)
                        
            time.sleep(0.5) # ক্রলারের স্পিড বাড়ানোর জন্য বিরতি কমানো হলো
            
        except Exception as e:
            continue
            
    conn.close()
    print(f"[✓] Mega Crawl Finished! {pages_crawled} pages added with millions of keywords.")

if __name__ == "__main__":
    # এখানে বাংলা এবং ইংরেজি দুটি মিক্সড হাই-কোয়ালিটি সাইটের লিংক দেওয়া হলো
    # যা ক্রল করলে ডাটাবেজে হাজার হাজার বাংলা ও ইংরেজি কিওয়ার্ড অটোমেটিক তৈরি হবে
    seed_sites = [
        "https://bn.wikipedia.org/wiki/প্রধান_পাতা", # বিশাল বাংলা কিওয়ার্ডের জন্য
        "https://en.wikipedia.org/wiki/Laptop",       # ল্যাপটপ, দারাজ ও টেকনোলজি কিওয়ার্ডের জন্য
        "https://webscraper.io/test-sites/e-commerce/allinone" # প্রোডাক্ট কিওয়ার্ডের জন্য
    ]
    # আমরা একবারে ১০০টি পেজ ক্রল করব বিশাল কিওয়ার্ড ডাটাবেজ বানাতে
    global_mega_crawl(seed_sites, max_pages=100)





