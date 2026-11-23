import sqlite3

import pytest

from cart import ShoppingCart
from models import CartLine
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def repo(tmp_path):
    """Give each test its own SQLite database with starter products."""
    db_path = tmp_path / "shop_test.db"
    initialize(str(db_path))
    return StoreRepository(str(db_path))


@pytest.fixture
def cart(repo):
    return ShoppingCart("student", repo)


# Defect 1: SQL queries must treat input as data, not SQL code.
def test_get_product_prevents_sql_injection(repo):
    assert repo.get_product("LAP-01") is not None
    assert repo.get_product("' OR 1=1 --") is None


def test_get_saved_cart_prevents_sql_injection(repo):
    repo.save_cart("alice", [CartLine("USB-01", "USB cable", 9.99, 2)])
    
    assert repo.get_saved_cart("alice") == [("USB-01", 2)]
    assert repo.get_saved_cart("' OR 1=1 --") == []


# Defect 2: Users should see only their own orders.
def test_list_orders_filters_by_user(repo):
    alice_order_id = repo.save_order("alice", 19.98, "paid", "req-alice")
    repo.save_order("bob", 29.95, "paid", "req-bob")

    assert repo.list_orders("alice") == [(alice_order_id, "alice", 19.98, "paid")]


# Defect 3: Stock changes must respect available inventory.
def test_update_stock_rejects_insufficient_stock(repo):
    assert repo.get_product("LAP-01").stock == 5

    with pytest.raises(ValueError, match="Insufficient stock"):
        repo.update_stock("LAP-01", 6)

    assert repo.get_product("LAP-01").stock == 5


def test_update_stock_reduces_stock_when_available(repo):
    repo.update_stock("LAP-01", 2)
    assert repo.get_product("LAP-01").stock == 3


# Defect 4: Connections must close when a SQLite operation raises an error.
def test_repository_closes_connection_on_database_error(monkeypatch):
    class FailingConnection:
        def __init__(self):
            self.closed = False

        def execute(self, *args, **kwargs):
            raise sqlite3.OperationalError("simulated database error")

        def close(self):
            self.closed = True

    failing_connection = FailingConnection()
    repository = StoreRepository("unused.db")
    monkeypatch.setattr(repository, "connect", lambda: failing_connection)

    with pytest.raises(sqlite3.OperationalError, match="simulated database error"):
        repository.get_product("USB-01")

    assert failing_connection.closed is True


# Defect 5: Cart quantities must be positive integers.
def test_add_item_rejects_invalid_quantities(cart):
    for invalid_quantity in (-1, 0, 1.5):
        assert cart.add_item("USB-01", invalid_quantity) is False

    assert cart.lines == []


def test_remove_item_rejects_invalid_quantities(cart):
    assert cart.add_item("USB-01", 4) is True

    for invalid_quantity in (-2, 0, 1.5):
        assert cart.remove_item("USB-01", invalid_quantity) is False

    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 4


# Defect 6: Repeated additions must not exceed total available stock.
def test_add_item_checks_combined_quantity(cart):
    assert cart.add_item("LAP-01", 4) is True
    assert cart.add_item("LAP-01", 2) is False

    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 4


# Defect 7: Discounts must reflect the current cart and current coupon.
def test_discount_updates_when_cart_changes(cart):
    assert cart.add_item("USB-01", 2) is True
    assert cart.apply_discount("WELCOME10") is True
    assert cart.total() == pytest.approx(17.98)

    assert cart.add_item("USB-01", 1) is True
    assert cart.total() == pytest.approx(26.97)


def test_new_discount_replaces_previous_discount(cart):
    assert cart.add_item("USB-01", 10) is True
    assert cart.apply_discount("WELCOME10") is True
    assert cart.total() == pytest.approx(89.91)

    assert cart.apply_discount("STUDENT20") is True
    assert cart.total() == pytest.approx(79.92)


# Defect 8: Loading a saved cart twice must not duplicate its items.
def test_repeated_cart_load_does_not_duplicate_items(repo):
    repo.save_cart("alice", [CartLine("USB-01", "USB cable", 9.99, 2)])
    saved_cart = ShoppingCart("alice", repo)

    saved_cart.load()
    saved_cart.load()

    assert len(saved_cart.lines) == 1
    assert saved_cart.lines[0].sku == "USB-01"
    assert saved_cart.lines[0].quantity == 2
