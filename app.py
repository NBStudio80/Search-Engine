from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# কনফিগারেশন
SERPER_API_KEY = "02bd8a6b124dfacf21240c8d78f2039ae0d5a0aa"
AFFILIATE_ID = "163322452"

def get_search_results(query):
    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('organic', [])

@app.route("/")
def home():
    return render_template_string('''
    <body style="font-family: Arial; text-align: center; padding-top: 150px;">
        <h1 style="color: #4285f4;">MegaEngine</h1>
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="কী খুঁজছেন?" style="width: 400px; padding: 15px; border-radius: 25px; border: 1px solid #ddd;">
        </form>
    </body>
    ''')

@app.route("/search")
def search():
    query = request.args.get("q", "")
    results = get_search_results(query)
    
    # ডিজাইন
    html = '''
    <style>
        body { font-family: arial; padding: 20px; }
        .result { margin-bottom: 20px; max-width: 600px; }
        .title { color: #1a0dab; font-size: 20px; text-decoration: none; }
        .footer { text-align: center; margin-top: 50px; border-top: 1px solid #eee; padding: 20px; }
    </style>
    <body>
        <h2>MegaEngine: ''' + query + '''</h2>
    '''
    
    for item in results:
        link = item['link']
        # দারাজ এফিলিয়েট লিঙ্ক কনভার্টার
        if "daraz.com.bd" in link:
            link = f"{link}?aff_id={AFFILIATE_ID}"
            
        html += f'''
            <div class="result">
                <a href="{link}" class="title" target="_blank">{item['title']}</a><br>
                <small>{item['link']}</small>
                <p>{item.get('snippet', '')}</p>
            </div>
        '''
        
    html += '''
        <div class="footer">
            <a href="/">Home</a> | <a href="#">About-Us</a> | <a href="#">Contact-Us</a><br>
            <a href="#">Privacy Policy</a> | <a href="#">Terms & Conditions</a><br>
            <a href="#">Disclaimer</a> | <a href="#">Sitemap</a>
        </div>
    </body>'''
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
