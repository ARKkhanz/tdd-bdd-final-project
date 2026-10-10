"""Load isolated background products before every scenario."""
import requests
from behave import given


@given("the following products")
def load_products(context):
    """Delete existing products and create the scenario background."""
    endpoint = f"{context.base_url}/products"
    response = requests.get(endpoint, timeout=30)
    assert response.status_code == 200, response.text
    for product in response.json():
        response = requests.delete(
            f"{endpoint}/{product['id']}", timeout=30
        )
        assert response.status_code == 204, response.text
    for row in context.table:
        payload = {
            "name": row["name"],
            "description": row["description"],
            "price": row["price"],
            "available": row["available"].lower() in ["true", "1"],
            "category": row["category"],
        }
        context.resp = requests.post(endpoint, json=payload, timeout=30)
        assert context.resp.status_code == 201, context.resp.text
