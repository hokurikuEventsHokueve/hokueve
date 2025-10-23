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

    # イベントカードを抽出（構造が変わる場合は調整が必要）
    cards = soup.select("li.TicketList__item")

    for c in cards:
        title_elem = c.select_one(".TicketList__ttl")
        date_elem = c.select_one(".TicketList__date")
        link_elem = c.select_one("a.TicketList__link")
        img_elem = c.select_one("img")

        title = title_elem.text.strip() if title_elem else "（タイトル不明）"
        date_text = date_elem.text.strip() if date_elem else None
        event_url = link_elem["href"] if link_elem else None
        image_url = img_elem["src"] if img_elem else None

        # 日付を整形
        try:
            date = datetime.strptime(date_text[:10], "%Y.%m.%d").date() if date_text else None
        except Exception:
            date = None

        events.append({
            "title": title,
            "date": date,
            "url": event_url,
            "image_url": image_url,
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
