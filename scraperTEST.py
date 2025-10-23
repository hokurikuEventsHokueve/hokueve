import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client

# Supabase接続設定
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# 検索キーワード（金沢市）
SEARCH_KEYWORD = "金沢市"

# e+検索URL
BASE_URL = "https://eplus.jp/sf/search"
params = {"keyword": SEARCH_KEYWORD}

def scrape_eplus():
    print("🔍 e+ からイベントを取得中...")
    res = requests.get(BASE_URL, params=params)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

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
