from typing import Optional

from flask import Flask
from app.extensions import db
import os


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, '..', 'finance.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    if test_config:
        # має застосовуватися до db.init_app, інакше engine створиться зі старим URI
        app.config.update(test_config)

    db.init_app(app)

    from app.controllers.main import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _seed_default_categories()

    return app


def _seed_default_categories():
    from app.models.category import Category
    from app.extensions import db

    if Category.query.count() == 0:
        defaults = [
            ("Зарплата", "income", "#28a745"),
            ("Підробіток", "income", "#20c997"),
            ("Подарунки", "income", "#17a2b8"),
            ("Продукти", "expense", "#dc3545"),
            ("Транспорт", "expense", "#fd7e14"),
            ("Житло", "expense", "#6f42c1"),
            ("Розваги", "expense", "#e83e8c"),
            ("Здоров'я", "expense", "#007bff"),
            ("Інше", "expense", "#6c757d"),
        ]
        for name, type_, color in defaults:
            db.session.add(Category(name=name, type=type_, color=color))
        db.session.commit()
