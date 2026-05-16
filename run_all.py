"""
MENA Investment Index — главный pipeline runner.
Запускает ETL (Фаза 1) и модель (Фаза 2) в правильном порядке.

Использование:
    python run_all.py                        # запустить всё
    python run_all.py --only wb wgi          # только ETL
    python run_all.py --only model           # только модель
    python run_all.py --skip acled           # пропустить ACLED
    python run_all.py --phase etl            # только Фаза 1 (ETL)
    python run_all.py --phase model          # только Фаза 2 (модель)
"""
import argparse
import sys
import time
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))


PIPELINES: dict[str, dict] = {
    # Фаза 1: ETL
    "wb":    {"name": "World Bank WDI",              "module": "src.etl.worldbank",    "phase": "etl"},
    "imf":   {"name": "IMF WEO",                     "module": "src.etl.imf",          "phase": "etl"},
    "wgi":   {"name": "World Governance Indicators", "module": "src.etl.wgi",          "phase": "etl"},
    "acled": {"name": "ACLED Conflict Data",         "module": "src.etl.acled",        "phase": "etl"},
    # Фаза 2: Model
    "panel": {"name": "Build Panel (факторы)",       "module": "src.model.build_panel","phase": "model"},
    "reg":   {"name": "Panel Regression (веса)",     "module": "src.model.regression", "phase": "model"},
    "cici":  {"name": "Compute CICI (рейтинг)",      "module": "src.model.cici",       "phase": "model"},
    "mc":    {"name": "Monte Carlo (sensitivity)",   "module": "src.model.monte_carlo","phase": "model"},
    "bt":    {"name": "Backtest (валидация)",         "module": "src.model.backtest",   "phase": "model"},
}

PHASE_ORDER = {
    "etl":   ["wb", "imf", "wgi", "acled"],
    "model": ["panel", "reg", "cici", "mc", "bt"],
}


def run_pipeline(key: str, info: dict) -> bool:
    """Запускает один ETL пайплайн. Возвращает True если успешно."""
    print(f"\n{'='*60}")
    print(f"  [{key.upper()}] {info['name']}")
    print(f"{'='*60}")

    start = time.time()
    try:
        import importlib
        module = importlib.import_module(info["module"])
        module.run()
        elapsed = time.time() - start
        print(f"\n  ⏱️  Время: {elapsed:.1f}с")
        return True
    except Exception as e:
        print(f"\n  ❌ Ошибка в {info['name']}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="MENA Investment Index — Pipeline")
    parser.add_argument(
        "--only", nargs="+", choices=list(PIPELINES.keys()),
        help="Запустить только указанные шаги",
    )
    parser.add_argument(
        "--skip", nargs="+", choices=list(PIPELINES.keys()), default=[],
        help="Пропустить указанные шаги",
    )
    parser.add_argument(
        "--phase", choices=["etl", "model", "all"], default="all",
        help="Запустить только одну фазу (etl / model / all)",
    )
    args = parser.parse_args()

    if args.only:
        to_run = args.only
    elif args.phase != "all":
        to_run = PHASE_ORDER[args.phase]
    else:
        to_run = list(PIPELINES.keys())

    to_run = [k for k in to_run if k not in (args.skip or [])]

    print("\n🚀 MENA Investment Index — ETL Pipeline")
    print(f"   Будет запущено: {', '.join(to_run)}\n")

    results: dict[str, bool] = {}
    total_start = time.time()

    for key in to_run:
        results[key] = run_pipeline(key, PIPELINES[key])

    total_elapsed = time.time() - total_start

    print(f"\n{'='*60}")
    print(f"  ИТОГ  (всего {total_elapsed:.0f}с)")
    print(f"{'='*60}")
    for key, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status}  [{key.upper()}] {PIPELINES[key]['name']}")

    failed = [k for k, ok in results.items() if not ok]
    if failed:
        print(f"\n  ⚠️  Упали: {', '.join(failed)}")
        print("  Проверь логи выше и наличие credentials в .env")
        sys.exit(1)
    else:
        print(f"\n  🎉 Все пайплайны выполнены успешно!")
        print(f"  Данные в: data/raw/")


if __name__ == "__main__":
    main()
