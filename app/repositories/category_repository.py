from typing import List, Optional
from app.models.category import Category
from app.repositories.base import BaseRepository
from app.extensions import db


class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)

    def get_by_type(self, category_type: str) -> List[Category]:
        return db.session.scalars(
            db.select(Category).where(Category.type == category_type)
        ).all()

    def get_by_name(self, name: str) -> Optional[Category]:
        return db.session.scalars(
            db.select(Category).where(Category.name == name)
        ).first()
