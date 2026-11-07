from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository


class AnalyticsStrategy(ABC):
    """Абстрактна стратегія аналітики (патерн Strategy)."""

    @abstractmethod
    def calculate(self, year: int, month: int) -> Dict[str, Any]:
        pass


class MonthlySummaryStrategy(AnalyticsStrategy):
    """Стратегія підсумків за місяць."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
    ):
        self.transaction_repo = transaction_repo
        self.budget_repo = budget_repo

    def calculate(self, year: int, month: int) -> Dict[str, Any]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        end = date.fromordinal(end.toordinal() - 1)

        income = self.transaction_repo.sum_by_type_and_period("income", start, end)
        expense = self.transaction_repo.sum_by_type_and_period("expense", start, end)
        balance = income - expense

        budget = self.budget_repo.get_by_year_month(year, month)
        limit = Decimal(budget.limit_amount) if budget else Decimal("0")
        remaining = limit - expense if budget else None

        return {
            "income": float(income),
            "expense": float(expense),
            "balance": float(balance),
            "budget_limit": float(limit) if budget else None,
            "budget_remaining": float(remaining) if remaining is not None else None,
            "is_over_budget": remaining is not None and remaining < 0,
        }


class CategoryBreakdownStrategy(AnalyticsStrategy):
    """Стратегія розбивки по категоріях (для діаграм)."""

    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo

    def calculate(self, year: int, month: int) -> Dict[str, Any]:
        data = self.transaction_repo.sum_by_category_and_month(year, month)
        labels = [item[0] for item in data]
        values = [item[1] for item in data]
        colors = [item[2] for item in data]
        return {
            "labels": labels,
            "values": values,
            "colors": colors,
        }


class AnalyticsContext:
    """Контекст для застосування стратегії."""

    def __init__(self, strategy: AnalyticsStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: AnalyticsStrategy) -> None:
        self._strategy = strategy

    def execute(self, year: int, month: int) -> Dict[str, Any]:
        return self._strategy.calculate(year, month)
