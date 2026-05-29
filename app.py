from flask import Flask, request, render_template_string
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading
import os
import re

app = Flask(__name__)

# ডাটাবেজ পাথ সেটআপ (Render বা যেকোনো ক্লাউড সার্ভারের জন্য)
DB_PATH = os.path.join(os.getcwd(), "search.db")

# ==========================================
# ১. গ্লোবাল মেগা ক্রলার (অটো-ইনডেক্সিং)
# ==========================================
def global_background_crawl(query):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    # আপনার দেওয়া তালিকা অনুযায়ী আপডেট করা সোর্স লিস্ট
    sources = [
        # --- নিউজ ও মিডিয়া ---
        {"name": "BBC News", "cat": "news", "url": f"https://www.bbc.com/search?q={query}"},
        {"name": "CNN", "cat": "news", "url": f"https://edition.cnn.com/search?q={query}"},
        {"name": "Reuters", "cat": "news", "url": f"https://www.reuters.com/site-search/?query={query}"},
        {"name": "AP News", "cat": "news", "url": f"https://apnews.com/search?q={query}"},
        {"name": "NY Times", "cat": "news", "url": f"https://www.nytimes.com/search?query={query}"},
        {"name": "Prothom Alo", "cat": "news", "url": f"https://www.prothomalo.com/search?q={query}"},
        {"name": "Somoy TV", "cat": "news", "url": f"https://www.somoynews.tv/search?q={query}"},
        {"name": "Jamuna TV", "cat": "news", "url": f"https://www.jamuna.tv/?s={query}"},
        {"name": "NDTV", "cat": "news", "url": f"https://www.ndtv.com/search?q={query}"},
        {"name": "Aaj Tak", "cat": "news", "url": f"https://www.aajtak.in/topic/{query}"},
        {"name": "Times of India", "cat": "news", "url": f"https://timesofindia.indiatimes.com/topic/{query}"},
        {"name": "Al Jazeera", "cat": "news", "url": f"https://www.aljazeera.com/search/{query}"},
        {"name": "Fox News", "cat": "news", "url": f"https://www.foxnews.com/search-results/search?q={query}"},
        {"name": "Daily Mail", "cat": "news", "url": f"https://www.dailymail.co.uk/home/search.html?sel=site&searchFTS={query}"},
        {"name": "The Guardian", "cat": "news", "url": f"https://www.theguardian.com/search?q={query}"},
        {"name": "BuzzFeed", "cat": "news", "url": f"https://www.buzzfeed.com/search?q={query}"},
        {"name": "The Verge", "cat": "news", "url": f"https://www.theverge.com/search?q={query}"},

        # --- ই-কমার্স ---
        {"name": "Amazon", "cat": "product", "url": f"https://www.amazon.com/s?k={query}"},
        {"name": "eBay", "cat": "product", "url": f"https://www.ebay.com/sch/i.html?_nkw={query}"},
        {"name": "AliExpress", "cat": "product", "url": f"https://www.aliexpress.com/w/wholesale-{query}.html"},
        {"name": "Daraz (BD)", "cat": "product", "url": f"https://www.daraz.com.bd/catalog/?q={query}&aff_id=163322452"},
        {"name": "Rokomari", "cat": "product", "url": f"https://www.rokomari.com/search?term={query}"},
        {"name": "Chaldal", "cat": "product", "url": f"https://chaldal.com/search/{query}"},
        {"name": "Flipkart", "cat": "product", "url": f"https://www.flipkart.com/search?q={query}"},
        {"name": "Myntra", "cat": "product", "url": f"https://www.myntra.com/{query}"},
        {"name": "Shopee", "cat": "product", "url": f"https://shopee.sg/search?keyword={query}"},
        {"name": "Lazada", "cat": "product", "url": f"https://www.lazada.sg/catalog/?q={query}"},
        {"name": "Noon", "cat": "product", "url": f"https://www.noon.com/search?q={query}"},
        {"name": "Temu", "cat": "product", "url": f"https://www.temu.com/search_result.html?search_key={query}"},
        {"name": "Shein", "cat": "product", "url": f"https://www.shein.com/pdsearch/{query}/"}
    ]

    # এখন আপনার আগের লজিক (লুপ, ডাটাবেজ ইনসার্ট) এখানে বসিয়ে দিন
    for source in sources:
        # ... (আপনার ইনসার্ট লজিক)

            try:
                res = requests.get(source["url"], headers=headers, timeout=6)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    title = soup.title.string.strip() if soup.title else query
                    paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
                    content = " ".join(paragraphs[:3])
                    
                    # ডাটাবেজে সেভ
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
                    cur.execute("""INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url)
                        VALUES (?, ?, ?, ?, ?, ?)""", (source["cat"], source["name"], title, content, "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400", source["url"]))
                    conn.commit()
                    conn.close()
                    print(f"[⚡ Auto-Indexed] Added from {source['name']}: {query}")
            except: continue
    except Exception as e: print(f"[-] Global-crawl failed: {e}")

