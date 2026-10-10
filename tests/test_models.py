# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import DataValidationError
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat",
                          price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_product(self):
        """It should read a product and verify all saved attributes."""
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.id)
        saved = Product.find(product.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, product.id)
        self.assertEqual(saved.name, product.name)
        self.assertEqual(saved.description, product.description)
        self.assertEqual(saved.price, product.price)
        self.assertEqual(saved.available, product.available)
        self.assertEqual(saved.category, product.category)

    def test_update_product(self):
        """It should update the description without changing the ID."""
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.id)
        original_id = product.id
        product.description = "testing"
        product.update()
        self.assertEqual(product.id, original_id)
        db.session.expire_all()
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")
        saved = Product.find(original_id)
        self.assertEqual(saved.id, original_id)
        self.assertEqual(saved.description, "testing")

    def test_update_without_id(self):
        """It should reject an update without an ID."""
        product = ProductFactory(id=None)
        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_product(self):
        """It should delete a saved product."""
        product = ProductFactory()
        product.create()
        product_id = product.id
        product.delete()
        self.assertIsNone(Product.find(product_id))
        self.assertEqual(Product.all(), [])

    def test_list_all_products(self):
        """It should list exactly five saved products."""
        self.assertEqual(Product.all(), [])
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        saved = Product.all()
        self.assertEqual(len(saved), 5)
        self.assertEqual(
            {product.id for product in saved},
            {product.id for product in products},
        )

    def test_find_by_name(self):
        """It should return only products with the requested name."""
        for name in ["Hat", "Hat", "Shoes"]:
            ProductFactory(name=name).create()
        matches = list(Product.find_by_name("Hat"))
        self.assertEqual(len(matches), 2)
        self.assertTrue(all(product.name == "Hat" for product in matches))
        self.assertEqual(list(Product.find_by_name("Missing")), [])

    def test_find_by_category(self):
        """It should find matching categories among ten products."""
        products = ProductFactory.create_batch(10)
        products[0].category = Category.FOOD
        products[1].category = Category.TOOLS
        for product in products:
            product.create()
        category = products[0].category
        expected_count = len([
            product for product in products if product.category == category
        ])
        matches = list(Product.find_by_category(category))
        self.assertEqual(len(matches), expected_count)
        for product in matches:
            self.assertEqual(product.category, category)

    def test_find_by_availability(self):
        """It should find matching availability among ten products."""
        products = ProductFactory.create_batch(10)
        products[0].available = True
        products[1].available = False
        for product in products:
            product.create()
        for available in [True, False]:
            expected_count = len([
                product for product in products
                if product.available == available
            ])
            matches = list(Product.find_by_availability(available))
            self.assertEqual(len(matches), expected_count)
            for product in matches:
                self.assertEqual(product.available, available)

    def test_serialize_deserialize(self):
        """It should preserve every product attribute."""
        product = ProductFactory()
        result = Product().deserialize(product.serialize())
        self.assertEqual(result.name, product.name)
        self.assertEqual(result.description, product.description)
        self.assertEqual(result.price, product.price)
        self.assertEqual(result.available, product.available)
        self.assertEqual(result.category, product.category)

    def test_deserialize_invalid_data(self):
        """It should reject missing fields and invalid attribute types."""
        payload = ProductFactory().serialize()
        missing = payload.copy()
        del missing["name"]
        invalid_category = dict(payload, category="INVALID")
        invalid_boolean = dict(payload, available="True")
        for data in [None, missing, invalid_category, invalid_boolean]:
            with self.subTest(data=data):
                with self.assertRaises(DataValidationError):
                    Product().deserialize(data)

    def test_find_by_price(self):
        """It should accept decimal and string price queries."""
        ProductFactory(price=Decimal("12.50")).create()
        ProductFactory(price=Decimal("20.00")).create()
        for price in [Decimal("12.50"), ' "12.50" ']:
            matches = list(Product.find_by_price(price))
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].price, Decimal("12.50"))
