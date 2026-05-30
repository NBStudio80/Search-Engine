from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# দারাজ এফিলিয়েট সেটিংস
AFFILIATE_ID = "163322452" 

def fetch_daraz_data(query):
    search_url = f"https://www.daraz.com.bd/catalog/?q={query.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        items = soup.select('.gridItem--Yd0NQ')[:6] 
        for item in items:
            title = item.select_one('.title--wFj93 a').text
            img = item.select_one('img')['src']
            link = "https:" + item.select_one('a')['href']
            products.append({'title': title, 'img': img, 'link': f"{link}?aff_id={AFFILIATE_ID}"})
        return products
    except: return []

@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    products = fetch_daraz_data(q)
    
    html_output = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{q} - Google Style</title>
        <style>
            body {{ font-family: arial,sans-serif; margin: 0; background: #fff; }}
            .header {{ padding: 20px; border-bottom: 1px solid #dfe1e5; display: flex; align-items: center; }}
            .logo {{ font-size: 24px; font-weight: bold; color: #4285f4; margin-right: 30px; }}
            .search-input {{ width: 500px; padding: 12px 20px; border-radius: 25px; border: 1px solid #dfe1e5; outline: none; box-shadow: 0 1px 6px rgba(0,0,0,0.1); }}
            
            .main-wrapper {{ display: flex; padding: 20px; gap: 40px; }}
            .left-side {{ flex: 2; max-width: 700px; }}
            .right-side {{ flex: 1; border: 1px solid #dfe1e5; padding: 20px; border-radius: 8px; height: fit-content; }}
            
            .product-card {{ display: flex; margin-bottom: 25px; align-items: center; }}
            .product-card img {{ width: 100px; height: 100px; object-fit: contain; margin-right: 20px; border: 1px solid #eee; }}
            .title {{ font-size: 18px; color: #1a0dab; text-decoration: none; }}
            
            .footer {{ text-align: center; padding: 20px; border-top: 1px solid #ddd; margin-top: 50px; color: #5f6368; }}
            .footer a {{ margin: 0 10px; color: #5f6368; text-decoration: none; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">MegaEngine</div>
            <form action="/search" method="get">
                <input type="text" name="q" class="search-input" value="{q}">
            </form>
        </div>

        <div class="main-wrapper">
            <div class="left-side">
    '''

    for p in products:
        html_output += f'''
            <div class="product-card">
                <img src="{p['img']}">
                <div>
                    <a href="{p['link']}" class="title" target="_blank">{p['title']}</a>
                </div>
            </div>
        '''

    html_output += '''
            </div>
            <div class="right-side">
                <h3>Daraz Info Panel</h3>
                <p>এখানে আপনার সার্চ করা পণ্যের নলেজ প্যানেল প্রদর্শিত হবে।</p>
            </div>
        </div>

        <div class="footer">
            <a href="#">Home</a> | <a href="#">About-Us</a> | <a href="#">Contact-Us</a><br>
            <a href="#">Privacy Policy</a> | <a href="#">Terms & Conditions</a><br>
            <a href="#">Disclaimer</a> | <a href="#">Sitemap</a>
        </div>
    </body></html>
    '''
    return render_template_string(html_output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
