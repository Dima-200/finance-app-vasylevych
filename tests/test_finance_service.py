from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.services.analytics_factory import AnalyticsStrategyFactory
from app.services.analytics_strategy import AnalyticsContext
from app.services.events import BudgetExceededEvent, BudgetObserver
from app.services.finance_service import FinanceService


@pytest.fixture
def app():
    # конфігурація передається до db.init_app, тож тести працюють
    # з окремою БД у пам'яті і не зачіпають finance.db
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def service(app):
    return FinanceService()


class SpyObserver(BudgetObserver):
    """Тестовий спостерігач, що запам'ятовує події."""

    def __init__(self):
        self.events = []

    def update(self, event: BudgetExceededEvent) -> None:
        self.events.append(event)


# ---------- категорії ----------
def test_create_category(service):
    cat = service.create_category("Тест", "expense", "#ff0000")
    assert cat.name == "Тест"
    assert cat.type == "expense"


def test_create_category_duplicate_name(service):
    service.create_category("Дубль", "expense")
    with pytest.raises(ValueError):
        service.create_category("Дубль", "expense")


def test_create_category_wrong_type(service):
    with pytest.raises(ValueError):
        service.create_category("Невірний тип", "other")


def test_get_categories_by_type(service):
    income = service.get_categories("income")
    assert income and all(c.type == "income" for c in income)


# ---------- транзакції ----------
def test_add_transaction_and_summary(service):
    income_cat = service.create_category("Зарплата тест", "income")
    expense_cat = service.create_category("Їжа тест", "expense")

    service.add_transaction(Decimal("10000"), income_cat.id, "Зарплата")
    service.add_transaction(Decimal("2500"), expense_cat.id, "Продукти")

    today = date.today()
    summary = service.get_monthly_summary(today.year, today.month)

    assert summary["income"] == 10000.0
    assert summary["expense"] == 2500.0
    assert summary["balance"] == 7500.0


def test_add_transaction_rejects_non_positive_amount(service):
    cat = service.create_category("Нуль", "expense")
    with pytest.raises(ValueError):
        service.add_transaction(Decimal("0"), cat.id)


def test_add_transaction_unknown_category(service):
    with pytest.raises(ValueError):
        service.add_transaction(Decimal("10"), 999999)


def test_delete_transaction(service):
    cat = service.create_category("Для видалення", "expense")
    tx = service.add_transaction(Decimal("50"), cat.id)
    assert len(service.get_all_transactions()) == 1
    service.delete_transaction(tx.id)
    assert service.get_all_transactions() == []


def test_december_summary_uses_year_boundary(service):
    cat = service.create_category("Грудень", "income")
    service.add_transaction(Decimal("700"), cat.id, tx_date=date(2026, 12, 31))
    summary = service.get_monthly_summary(2026, 12)
    assert summary["income"] == 700.0


def test_all_time_summary(service):
    inc = service.create_category("Дохід всього", "income")
    exp = service.create_category("Витрата всього", "expense")
    service.add_transaction(Decimal("1000"), inc.id, tx_date=date(2026, 1, 10))
    service.add_transaction(Decimal("300"), exp.id, tx_date=date(2026, 2, 10))
    summary = service.get_all_time_summary()
    assert summary["balance"] == 700.0
    assert service.get_all_time_breakdown()["values"]


# ---------- бюджет ----------
def test_budget_over(service):
    expense_cat = service.create_category("Тест витрата", "expense")
    today = date.today()
    service.set_monthly_budget(today.year, today.month, Decimal("1000"))
    service.add_transaction(Decimal("1500"), expense_cat.id)

    summary = service.get_monthly_summary(today.year, today.month)
    assert summary["is_over_budget"] is True
    assert summary["budget_remaining"] == -500.0


def test_set_budget_twice_updates_existing(service):
    today = date.today()
    service.set_monthly_budget(today.year, today.month, Decimal("1000"))
    service.set_monthly_budget(today.year, today.month, Decimal("2000"))
    budget = service.get_budget(today.year, today.month)
    assert budget.limit_amount == Decimal("2000")


