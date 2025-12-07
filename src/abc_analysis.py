# Установка библиотек
!pip install supabase pandas numpy matplotlib seaborn tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from supabase import create_client, Client

# ============= НАСТРОЙКИ =============
SUPABASE_URL = "https://ntlhmoodpscxxyzfazpt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50bGhtb29kcHNjeHh5emZhenB0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNDUwNDcsImV4cCI6MjA3OTkyMTA0N30.7BQneG11trwA7L8-cepfFXbiGzoHg04qsd37Rc7aSoY"

# Настройки визуализации
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# ============= ПОДКЛЮЧЕНИЕ К SUPABASE =============
print("🔌 Подключение к Supabase...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✓ Подключение установлено\n")

# ============= ЗАГРУЗКА ДАННЫХ С ПАГИНАЦИЕЙ =============
print("📥 Загрузка всех данных из таблицы sales...")

all_data = []
offset = 0
limit = 10000  # за один запрос можно забрать до 5000 строк (можно увеличить, если сервер позволяет)

try:
    while True:
        response = supabase.table('sales').select('*').range(offset, offset + limit - 1).execute()
        data = response.data
        if not data:  # если данных больше нет
            break
        all_data.extend(data)
        offset += limit
        print(f"Загружено: {len(all_data):,} записей")

    df = pd.DataFrame(all_data)
    print(f"\n✓ Всего загружено записей: {len(df):,}\n")

except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    exit()

# ============= ПЕРВИЧНЫЙ ОСМОТР =============
print("="*70)
print("📊 ПЕРВИЧНЫЙ АНАЛИЗ ДАННЫХ")
print("="*70)

# Проверка структуры
print("\n1. Структура данных:")
print(df.info())

print("\n2. Первые 5 строк:")
print(df.head())

print("\n3. Пропущенные значения:")
print(df.isnull().sum())

# ============= ПОДГОТОВКА ДАННЫХ =============
# Преобразуем в datetime, если ещё не сделали
df['purchase_datetime'] = pd.to_datetime(df['purchase_datetime'])

# Столбец только с датой (тип datetime64 без UTC)
df['purchase_date'] = df['purchase_datetime'].dt.date

# Для группировки нужно преобразовать обратно в datetime64[ns]
df['purchase_date'] = pd.to_datetime(df['purchase_date'])

# ============= БАЗОВАЯ СТАТИСТИКА =============
print("="*70)
print("📈 ОСНОВНЫЕ ПОКАЗАТЕЛИ")
print("="*70)

# Товары
print(f"\n📦 Товары:")
print(f"   Уникальных: {df['product_id'].nunique():,}")
print(f"   Продано единиц: {df['quantity'].sum():,.0f}")

# Клиенты
print(f"\n👥 Клиенты:")
unique_clients = df['client_id'].nunique()
print(f"   Уникальных клиентов: {unique_clients:,}")
print(f"   Покупок на клиента (среднее): {len(df) / unique_clients:.2f}")

# Финансы
total_revenue = df['total_price'].sum()
avg_check = df['total_price'].mean()

print(f"\n💵 Финансовые показатели:")
print(f"   Общая выручка: {total_revenue:,.2f}")
print(f"   Средний чек: {avg_check:,.2f}")

# Распределение по полу
if 'gender' in df.columns:
    print(f"\n👤 Распределение по полу:")
    print(df['gender'].value_counts())

# ============= ПРОВЕРКА КАЧЕСТВА ДАННЫХ =============
print("\n" + "="*70)
print("🔍 ПРОВЕРКА КАЧЕСТВА ДАННЫХ")
print("="*70)

anomalies = []

# Отрицательные значения
if (df['quantity'] <= 0).any():
    anomalies.append("⚠️ Найдены записи с quantity <= 0")

if (df['total_price'] <= 0).any():
    anomalies.append("⚠️ Найдены записи с total_price <= 0")

# Выбросы
q99 = df['total_price'].quantile(0.99)
outliers = df[df['total_price'] > q99 * 10]
if not outliers.empty:
    anomalies.append(f"⚠️ Аномально высокие total_price: {len(outliers)} записей")

# Дубликаты sale_id
duplicates = df.duplicated(subset=['sale_id']).sum()
if duplicates > 0:
    anomalies.append(f"⚠️ Дубликаты sale_id: {duplicates} записей")

if anomalies:
    print("\nОбнаружены аномалии:")
    for a in anomalies:
        print("  " + a)
else:
    print("Проблемы не обнаружены.")


# ============= БАЗОВАЯ ВИЗУАЛИЗАЦИЯ =============
print("\n📊 Создание графиков...")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 1. Динамика выручки по дням
daily_sales = (
    df.groupby('purchase_datetime')['total_price']
    .sum()
    .reset_index()
    .sort_values('purchase_datetime')
)

axes[0, 0].plot(
    daily_sales['purchase_datetime'],
    daily_sales['total_price'],
    linewidth=2,
    marker='o'
)
axes[0, 0].set_title('Динамика выручки по дням', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Дата')
axes[0, 0].set_ylabel('Выручка')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].tick_params(axis='x', rotation=45)

# 2. Топ-10 товаров по выручке
top10 = df.groupby('product_id')['total_price'].sum().nlargest(10).sort_values()

axes[0, 1].barh(top10.index.astype(str), top10.values)
axes[0, 1].set_title('ТОП-10 товаров по выручке', fontsize=14)
axes[0, 1].set_xlabel('Выручка')
axes[0, 1].grid(True, axis='x', alpha=0.3)

