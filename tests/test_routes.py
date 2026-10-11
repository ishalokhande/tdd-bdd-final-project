######################################################################
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
######################################################################

"""
Product API Service Test Suite
"""

import os
import logging
from decimal import Decimal
from unittest import TestCase

from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)
BASE_URL = "/products"


class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests."""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests."""
        db.session.close()

    def setUp(self):
        """Run before each test."""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Run after each test."""
        db.session.remove()

    def _create_products(self, count=1):
        """Create products through the API."""
        products = []

        for _ in range(count):
            product = ProductFactory()
            response = self.client.post(
                BASE_URL,
                json=product.serialize(),
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
            )

            data = response.get_json()
            product.id = data["id"]
            products.append(product)

        return products

    def test_index(self):
        """It should return the index page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["message"], "OK")

    def test_create_product(self):
        """It should create a new Product."""
        product = ProductFactory()
        response = self.client.post(BASE_URL, json=product.serialize())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        location = response.headers.get("Location")
        self.assertIsNotNone(location)

        data = response.get_json()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(Decimal(data["price"]), product.price)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_create_product_with_no_name(self):
        """It should reject a product without a name."""
        product = self._create_products()[0].serialize()
        del product["name"]

        response = self.client.post(BASE_URL, json=product)
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_product_no_content_type(self):
        """It should reject a request without Content-Type."""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_create_product_wrong_content_type(self):
        """It should reject the wrong Content-Type."""
        response = self.client.post(
            BASE_URL,
            data="{}",
            content_type="plain/text",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # READ

    def test_read_product(self):
        """It should read a product by ID."""
        product = self._create_products()[0]

        response = self.client.get(f"{BASE_URL}/{product.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)

    # UPDATE

    def test_update_product(self):
        """It should update an existing product."""
        product = self._create_products()[0]
        updated = product.serialize()
        updated["name"] = "Updated Hammer"
        updated["description"] = "Updated description"

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            json=updated,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Updated Hammer")
        self.assertEqual(data["description"], "Updated description")

    # DELETE

    def test_delete_product(self):
        """It should delete a product."""
        product = self._create_products()[0]

        response = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # LIST ALL

    def test_list_all_products(self):
        """It should list all products."""
        self._create_products(3)

        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 3)

    # LIST BY NAME

    def test_list_products_by_name(self):
        """It should list products by name."""
        product = ProductFactory()
        product.name = "Special Hammer"
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            BASE_URL,
            query_string={"name": "Special Hammer"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(any(p["name"] == "Special Hammer" for p in data))

    # LIST BY CATEGORY

    def test_list_products_by_category(self):
        """It should list products by category."""
        product = ProductFactory()
        product.category = Category.TOOLS
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            BASE_URL,
            query_string={"category": "TOOLS"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(data)
        self.assertTrue(all(p["category"] == "TOOLS" for p in data))

    # LIST BY AVAILABILITY

    def test_list_products_by_availability(self):
        """It should list products by availability."""
        product = ProductFactory()
        product.available = False
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            BASE_URL,
            query_string={"available": "false"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(data)
        self.assertTrue(all(p["available"] is False for p in data))

    def get_product_count(self):
        """Return the current number of products."""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(response.get_json())
