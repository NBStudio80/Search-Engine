from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

# দারাজ এফিলিয়েট আইডি
AFFILIATE_ID = "163322452"

@app.route("/")
def home():
    return '''
    <body style="font-family:sans-serif; text-align:center; padding-top:100px;">
        <h1>MegaEngine</h1>
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="কী খুঁজছেন?" style="width:300px; padding:10px; border-radius:20px; border:1px solid #ccc;">
            <button type="submit">Search</button>
        </form>
    </body>
    '''

@app.route("/search")
def search_page():
    q = request.args.get("q", "")
    if not q:
        return redirect("/")

    # এখানে আমরা সরাসরি ইউআরএল জেনারেট করছি, স্ক্র্যাপিং এরর এড়িয়ে চলার জন্য
    daraz_search_url = f"https://www.daraz.com.bd/catalog/?q={q.replace(' ', '+')}&aff_id={AFFILIATE_ID}"
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><title>{q} - MegaEngine</title>
    <style>
        body {{ font-family: arial; margin: 0; }}
        .header {{ padding: 20px; border-bottom: 1px solid #ddd; }}
        .btn {{ background: #ff6801; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h2>MegaEngine: Results for "{q}"</h2>
        </div>
        <div style="padding: 50px; text-align: center;">
            <h3>আপনার সার্চ করা পণ্যের জন্য দারাজে ক্লিক করুন</h3>
            <p>নিরাপত্তা সিস্টেমের কারণে আমরা সরাসরি ইমেজ দেখাতে পারছি না, তবে এই লিঙ্কে ক্লিক করলে আপনি সব রেজাল্ট পেয়ে যাবেন:</p>
            <br>
            <a href="{daraz_search_url}" class="btn" target="_blank">দারাজে রেজাল্ট দেখুন</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
