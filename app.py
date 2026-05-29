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
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # আপনার মূল ক্রলিং সোর্সগুলো এখানে দেওয়া আছে
        sources = [
            {"name": "Daraz (BD)", "cat": "product", "url": f"https://www.daraz.com.bd/catalog/?q={query}&aff_id=163322452"},
            {"name": "Wikipedia", "cat": "info", "url": f"https://en.wikipedia.org/wiki/{query}"},
            {"name": "BBC News", "cat": "news", "url": f"https://www.bbc.com/search?q={query}"}
        ]

        for source in sources:
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
    
    html = f'<h2>Results for "{q}"</h2><div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:20px;">'
    
    if not results:
        html += '<p>Data generating... please refresh after 10 seconds.</p>'
        
    for r in results:
        html += f'''
        <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
            <small style="color:#e84118;">{r[1]}</small>
            <h3>{r[2]}</h3>
            <p>{r[3][:100]}...</p>
            <a href="{r[5]}" target="_blank">View More</a>
        </div>
        '''
    return render_template_string(html + "</div>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
