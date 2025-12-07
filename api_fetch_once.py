!pip install supabase pandas numpy matplotlib seaborn tqdm
import pandas as pd
import requests
from tqdm import tqdm
from supabase import create_client, Client
from datetime import datetime

# ----------------- Настройки Supabase -----------------
SUPABASE_URL = "https://ntlhmoodpscxxyzfazpt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50bGhtb29kcHNjeHh5emZhenB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNDUwNDcsImV4cCI6MjA3OTkyMTA0N30.7BQneG11trwA7L8-cepfFXbiGzoHg04qsd37Rc7aSoY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- Настройки API -----------------
API_URL = "http://final-project.simulative.ru/data"
LIMIT = 1000  # по 1000 записей за запрос

# ----------------- Даты для загрузки -----------------
start_date = datetime(2025, 11, 1)
end_date = datetime.today()
date_list = pd.date_range(start_date, end_date)

all_records = []

# ----------------- Сбор данных по датам -----------------
for date in tqdm(date_list, desc="Сбор данных по датам"):
    date_str = date.strftime("%Y-%m-%d")

    try:
        resp = requests.get(API_URL, params={"date": date_str, "limit": LIMIT}, timeout=30)
        resp.raise_for_status()
        daily_data = resp.json()
    except Exception as e:
        print(f"❌ Ошибка запроса за {date_str}: {e}")
        continue

    if not daily_data:
        continue

    df = pd.DataFrame(daily_data)

    # Убираем строки без ключевых данных
    df = df.dropna(subset=["client_id", "product_id", "purchase_datetime"])
    if df.empty:
        continue

    # 👉 Сохраняем дату строго как пришла из API
    df["purchase_datetime"] = df["purchase_datetime"].astype(str)

    all_records.extend(df.to_dict(orient="records"))

# ----------------- Вставка в Supabase батчами -----------------
batch_size = 500

for i in tqdm(range(0, len(all_records), batch_size), desc="Загрузка в Supabase"):
    batch = all_records[i:i+batch_size]
    try:
        res = supabase.table("sales").insert(batch).execute()

        # Проверяем наличие ошибки
        if hasattr(res, "error") and res.error:
            print(f"❌ Ошибка вставки batch {i}-{i+batch_size}: {res.error}")

    except Exception as e:
        print(f"❌ Исключение при вставке batch {i}-{i+batch_size}: {e}")

print(f"✅ Загрузка завершена! Всего записей отправлено: {len(all_records)}")