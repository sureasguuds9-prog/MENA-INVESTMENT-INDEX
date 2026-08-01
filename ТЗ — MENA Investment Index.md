# Индекс инвестиционного климата стран MENA
## Техническое задание v1.0

> **Позиционирование:** Аналитический продукт уровня EIU Country Risk / Bloomberg CACR — количественная оценка инвестиционного климата 19 стран MENA на основе открытых данных, панельной регрессии и интерактивного дашборда.

---

## 1. ЦЕЛИ И КОНЦЕПЦИЯ

### Что строим
Composite Investment Climate Index (CICI) — числовой индекс от 0 до 100 для каждой из 19 стран MENA, обновляемый ежеквартально. Индекс агрегирует 7 факторных блоков, веса которых обоснованы регрессией FDI ~ факторы (панельные данные, Fixed Effects).

### Для кого
- Инвестиционные аналитики и фонды (PE, sovereign wealth)
- Академические исследователи MENA
- Государственные структуры (investment promotion agencies)
- Личное портфолио: демонстрация data science + geopolitics компетенций

### Чем отличается от EIU/Bloomberg
| Параметр | EIU/Bloomberg | MENA CICI |
|----------|--------------|-----------|
| Доступ | Платный ($10k+/год) | Open source |
| Прозрачность методологии | Закрытая | Полная (код + данные) |
| Кастомизация весов | Нет | Да (real-time в дашборде) |
| Покрытие | Global | MENA фокус (глубина) |
| Обновление | Ежегодно | Ежеквартально |

---

## 2. ПОКРЫТИЕ: 19 СТРАН MENA

| # | Страна | ISO | Субрегион |
|---|--------|-----|-----------|
| 1 | 🇸🇦 Saudi Arabia | SAU | Gulf |
| 2 | 🇦🇪 UAE | ARE | Gulf |
| 3 | 🇶🇦 Qatar | QAT | Gulf |
| 4 | 🇰🇼 Kuwait | KWT | Gulf |
| 5 | 🇧🇭 Bahrain | BHR | Gulf |
| 6 | 🇴🇲 Oman | OMN | Gulf |
| 7 | 🇪🇬 Egypt | EGY | North Africa |
| 8 | 🇲🇦 Morocco | MAR | North Africa |
| 9 | 🇹🇳 Tunisia | TUN | North Africa |
| 10 | 🇱🇾 Libya | LBY | North Africa |
| 11 | 🇩🇿 Algeria | DZA | North Africa |
| 12 | 🇸🇩 Sudan | SDN | North Africa |
| 13 | 🇮🇶 Iraq | IRQ | Levant/Mashreq |
| 14 | 🇯🇴 Jordan | JOR | Levant/Mashreq |
| 15 | 🇱🇧 Lebanon | LBN | Levant/Mashreq |
| 16 | 🇸🇾 Syria | SYR | Levant/Mashreq |
| 17 | 🇾🇪 Yemen | YEM | Levant/Mashreq |
| 18 | 🇮🇱 Israel | ISR | Levant/Mashreq |
| 19 | 🇮🇷 Iran | IRN | Other |

---

## 3. АРХИТЕКТУРА МОДЕЛИ: 7 ФАКТОРОВ

### Формула композитного индекса
```
CICI = Σ (wᵢ × Fᵢ_normalized)    где Σwᵢ = 1, Fᵢ ∈ [0, 100]
```

### Факторные блоки

| ID | Фактор | Базовый вес | Обоснование |
|----|--------|-------------|-------------|
| F1 | Институциональное качество | 0.25 | ████████████ | Сильнейший предиктор FDI (WGI, Freedom House) |
| F2 | Макроэкономическая стабильность | 0.20 | ██████████ | GDP growth, инфляция, долг/ВВП (IMF WEO) |
| F3 | Открытость торговли и бизнеса | 0.18 | █████████ | Ease of Doing Business, trade/GDP (World Bank) |
| F4 | Энергетические ресурсы | 0.15 | ███████ | Oil rents, reserves, энергетический микс |
| F5 | Безопасность и стабильность | 0.12 | ██████ | ACLED conflict events, политическая стабильность |
| F6 | Человеческий капитал | 0.05 | ██ | HDI, грамотность, участие рынка труда (ILO) |
| F7 | Финансовая глубина | 0.05 | ██ | Кредит к ВВП, капитализация рынка (World Bank) |

> **Примечание:** Веса F1–F7 — стартовые (prior). Итоговые веса определяются коэффициентами панельной регрессии: `FDI_inflow ~ F1 + F2 + ... + F7 + country_FE + year_FE`

### Нормализация факторов
```python
# Min-Max нормализация в диапазон [0, 100]
F_normalized = (F_raw - F_min) / (F_max - F_min) * 100

# Инвертирование для негативных индикаторов
# (инфляция, conflict events, политический риск)
F_normalized_inv = 100 - F_normalized
```

---

## 4. ИСТОЧНИКИ ДАННЫХ

