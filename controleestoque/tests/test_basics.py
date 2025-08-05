import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from app.models import User, Product, Employee, Request

class BasicTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['MAIL_DEFAULT_SENDER'] = 'test@example.com'
        app.config['MAIL_SUPPRESS_SEND'] = True
        os.environ['MAIL_DEFAULT_SENDER'] = 'test@example.com'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_user_model(self):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertTrue(user.check_password('password'))

    def test_product_model(self):
        product = Product(name='Test Product', description='Test Description', quantity=10, min_quantity=5, periodicity=30)
        self.assertEqual(product.name, 'Test Product')

    def test_employee_model(self):
        employee = Employee(name='Test Employee', company='Test Company')
        self.assertEqual(employee.name, 'Test Employee')

    def test_request_model(self):
        request = Request(quantity=1)
        self.assertEqual(request.quantity, 1)

import mock

class BasicTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_user_model(self):
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertTrue(user.check_password('password'))

    def test_product_model(self):
        product = Product(name='Test Product', description='Test Description', quantity=10, min_quantity=5, periodicity=30)
        self.assertEqual(product.name, 'Test Product')

    def test_employee_model(self):
        employee = Employee(name='Test Employee', company='Test Company')
        self.assertEqual(employee.name, 'Test Employee')

    def test_request_model(self):
        request = Request(quantity=1)
        self.assertEqual(request.quantity, 1)

    @mock.patch('app.email.mail.send')
    def test_low_stock_email(self, mock_send):
        with app.app_context():
            user = User(username='admin', email='admin@example.com', is_admin=True)
            user.set_password('admin')
            db.session.add(user)
            product = Product(name='Test Product', description='Test Description', quantity=5, min_quantity=5, periodicity=30)
            db.session.add(product)
            employee = Employee(name='Test Employee', company='Test Company')
            db.session.add(employee)
            db.session.commit()
            request = Request(employee_id=employee.id, product_id=product.id, quantity=1)
            db.session.add(request)
            db.session.commit()

            self.app.post('/login', data=dict(
                username='admin',
                password='admin'
            ), follow_redirects=True)

            response = self.app.get(f'/approve_request/{request.id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            mock_send.assert_called_once()

if __name__ == "__main__":
    unittest.main()
