!pip install supabase

import pandas as pd
import requests
from tqdm import tqdm
from supabase import create_client, Client
from datetime import datetime, timedelta

# ----------------- Настройки Supabase -----------------
SUPABASE_URL = "https://ntlhmoodpscxxyzfazpt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50bGhtb29kcHNjeHh5emZhenB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNDUwNDcsImV4cCI6MjA3OTkyMTA0N30.7BQneG11trwA7L8-cepfFXbiGzoHg04qsd37Rc7aSoY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- Настройки API -----------------
API_URL = "http://final-project.simulative.ru/data"
LIMIT = 1000  # по 1000 записей за запрос

# ----------------- Берём только вчерашний день -----------------
yesterday = datetime.today() - timedelta(days=1)
date_list = [yesterday]

all_records = []

# ----------------- Сбор данных -----------------
for date in tqdm(date_list, desc="Сбор данных за вчера"):
    date_str = date.strftime("%Y-%m-%d")
    try:
        resp = requests.get(API_URL, params={"date": date_str, "limit": LIMIT}, timeout=30)
        resp.raise_for_status()
        daily_data = resp.json()
    except Exception as e:
        print(f"❌ Ошибка запроса за {date_str}: {e}")
        continue

    if not daily_data:
        print(f"⚠️ Данных за {date_str} нет")
        continue

    df = pd.DataFrame(daily_data)
    df = df.dropna(subset=["client_id", "product_id", "purchase_datetime"])
    if df.empty:
        print(f"⚠️ Нет данных с ключевыми полями за {date_str}")
        continue

    # Сохраняем дату строго как пришла из API
    df["purchase_datetime"] = df["purchase_datetime"].astype(str)

    all_records.extend(df.to_dict(orient="records"))

# ----------------- Вставка в Supabase батчами -----------------
batch_size = 500
TARGET_TABLE = "sales"

for i in tqdm(range(0, len(all_records), batch_size), desc=f"Загрузка в {TARGET_TABLE}"):
    batch = all_records[i:i+batch_size]
    try:
        res = supabase.table(TARGET_TABLE).insert(batch).execute()
        if hasattr(res, "error") and res.error:
            print(f"❌ Ошибка вставки batch {i}-{i+batch_size}: {res.error}")
    except Exception as e:
        print(f"❌ Исключение при вставке batch {i}-{i+batch_size}: {e}")

print(f"✅ Загрузка завершена в {TARGET_TABLE}! Всего записей отправлено: {len(all_records)}")