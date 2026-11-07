from datetime import date
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import func, extract
from app.models.transaction import Transaction
from app.models.category import Category
from app.repositories.base import BaseRepository
from app.extensions import db


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    def get_by_period(self, start: date, end: date) -> List[Transaction]:
        return db.session.scalars(
            db.select(Transaction)
            .where(Transaction.date >= start, Transaction.date <= end)
            .order_by(Transaction.date.desc())
        ).all()

    def get_by_month(self, year: int, month: int) -> List[Transaction]:
        return db.session.scalars(
            db.select(Transaction)
            .where(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .order_by(Transaction.date.desc())
        ).all()

    def get_all_ordered(self) -> List[Transaction]:
        return db.session.scalars(
            db.select(Transaction).order_by(Transaction.date.desc())
        ).all()

    def sum_by_type_and_period(
        self, category_type: str, start: date, end: date
    ) -> Decimal:
        result = db.session.scalar(
            db.select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category)
            .where(
                Category.type == category_type,
                Transaction.date >= start,
                Transaction.date <= end,
            )
        )
        return Decimal(result or 0)

    def sum_by_type_all(self, category_type: str) -> Decimal:
        result = db.session.scalar(
            db.select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Category)
            .where(Category.type == category_type)
        )
        return Decimal(result or 0)

    def sum_by_category_and_month(self, year: int, month: int) -> List[tuple]:
        rows = db.session.execute(
            db.select(
                Category.name,
                func.sum(Transaction.amount).label("total"),
                Category.color,
            )
            .join(Category)
            .where(
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .group_by(Category.id)
        ).all()
        return [(r[0], float(r[1]), r[2]) for r in rows]

    def sum_by_category_all(self) -> List[tuple]:
        rows = db.session.execute(
            db.select(
                Category.name,
                func.sum(Transaction.amount).label("total"),
                Category.color,
            )
            .join(Category)
            .group_by(Category.id)
        ).all()
        return [(r[0], float(r[1]), r[2]) for r in rows]
