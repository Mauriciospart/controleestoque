import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from app.models import User, Product, Employee
import mock

class FeatureTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a non-admin user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_admin_routes_unauthorized_access(self):
        self.login('testuser', 'password')
        # Test product routes
        response = self.app.get('/add_product', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)
        response = self.app.get('/edit_product/1', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)
        response = self.app.get('/delete_product/1', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)
        # Test employee routes
        response = self.app.get('/add_employee', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)
        response = self.app.get('/edit_employee/1', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)
        response = self.app.get('/delete_employee/1', follow_redirects=True)
        self.assertIn(b'You are not authorized to perform this action.', response.data)

    def test_soft_delete_product(self):
        with app.app_context():
            # Create an admin user
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('password')
            db.session.add(admin)
            # Create a product
            product = Product(name='Test Product', description='Test Description', quantity=10, min_quantity=5, periodicity=30)
            db.session.add(product)
            db.session.commit()

            self.login('admin', 'password')

            # Deactivate the product
            self.app.get(f'/delete_product/{product.id}', follow_redirects=True)

            # Check that the product is inactive in the database
            deactivated_product = Product.query.get(product.id)
            self.assertIsNotNone(deactivated_product)
            self.assertFalse(deactivated_product.is_active)

            # Check that the product is not in the product list
            response = self.app.get('/products')
            self.assertNotIn(b'Test Product', response.data)

if __name__ == "__main__":
    unittest.main()
