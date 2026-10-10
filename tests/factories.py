"""Factories for product tests."""
# pylint: disable=too-few-public-methods
import factory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal
from service.models import Product, Category


class ProductFactory(factory.Factory):
    """Create realistic fake products."""

    class Meta:
        """Map the factory to Product."""
        model = Product

    id = factory.Sequence(lambda number: number)
    name = FuzzyChoice([
        "Hat", "Pants", "Shirt", "Apple", "Banana", "Pots",
        "Towels", "Ford", "Chevy", "Hammer", "Wrench",
    ])
    description = factory.Faker("text", max_nb_chars=200)
    price = FuzzyDecimal(0.5, 2000.0, 2)
    available = FuzzyChoice([True, False])
    category = FuzzyChoice(list(Category))
