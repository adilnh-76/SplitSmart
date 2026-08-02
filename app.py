"""
app.py
------
SplitSmart — Flask application entry point.
"""

import os
import random
import string

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from models import db, Group, Participant, Expense
from algorithm import compute_balances, simplify_debts

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "splitsmart-dev-secret-key")

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    if os.environ.get("VERCEL"):
        db_url = "sqlite:////tmp/splitsmart.db"
    else:
        db_url = "sqlite:///splitsmart.db"

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def generate_code(length: int = 6) -> str:
    """Generate a unique alphanumeric group code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=length))
        if not Group.query.filter_by(code=code).first():
            return code


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Landing page — create or join a group."""
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create_group():
    """Handle new-group creation form."""
    group_name = request.form.get("group_name", "").strip()
    participants_raw = request.form.get("participants", "").strip()

    if not group_name:
        flash("Group name is required.", "error")
        return redirect(url_for("index"))

    names = [n.strip() for n in participants_raw.split(",") if n.strip()]
    if len(names) < 2:
        flash("Please add at least 2 participants (comma-separated).", "error")
        return redirect(url_for("index"))

    # Deduplicate while preserving order
    seen = set()
    unique_names = []
    for n in names:
        if n.lower() not in seen:
            seen.add(n.lower())
            unique_names.append(n)

    group = Group(name=group_name, code=generate_code())
    db.session.add(group)
    db.session.flush()  # get group.id before commit

    for name in unique_names:
        db.session.add(Participant(group_id=group.id, name=name))

    db.session.commit()
    flash(f'Group "{group_name}" created! Share code <strong>{group.code}</strong> with your friends.', "success")
    return redirect(url_for("group_dashboard", code=group.code))


@app.route("/join", methods=["POST"])
def join_group():
    """Redirect to group dashboard using a shared code."""
    code = request.form.get("code", "").strip().upper()
    if not code:
        flash("Please enter a group code.", "error")
        return redirect(url_for("index"))
    group = Group.query.filter_by(code=code).first()
    if not group:
        flash(f'No group found with code "{code}".', "error")
        return redirect(url_for("index"))
    return redirect(url_for("group_dashboard", code=code))


@app.route("/g/<code>")
def group_dashboard(code):
    """Main group dashboard: ledger + settle-up summary."""
    group = Group.query.filter_by(code=code.upper()).first_or_404()
    participants = Participant.query.filter_by(group_id=group.id).all()
    expenses = (
        Expense.query.filter_by(group_id=group.id)
        .order_by(Expense.created_at.desc())
        .all()
    )

    balances = compute_balances(expenses, participants)
    transactions = simplify_debts(balances)

    # Total group spend
    total_spent = round(sum(e.amount for e in expenses), 2)

    # Calculate max absolute balance for rendering percentage bars safely
    max_balance = max([abs(b) for b in balances.values()] + [1.0])

    return render_template(
        "dashboard.html",
        group=group,
        participants=participants,
        expenses=expenses,
        balances=balances,
        transactions=transactions,
        total_spent=total_spent,
        max_balance=max_balance,
    )


@app.route("/g/<code>/add-expense", methods=["POST"])
def add_expense(code):
    """Add a new expense to a group."""
    group = Group.query.filter_by(code=code.upper()).first_or_404()
    participants = Participant.query.filter_by(group_id=group.id).all()
    participant_names = {p.name for p in participants}

    description = request.form.get("description", "").strip()
    amount_str = request.form.get("amount", "").strip()
    paid_by = request.form.get("paid_by", "").strip()
    split_type = request.form.get("split_type", "equal")
    custom_split = request.form.getlist("split_among")

    # Validation
    errors = []
    if not description:
        errors.append("Description is required.")
    if not amount_str:
        errors.append("Amount is required.")
    else:
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

    if paid_by not in participant_names:
        errors.append("Payer must be a participant in this group.")

    if split_type == "equal":
        split_among = ",".join(p.name for p in participants)
    else:
        valid_custom = [n for n in custom_split if n in participant_names]
        if not valid_custom:
            errors.append("Select at least one person for custom split.")
        split_among = ",".join(valid_custom)

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("group_dashboard", code=code))

    expense = Expense(
        group_id=group.id,
        description=description,
        amount=round(float(amount_str), 2),
        paid_by=paid_by,
        split_among=split_among,
    )
    db.session.add(expense)
    db.session.commit()
    flash(f'Expense "{description}" of ₹{expense.amount:.2f} added!', "success")
    return redirect(url_for("group_dashboard", code=code))


@app.route("/g/<code>/delete-expense/<int:expense_id>", methods=["POST"])
def delete_expense(code, expense_id):
    """Delete an expense from a group."""
    group = Group.query.filter_by(code=code.upper()).first_or_404()
    expense = Expense.query.filter_by(id=expense_id, group_id=group.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("group_dashboard", code=code))


# ─── Init DB & Run ────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
