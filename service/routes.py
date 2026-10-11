######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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

"""Product Store Service with UI."""

from flask import abort, jsonify, request, url_for

from service.common import status
from service.models import Category, Product
from . import app


@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating."""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


@app.route("/")
def index():
    """Base URL for our service."""
    return app.send_static_file("index.html")


def check_content_type(content_type):
    """Checks that the media type is correct."""
    if request.headers.get("Content-Type") != content_type:
        app.logger.error("Invalid or missing Content-Type.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )


@app.route("/products", methods=["POST"])
def create_products():
    """Creates a Product."""
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)

    product = Product()
    product.deserialize(data)
    product.create()

    app.logger.info("Product with new id [%s] saved!", product.id)
    location_url = url_for(
        "get_product", product_id=product.id, _external=True
    )
    return (
        jsonify(product.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


@app.route("/products", methods=["GET"])
def list_products():
    """Returns a list of products, optionally filtered."""
    app.logger.info("Request to List Products...")
    products = Product.all()

    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    if name:
        products = Product.find_by_name(name)

    if category:
        try:
            category_value = Category[category.upper()]
        except KeyError:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Invalid category: {category}",
            )
        products = Product.find_by_category(category_value)

    if available is not None:
        if available.lower() not in ["true", "false"]:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Invalid availability: {available}",
            )
        products = Product.find_by_availability(
            available.lower() == "true"
        )

    return (
        jsonify([product.serialize() for product in products]),
        status.HTTP_200_OK,
    )


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Reads a product by its ID."""
    app.logger.info("Request to Read a Product...")
    product = Product.find(product_id)

    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product with id '{product_id}' was not found.",
        )

    return jsonify(product.serialize()), status.HTTP_200_OK


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Updates an existing product."""
    app.logger.info("Request to Update a Product...")
    check_content_type("application/json")

    product = Product.find(product_id)
    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product with id '{product_id}' was not found.",
        )

    data = request.get_json()
    product.deserialize(data)
    product.update()

    return jsonify(product.serialize()), status.HTTP_200_OK


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Deletes a product by its ID."""
    app.logger.info("Request to Delete a Product...")
    product = Product.find(product_id)

    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product with id '{product_id}' was not found.",
        )

    product.delete()
    return "", status.HTTP_204_NO_CONTENT