| Источник | Покрытие | Индикаторы | Доступ | Формат |
|----------|----------|------------|--------|--------|
| **World Bank WDI** | 1990–2024 | GDP, FDI, trade, financial depth | Free API | JSON/CSV |
| **IMF WEO** | 1980–2029 | Macro: инфляция, долг, текущий счёт | Free bulk | CSV/XLSX |
| **World Governance Indicators** | 1996–2023 | 6 governance dims | Free API | XLSX |
| **UNCTAD** | 2000–2023 | FDI flows & stock (target variable) | Free | CSV |
| **ACLED** | 2010–2024 | Conflict events, fatalities | Free (reg) | CSV |
| **ILO ILOSTAT** | 2000–2023 | Labour market, human capital | Free API | JSON |
| **Freedom House** | 1972–2024 | Political rights, civil liberties | Free | XLSX |

### API ключи и регистрации
- [ ] World Bank API — без ключа (`api.worldbank.org`)
- [ ] IMF WEO — без ключа (bulk download)
- [ ] ACLED — требует регистрацию на `acleddata.com` (бесплатно)
- [ ] ILO — без ключа (`ilostat.ilo.org/api`)
- [ ] Freedom House — ручная загрузка XLSX ежегодно

---

## 5. МЕТОДОЛОГИЯ

### 5.1 Панельная регрессия с фиксированными эффектами

```python
# Модель: FDI ~ факторы + country_FE + year_FE
# Библиотека: linearmodels (Python) или plm (R)

from linearmodels.panel import PanelOLS

model = PanelOLS(
    dependent=data['fdi_pct_gdp'],
    exog=data[['F1','F2','F3','F4','F5','F6','F7']],
    entity_effects=True,   # country fixed effects
    time_effects=True      # year fixed effects
)
result = model.fit(cov_type='clustered', cluster_entity=True)
```

**Цель:** Получить коэффициенты β₁–β₇, нормировать их в веса: `wᵢ = |βᵢ| / Σ|βᵢ|`

### 5.2 Анализ чувствительности методом Монте-Карло

```python
# 10 000 итераций с рандомными весами вблизи baseline
# Цель: оценить устойчивость рейтинга стран

import numpy as np

n_simulations = 10_000
results = []

for _ in range(n_simulations):
    # Случайные веса с шумом ±20% от базовых
    weights = baseline_weights * (1 + np.random.uniform(-0.2, 0.2, 7))
    weights = weights / weights.sum()  # нормируем в 1
    scores = data[factors].values @ weights
    results.append(scores)

# Bootstrap CI 95% для каждой страны
ci_lower = np.percentile(results, 2.5, axis=0)
ci_upper = np.percentile(results, 97.5, axis=0)
```

### 5.3 Бэктест

- Обучение модели на данных 2000–2018
- Прогноз FDI притоков 2019–2023
- Метрики: RMSE, MAE, Spearman rank correlation (рейтинги vs факт)
- Цель: Spearman ρ > 0.75

### 5.4 Обработка пропущенных данных

| Ситуация | Метод |
|----------|-------|
| Страна пропускает 1–2 года | Линейная интерполяция |
| Конфликтные страны (Сирия, Йемен, Ливия) | ACLED + экспертный prior |
| Систематические пропуски (>30%) | Исключить из регрессии, сохранить в дашборде с пометкой |

---

## 6. ДАШБОРД: 7 МОДУЛЕЙ

### Стек
```
Frontend:  Plotly Dash (Python) — MVP
           React + D3.js — финальная версия
Backend:   FastAPI
Database:  DuckDB (аналитика) + PostgreSQL (prod)
Hosting:   Render / Railway (бесплатный tier для MVP)
```

### Модули дашборда

#### M1: карточка страны
- Общий CICI score (0–100) с цветовой шкалой
- Breakdown по 7 факторам (радарная диаграмма)
- Динамика score за 10 лет (спарклайн)
- Позиция в рейтинге + изменение за год

#### M2: таблица сравнительного рейтинга
- Таблица всех 19 стран с сортировкой
- Цветовая тепловая карта по факторам
- Фильтр по субрегиону (Gulf / North Africa / Levant)
- Экспорт в CSV / PDF

#### M3: временной ряд — динамика
- Линейный график CICI для выбранных стран (мультиселект)
- Аннотации ключевых событий (Arab Spring 2011, COVID 2020, нефтяные шоки)
- Сравнение с притоком FDI (secondary axis)

#### M4: карта конфликтов и стабильности
- Интерактивная карта MENA (Plotly choropleth)
- Цвет = CICI score, размер пузыря = FDI объём
- Слой: ACLED conflict intensity (heatmap overlay)

#### M5: пользовательские веса
- 7 слайдеров для весов F1–F7 (реалтайм пересчёт)
- Кнопки пресетов: "Энергетический инвестор" / "Tech инвестор" / "Balanced"
- Instant рейтинг-пересчёт при изменении весов

