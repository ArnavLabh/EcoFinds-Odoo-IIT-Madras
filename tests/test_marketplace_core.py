import unittest

from app import create_app, db
from app.config import Config
from app.models import User, Product, CartItem


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False


class MarketplaceCoreTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            user = User(
                email='testbuyer@example.com',
                username='testbuyer',
                phone_number='+15550000001',
                is_email_verified=True,
                is_phone_verified=True,
                eco_points=120,
            )
            user.set_password('Password123!')
            db.session.add(user)
            db.session.commit()
            self.user = user

            product = Product(
                title='Test Product',
                description='A useful reused item',
                price=125.0,
                category_id=1,
                condition='like_new',
                image_url='https://example.com/product.jpg',
                seller_id=self.user.id,
                city='Bengaluru',
                state='Karnataka',
            )
            db.session.add(product)
            db.session.commit()
            self.product = product

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        return self.client.post(
            '/auth/login',
            data={'email': 'testbuyer@example.com', 'password': 'Password123!'},
            follow_redirects=True,
        )

    def test_product_detail_renders_without_template_errors(self):
        with self.app.app_context():
            product_id = Product.query.filter_by(title='Test Product').first().id
        response = self.client.get(f'/product/{product_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Product', response.data)

    def test_edit_product_page_renders_for_owner(self):
        self.login()
        with self.app.app_context():
            product_id = Product.query.filter_by(title='Test Product').first().id
        response = self.client.get(f'/product/{product_id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Product', response.data)

    def test_purchase_cart_rejects_unavailable_products(self):
        self.login()
        with self.app.app_context():
            product = Product.query.filter_by(title='Test Product').first()
            product.is_sold = True
            db.session.add(product)
            db.session.commit()

            cart_item = CartItem(user_id=User.query.filter_by(email='testbuyer@example.com').first().id, product_id=product.id, quantity=1)
            db.session.add(cart_item)
            db.session.commit()

        response = self.client.post('/purchase_cart', follow_redirects=True)
        self.assertIn(b'not available', response.data.lower())

    def test_login_rejects_external_next_redirect(self):
        response = self.client.post(
            '/auth/login',
            data={'email': 'testbuyer@example.com', 'password': 'Password123!', 'next': 'https://evil.example/steal'},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/')


if __name__ == '__main__':
    unittest.main()
