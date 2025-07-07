# tests/conftest.py (archivo recomendado para fixtures globales)

import pytest
from DataBase.DatabaseManager import DatabaseManager


@pytest.fixture
def db():
    """Fixture que crea una base de datos en memoria para cada test."""
    manager = DatabaseManager(":memory:")
    manager.create_tables()
    yield manager
    manager.close()


def test_create_tables(db):
    """Test para verificar que las tablas se crean correctamente."""
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = db.cursor.fetchall()
    table_names = [table[0] for table in tables]

    assert "sender" in table_names
    assert "clients" in table_names
    assert "products" in table_names
    assert "invoices" in table_names
    assert "invoice_details" in table_names


def test_insertar_sender(db):  # primero se crea la conexion
    db.insert_sender("Empresa Test", "12345678901", "user_test", "pass_test")
    remitentes = db.get_senders()

    assert len(remitentes) == 1  # si hay un insert
    assert remitentes[0][1] == "Empresa Test"  # si el nombre es correcto


def test_insertar_cliente(db):
    db.insert_client("Cliente Test", "12345678", "10492621")
    clientes = db.get_clients()

    assert len(clientes) == 1  # si hay un insert
    assert clientes[0][1] == "Cliente Test"  # si el nombre es correcto


def test_insertar_producto(db):
    db.insert_product(1, "Producto Test", "KILOGRAMO", 10.0, 1)
    productos = db.get_products()

    assert len(productos) == 1  # si hay un insert
    assert productos[0][2] == "Producto Test"  # si el nombre es correcto


def test_insert_invoice(db):
    # Arrange
    db.insert_sender("Empresa Test", "12345678901", "user_test", "pass_test")  # id 1
    db.insert_client("Cliente Test", "12345678", "10492621")  # id 1
    db.insert_product(1, "Producto Test", "KILOGRAMO", 10.0, 1)  # para el sende=1
    # Act
    db.insert_invoice(1, 1, 100.0, 1)
    boletas = db.get_invoices()

    # Assert
    assert len(boletas) == 1  # si hay un insert
    assert boletas[0][3] == 100.0  # si el total es correcto
    assert boletas[0][0] == 1  # id es el primero que se crea


def test_insert_invoice_detail(db):
    # Arrange
    db.insert_sender("Empresa Test", "12345678901", "user_test", "pass_test")  # id 1
    db.insert_client("Cliente Test", "12345678", "10492621")  # id 1
    db.insert_product(1, "Producto Test", "KILOGRAMO", 10.0, 1)  # para el sende=1
    db.insert_product(2, "Producto2 Test", "KILOGRAMO", 90.0, 1)  # para el sende=1
    db.insert_invoice(1, 1, 100.0, 1)

    # ACT
    db.insert_invoice_detail(1, 1, 1, 20.0)
    db.insert_invoice_detail(1, 2, 1, 80.0)
    detalles = db.get_invoice_details(1)

    # Assert
    assert len(detalles) >= 1  # si hay un insert
    assert (
        sum([detalle[4] for detalle in detalles]) == 100
    )  # si el subtotal es correcto


def test_delete_sender(db):
    db.insert_sender("Empresa X", "12345678901", "userx", "passx")
    assert len(db.get_senders()) == 1

    db.delete_sender(1)
    assert db.get_senders() == []


def test_delete_client(db):
    db.insert_client("Cliente A", "11111111", "22222222")
    assert len(db.get_clients()) == 1

    db.delete_client(1)
    assert db.get_clients() == []


def test_delete_product(db):
    db.insert_product(1, "Producto A", "KILOGRAMO", 10.0, 1)
    assert len(db.get_products()) == 1

    db.delete_product(1)
    assert db.get_products() == []


def test_update_sender(db):
    db.insert_sender("Empresa A", "12345678901", "user_a", "pass_a")
    remitentes = db.get_senders()
    assert remitentes[0][1] == "Empresa A"

    db.update_sender(1, "Empresa B", "98765432101", "user_b", "pass_b")
    remitentes_actualizados = db.get_senders()
    assert remitentes_actualizados[0][1] == "Empresa B"
    assert remitentes_actualizados[0][2] == "98765432101"


def test_update_client(db):
    db.insert_client("Cliente A", "11111111", "22222222")
    clientes = db.get_clients()
    assert clientes[0][1] == "Cliente A"

    db.update_client(1, "Cliente B", "99999999", "88888888")
    clientes_actualizados = db.get_clients()
    assert clientes_actualizados[0][1] == "Cliente B"
    assert clientes_actualizados[0][2] == "99999999"


def test_update_product(db):
    db.insert_sender("Empresa A", "12345678901", "user_a", "pass_a")
    db.insert_product(1, "Producto A", "KILOGRAMO", 10.0, 1)
    productos = db.get_products()
    assert productos[0][2] == "Producto A"

    db.update_product(1, 1, "Producto B", "KILOGRAMO", 20.0, 1)
    productos_actualizados = db.get_products()
    assert productos_actualizados[0][2] == "Producto B"
    assert productos_actualizados[0][4] == 20.0


if __name__ == "__main__":
    pytest.main()
