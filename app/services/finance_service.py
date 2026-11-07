from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository
from app.services.analytics_factory import AnalyticsStrategyFactory
from app.services.analytics_strategy import AnalyticsContext
from app.services.events import (
    BudgetExceededEvent,
    BudgetObserver,
    BudgetSubject,
)


class FinanceService:
    """Сервісний шар (бізнес-логіка) і фасад (патерн Facade) над
    репозиторіями, стратегіями аналітики та сповіщеннями.

    Залежності передаються через конструктор (Dependency Inversion);
    якщо їх не вказано, використовуються репозиторії за замовчуванням.
    """

    def __init__(
        self,
        category_repo: Optional[CategoryRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
        budget_repo: Optional[BudgetRepository] = None,
        budget_subject: Optional[BudgetSubject] = None,
    ):
        self.category_repo = category_repo if category_repo is not None else CategoryRepository()
        self.transaction_repo = (
            transaction_repo if transaction_repo is not None else TransactionRepository()
        )
        self.budget_repo = budget_repo if budget_repo is not None else BudgetRepository()
        self._strategy_factory = AnalyticsStrategyFactory(
            self.transaction_repo, self.budget_repo
        )
        self._budget_subject = (
            budget_subject if budget_subject is not None else BudgetSubject()
        )

    # --- Observer ---
    def attach_budget_observer(self, observer: BudgetObserver) -> None:
        self._budget_subject.attach(observer)

    def detach_budget_observer(self, observer: BudgetObserver) -> None:
        self._budget_subject.detach(observer)

    def _notify_if_over_budget(self, year: int, month: int) -> None:
        summary = self.get_monthly_summary(year, month)
        if summary["is_over_budget"]:
            self._budget_subject.notify(
                BudgetExceededEvent(
                    year=year,
                    month=month,
                    limit=summary["budget_limit"],
                    spent=summary["expense"],
                )
            )

    # --- Categories ---
    def create_category(self, name: str, type_: str, color: str = "#6c757d") -> Category:
        if type_ not in ("income", "expense"):
            raise ValueError("Тип категорії має бути 'income' або 'expense'")
        existing = self.category_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Категорія '{name}' вже існує")
        cat = Category(name=name, type=type_, color=color)
        return self.category_repo.add(cat)

    def get_categories(self, type_: Optional[str] = None) -> List[Category]:
        if type_:
            return self.category_repo.get_by_type(type_)
        return self.category_repo.get_all()

    # --- Transactions ---
    def add_transaction(
        self,
        amount: Decimal,
        category_id: int,
        description: str = "",
        tx_date: Optional[date] = None,
    ) -> Transaction:
        if amount <= 0:
            raise ValueError("Сума має бути додатною")
        cat = self.category_repo.get_by_id(category_id)
        if not cat:
            raise ValueError("Категорію не знайдено")
        when = tx_date or date.today()
        tx = Transaction(
            amount=amount,
            category_id=category_id,
            description=description,
            date=when,
        )
        saved = self.transaction_repo.add(tx)
        if cat.type == "expense":
            self._notify_if_over_budget(when.year, when.month)
        return saved

    def get_transactions_for_month(self, year: int, month: int) -> List[Transaction]:
        return self.transaction_repo.get_by_month(year, month)

    def get_all_transactions(self) -> List[Transaction]:
        return self.transaction_repo.get_all_ordered()

    def delete_transaction(self, tx_id: int) -> None:
        tx = self.transaction_repo.get_by_id(tx_id)
        if tx:
            self.transaction_repo.delete(tx)

    # --- Budget ---
    def set_monthly_budget(self, year: int, month: int, limit: Decimal) -> Budget:
        if limit < 0:
            raise ValueError("Ліміт бюджету не може бути від'ємним")
        existing = self.budget_repo.get_by_year_month(year, month)
        if existing:
            existing.limit_amount = limit
            return self.budget_repo.update(existing)
        budget = Budget(year=year, month=month, limit_amount=limit)
        return self.budget_repo.add(budget)

    def get_budget(self, year: int, month: int) -> Optional[Budget]:
        return self.budget_repo.get_by_year_month(year, month)

    # --- Analytics ---
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        strategy = self._strategy_factory.create(AnalyticsStrategyFactory.SUMMARY)
        return AnalyticsContext(strategy).execute(year, month)

    def get_category_breakdown(self, year: int, month: int) -> Dict[str, Any]:
        strategy = self._strategy_factory.create(AnalyticsStrategyFactory.BREAKDOWN)
        return AnalyticsContext(strategy).execute(year, month)

    def get_all_time_summary(self) -> Dict[str, Any]:
        income = self.transaction_repo.sum_by_type_all("income")
        expense = self.transaction_repo.sum_by_type_all("expense")
        balance = income - expense
        return {
            "income": float(income),
            "expense": float(expense),
            "balance": float(balance),
            "budget_limit": None,
            "budget_remaining": None,
            "is_over_budget": False,
        }

    def get_all_time_breakdown(self) -> Dict[str, Any]:
        data = self.transaction_repo.sum_by_category_all()
        labels = [item[0] for item in data]
        values = [item[1] for item in data]
        colors = [item[2] for item in data]
        return {
            "labels": labels,
            "values": values,
            "colors": colors,
        }
