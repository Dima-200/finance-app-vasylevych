from datetime import date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.events import LoggingBudgetObserver, MessageBudgetObserver
from app.services.finance_service import FinanceService

main_bp = Blueprint("main", __name__)
service = FinanceService()
budget_messages = MessageBudgetObserver()
service.attach_budget_observer(budget_messages)
service.attach_budget_observer(LoggingBudgetObserver())

MONTH_NAMES = {
    1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
    5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
    9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень",
}


def _get_selected_period():
    """Повертає (year, month, is_all). is_all=True означає статистику за весь час."""
    today = date.today()
    period = request.args.get("period", "month")  

    if period == "all":
        return today.year, today.month, True

    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        if month < 1 or month > 12:
            month = today.month
        if year < 2020 or year > 2035:
            year = today.year
    except (TypeError, ValueError):
        year, month = today.year, today.month
    return year, month, False


@main_bp.route("/")
def index():
    year, month, is_all = _get_selected_period()

    if is_all:
        summary = service.get_all_time_summary()
        breakdown = service.get_all_time_breakdown()
        transactions = service.get_all_transactions()
        budget = None
        period_label = "Весь час"
    else:
        summary = service.get_monthly_summary(year, month)
        breakdown = service.get_category_breakdown(year, month)
        transactions = service.get_transactions_for_month(year, month)
        budget = service.get_budget(year, month)
        period_label = f"{MONTH_NAMES.get(month, month)} {year}"

    categories = service.get_categories()
    current_year = date.today().year
    years = list(range(current_year - 3, current_year + 2))

    return render_template(
        "index.html",
        summary=summary,
        breakdown=breakdown,
        transactions=transactions,
        categories=categories,
        budget=budget,
        year=year,
        month=month,
        is_all=is_all,
        period_label=period_label,
        month_name=MONTH_NAMES.get(month, str(month)),
        years=years,
        months=MONTH_NAMES,
    )


@main_bp.route("/transactions/add", methods=["POST"])
def add_transaction():
    year, month, is_all = _get_selected_period()
    try:
        amount = Decimal(request.form.get("amount", "0"))
        category_id = int(request.form.get("category_id"))
        description = request.form.get("description", "")
        tx_date_str = request.form.get("date")
        tx_date = date.fromisoformat(tx_date_str) if tx_date_str else date.today()
        service.add_transaction(amount, category_id, description, tx_date)
        flash("Транзакцію додано успішно", "success")
        for message in budget_messages.pop_messages():
            flash(message, "warning")
        year, month = tx_date.year, tx_date.month
        is_all = False
    except Exception as e:
        flash(str(e), "danger")

    if is_all:
        return redirect(url_for("main.index", period="all"))
    return redirect(url_for("main.index", year=year, month=month))


@main_bp.route("/transactions/<int:tx_id>/delete", methods=["POST"])
def delete_transaction(tx_id: int):
    year, month, is_all = _get_selected_period()
    try:
        if request.form.get("period") == "all":
            is_all = True
        else:
            year = int(request.form.get("year", year))
            month = int(request.form.get("month", month))
            is_all = False
    except (TypeError, ValueError):
        pass

    service.delete_transaction(tx_id)
    flash("Транзакцію видалено", "info")

    if is_all:
        return redirect(url_for("main.index", period="all"))
    return redirect(url_for("main.index", year=year, month=month))


@main_bp.route("/budget/set", methods=["POST"])
def set_budget():
    try:
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        limit = Decimal(request.form.get("limit", "0"))
        service.set_monthly_budget(year, month, limit)
        flash("Бюджет встановлено", "success")
    except Exception as e:
        flash(str(e), "danger")
        year, month, _ = _get_selected_period()
    return redirect(url_for("main.index", year=year, month=month))
