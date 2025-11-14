from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from flask import current_app
from datetime import datetime, timedelta, timezone
import re

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='Requisitante')
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', password):
            raise ValueError('Password must contain at least one number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Password must contain at least one special character.')

        password_history = PasswordHistory.query.filter_by(user_id=self.id).order_by(PasswordHistory.timestamp.desc()).limit(3).all()
        for old_password in password_history:
            if check_password_hash(old_password.password_hash, password):
                raise ValueError('You cannot reuse one of your last 3 passwords.')

        # Add the old password to the history
        if self.password_hash:
            password_history = PasswordHistory(user_id=self.id, password_hash=self.password_hash)
            db.session.add(password_history)
            # Keep only the last 3 passwords in the history
            passwords_to_keep = PasswordHistory.query.filter_by(user_id=self.id).order_by(PasswordHistory.timestamp.desc()).limit(3).all()
            if len(passwords_to_keep) == 3:
                passwords_to_delete = PasswordHistory.query.filter_by(user_id=self.id).order_by(PasswordHistory.timestamp.asc()).first()
                db.session.delete(passwords_to_delete)

        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.now(timezone.utc)

    def is_requisitante(self):
        return self.role == 'Requisitante'

    def is_aprovador(self):
        return self.role == 'Aprovador'

    def is_administrador(self):
        return self.role == 'Administrador'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(500))
    quantity = db.Column(db.Integer)
    min_quantity = db.Column(db.Integer)
    periodicity = db.Column(db.Integer)
    attachment_filename = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return '<Product {}>'.format(self.name)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    company = db.Column(db.String(140))

    def __repr__(self):
        return '<Employee {}>'.format(self.name)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quantity = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
    approved = db.Column(db.Boolean, default=False)

    employee = db.relationship('Employee', backref='requests')
    product = db.relationship('Product', backref='requests')
    user = db.relationship('User', backref='requests')

    def __repr__(self):
        return '<Request {}>'.format(self.id)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())

    user = db.relationship('User', backref='logs')

    def __repr__(self):
        return '<Log {}>'.format(self.action)

class PasswordHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    password_hash = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='password_history')

    def __repr__(self):
        return f'<PasswordHistory {self.user_id} {self.timestamp}>'
