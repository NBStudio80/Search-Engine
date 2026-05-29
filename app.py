from flask import Flask, request, render_template_string
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading

app = Flask(__name__)
DB_PATH = "database/search.db"

# ==========================================
# ১. স্বয়ংক্রিয় লাইভ ক্রলার (আপনার আসল দারাজ আইডিসহ)
# ==========================================
def auto_background_crawl(query):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # 🎯 আপনার মেম্বার আইডি দিয়ে ট্র্যাকিং লিংক সেটআপ করা হয়েছে
        sources_to_try = [
            {
                "name": "Daraz",
                "cat": "product",
                "url": f"https://www.daraz.com.bd/catalog/?q={query}&aff_id=163322452"
            },
            {
                "name": "Wikipedia Bangla",
                "cat": "news",
                "url": f"https://bn.wikipedia.org/wiki/{query}"
            },
            {
                "name": "Wikipedia English",
                "cat": "news",
                "url": f"https://en.wikipedia.org/wiki/{query}"
            }
        ]
        
        for source in sources_to_try:
            try:
                res = requests.get(source["url"], headers=headers, timeout=4)
                if res.status_code == 200:
                    res.encoding = 'utf-8'
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    title = soup.title.string.strip() if soup.title else query
                    paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
                    content = " ".join(paragraphs[:3])
                    
                    if content and len(content) > 15:
                        conn = sqlite3.connect(DB_PATH)
                        cur = conn.cursor()
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
                        cur.execute("""
                            INSERT OR IGNORE INTO mega_search (category, source, title, content, image_url, target_url)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (source["cat"], source["name"], title, content, "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=200", source["url"]))
                        conn.commit()
                        conn.close()
                        print(f"[⚡ Auto-Indexed] Successfully added from {source['name']}: {query}")
                        break 
            except:
                continue
                
    except Exception as e:
        print(f"[-] Auto-crawl failed: {e}")

# ==========================================
# ২. সার্চ ইঞ্জিন ফাংশন
# ==========================================
def search_mega_engine(query, category=None):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = str
    cur = conn.cursor()
    
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
    
    search_query = f"%{query}%"
    
    if category:
        cur.execute("""
            SELECT category, source, title, content, image_url, target_url 
            FROM mega_search 
            WHERE (title LIKE ? OR content LIKE ?) AND category = ?
        """, (search_query, search_query, category))
    else:
        cur.execute("""
            SELECT category, source, title, content, image_url, target_url 
            FROM mega_search 
            WHERE title LIKE ? OR content LIKE ?
        """, (search_query, search_query))
        
    results = cur.fetchall()
    conn.close()
    
    if not results:
        print(f"[🔍 Trigger] '{query}' not found. Auto-crawler started...")
        threading.Thread(target=auto_background_crawl, args=(query,)).start()
        
    return results

# ==========================================
# ৩. ইউজার ইন্টারফেস (HTML UI)
# ==========================================
@app.route("/")
def home():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mega_search")
        total = cur.fetchone()[0]
        conn.close()
    except:
        total = 0

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MegaEngine Affiliate Tracker</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; text-align: center; }}
            .main {{ margin-top: 150px; }}
            h1 {{ color: #e84118; font-size: 45px; margin-bottom: 5px; }}
            p {{ color: #5f6368; margin-bottom: 25px; }}
            input[type="text"] {{ width: 450px; max-width: 80%; padding: 14px 25px; font-size: 16px; border: 1px solid #dfe1e5; border-radius: 30px; outline: none; }}
            button {{ padding: 14px 30px; font-size: 16px; background-color: #e84118; color: white; border: none; border-radius: 30px; margin-left: 10px; cursor: pointer; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="main">
            <h1>🛍️ MegaEngine Store</h1>
            <p>Daraz Affiliate ID connected: <strong>163322452</strong></p>
            <form action="/search" method="get">
                <input type="text" name="q" placeholder="যেকোনো প্রোডাক্টের নাম লিখে সার্চ করুন..." required>
                <button type="submit">Search</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    cat = request.args.get("cat", "")
    results = search_mega_engine(q, cat)
    
    html_output = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Results for "{q}"</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; background-color: #f1f3f4; padding: 20px; }}
            .nav {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .back {{ padding: 8px 15px; background: #5f6368; color: white; text-decoration: none; border-radius: 20px; text-align: center; display: inline-block;}}
            .container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); grid-gap: 20px; }}
            .card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); display: flex; flex-direction: column; }}
            .title {{ font-size: 16px; font-weight: bold; color: #1a0dab; text-decoration: none; margin-top: 10px; display: block; }}
            .desc {{ font-size: 13px; color: #545454; margin-top: 10px; margin-bottom: 15px; }}
            .buy-btn {{ display: block; text-align: center; padding: 10px; background: #e84118; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: auto; }}
        </style>
    </head>
    <body>
        <div class="nav">
            <h2>🛒 Shopping Results</h2>
            <a href="/" class="back">← New Search</a>
        </div>
        <p>Showing {len(results)} matches for: <strong>"{q}"</strong></p>
        <div class="container">
    '''
    
    if not results:
        html_output += f"""
        <div style='grid-column:1/-1; text-align:center; padding: 40px; background: white; border-radius: 8px;'>
            <h3>⚠️ '{q}' এর কোনো কন্টেন্ট ডাটাবেজে নেই!</h3>
            <p style='color: #ff9100; font-weight: bold;'>[⚡ প্রসেসিং] আপনার রোবট দারাজ এবং উইকিপিডিয়া থেকে লাইভ ডেটা জেনারেট করছে।</p>
            <p>দয়া করে ৫ সেকেন্ড পর পেজটি <strong>Refresh (রিলোড)</strong> করুন।</p>
        </div>
        """
        
    for r in results:
        html_output += f'''
        <div class="card">
            <div>
                <span style="background:#e84118; color:white; padding:2px 6px; font-size:10px; border-radius:4px;">{r[1].upper()}</span>
                <br>
                <a href="{r[5]}" target="_blank" class="title">{r[2]}</a>
                <div class="desc">{r[3]}</div>
            </div>
            <a href="{r[5]}" target="_blank" class="buy-btn">View Deal / Buy Now ➜</a>
        </div>
        '''
        
    html_output += "</div></body></html>"
    return render_template_string(html_output)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

