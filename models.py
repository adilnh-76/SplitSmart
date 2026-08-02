"""
models.py
---------
SQLAlchemy ORM models for SplitSmart.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

    participants = db.relationship("Participant", backref="group", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="group", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group {self.code}: {self.name}>"


class Participant(db.Model):
    __tablename__ = "participants"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f"<Participant {self.name}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.String(80), nullable=False)
    split_among = db.Column(db.Text, nullable=False)  # comma-separated participant names
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def split_list(self):
        return [n.strip() for n in self.split_among.split(",") if n.strip()]

    def __repr__(self):
        return f"<Expense '{self.description}' ₹{self.amount}>"
