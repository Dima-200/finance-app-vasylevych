from datetime import datetime
from app.extensions import db


class Category(db.Model):
    """Клас категорії доходів/витрат (Entity)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(20), nullable=False)  # 'income' | 'expense'
    color = db.Column(db.String(7), default="#6c757d")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Category {self.name} ({self.type})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "color": self.color,
        }
