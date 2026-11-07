# Вебзастосунок для обліку особистих фінансів

Курсова робота з дисципліни «Об’єктно орієнтоване програмування».

## Стек

- Python 3.11+
- Flask 3
- SQLAlchemy 2 (ORM)
- SQLite
- Bootstrap 5 + Chart.js
- pytest

## Архітектура

- **MVC** (Flask routes → controllers, Jinja templates → views, SQLAlchemy models)
- **Repository** + **Service Layer** (залежності передаються через конструктор — DIP)
- Патерни GoF:
  - **Strategy** — види аналітики (`AnalyticsStrategy`, `AnalyticsContext`)
  - **Observer** — сповіщення про перевищення бюджету (`BudgetSubject`, `BudgetObserver`)
  - **Facade** — `FinanceService` як єдина точка входу для контролерів
  - додатково: проста фабрика стратегій (`AnalyticsStrategyFactory`)

## Запуск

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Відкрити http://127.0.0.1:5000

## Тести

```bash
pytest tests/ -v --cov=app
```

## Структура

```
app/
  models/          # Entity-класи
  repositories/    # Repository pattern
  services/        # Бізнес-логіка, Strategy, Observer, фабрика
  controllers/     # MVC Controllers
  templates/       # Views
tests/
```
