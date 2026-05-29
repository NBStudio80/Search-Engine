from flask import Flask, request, render_template_string
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading
import os

app = Flask(__name__)

# ডাটাবেজ পাথ
DB_PATH = os.path.join(os.getcwd(), "search.db")

# ==========================================
# ১. গ্লোবাল মেগা ক্রলার
# ==========================================
def global_background_crawl(query):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

    sources = [
        {"name": "BBC News", "cat": "news", "url": f"https://www.bbc.com/search?q={query}"},
        {"name": "CNN", "cat": "news", "url": f"https://edition.cnn.com/search?q={query}"},
        {"name": "Reuters", "cat": "news", "url": f"https://www.reuters.com/site-search/?query={query}"},
        {"name": "Prothom Alo", "cat": "news", "url": f"https://www.prothomalo.com/search?q={query}"},
        {"name": "Amazon", "cat": "product", "url": f"https://www.amazon.com/s?k={query}"},
        {"name": "Daraz (BD)", "cat": "product", "url": f"https://www.daraz.com.bd/catalog/?q={query}&aff_id=163322452"}
    ]

    for source in sources:
        try:
            res = requests.get(source["url"], headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                title = soup.title.string.strip() if soup.title else query
                paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
                content = " ".join(paragraphs[:3])
                
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("""CREATE TABLE IF NOT EXISTS mega_search (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)""")
                cur.execute("""INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url)
                    VALUES (?, ?, ?, ?, ?, ?)""", (source["cat"], source["name"], title, content, "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400", source["url"]))
                conn.commit()
                conn.close()
                print(f"[⚡] Added: {source['name']}")
        except Exception as e:
            print(f"[-] Error in {source['name']}: {e}")

# ==========================================
# ২. সার্চ ইঞ্জিন ফাংশন
# ==========================================
def search_mega_engine(query):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS mega_search (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, source TEXT, title TEXT, content TEXT, image_url TEXT, target_url TEXT UNIQUE)")
    
    search_query = f"%{query}%"
    cur.execute("SELECT category, source, title, content, image_url, target_url FROM mega_search WHERE title LIKE ? OR content LIKE ?", (search_query, search_query))
    results = cur.fetchall()
    conn.close()

    if not results:
        threading.Thread(target=global_background_crawl, args=(query,)).start()
    return results

# ==========================================
# ৩. ইউজার ইন্টারফেস
# ==========================================
@app.route("/")
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>MegaEngine</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 100px 20px; background: #f9f9f9; }
        .box { width: 500px; padding: 15px; border-radius: 25px; border: 1px solid #ccc; outline: none; }
    </style></head>
    <body>
        <h1>🌐 Mega Engine Search</h1>
        <form action="/search" method="get">
            <input type="text" name="q" class="box" placeholder="Search..." required>
        </form>
    </body>
    </html>
    '''

@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    results = search_mega_engine(q)
    
    html = f'<h2>Results for "{q}"</h2><div style="max-width:700px; margin:auto;">'
    if not results:
        html += '<p>Searching online... please wait 10 seconds and refresh.</p>'
    
    for r in results:
        html += f'''
        <div style="margin-bottom:20px; text-align:left;">
            <div style="font-size:12px; color:grey;">{r[1]}</div>
            <a href="{r[5]}" target="_blank" style="font-size:18px; color:blue;">{r[2]}</a>
            <p style="font-size:14px; color:#444;">{r[3][:150]}...</p>
        </div>'''
    return render_template_string(html + "</div>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
