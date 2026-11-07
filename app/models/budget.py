from datetime import datetime
from app.extensions import db


class Budget(db.Model):
    """Клас місячного бюджету."""

    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    limit_amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("year", "month", name="uq_budget_year_month"),
    )

    def __repr__(self) -> str:
        return f"<Budget {self.year}-{self.month}: {self.limit_amount}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "year": self.year,
            "month": self.month,
            "limit_amount": float(self.limit_amount),
        }
