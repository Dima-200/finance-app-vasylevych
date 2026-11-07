from app.repositories.budget_repository import BudgetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.analytics_strategy import (
    AnalyticsStrategy,
    CategoryBreakdownStrategy,
    MonthlySummaryStrategy,
)


class AnalyticsStrategyFactory:
    """Проста фабрика стратегій аналітики (Simple Factory)."""

    SUMMARY = "summary"
    BREAKDOWN = "breakdown"

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        budget_repo: BudgetRepository,
    ) -> None:
        self._transaction_repo = transaction_repo
        self._budget_repo = budget_repo

    def create(self, kind: str) -> AnalyticsStrategy:
        if kind == self.SUMMARY:
            return MonthlySummaryStrategy(self._transaction_repo, self._budget_repo)
        if kind == self.BREAKDOWN:
            return CategoryBreakdownStrategy(self._transaction_repo)
        raise ValueError(f"Невідомий тип аналітики: {kind}")
