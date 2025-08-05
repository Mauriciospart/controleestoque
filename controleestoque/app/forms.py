from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    min_quantity = IntegerField('Minimum Quantity', validators=[DataRequired()])
    periodicity = IntegerField('Periodicity (days)', validators=[DataRequired()])
    submit = SubmitField('Submit')

from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import Employee, Product

class EmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    submit = SubmitField('Submit')

def get_employees():
    return Employee.query.all()

def get_products():
    return Product.query.all()

from wtforms.validators import Email, EqualTo

class RequestForm(FlaskForm):
    employee = QuerySelectField('Employee', query_factory=get_employees, get_label='name', allow_blank=False)
    product = QuerySelectField('Product', query_factory=get_products, get_label='name', allow_blank=False)
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
