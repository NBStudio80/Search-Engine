from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# আপনার এফিলিয়েট আইডি
AFFILIATE_ID = "163322452" 

def get_daraz_results(query):
    # দারাজ থেকে সরাসরি ডেটা ফেচিং
    url = f"https://www.daraz.com.bd/catalog/?q={query.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []
        items = soup.select('.gridItem--Yd0NQ')[:6]
        for item in items:
            title = item.select_one('.title--wFj93 a').text
            img = item.select_one('img')['src']
            link = "https:" + item.select_one('a')['href']
            results.append({'title': title, 'img': img, 'link': f"{link}?aff_id={AFFILIATE_ID}"})
        return results
    except: return []

@app.route("/")
def home():
    return '''
    <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 150px;">
        <h1 style="color: #4285f4; font-size: 50px;">MegaEngine</h1>
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="কী খুঁজছেন?" style="width: 400px; padding: 15px; border-radius: 25px; border: 1px solid #ddd; outline: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        </form>
    </body>
    '''

@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    products = get_daraz_results(q)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>{q} - MegaEngine</title>
    <style>
        body {{ font-family: arial; margin: 0; background: #fff; }}
        .header {{ padding: 20px; border-bottom: 1px solid #dfe1e5; display: flex; align-items: center; }}
        .search-input {{ width: 500px; padding: 10px 20px; border-radius: 25px; border: 1px solid #dfe1e5; }}
        .main {{ display: flex; padding: 20px; gap: 40px; }}
        .left {{ flex: 2; max-width: 650px; }}
        .right {{ flex: 1; border: 1px solid #eee; padding: 20px; border-radius: 10px; height: 300px; }}
        .card {{ display: flex; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }}
        .card img {{ width: 100px; height: 100px; object-fit: contain; margin-right: 20px; }}
        .footer {{ text-align: center; padding: 40px; border-top: 1px solid #ddd; margin-top: 50px; color: #5f6368; }}
        .footer a {{ margin: 0 10px; color: #5f6368; text-decoration: none; }}
    </style></head>
    <body>
        <div class="header">
            <h2 style="margin-right: 20px; color: #4285f4;">MegaEngine</h2>
            <form action="/search" method="get"><input type="text" name="q" class="search-input" value="{q}"></form>
        </div>
        <div class="main">
            <div class="left">
    '''
    for p in products:
        html += f'''
            <div class="card">
                <img src="{p['img']}">
                <div><a href="{p['link']}" style="font-size:18px; color:#1a0dab; text-decoration:none;" target="_blank">{p['title']}</a></div>
            </div>
        '''
    html += '''
            </div>
            <div class="right"><h3>Info Panel</h3><p>Daraz Shopping results.</p></div>
        </div>
        <div class="footer">
            <a href="#">Home</a> | <a href="#">About-Us</a> | <a href="#">Contact-Us</a><br>
            <a href="#">Privacy Policy</a> | <a href="#">Terms & Conditions</a><br>
            <a href="#">Disclaimer</a> | <a href="#">Sitemap</a>
        </div>
    </body></html>
    '''
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