def test_negative_budget_rejected(service):
    with pytest.raises(ValueError):
        service.set_monthly_budget(2026, 11, Decimal("-1"))


# ---------- аналітика (Strategy + Factory) ----------
def test_category_breakdown(service):
    cat1 = service.create_category("А", "expense", "#111")
    cat2 = service.create_category("Б", "expense", "#222")
    service.add_transaction(Decimal("100"), cat1.id)
    service.add_transaction(Decimal("200"), cat2.id)

    today = date.today()
    breakdown = service.get_category_breakdown(today.year, today.month)
    assert len(breakdown["labels"]) == 2
    assert sum(breakdown["values"]) == 300.0


def test_factory_creates_strategies_and_context_switches(service):
    factory = AnalyticsStrategyFactory(service.transaction_repo, service.budget_repo)
    context = AnalyticsContext(factory.create(AnalyticsStrategyFactory.SUMMARY))
    today = date.today()
    assert "balance" in context.execute(today.year, today.month)

    context.set_strategy(factory.create(AnalyticsStrategyFactory.BREAKDOWN))
    assert "labels" in context.execute(today.year, today.month)


def test_factory_unknown_kind(service):
    factory = AnalyticsStrategyFactory(service.transaction_repo, service.budget_repo)
    with pytest.raises(ValueError):
        factory.create("unknown")


# ---------- Observer ----------
def test_observer_notified_when_budget_exceeded(service):
    spy = SpyObserver()
    service.attach_budget_observer(spy)
    cat = service.create_category("Observer витрата", "expense")
    today = date.today()
    service.set_monthly_budget(today.year, today.month, Decimal("1000"))

    service.add_transaction(Decimal("1500"), cat.id)

    assert len(spy.events) == 1
    assert spy.events[0].overspent == 500.0


def test_observer_not_notified_within_budget_or_for_income(service):
    spy = SpyObserver()
    service.attach_budget_observer(spy)
    exp = service.create_category("Observer ок", "expense")
    inc = service.create_category("Observer дохід", "income")
    today = date.today()
    service.set_monthly_budget(today.year, today.month, Decimal("1000"))

    service.add_transaction(Decimal("500"), exp.id)
    service.add_transaction(Decimal("5000"), inc.id)

    assert spy.events == []


def test_detached_observer_is_not_notified(service):
    spy = SpyObserver()
    service.attach_budget_observer(spy)
    service.detach_budget_observer(spy)
    cat = service.create_category("Observer detach", "expense")
    today = date.today()
    service.set_monthly_budget(today.year, today.month, Decimal("10"))
    service.add_transaction(Decimal("100"), cat.id)
    assert spy.events == []


# ---------- Dependency Injection ----------
class FakeCategoryRepo:
    """Підміна репозиторію без БД: доводить, що сервіс залежить від абстракції."""

    def __init__(self):
        self.items = {}
        self._next_id = 0

    def get_by_name(self, name):
        return next((c for c in self.items.values() if c.name == name), None)

    def get_by_id(self, id):
        return self.items.get(id)

    def add(self, category):
        self._next_id += 1
        category.id = self._next_id
        self.items[category.id] = category
        return category


def test_service_uses_injected_repository():
    repo = FakeCategoryRepo()
    svc = FinanceService(
        category_repo=repo, transaction_repo=object(), budget_repo=object()
    )
    cat = svc.create_category("Через DI", "expense")
    assert repo.get_by_id(cat.id) is cat


# ---------- контролери (HTTP) ----------
def test_index_page_available(app):
    response = app.test_client().get("/")
    assert response.status_code == 200


def test_add_transaction_via_http(app):
    client = app.test_client()
    response = client.post(
        "/transactions/add",
        data={"amount": "250", "category_id": "1", "description": "тест", "date": "2026-11-05"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Транзакцію додано успішно" in response.get_data(as_text=True)


def test_add_transaction_invalid_amount_via_http(app):
    response = app.test_client().post(
        "/transactions/add",
        data={"amount": "-5", "category_id": "1"},
        follow_redirects=True,
    )
    assert "Сума має бути додатною" in response.get_data(as_text=True)
