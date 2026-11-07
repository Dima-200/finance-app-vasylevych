from datetime import date, datetime
from app.extensions import db


class Transaction(db.Model):
    """Клас транзакції (дохід або витрата)."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.amount} on {self.date}>"

    @property
    def is_income(self) -> bool:
        return self.category.type == "income"

    @property
    def is_expense(self) -> bool:
        return self.category.type == "expense"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": float(self.amount),
            "description": self.description,
            "date": self.date.isoformat(),
            "category": self.category.to_dict() if self.category else None,
        }