# ==========================================
# ২. সার্চ ইঞ্জিন মূল ফাংশন
# ==========================================
def search_mega_engine(query, category=None):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = str
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS mega_search (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)")
    
    search_query = f"%{query}%"
    if category:
        cur.execute("SELECT category, source, title, content, image_url, target_url FROM mega_search WHERE (title LIKE ? OR content LIKE ?) AND category = ?", (search_query, search_query, category))
    else:
        cur.execute("SELECT category, source, title, content, image_url, target_url FROM mega_search WHERE title LIKE ? OR content LIKE ?", (search_query, search_query))
    
    results = cur.fetchall()
    conn.close()

    # ডাটা না পেলে ক্রলার ট্রিগার
    if not results:
        threading.Thread(target=global_background_crawl, args=(query,)).start()
    return results

# ==========================================
# ৩. ইউজার ইন্টারফেস (HTML UI)
# ==========================================
@app.route("/")
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DarazPlus Media Mega Engine</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; text-align: center; padding: 150px 20px; margin: 0; }
            h1 { color: #e84118; font-size: 50px; }
            .search-box { max-width: 600px; margin: 0 auto; }
            input { width: 100%; padding: 18px 28px; border-radius: 35px; border: 2px solid #dfe1e5; outline: none; box-sizing: border-box; }
            button { padding: 15px 40px; background: #e84118; color: white; border: none; border-radius: 35px; margin-top: 20px; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🌐 DarazPlus Global Media</h1>
        <div class="search-box">
            <form action="/search" method="get">
                <input type="text" name="q" placeholder="পণ্য বা তথ্যের নাম লিখুন..." required>
                <button type="submit">Search Globally</button>
            </form>
        </div>
    </body>
    </html>
    '''


@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    results = search_mega_engine(q)

    html_output = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{q} - Mega Search</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; color: #202124; background: #fff; }}
            .header {{ display: flex; align-items: center; border-bottom: 1px solid #dfe1e5; padding-bottom: 20px; margin-bottom: 20px; }}
            .search-bar {{ padding: 12px 25px; width: 400px; border-radius: 25px; border: 1px solid #dfe1e5; outline: none; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }}
            
            /* গুগল স্টাইল রেজাল্ট কার্ড */
            .result-container {{ max-width: 650px; }}
            .result-item {{ margin-bottom: 25px; }}
            .result-source {{ font-size: 14px; color: #202124; margin-bottom: 4px; }}
            .result-title {{ font-size: 20px; color: #1a0dab; text-decoration: none; display: block; margin-bottom: 4px; }}
            .result-title:hover {{ text-decoration: underline; }}
            .result-desc {{ font-size: 14px; color: #4d5156; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin-right: 20px; color: #4285f4;">MegaEngine</h2>
            <form action="/search" method="get">
                <input type="text" name="q" class="search-bar" value="{q}">
            </form>
        </div>
        
        <div class="result-container">
    '''

    for r in results:
        # r[1]=source, r[2]=title, r[3]=content, r[5]=url
        html_output += f'''
            <div class="result-item">
                <div class="result-source">{r[1]}</div>
                <a href="{r[5]}" class="result-title" target="_blank">{r[2]}</a>
                <div class="result-desc">{r[3][:160]}...</div>
            </div>
        '''

    html_output += "</div></body></html>"
    return render_template_string(html_output)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
