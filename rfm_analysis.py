!pip install supabase pandas numpy matplotlib seaborn tqdm

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from supabase import create_client, Client

# Настройки визуализаций
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

SUPABASE_URL = "https://ntlhmoodpscxxyzfazpt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50bGhtb29kcHNjeHh5emZhenB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNDUwNDcsImV4cCI6MjA3OTkyMTA0N30.7BQneG11trwA7L8-cepfFXbiGzoHg04qsd37Rc7aSoY"

print("🔌 Подключаюсь...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✓ Успешно\n")

print("📥 Загрузка данных из таблицы sales...")

all_data = []
offset = 0
limit = 10000

while True:
    res = supabase.table('sales').select('*').range(offset, offset+limit-1).execute()
    data = res.data
    if not data:
        break
    all_data.extend(data)
    offset += limit
    print(f"Загружено: {len(all_data):,} строк")

df = pd.DataFrame(all_data)
print(f"\n✓ Всего загружено: {len(df):,} записей\n")

print("🔧 Приведение типов...")

df["purchase_datetime"] = pd.to_datetime(df["purchase_datetime"], errors="coerce")
df = df.dropna(subset=["purchase_datetime"])

num_columns = [
    "sale_id", "client_id", "product_id",
    "quantity", "price_per_item", "discount_per_item", "total_price"
]
df[num_columns] = df[num_columns].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=num_columns)

print(df.info())
print(df.head(), "\n✓ Данные готовы\n")

print("📊 Старт RFM анализа...")

snapshot_date = df['purchase_datetime'].max() + pd.Timedelta(days=1)

rfm = df.groupby('client_id').agg({
    'purchase_datetime': lambda x: (snapshot_date - x.max()).days,
    'sale_id': 'count',
    'total_price': 'sum'
})
rfm.columns = ['Recency', 'Frequency', 'Monetary']

# Recency — чем меньше, тем лучше
rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1]).astype(int)

# Frequency — вручную, чтобы избежать ошибок квантилей
rfm['F_score'] = rfm['Frequency'].apply(
    lambda x: 1 if x == 1 else
              2 if x == 2 else
              3 if x == 3 else
              4 if x == 4 else 5
)

# Monetary — ранжируем перед qcut
rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5,
                         labels=[1,2,3,4,5]).astype(int)

rfm['RFM'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

def segment_client(x):
    if x >= 13:  return "VIP ⭐"
    if x >= 10:  return "Лояльные"
    if x >= 7:   return "Потенциально лояльные"
    if x >= 4:   return "Спящие"
    return "Ушедшие"

rfm['Segment'] = rfm['RFM'].apply(segment_client)

rfm_reset = rfm.reset_index()

rfm_summary = rfm_reset.groupby('Segment').agg({
    'client_id': 'count',
    'Monetary': 'sum'
}).rename(columns={"client_id": "Customers", "Monetary": "Revenue"})

rfm_summary['Revenue_share_%'] = (
    rfm_summary['Revenue'] / rfm_summary['Revenue'].sum() * 100
).round(2)

rfm_summary = rfm_summary.sort_values('Revenue', ascending=False)

print("📊 Итоги по сегментам:")
print(rfm_summary, "\n")
print(rfm['Segment'].value_counts())

# Кол-во клиентов по сегментам
plt.figure(figsize=(10,5))
seg_counts = rfm['Segment'].value_counts().sort_values()
plt.barh(seg_counts.index, seg_counts.values)
plt.title("Распределение клиентов по RFM-сегментам")
plt.xlabel("Количество клиентов")
plt.grid(axis="x", alpha=0.3)
plt.show()

# Выручка по сегментам
plt.figure(figsize=(10,5))
plt.pie(rfm_summary['Revenue'], labels=rfm_summary.index,
        autopct='%1.1f%%', startangle=140)
plt.title("Вклад сегментов в выручку")
plt.show()