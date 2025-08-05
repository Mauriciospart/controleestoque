from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from flask import current_app
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
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
    quantity = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
    approved = db.Column(db.Boolean, default=False)

    employee = db.relationship('Employee', backref='requests')
    product = db.relationship('Product', backref='requests')

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
