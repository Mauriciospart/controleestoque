import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import User, Product, Employee, Request
import mock

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['MAIL_DEFAULT_SENDER'] = 'test@example.com'
        self.app.config['MAIL_SUPPRESS_SEND'] = True
        os.environ['MAIL_DEFAULT_SENDER'] = 'test@example.com'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index_page(self):
        response = self.client.get('/', follow_redirects=True)
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
        user = User(username='admin', email='admin@example.com', is_admin=True)
        user.set_password('admin')
        requester = User(username='requester', email='requester@example.com')
        requester.set_password('password')
        db.session.add(user)
        db.session.add(requester)
        product = Product(name='Test Product', description='Test Description', quantity=5, min_quantity=5, periodicity=30)
        db.session.add(product)
        employee = Employee(name='Test Employee', company='Test Company')
        db.session.add(employee)
        db.session.commit()
        request = Request(employee_id=employee.id, product_id=product.id, quantity=1, user_id=requester.id)
        db.session.add(request)
        db.session.commit()

        self.client.post('/login', data=dict(
            username='admin',
            password='admin'
        ), follow_redirects=True)

        response = self.client.get(f'/approve_request/{request.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_send.call_count, 2) # One for low stock, one for approval

    def test_cannot_request_more_than_in_stock(self):
        # Create a user and log in
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        self.client.post('/login', data=dict(username='testuser', password='password'), follow_redirects=True)

        # Create an employee and a product with a limited quantity
        employee = Employee(name='Test Employee', company='Test Company')
        product = Product(name='Limited Stock Product', description='Description', quantity=10, min_quantity=5, periodicity=30)
        db.session.add(employee)
        db.session.add(product)
        db.session.commit()

        # Attempt to request more than the available quantity
        response = self.client.post('/add_request', data=dict(
            employee=employee.id,
            product=product.id,
            quantity=11
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Check if the correct flash message appears
        self.assertIn(b'Cannot request 11 of &#34;Limited Stock Product&#34;. Only 10 available.', response.data)

        # Ensure no request was created
        request = Request.query.filter_by(product_id=product.id).first()
        self.assertIsNone(request)

if __name__ == "__main__":
    unittest.main()
