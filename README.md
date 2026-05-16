# MENA Investment Climate Index

Composite Investment Climate Index (CICI) для 19 стран MENA.
Панельная регрессия + Monte Carlo + интерактивный дашборд.

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить credentials (только для ACLED)
cp .env.example .env
# Отредактируй .env — добавь ACLED_EMAIL и ACLED_KEY

# 3. Запустить все ETL пайплайны
python run_all.py

# Или только World Bank + WGI (без регистраций)
python run_all.py --only wb wgi

# Пропустить ACLED если нет credentials
python run_all.py --skip acled
```

## Структура проекта

```
data/raw/          — сырые данные из источников
data/processed/    — очищенные данные
data/final/        — финальная панель для модели
src/etl/           — ETL пайплайны
src/model/         — регрессия и расчёт CICI
src/dashboard/     — Dash приложение
notebooks/         — исследовательский анализ
```

## Источники данных

| Источник | Регистрация | Статус |
|----------|------------|--------|
| World Bank WDI | Не нужна | ✅ Готово |
| IMF WEO | Не нужна | ✅ Готово |
| World Governance Indicators | Не нужна | ✅ Готово |
| ACLED | [Бесплатная](https://developer.acleddata.com/) | ⚙️ Нужен API key |

## Фазы разработки

- [x] **Фаза 1:** ETL пайплайны (текущая)
- [ ] **Фаза 2:** Панельная регрессия + веса факторов
- [ ] **Фаза 3:** MVP Dashboard (Scorecard, Ranking, Map)
- [ ] **Фаза 4:** Полный продукт + автоматизация