#### M6: подробный разбор факторов
- Drill-down в любой фактор
- Исходные данные по каждому индикатору
- Источник, год обновления, ссылка

#### M7: методология и качество данных
- Описание модели
- Data coverage matrix (страна × индикатор)
- Confidence intervals по Monte Carlo
- Ссылки на все источники

---

## 7. ДОРОЖНАЯ КАРТА

### Фаза 1: Данные и модель (Недели 1–4)
- [ ] Написать data pipeline (ETL) для всех 7 источников
- [ ] Собрать панельный датасет 19 стран × 2000–2024
- [ ] Нормализация и обработка пропусков
- [ ] Базовый расчёт CICI с фиксированными весами

### Фаза 2: Регрессия и валидация (Недели 5–8)
- [ ] Панельная регрессия Fixed Effects (linearmodels)
- [ ] Обновление весов по коэффициентам
- [ ] Monte Carlo sensitivity analysis
- [ ] Backtesting 2019–2023
- [ ] Написание методологической секции (LaTeX/PDF)

### Фаза 3: MVP дашборда (недели 9–12)
- [ ] Dash приложение: M1 Scorecard + M2 Ranking + M4 Map
- [ ] M5 Custom Weights (слайдеры)
- [ ] Деплой на Render (публичный URL)
- [ ] README с описанием методологии

### Фаза 4: Полный продукт (Недели 13–14+)
- [ ] M3 Time Series + M6 Deep Dive + M7 Methodology
- [ ] Quarterly update pipeline (автоматизация через Airflow/cron)
- [ ] PDF-экспорт country brief (шаблон EIU-style)
- [ ] GitHub публикация + статья на Medium/Towards Data Science

### Ежеквартальные обновления после запуска
- Q1/Q3: обновление World Bank + IMF данных
- Q2/Q4: обновление Freedom House + WGI
- Реалтайм: ACLED (еженедельно через API)

---

## 8. СТРУКТУРА ПРОЕКТА

```
MENA-Investment-Index/
│
├── ТЗ — MENA Investment Index.md     ← этот файл
│
├── data/
│   ├── raw/                          # сырые данные из источников
│   │   ├── worldbank/
│   │   ├── imf/
│   │   ├── wgi/
│   │   ├── unctad/
│   │   ├── acled/
│   │   ├── ilo/
│   │   └── freedom_house/
│   ├── processed/                    # очищенные датасеты
│   └── final/                        # финальная панель для модели
│
├── src/
│   ├── etl/                          # пайплайны загрузки данных
│   │   ├── worldbank.py
│   │   ├── imf.py
│   │   ├── acled.py
│   │   └── ...
│   ├── model/                        # модель и регрессия
│   │   ├── normalize.py
│   │   ├── regression.py
│   │   ├── monte_carlo.py
│   │   └── backtest.py
│   └── dashboard/                    # Dash приложение
│       ├── app.py
│       ├── layouts/
│       └── callbacks/
│
├── notebooks/                        # Jupyter: исследование и EDA
│   ├── 01_data_exploration.ipynb
│   ├── 02_regression_analysis.ipynb
│   └── 03_dashboard_prototype.ipynb
│
├── reports/                          # финальные отчёты
│   └── methodology.pdf
│
├── requirements.txt
├── README.md
└── .env.example                      # шаблон переменных окружения
```

---

## 9. СТЕК ТЕХНОЛОГИЙ

| Слой | Инструмент | Назначение |
|------|-----------|------------|
| **Data** | `pandas`, `numpy` | Обработка данных |
| **API клиенты** | `wbgapi`, `requests` | World Bank, ACLED API |
| **Регрессия** | `linearmodels`, `statsmodels` | Panel FE regression |
| **Статистика** | `scipy`, `sklearn` | Monte Carlo, нормализация |
| **Визуализация** | `plotly`, `matplotlib` | Графики |
| **Dashboard** | `dash`, `dash-bootstrap-components` | MVP frontend |
| **База данных** | `duckdb` | Аналитические запросы |
| **Окружение** | `python-dotenv` | Переменные окружения |
| **Тесты** | `pytest` | Тестирование пайплайнов |
| **Деплой** | Render / Railway | Хостинг дашборда |

---

## СЛЕДУЮЩИЙ ШАГ

**Фаза 1, Задача 1:** Написать ETL-пайплайн для World Bank API — загрузить базовые индикаторы (GDP, FDI, trade) для всех 19 стран за 2000–2024 и сохранить в `data/raw/worldbank/`.

Индикаторы для старта:
- `NY.GDP.MKTP.CD` — GDP (current USD)
- `BX.KLT.DINV.WD.GD.ZS` — FDI net inflows (% of GDP)  
- `NE.TRD.GNFS.ZS` — Trade (% of GDP)
- `FP.CPI.TOTL.ZG` — Inflation (CPI)
- `GC.DOD.TOTL.GD.ZS` — Central government debt (% of GDP)

---

*Версия: 1.0 | Дата: 2026-05-15 | Автор: MENA CICI Project*
