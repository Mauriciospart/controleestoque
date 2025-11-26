from flask import Blueprint, current_app, render_template, flash, redirect, url_for, request, send_from_directory
from app import db
from app.forms import LoginForm, ProductForm, EmployeeForm, RequestForm, PasswordResetRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.email import send_password_reset_email, send_email
from app.models import User, Product, Employee, Request, Log
from markdown import markdown
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import pandas as pd
from flask import Response

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    period = request.args.get('period', 'all')

    if period == '7days':
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == '30days':
        start_date = datetime.utcnow() - timedelta(days=30)
    elif period == '90days':
        start_date = datetime.utcnow() - timedelta(days=90)
    else:
        start_date = None

    if start_date:
        last_requests_query = Request.query.filter(Request.timestamp >= start_date)
    else:
        last_requests_query = Request.query

    low_stock_products = Product.query.filter(Product.quantity <= Product.min_quantity).all()
    last_requests = last_requests_query.order_by(Request.timestamp.desc()).limit(5).all()

    return render_template('index.html', title='Home', low_stock_products=low_stock_products, last_requests=last_requests, period=period)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/products')
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

@main.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            form.attachment.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

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
        return redirect(url_for('main.products'))
    return render_template('add_product.html', form=form)

@main.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
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
        return redirect(url_for('main.products'))
    return render_template('edit_product.html', form=form)

@main.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    add_log(f'Deleted product {product.name}')
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('main.products'))

@main.route('/employees')
@login_required
def employees():
    page = request.args.get('page', 1, type=int)
    employees = Employee.query.paginate(page=page, per_page=10)
    return render_template('employees.html', employees=employees)

@main.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        employee = Employee(name=form.name.data, company=form.company.data)
        db.session.add(employee)
        db.session.commit()
        add_log(f'Added employee {employee.name}')
        flash('Employee added successfully.')
        return redirect(url_for('main.employees'))
    return render_template('add_employee.html', form=form)

@main.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        employee.name = form.name.data
        employee.company = form.company.data
        db.session.commit()
        add_log(f'Edited employee {employee.name}')
        flash('Employee updated successfully.')
        return redirect(url_for('main.employees'))
    return render_template('edit_employee.html', form=form)

@main.route('/delete_employee/<int:id>')
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    add_log(f'Deleted employee {employee.name}')
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully.')
    return redirect(url_for('main.employees'))

@main.route('/requests')
@login_required
def requests():
    page = request.args.get('page', 1, type=int)
    requests = Request.query.paginate(page=page, per_page=10)
    return render_template('requests.html', requests=requests)

@main.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    form = RequestForm()
    if form.validate_on_submit():
        product = form.product.data
        employee = form.employee.data

        # Check for stock availability
        if form.quantity.data > product.quantity:
            flash(f'Cannot request {form.quantity.data} of "{product.name}". Only {product.quantity} available.')
            return redirect(url_for('main.requests'))

        last_request = Request.query.filter_by(employee_id=employee.id, product_id=product.id).order_by(Request.timestamp.desc()).first()
        if last_request and last_request.timestamp + timedelta(days=product.periodicity) > datetime.utcnow() and not current_user.is_admin:
            flash('This product can only be requested every {} days.'.format(product.periodicity))
            return redirect(url_for('main.requests'))
        request = Request(employee_id=employee.id, product_id=product.id, quantity=form.quantity.data, user_id=current_user.id)
        db.session.add(request)
        db.session.commit()
        add_log(f'Added request for {product.name} by {employee.name}')

        # Notify admins
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            send_email('New Material Request',
                       recipients=[admin.email],
                       text_body=render_template('email/new_request.txt', request=request),
                       html_body=render_template('email/new_request.html', request=request))

        flash('Request added successfully.')
        return redirect(url_for('main.requests'))
    return render_template('add_request.html', form=form)

@main.route('/approve_request/<int:id>')
@login_required
def approve_request(id):
    request = Request.query.get_or_404(id)
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.')
        return redirect(url_for('main.requests'))
    request.approved = True
    if request.product.quantity - request.quantity <= request.product.min_quantity:
        send_email('Low Stock Notification',
                   recipients=[current_app.config['LOW_STOCK_EMAIL']],
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
    return redirect(url_for('main.requests'))

@main.route('/delete_request/<int:id>')
@login_required
def delete_request(id):
    req = Request.query.get_or_404(id)
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.')
        return redirect(url_for('main.requests'))

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
    return redirect(url_for('main.requests'))

@main.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@main.route('/report_by_employee')
@login_required
def report_by_employee():
    employees = Employee.query.all()
    return render_template('report_by_employee.html', employees=employees)

@main.route('/report_by_product')
@login_required
def report_by_product():
    products = Product.query.all()
    return render_template('report_by_product.html', products=products)

@main.route('/report_by_client')
@login_required
def report_by_client():
    employees = Employee.query.all()
    return render_template('report_by_client.html', employees=employees)

@main.route('/logs')
@login_required
def logs():
    if not current_user.is_admin:
        flash('You are not authorized to view this page.')
        return redirect(url_for('main.index'))
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)

@main.route('/export_products')
@login_required
def export_products():
    products = Product.query.all()
    df = pd.DataFrame([(p.name, p.description, p.quantity, p.min_quantity, p.periodicity) for p in products], columns=['Name', 'Description', 'Quantity', 'Min Quantity', 'Periodicity'])
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=products.csv"})

@main.route('/import_products', methods=['GET', 'POST'])
@login_required
def import_products():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            df = pd.read_csv(file)
            for index, row in df.iterrows():
                product = Product(name=row['Name'], description=row['Description'], quantity=row['Quantity'], min_quantity=row['Min Quantity'], periodicity=row['Periodicity'])
                db.session.add(product)
            db.session.commit()
            flash('Products imported successfully.')
            return redirect(url_for('main.products'))
    return render_template('import_products.html')

@main.route('/help')
@login_required
def help():
    with open('manual.md', 'r') as f:
        content = f.read()
    html_content = markdown(content)
    return render_template('help.html', content=html_content)

@main.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('main.login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form)

@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