# 3. Распределение количества единиц в покупке
axes[1, 0].hist(df['quantity'], bins=30, edgecolor='black')
axes[1, 0].set_title('Распределение количества товаров в чеке', fontsize=14)
axes[1, 0].set_xlabel('Количество')
axes[1, 0].set_ylabel('Частота')
axes[1, 0].grid(True, alpha=0.3)

# 4. Распределение выручки
axes[1, 1].hist(df['total_price'], bins=30, edgecolor='black')
axes[1, 1].set_title('Распределение выручки по чекам', fontsize=14)
axes[1, 1].set_xlabel('Выручка чека')
axes[1, 1].set_ylabel('Частота')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('01_initial_analysis_no_margin.png', dpi=300)
print("✓ Графики сохранены: 01_initial_analysis_no_margin.png")

# ===========================================
# 🔤 ABC АНАЛИЗ
# ===========================================

print("\n📊 Выполняю ABC-анализ...\n")

abc = (
    df.groupby('product_id')['total_price']
    .sum()
    .reset_index()
    .rename(columns={'total_price': 'revenue'})
    .sort_values('revenue', ascending=False)
)

total_rev = abc['revenue'].sum()

abc['share'] = abc['revenue'] / total_rev
abc['cum_share'] = abc['share'].cumsum()

def assign_abc_class(cum):
    if cum <= 0.80:
        return 'A'
    elif cum <= 0.95:
        return 'B'
    else:
        return 'C'

abc['ABC'] = abc['cum_share'].apply(assign_abc_class)

print("📦 Распределение ABC:")
print(abc['ABC'].value_counts(), "\n")

# ===========================================
# 🔤 XYZ АНАЛИЗ
# ===========================================

print("\n📊 Выполняю XYZ-анализ...\n")

daily = (
    df.groupby(['product_id', 'purchase_date'])['quantity']
    .sum()
    .reset_index()
)

xyz_list = []

for product, group in daily.groupby('product_id'):
    mean_sales = group['quantity'].mean()
    std_sales = group['quantity'].std()
    cv = 999 if mean_sales == 0 else std_sales / mean_sales

    if cv <= 0.2:
        xyz_class = 'X'
    elif cv <= 0.5:
        xyz_class = 'Y'
    else:
        xyz_class = 'Z'

    xyz_list.append([product, mean_sales, std_sales, cv, xyz_class])

xyz = pd.DataFrame(
    xyz_list,
    columns=['product_id', 'mean_sales', 'std_sales', 'cv', 'XYZ']
)

print("📦 Распределение XYZ:")
print(xyz['XYZ'].value_counts(), "\n")

# ===========================================
# 🔤 ABC-XYZ МАТРИЦА
# ===========================================

abc_xyz = abc.merge(xyz, on='product_id', how='left')
abc_xyz['ABC_XYZ'] = abc_xyz['ABC'] + abc_xyz['XYZ']

print("📦 Пример объединённой матрицы ABC-XYZ:")
print(abc_xyz.head(), "\n")

sns.set_style("whitegrid")    # делает фон с сеткой
sns.set_palette("Set2")       # мягкая цветовая палитра
plt.rcParams.update({'font.size': 12})

fig, axes = plt.subplots(2, 3, figsize=(22, 12))

# 1 — ABC распределение
sns.countplot(data=abc, x='ABC', order=['A','B','C'], ax=axes[0,0])
axes[0,0].set_title('Распределение ABC', fontsize=16, fontweight='bold')
axes[0,0].set_xlabel('')
axes[0,0].set_ylabel('Количество товаров')
axes[0,0].grid(axis='y', alpha=0.3)

# 2 — Доля выручки ABC
abc_rev = abc.groupby('ABC')['revenue'].sum().reindex(['A','B','C'])
sns.barplot(x=abc_rev.index, y=abc_rev.values, ax=axes[0,1])
axes[0,1].set_title('Доля выручки ABC', fontsize=16, fontweight='bold')
axes[0,1].set_xlabel('')
axes[0,1].set_ylabel('Выручка')
axes[0,1].grid(axis='y', alpha=0.3)

# 3 — Парето по рангу с красной линией
pareto = abc.sort_values('revenue', ascending=False).reset_index(drop=True)
pareto['rank'] = pareto.index + 1
pareto['cum_share'] = pareto['revenue'].cumsum() / pareto['revenue'].sum()

ax1 = axes[0,2]
ax1.bar(pareto['rank'], pareto['revenue'], color='skyblue', alpha=0.7)
ax1.set_xlabel('Ранг товара')
ax1.set_ylabel('Выручка')
ax1.set_title('Парето (по рангу)', fontsize=16, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(pareto['rank'], pareto['cum_share'], color='red', marker='o', linewidth=2)
ax2.set_ylabel('Накопленная доля')
ax2.axhline(0.8, color='green', linestyle='--', label='80%')
ax2.axhline(0.95, color='orange', linestyle='--', label='95%')
ax2.legend(loc='lower right')

# 4 — XYZ распределение
sns.countplot(data=xyz, x='XYZ', order=['X','Y','Z'], ax=axes[1,0])
axes[1,0].set_title('XYZ распределение', fontsize=16, fontweight='bold')
axes[1,0].set_xlabel('')
axes[1,0].set_ylabel('Количество товаров')
axes[1,0].grid(axis='y', alpha=0.3)

# 5 — ABC–XYZ матрица
matrix = abc_xyz.groupby(['ABC','XYZ']).size().unstack(fill_value=0)
sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', ax=axes[1,2], cbar=False)
axes[1,2].set_title('Матрица ABC–XYZ', fontsize=16, fontweight='bold')
axes[1,2].set_xlabel('')
axes[1,2].set_ylabel('')

# 6 — можно оставить пустую, или добавить другой график
axes[1,1].axis('off')

plt.tight_layout()
plt.show()
