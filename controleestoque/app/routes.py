from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_from_directory
from app.forms import LoginForm, ProductForm, EmployeeForm, RequestForm, PasswordResetRequestForm, ResetPasswordForm, UserForm, EditUserForm
from flask_login import current_user, login_user, logout_user, login_required
from app.email import send_password_reset_email, send_email
from app.models import User, Product, Employee, Request, Log
from markdown import markdown

from datetime import datetime, timedelta, timezone

@app.route('/')
@app.route('/index')
@login_required
def index():
    period = request.args.get('period', 'all')

    if period == '7days':
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
    elif period == '30days':
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    elif period == '90days':
        start_date = datetime.now(timezone.utc) - timedelta(days=90)
    else:
        start_date = None

    if start_date:
        last_requests_query = Request.query.filter(Request.timestamp >= start_date)
    else:
        last_requests_query = Request.query

    low_stock_products = Product.query.filter(Product.quantity <= Product.min_quantity).all()
    last_requests = last_requests_query.order_by(Request.timestamp.desc()).limit(5).all()

    return render_template('index.html', title='Home', low_stock_products=low_stock_products, last_requests=last_requests, period=period)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.is_locked:
                flash('Your account is locked. Please contact an administrator.')
                return redirect(url_for('login'))
            if not user.check_password(form.password.data):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 3:
                    user.is_locked = True
                db.session.commit()
                flash('Invalid username or password')
                return redirect(url_for('login'))
            user.failed_login_attempts = 0
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            if user.password_changed_at + timedelta(days=45) < datetime.now(timezone.utc):
                return redirect(url_for('force_password_change'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    if search:
        products = Product.query.filter(Product.name.like(f'%{search}%')).paginate(page=page, per_page=10)
    else:
        products = Product.query.paginate(page=page, per_page=10)
    return render_template('products.html', products=products, search=search)

from app.log import add_log

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('products'))
    form = ProductForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            form.attachment.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        product = Product(name=form.name.data,
                          description=form.description.data,
                          quantity=form.quantity.data,
                          min_quantity=form.min_quantity.data,
                          periodicity=form.periodicity.data,
                          attachment_filename=filename)
        db.session.add(product)
        db.session.commit()
        add_log(f'Added product {product.name}')
        flash('Product added successfully.')
        return redirect(url_for('products'))
    return render_template('add_product.html', form=form)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('products'))
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.quantity = form.quantity.data
        product.min_quantity = form.min_quantity.data
        product.periodicity = form.periodicity.data
        db.session.commit()
        add_log(f'Edited product {product.name}')
        flash('Product updated successfully.')
        return redirect(url_for('products'))
    return render_template('edit_product.html', form=form)

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('products'))
    product = Product.query.get_or_404(id)
    add_log(f'Deleted product {product.name}')
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('products'))

@app.route('/employees')
@login_required
def employees():
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.paginate(page=page, per_page=10)
    return render_template('employees.html', employees=employees)

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('employees'))
    form = EmployeeForm()
    if form.validate_on_submit():
        employee = Employee(name=form.name.data, company=form.company.data)
        db.session.add(employee)
        db.session.commit()
        add_log(f'Added employee {employee.name}')
        flash('Employee added successfully.')
        return redirect(url_for('employees'))
    return render_template('add_employee.html', form=form)

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('employees'))
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        employee.name = form.name.data
        employee.company = form.company.data
        db.session.commit()
        add_log(f'Edited employee {employee.name}')
        flash('Employee updated successfully.')
        return redirect(url_for('employees'))
    return render_template('edit_employee.html', form=form)

@app.route('/delete_employee/<int:id>')
@login_required
def delete_employee(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('employees'))
    employee = Employee.query.get_or_404(id)
    add_log(f'Deleted employee {employee.name}')
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully.')
    return redirect(url_for('employees'))

@app.route('/requests')
@login_required
def requests():
    page = request.args.get('page', 1, type=int)
    requests = Request.query.paginate(page=page, per_page=10)
    return render_template('requests.html', requests=requests)

@app.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    form = RequestForm()
    if form.validate_on_submit():
        product = form.product.data
        employee = form.employee.data
        last_request = Request.query.filter_by(employee_id=employee.id, product_id=product.id).order_by(Request.timestamp.desc()).first()
        if last_request and last_request.timestamp + timedelta(days=product.periodicity) > datetime.now(timezone.utc) and not (current_user.is_aprovador() or current_user.is_administrador()):
            flash('This product can only be requested every {} days.'.format(product.periodicity))
            return redirect(url_for('requests'))
        request = Request(employee_id=employee.id, product_id=product.id, quantity=form.quantity.data, user_id=current_user.id)
        db.session.add(request)
        db.session.commit()
        add_log(f'Added request for {product.name} by {employee.name}')

        # Notify approvers and admins
        approvers = User.query.filter(User.role.in_(['Aprovador', 'Administrador'])).all()
        for approver in approvers:
            send_email('New Material Request',
                       recipients=[approver.email],
                       text_body=render_template('email/new_request.txt', request=request),
                       html_body=render_template('email/new_request.html', request=request))

        flash('Request added successfully.')
        return redirect(url_for('requests'))
    return render_template('add_request.html', form=form)

