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
"""

import os
import logging
import unittest
from decimal import Decimal

from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)


######################################################################
# PRODUCT MODEL TEST CASES
######################################################################
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """Run once before the entire test suite."""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after the entire test suite."""
        db.session.close()

    def setUp(self):
        """Run before each test."""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Run after each test."""
        db.session.remove()

    ##################################################################
    # CREATE TESTS
    ##################################################################

    def test_create_a_product(self):
        """It should create a product."""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )

        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertIsNotNone(product)
        self.assertIsNone(product.id)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertTrue(product.available)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should create a product and add it to the database."""
        self.assertEqual(Product.all(), [])

        product = ProductFactory()
        product.id = None
        product.create()

        self.assertIsNotNone(product.id)

        products = Product.all()
        self.assertEqual(len(products), 1)

        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    ##################################################################
    # READ TEST
    ##################################################################

    def test_read_a_product(self):
        """It should read a product by its ID."""
        product = ProductFactory()
        product.id = None
        product.create()

        found = Product.find(product.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, product.id)
        self.assertEqual(found.name, product.name)

    ##################################################################
    # UPDATE TEST
    ##################################################################

    def test_update_a_product(self):
        """It should update an existing product."""
        product = ProductFactory()
        product.id = None
        product.create()

        product.name = "Updated Product"
        product.description = "Updated description"
        product.update()

        found = Product.find(product.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Updated Product")
        self.assertEqual(found.description, "Updated description")

    ##################################################################
    # DELETE TEST
    ##################################################################

    def test_delete_a_product(self):
        """It should delete a product."""
        product = ProductFactory()
        product.id = None
        product.create()
        product_id = product.id

        product.delete()

        self.assertIsNone(Product.find(product_id))
        self.assertEqual(Product.all(), [])

    ##################################################################
    # LIST ALL TEST
    ##################################################################

    def test_list_all_products(self):
        """It should list all products."""
        first = ProductFactory()
        first.id = None
        first.create()

        second = ProductFactory()
        second.id = None
        second.create()

        products = Product.all()

        self.assertEqual(len(products), 2)

    ##################################################################
    # FIND BY NAME TEST
    ##################################################################

    def test_find_by_name(self):
        """It should find products by name."""
        product = Product(
            name="Hammer",
            description="Claw hammer",
            price=34.95,
            available=True,
            category=Category.TOOLS,
        )
        product.create()

        found = Product.find_by_name("Hammer").all()

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "Hammer")

    ##################################################################
    # FIND BY CATEGORY TEST
    ##################################################################

    def test_find_by_category(self):
        """It should find products by category."""
        product = Product(
            name="Hammer",
            description="Claw hammer",
            price=34.95,
            available=True,
            category=Category.TOOLS,
        )
        product.create()

        found = Product.find_by_category(Category.TOOLS).all()

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].category, Category.TOOLS)

    ##################################################################
    # FIND BY AVAILABILITY TEST
    ##################################################################

    def test_find_by_availability(self):
        """It should find products by availability."""
        product = Product(
            name="Unavailable Product",
            description="Not available",
            price=10.00,
            available=False,
            category=Category.TOOLS,
        )
        product.create()

        found = Product.find_by_availability(False).all()

        self.assertEqual(len(found), 1)
        self.assertFalse(found[0].available)
