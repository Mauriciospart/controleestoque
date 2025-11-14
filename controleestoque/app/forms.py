from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, FileField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo
from app.models import User, PasswordHistory, Employee, Product
from werkzeug.security import check_password_hash
import re

def password_complexity_validator(form, field):
    user = None
    if hasattr(form, 'user'):
        user = form.user
    elif hasattr(form, 'email'):
        user = User.query.filter_by(email=form.email.data).first()

    if not user:
        user = User()

    try:
        user.set_password(field.data)
    except ValueError as e:
        raise ValidationError(str(e))

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
    attachment = FileField('Attachment (Optional)')
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
    password = PasswordField('Password', validators=[DataRequired(), password_complexity_validator])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

    def __init__(self, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        self.user = kwargs.get('user')

from wtforms import SelectField

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), password_complexity_validator])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('Requisitante', 'Requisitante'), ('Aprovador', 'Aprovador'), ('Administrador', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Create User')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = kwargs.get('user')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('Requisitante', 'Requisitante'), ('Aprovador', 'Aprovador'), ('Administrador', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Update User')
