from app import db
from datetime import datetime
from flask_login import UserMixin
import pytz


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.now(pytz.timezone('Asia/Tokyo')))
    task_streak = db.Column(db.Integer, nullable=False, default=0)
    last_task_date = db.Column(db.DateTime)


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    hp = db.Column(db.Integer, nullable=False, default=100)
    max_hp = db.Column(db.Integer, nullable=False, default=100)
    xp = db.Column(db.Integer, nullable=False, default=0)
    next_xp = db.Column(db.Integer, nullable=False, default=100)
    status = db.Column(db.String(20), nullable=False, default='alive')
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.now(pytz.timezone('Asia/Tokyo')))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    limit = db.Column(db.DateTime, nullable=True, default=None)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.now(pytz.timezone('Asia/Tokyo')))