from app.email import send_email

@app.route('/approve_request/<int:id>')
@login_required
def approve_request(id):
    request = Request.query.get_or_404(id)
    if not (current_user.is_aprovador() or current_user.is_administrador()):
        flash('You are not authorized to perform this action.')
        return redirect(url_for('requests'))
    request.approved = True
    if request.product.quantity - request.quantity <= request.product.min_quantity:
        send_email('Low Stock Notification',
                   recipients=['compras@example.com'],
                   text_body=render_template('email/low_stock.txt', product=request.product),
                   html_body=render_template('email/low_stock.html', product=request.product))
    request.product.quantity -= request.quantity
    add_log(f'Approved request {request.id}')
    db.session.commit()

    # Notify requester
    send_email('Your Material Request has been Approved',
               recipients=[request.user.email],
               text_body=render_template('email/request_approved.txt', request=request),
               html_body=render_template('email/request_approved.html', request=request))

    flash('Request approved successfully.')
    return redirect(url_for('requests'))

@app.route('/delete_request/<int:id>')
@login_required
def delete_request(id):
    req = Request.query.get_or_404(id)
    if not (current_user.is_administrador() or (req.user_id == current_user.id and not req.approved)):
        flash('You are not authorized to perform this action.')
        return redirect(url_for('requests'))

    # If the request was approved, return the quantity to the stock
    if req.approved:
        req.product.quantity += req.quantity

    add_log(f'Deleted request {req.id}')

    # Notify requester
    send_email('Your Material Request has been Returned',
               recipients=[req.user.email],
               text_body=render_template('email/request_returned.txt', request=req),
               html_body=render_template('email/request_returned.html', request=req))

    db.session.delete(req)
    db.session.commit()
    flash('Request deleted successfully and stock updated.')
    return redirect(url_for('requests'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/report_by_employee')
@login_required
def report_by_employee():
    employees = Employee.query.all()
    return render_template('report_by_employee.html', employees=employees)

@app.route('/report_by_product')
@login_required
def report_by_product():
    products = Product.query.all()
    return render_template('report_by_product.html', products=products)

import pandas as pd
from flask import Response, request

@app.route('/report_by_client')
@login_required
def report_by_client():
    employees = Employee.query.all()
    return render_template('report_by_client.html', employees=employees)

@app.route('/logs')
@login_required
def logs():
    if not current_user.is_administrador():
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)

import os
from werkzeug.utils import secure_filename

@app.route('/export_products')
@login_required
def export_products():
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('products'))
    products = Product.query.all()
    df = pd.DataFrame([(p.name, p.description, p.quantity, p.min_quantity, p.periodicity) for p in products], columns=['Name', 'Description', 'Quantity', 'Min Quantity', 'Periodicity'])
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=products.csv"})

@app.route('/import_products', methods=['GET', 'POST'])
@login_required
def import_products():
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('products'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            for index, row in df.iterrows():
                product = Product(name=row['Name'], description=row['Description'], quantity=row['Quantity'], min_quantity=row['Min Quantity'], periodicity=row['Periodicity'])
                db.session.add(product)
            db.session.commit()
            flash('Products imported successfully.')
            return redirect(url_for('products'))
    return render_template('import_products.html')

@app.route('/help')
@login_required
def help():
    with open('manual.md', 'r') as f:
        content = f.read()
    html_content = markdown(content)
    return render_template('help.html', content=html_content)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/users')
@login_required
def users():
    if not current_user.is_administrador():
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('index'))
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        add_log(f'Added user {user.username}')
        flash('User added successfully.')
        return redirect(url_for('users'))
    return render_template('add_user.html', form=form)

@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        add_log(f'Edited user {user.username}')
        flash('User updated successfully.')
        return redirect(url_for('users'))
    return render_template('edit_user.html', form=form)

@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    add_log(f'Deleted user {user.username}')
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('users'))

@app.route('/unlock_user/<int:id>')
@login_required
def unlock_user(id):
    if not current_user.is_administrador():
        flash('You are not authorized to perform this action.')
        return redirect(url_for('users'))
    user = User.query.get_or_404(id)
    user.is_locked = False
    user.failed_login_attempts = 0
    db.session.commit()
    add_log(f'Unlocked user {user.username}')
    flash('User unlocked successfully.')
    return redirect(url_for('users'))

@app.route('/force_password_change', methods=['GET', 'POST'])
@login_required
def force_password_change():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated. Please log in again.')
        return redirect(url_for('logout'))
    return render_template('force_password_change.html', form=form)
