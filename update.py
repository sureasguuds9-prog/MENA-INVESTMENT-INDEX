"""
Quarterly Update Pipeline — автоматическое обновление данных и модели.

Запуск вручную:
    python update.py                 # полное обновление
    python update.py --etl-only      # только данные
    python update.py --model-only    # только пересчёт модели

Автоматизация (cron):
    # Каждый квартал — 1-го числа 1, 4, 7, 10 месяца в 03:00
    0 3 1 1,4,7,10 * cd ~/Desktop/MENA-Investment-Index && python update.py >> logs/update.log 2>&1
"""
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / f"update_{datetime.now().strftime('%Y%m')}.log"),
    ],
)
log = logging.getLogger(__name__)


# Какие источники обновляем в каком квартале
QUARTERLY_SCHEDULE: dict[str, list[str]] = {
    "Q1": ["wb", "imf", "acled"],           # январь — World Bank + IMF + ACLED
    "Q2": ["wb", "wgi", "acled"],           # апрель — WB + WGI + ACLED
    "Q3": ["wb", "imf", "acled"],           # июль — WB + IMF + ACLED
    "Q4": ["wb", "wgi", "acled"],           # октябрь — WB + WGI + ACLED (Freedom House вручную)
}


def get_current_quarter() -> str:
    month = datetime.now().month
    return f"Q{(month - 1) // 3 + 1}"


def run_etl(sources: list[str]) -> dict[str, bool]:
    import importlib
    results = {}
    for src in sources:
        module_map = {
            "wb":    "src.etl.worldbank",
            "imf":   "src.etl.imf",
            "wgi":   "src.etl.wgi",
            "acled": "src.etl.acled",
        }
        module_path = module_map.get(src)
        if not module_path:
            continue
        try:
            log.info(f"  ▶ ETL: {src}")
            m = importlib.import_module(module_path)
            m.run()
            results[src] = True
            log.info(f"  ✅ {src} — OK")
        except Exception as e:
            results[src] = False
            log.error(f"  ❌ {src} — FAIL: {e}")
    return results


def run_model() -> dict[str, bool]:
    import importlib
    steps = [
        ("panel", "src.model.build_panel"),
        ("reg",   "src.model.regression"),
        ("cici",  "src.model.cici"),
        ("mc",    "src.model.monte_carlo"),
        ("bt",    "src.model.backtest"),
    ]
    results = {}
    for name, path in steps:
        try:
            log.info(f"  ▶ Model: {name}")
            m = importlib.import_module(path)
            m.run()
            results[name] = True
            log.info(f"  ✅ {name} — OK")
        except Exception as e:
            results[name] = False
            log.error(f"  ❌ {name} — FAIL: {e}")
    return results


def write_update_manifest(etl_results: dict, model_results: dict) -> None:
    """Сохраняет лог последнего обновления — дашборд покажет дату."""
    from src.config import DATA_FINAL
    import json

    manifest = {
        "updated_at": datetime.now().isoformat(),
        "quarter": get_current_quarter(),
        "etl": etl_results,
        "model": model_results,
        "success": all(etl_results.values()) and all(model_results.values()),
    }
    path = DATA_FINAL / "last_update.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"  📄 Манифест обновления: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MENA Investment Index — Quarterly Update")
    parser.add_argument("--etl-only",   action="store_true", help="Только данные")
    parser.add_argument("--model-only", action="store_true", help="Только пересчёт модели")
    parser.add_argument("--sources",    nargs="+", help="Конкретные источники (wb imf wgi acled)")
    args = parser.parse_args()

    quarter = get_current_quarter()
    start = time.time()

    log.info("=" * 55)
    log.info(f"  MENA Investment Index — Quarterly Update")
    log.info(f"  Квартал: {quarter} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log.info("=" * 55)

    etl_results: dict[str, bool] = {}
    model_results: dict[str, bool] = {}

    if not args.model_only:
        sources = args.sources or QUARTERLY_SCHEDULE.get(quarter, ["wb", "acled"])
        log.info(f"\n📥 ETL — обновляю: {', '.join(sources)}")
        etl_results = run_etl(sources)

    if not args.etl_only:
        log.info("\n⚙️  Пересчитываю модель...")
        model_results = run_model()

    write_update_manifest(etl_results, model_results)

    elapsed = time.time() - start
    total_ok  = sum(etl_results.values()) + sum(model_results.values())
    total_all = len(etl_results) + len(model_results)

    log.info(f"\n{'=' * 55}")
    log.info(f"  Готово за {elapsed:.0f}с — {total_ok}/{total_all} шагов успешно")
    if total_ok < total_all:
        log.warning("  ⚠️  Есть ошибки — проверь logs/")
        sys.exit(1)
    else:
        log.info("  🎉 Всё ОК")


if __name__ == "__main__":
    main()
