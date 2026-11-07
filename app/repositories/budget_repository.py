from typing import Optional
from app.models.budget import Budget
from app.repositories.base import BaseRepository
from app.extensions import db


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self):
        super().__init__(Budget)

    def get_by_year_month(self, year: int, month: int) -> Optional[Budget]:
        return db.session.scalars(
            db.select(Budget).where(
                Budget.year == year,
                Budget.month == month,
            )
        ).first()
