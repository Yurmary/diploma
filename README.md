# Дипломная работа

Набор Python-скриптов для аналитики данных:

| Скрипт | Назначение |
|-------|------------|
| `api_fetch_once.py` | Единоразовая загрузка данных через API |
| `api_fetch_daily.py` | Получение данных за предыдущий день через API (регулярная задача) |
| `abc_analysis.py` | ABC-анализ данных |
| `rfm_analysis.py` | RFM-анализ данных |

---

##  Установка и запуск

### 1️⃣ Клонировать проект
git clone https://github.com/Yurmary/diploma.git
cd diploma

### 2️⃣ Установить зависимости
pip install -r requirements.txt

### 3️⃣ Запуск скриптов

python src/api_fetch_once.py
python src/abc_analysis.py
python src/rfm_analysis.py
python src/api_fetch_daily.py

### Структура проекта
```
diploma/
│
├─ src/                        # Весь код проекта
│   ├─ api_fetch_once.py       # Единоразовый API скрипт по забору данных
│   ├─ api_fetch_daily.py      # API - данные за предыдущий день
│   ├─ abc_analysis.py         # ABC - анализ
│   └─ rfm_analysis.py         # RFM-анализ
│
├─ requirements.txt            # Зависимости проекта (для установки pip)
├─ README.md                   # Описание проекта
└─ .gitignore                 
```

