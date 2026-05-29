from flask import Flask, request, render_template_string
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading
import os
import re

app = Flask(__name__)

# Render ক্লাউড সার্ভারের জন্য ডাটাবেজ পাথ সেটআপ
DB_PATH = os.path.join(os.getcwd(), "search.db")

# ==========================================
# ১. গ্লোবাল মেগা ক্রলার (ছবি ও ভিডিও থাম্বনেইল এক্সট্রাক্টরসহ)
# ==========================================
def global_background_crawl(query):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        sources_to_try = [
            # --- শপিং ও ই-কমার্স সাইট ---
            {"name": "Daraz (BD)", "cat": "product", "url": f"https://www.daraz.com.bd/catalog/?q={query}&aff_id=163322452"},
            {"name": "Amazon (Global)", "cat": "product", "url": f"https://www.amazon.com/s?k={query}"},
            {"name": "eBay (Global)", "cat": "product", "url": f"https://www.ebay.com/sch/i.html?_nkw={query}"},
            {"name": "AliExpress (Global)", "cat": "product", "url": f"https://www.aliexpress.com/w/wholesale-{query}.html"},
            {"name": "Temu (Trending)", "cat": "product", "url": f"https://www.temu.com/search_result.html?search_key={query}"},
            {"name": "Shein (Fashion)", "cat": "product", "url": f"https://www.shein.com/pdsearch/{query}/"},
            {"name": "Rokomari (Books)", "cat": "product", "url": f"https://www.rokomari.com/search?term={query}"},
            {"name": "Chaldal (Grocery)", "cat": "product", "url": f"https://chaldal.com/search/{query}"},
            {"name": "Flipkart (India)", "cat": "product", "url": f"https://www.flipkart.com/search?q={query}"},
            {"name": "Noon (Middle East)", "cat": "product", "url": f"https://www.noon.com/uae-en/search/?q={query}"},
            
            # --- গ্লোবাল ও আঞ্চলিক নিউজ সাইট ---
            {"name": "BBC News", "cat": "news", "url": f"https://www.bbc.com/search?q={query}"},
            {"name": "CNN", "cat": "news", "url": f"https://edition.cnn.com/search?q={query}"},
            {"name": "Reuters", "cat": "news", "url": f"https://www.reuters.com/site-search/?query={query}"},
            {"name": "Al Jazeera", "cat": "news", "url": f"https://www.aljazeera.com/search/{query}"},
            {"name": "Prothom Alo (BD)", "cat": "news", "url": f"https://www.prothomalo.com/search?q={query}"},
            {"name": "Somoy TV (BD)", "cat": "news", "url": f"https://www.somoynews.tv/search?q={query}"},
            {"name": "The Verge (Tech)", "cat": "news", "url": f"https://www.theverge.com/search?q={query}"},
            {"name": "BuzzFeed (Viral)", "cat": "news", "url": f"https://www.buzzfeed.com/search?q={query}"},
            
            # --- ভিডিও ও সোশ্যাল কন্টেন্ট ---
            {"name": "YouTube Video Search", "cat": "youtube", "url": f"https://www.youtube.com/results?search_query={query}"}
        ]

        for source in sources_to_try:
            try:
                res = requests.get(source["url"], headers=headers, timeout=6)
                if res.status_code == 200:
                    res.encoding = 'utf-8'
                    soup = BeautifulSoup(res.text, "html.parser")

                    title = soup.title.string.strip() if soup.title else f"{query} - {source['name']}"
                    
                    # 🖼️ ডায়নামিক ইমেজ ও ভিডিও থাম্বনেইল স্ক্র্যাপিং লজিক
                    image_url = None
                    
                    # ওপেন গ্রাফ মেটা ট্যাগ থেকে মেইন ছবি খোঁজার চেষ্টা (সবচেয়ে নির্ভরযোগ্য পদ্ধতি)
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        image_url = og_image["content"]

                    # ইউটিউবের জন্য স্পেশাল থাম্বনেইল ও কন্টেন্ট সেটআপ
                    if "youtube" in source["url"]:
                        content = f"Watch latest viral videos, reviews, and updates about '{query}' live on YouTube."
                        # ইউটিউব পেজ সোর্স থেকে প্রথম ভিডিও আইডি খোঁজার চেষ্টা
                        video_ids = re.findall(r"\"videoId\":\"([^\"]+)\"", res.text)
                        if video_ids:
                            image_url = f"https://img.youtube.com/vi/{video_ids[0]}/hqdefault.jpg"
                            source["url"] = f"https://www.youtube.com/watch?v={video_ids[0]}"
                        else:
                            image_url = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=400" # ডিফল্ট ইউটিউব লোগো
                    
                    # যদি কোনো ছবি না পাওয়া যায়, তবে ক্যাটাগরি অনুযায়ী সুন্দর ডিফল্ট ছবি দেওয়া
                    if not image_url or not image_url.startswith("http"):
                        if source["cat"] == "product":
                            image_url = "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400" # শপিং ইমেট
                        elif source["cat"] == "news":
                            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400" # নিউজ ইমেজ
                        else:
                            image_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400"

                    # প্যারাগ্রাফ কন্টেন্ট স্ক্র্যাপ করা
                    if "youtube" not in source["url"]:
                        paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text]
                        content = " ".join(paragraphs[:2])
                        if not content or len(content) < 10:
                            content = f"Explore best prices, specs, trends and breaking updates regarding '{query}' directly on {source['name']}."

                    # ডাটাবেজে ডাটা ইনসার্ট করা
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
                    """, (source["cat"], source["name"], title, content, image_url, source["url"]))
                    conn.commit()
                    conn.close()
                    print(f"[⚡ Media-Indexed] Added from {source['name']}: {query}")
            except Exception as inner_e:
                print(f"Skipped source due to error: {inner_e}")
                continue

    except Exception as e:
        print(f"[-] Global-crawl failed: {e}")

# ==========================================
# ২. সার্চ ইঞ্জিন মূল ফাংশন
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
        print(f"[🔍 Trigger] '{query}' not found. Global Media Crawler started...")
        threading.Thread(target=global_background_crawl, args=(query,)).start()

    return results

# ==========================================
# ৩. ইউজার ইন্টারফেস (HTML UI) - ইমেজ গ্রিডসহ লাক্সারি লুক
# ==========================================
@app.route("/")
def home():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DarazPlus Media Mega Engine</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); margin: 0; min-height: 100vh; text-align: center; color: #333; }}
            .main {{ padding-top: 120px; padding-bottom: 50px; }}
            h1 {{ color: #e84118; font-size: 50px; margin-bottom: 5px; font-weight: 800; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }}
            .subtitle {{ color: #5f6368; font-size: 16px; margin-bottom: 35px; font-weight: 500; }}
            .search-box {{ position: relative; max-width: 600px; margin: 0 auto; padding: 0 20px; }}
            input[type="text"] {{ width: 100%; padding: 18px 28px; font-size: 17px; border: 2px solid #dfe1e5; border-radius: 35px; outline: none; box-sizing: border-box; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: 0.3s; }}
            input[type="text"]:focus {{ border-color: #e84118; box-shadow: 0 4px 20px rgba(232,65,24,0.2); }}
            button {{ padding: 15px 40px; font-size: 16px; background-color: #e84118; color: white; border: none; border-radius: 35px; margin-top: 20px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 10px rgba(232,65,24,0.3); transition: 0.2s; }}
            button:hover {{ background-color: #c23313; transform: translateY(-1px); }}
            .badge-container {{ margin-top: 40px; font-size: 13px; color: #555; }}
            .badge {{ background: white; padding: 6px 14px; border-radius: 20px; display: inline-block; margin: 5px; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        </style>
    </head>
    <body>
        <div class="main">
            <h1>🌐 DarazPlus Global Media</h1>
            <p class="subtitle">Affiliate Sub-Network & Video Stream Tracker (ID: 163322452)</p>
            
            <div class="search-box">
                <form action="/search" method="get">
                    <input type="text" name="q" placeholder="পণ্য, গ্লোবাল নিউজ, ভিডিও বা ভাইরাল ট্রেন্ড..." required>
                    <button type="submit">Search Globally</button>
                </form>
            </div>

            <div class="badge-container">
                <p><strong>🔥 Live Sync Active:</strong></p>
                <span class="badge" style="color: #e84118;">🛒 Daraz & Amazon</span> 
                <span class="badge" style="color: #ff0000;">📺 YouTube Videos</span>
                <span class="badge" style="color: #27ae60;">📰 BBC & Prothom Alo</span> 
                <span class="badge" style="color: #f39c12;">⚡ Temu & Shein</span>
            </div>
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f3f4; padding: 20px; margin: 0; }}
            .nav {{ background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .nav h2 {{ margin: 0; color: #222; font-size: 22px; }}
            .back {{ padding: 10px 22px; background: #5f6368; color: white; text-decoration: none; border-radius: 25px; font-size: 14px; font-weight: bold; transition: 0.2s; }}
            .back:hover {{ background: #3c4043; }}
            .container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); grid-gap: 25px; padding: 10px 0; }}
            .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; transition: 0.3s; position: relative; }}
            .card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }}
            .img-container {{ width: 100%; height: 180px; background-color: #eaeaea; position: relative; }}
            .card-img {{ width: 100%; height: 100%; object-fit: cover; }}
            .card-body {{ padding: 18px; display: flex; flex-direction: column; flex-grow: 1; }}
            .source-tag {{ font-size: 10px; font-weight: bold; color: white; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; position: absolute; top: 12px; left: 12px; z-index: 10; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
            .title {{ font-size: 16px; font-weight: bold; color: #1a0dab; text-decoration: none; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
            .title:hover {{ text-decoration: underline; }}
            .desc {{ font-size: 13px; color: #4d5156; line-height: 1.5; margin-bottom: 15px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
            .buy-btn {{ display: block; text-align: center; padding: 12px; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: auto; transition: 0.2s; text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px; }}
            
            /* ভিডিও কার্ডের জন্য স্পেশাল প্লে বাটন ডিজাইন */
            .play-icon {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 50px; height: 50px; background: rgba(255, 0, 0, 0.85); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); pointer-events: none; }}
        </style>
    </head>
    <body>
        <div class="nav">
            <h2>🌍 Multi-Network Media Grid</h2>
            <a href="/" class="back">← New Search</a>
        </div>
        <p style="margin-left: 5px; color: #5f6368; font-weight: 500;">Showing real-time rich-media results for: <span style="color: #e84118;">"{q}"</span></p>
        <div class="container">
    '''

    if not results:
        html_output += f"""
        <div style='grid-column:1/-1; text-align:center; padding: 60px 20px; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>
            <h3 style='color: #222; font-size: 24px; margin-bottom: 10px;'>📸 Generating Rich-Media Content for "{q}"...</h3>
            <p style='color: #e67e22; font-weight: bold; font-size: 16px; margin-bottom: 5px;'>[⚡ এআই রোবট অ্যাক্টিভেটেড] আমাদের ক্রলার Amazon, Temu, BBC, YouTube এবং Daraz থেকে ছবি ও ভিডিও থাম্বনেইলসহ ডাটা টানছে।</p>
            <p style='color: #7f8c8d; font-size: 14px;'>দয়া করে ১০ সেকেন্ড অপেক্ষা করে ওপরের ব্যাক বাটনে ক্লিক করে আবার সার্চ করুন বা পেজটি <strong>Refresh (রিলোড)</strong> করুন।</p>
        </div>
        """

    for r in results:
        category, source_name, title, content, image_url, target_url = r[0], r[1], r[2], r[3], r[4], r[5]

        # সোর্স ভিত্তিক থিম এবং বাটন টেক্সট ফিক্স
        is_video = False
        if source_name == "Daraz (BD)":
            tag_color = "#e84118"
            btn_text = "View Daraz Deal ➜"
        elif "Amazon" in source_name or "eBay" in source_name or "AliExpress" in source_name:
            tag_color = "#2c3e50"
            btn_text = "View Global Deal ➜"
        elif "Temu" in source_name or "Shein" in source_name:
            tag_color = "#f39c12"
            btn_text = "View Trending Deal ➜"
        elif "YouTube" in source_name:
            tag_color = "#ff0000"
            btn_text = "Play Video on YouTube ➜"
            is_video = True
        else:
            tag_color = "#27ae60"
            btn_text = "Read Full Article ➜"

        html_output += f'''
        <div class="card">
            <span class="source-tag" style="background: {tag_color};">{source_name}</span>
            <div class="img-container">
                <img class="card-img" src="{image_url}" alt="{title}" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400';">
                {'<div class="play-icon">▶</div>' if is_video else ''}
            </div>
            <div class="card-body">
                <a href="{target_url}" target="_blank" class="title">{title}</a>
                <div class="desc">{content}</div>
                <a href="{target_url}" target="_blank" class="buy-btn" style="background: {tag_color};">{btn_text}</a>
            </div>
        </div>
        '''

    html_output += "</div></body></html>"
    return render_template_string(html_output)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)            try:
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

