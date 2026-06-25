import os, json, time, random, logging, hashlib, schedule, requests
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8289872410:AAFBt5xJGKZfAK2v-nbm0NbcdVgJz2wXEfs")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@jobinbime")
SENT_FILE = "sent_jobs.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

KEYWORDS = ["ارزیاب خسارت", "کارشناس بیمه", "کارشناس خسارت درمان", "کارشناس بیمه تکمیلی"]

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE) as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent), f)

def job_hash(job):
    return hashlib.md5((job["title"]+job["url"]).encode()).hexdigest()

def scrape(keyword):
    jobs = []
    try:
        url = f"https://jobinja.ir/jobs?q={requests.utils.quote(keyword)}&sort_by=published_at_desc"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("li.o-listView__item--jobs")[:5]:
            t = card.select_one("h2")
            l = card.select_one("a[href]")
            c = card.select_one("[class*='company']")
            if t and l:
                jobs.append({"title": t.get_text(strip=True), "company": c.get_text(strip=True) if c else "نامشخص", "url": l["href"] if l["href"].startswith("http") else "https://jobinja.ir"+l["href"], "source": "Jobinja"})
    except Exception as e:
        log.warning(f"خطا: {e}")
    return jobs

def send(job):
    text = f"💼 *{job['title']}*\n\n🏢 شرکت: {job['company']}\n💰 حقوق: توافقی\n🌐 منبع: {job['source']}\n\n🔗 [مشاهده آگهی]({job['url']})\n\n📢 @jobinbime"
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    return r.ok

def cycle():
    sent = load_sent()
    jobs = []
    for kw in KEYWORDS:
        jobs += scrape(kw)
        time.sleep(2)
    new = [j for j in jobs if job_hash(j) not in sent]
    log.info(f"کل: {len(jobs)} | جدید: {len(new)}")
    if not new:
        return
    job = random.choice(new)
    if send(job):
        sent.add(job_hash(job))
        save_sent(sent)
        log.info(f"ارسال شد: {job['title']}")

schedule.every(2).hours.do(cycle)
cycle()
while True:
    schedule.run_pending()
    time.sleep(60)
