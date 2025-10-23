# scraperTEST.py
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
from playwright.sync_api import sync_playwright
import os

# Supabase 認証情報
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# 検索キーワード
SEARCH_KEYWORD = "金沢市"
BASE_URL = f"https://eplus.jp/sf/search?keyword={SEARCH_KEYWORD}"

def scrape_eplus():
    print("🔍 e+（Playwright）でイベントを取得中...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL)
        # チケット要素が描画されるまで最大10秒待機
        page.wait_for_selector("a.ticket-item", timeout=10000)
        html = page.content()
        browser.close()

    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(html, "html.parser")
    events = []

    cards = soup.select("a.ticket-item")
    for c in cards:
        title_elem = c.select_one(".ticket-item__title")
        year_elem = c.select_one(".ticket-item__yyyy")
        date_elem = c.select_one(".ticket-item__mmdd")
        venue_elem = c.select_one(".ticket-item__venue")
        link = c.get("href")

        title = title_elem.get_text(strip=True) if title_elem else "（タイトル不明）"
        year = year_elem.get_text(strip=True) if year_elem else ""
        mmdd = date_elem.get_text(strip=True) if date_elem else ""
        venue = venue_elem.get_text(strip=True) if venue_elem else ""
        event_url = f"https://eplus.jp{link}" if link and link.startswith("/") else link

        # 日付を整形
        try:
            date_str = f"{year}.{mmdd}".replace("/", ".")
            date = datetime.strptime(date_str, "%Y.%m.%d").date()
        except Exception:
            date = None

        events.append({
            "title": title,
            "date": date,
            "venue": venue,
            "url": event_url,
            "image_url": None,
            "source": "eplus",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

    print(f"✅ {len(events)} 件のイベントを取得しました")
    return events

def save_to_supabase(events):
    if not events:
        print("⚠️ 登録するイベントがありません。")
        return
    try:
        supabase.table("events").insert(events).execute()
        print(f"💾 Supabaseに {len(events)} 件のデータを保存しました")
    except Exception as e:
        print(f"❌ Supabaseへの保存中にエラー: {e}")

if __name__ == "__main__":
    events = scrape_eplus()
    save_to_supabase(events)
