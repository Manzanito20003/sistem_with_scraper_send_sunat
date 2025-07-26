# DataBase/DatabaseManager.py

import os
import sqlite3

from rapidfuzz import process, fuzz  # asegúrate de tener rapidfuzz instalado


class DatabaseManager:
    # Encapsulamiento de la base de datos
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "billing_system.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def create_tables(self):
        """Crea todas las tablas necesarias en la base de datos."""
        self.cursor.executescript(
            """
        -- Tabla de Remitentes
        CREATE TABLE IF NOT EXISTS sender (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ruc TEXT UNIQUE,
            user TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla de Clientes
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sender INTEGER NOT NULL,
            name TEXT NOT NULL,
            dni TEXT UNIQUE,
            ruc TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_sender) REFERENCES sender(id) ON DELETE CASCADE
        );

        -- Tabla de Productos
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sender INTEGER NOT NULL,
            name TEXT NOT NULL,
            unit TEXT CHECK (unit IN ('KILOGRAMO', 'CAJA', 'UNIDAD', 'BOLSA')) NOT NULL,
            price REAL NOT NULL,
            igv INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (id_sender, name, unit, price, igv)
        );

        -- Tabla de Boletas
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_client INTEGER NOT NULL,
            id_sender INTEGER NOT NULL,
            total REAL NOT NULL,
            igv REAL NOT NULL,
            tipo TEXT NOT NULL,
            serie TEXT NOT NULL,
            numero TEXT NOT NULL,
            emision_fecha DATE NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_client) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (id_sender) REFERENCES sender(id) ON DELETE CASCADE
        );

        -- Tabla de Detalles de Boletas
        CREATE TABLE IF NOT EXISTS invoice_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """
        )
        self.conn.commit()

    # ===============================
    # Métodos de inserción
    # ===============================

    def insert_sender(self, name, ruc, user, password):
        """Inserta un nuevo remitente."""
        self.cursor.execute(
            """
            INSERT INTO sender (name, ruc, user, password)
            VALUES (?, ?, ?, ?)
        """,
            (name, ruc, user, password),
        )
        self.conn.commit()

    def insert_client(self, id_sender, name, dni, ruc):
        """Inserta un nuevo cliente o devuelve ID si ya existe."""
        self.cursor.execute(
            """
            SELECT id FROM clients WHERE name = ? OR dni = ? OR ruc = ?
            """,
            (name, dni, ruc),
        )
        existing_client = self.cursor.fetchone()
        if existing_client:
            return existing_client[0]

        self.cursor.execute(
            """
            INSERT INTO clients (id_sender, name, dni, ruc)
            VALUES (?, ?, ?, ?)
            """,
            (id_sender, name, dni, ruc),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_product(self, id_sender, name, unit, price, igv):
        """Inserta un producto para un remitente."""
        self.cursor.execute(
            """
            SELECT id FROM products
            WHERE id_sender = ? AND name = ? AND unit = ? AND price = ? AND igv = ?
        """,
            (id_sender, name, unit, price, igv),
        )
        existing_product = self.cursor.fetchone()
        if existing_product:
            return existing_product[0]
        self.cursor.execute(
            """
            INSERT INTO products (id_sender, name, unit, price, igv)
            VALUES (?, ?, ?, ?, ?)
        """,
            (id_sender, name, unit, price, igv),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_invoice(
        self, id_client, id_sender, total, igv, tipo, serie, numero, emision_fecha
    ):
        """Inserta una nueva boleta."""
        self.cursor.execute(
            """
            INSERT INTO invoices (id_client, id_sender, total, igv, tipo, serie, numero, emision_fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (id_client, id_sender, total, igv, tipo, serie, numero, emision_fecha),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_invoice_detail(self, invoice_id, product_id, quantity, subtotal):
        """Inserta un detalle de boleta."""
        self.cursor.execute(
            """
            INSERT INTO invoice_details (invoice_id, product_id, quantity, subtotal)
            VALUES (?, ?, ?, ?)
        """,
            (invoice_id, product_id, quantity, subtotal),
        )
        self.conn.commit()

    # ===============================
    # Métodos de consulta
    # ===============================

    def get_senders(self):
        self.cursor.execute("SELECT * FROM sender")
        return self.cursor.fetchall()

    def get_clients(self):
        self.cursor.execute("SELECT * FROM clients")
        return self.cursor.fetchall()

    def get_products_by_sender(self, id_sender=None):
        self.cursor.execute("SELECT * FROM products where id_sender = ?", (id_sender,))
        return self.cursor.fetchall()

    def get_products(self):
        self.cursor.execute("SELECT * FROM products")
        return self.cursor.fetchall()

    def get_invoices_by_sender_id(self, id_sender):
        self.cursor.execute(
            """
            SELECT inv.id, cl.name, se.name, inv.total,inv.tipo, inv.igv, inv.emision_fecha
            FROM invoices inv
            JOIN clients cl ON inv.id_client = cl.id
            JOIN sender se ON inv.id_sender = se.id
            WHERE inv.id_sender = ?
            """,
            (id_sender,),
        )
        return self.cursor.fetchall()

    def get_sender_by_id(self, id_sender):
        self.cursor.execute("SELECT * FROM sender WHERE id = ?", (id_sender,))
        return self.cursor.fetchone()

    def get_next_invoice_number(self, id_sender):
        self.cursor.execute(
            """
            SELECT COUNT(*) FROM invoices WHERE id_sender = ?
            """,
            (id_sender,),
        )
        count = self.cursor.fetchone()[0]
        return count + 1

    def get_invoice_details(self, invoice_id):
        """Obtiene los detalles de una boleta específica con información de productos y boleta."""
        self.cursor.execute(
            """
            SELECT 
                invd.quantity,
                invd.subtotal,
                inv.total,
                inv.igv,
                inv.tipo,
                prd.name,
                prd.unit,
                prd.price,
                prd.igv
            FROM invoice_details AS invd
            INNER JOIN invoices AS inv ON inv.id = invd.invoice_id
            INNER JOIN products AS prd ON prd.id = invd.product_id
            WHERE invd.invoice_id = ?
            """,
            (invoice_id,),
        )
        return self.cursor.fetchall()

    def get_senders_and_id(self):
        """Obtiene todos los remitentes (id y nombre)."""
        self.cursor.execute("SELECT id, name FROM sender")
        senders = self.cursor.fetchall()
        return senders

    # ===============================
    # Métodos de delete
    # ===============================
    def delete_sender(self, id_sender):
        self.cursor.execute("DELETE FROM sender WHERE id = ?", (id_sender,))
        self.conn.commit()

    def delete_client(self, id_client):
        self.cursor.execute("DELETE FROM clients WHERE id = ?", (id_client,))
        self.conn.commit()

    def delete_product_by_sender(self, id_sender, id_product):
        self.cursor.execute(
            "DELETE FROM products WHERE id = ? and id_sender=?",
            (
                id_product,
                id_sender,
            ),
        )
        self.conn.commit()

    def delete_invoice(self, id_invoice):
        self.cursor.execute("DELETE FROM invoices WHERE id = ?", (id_invoice,))
        self.conn.commit()

    def delete_invoice_detail(self, id_invoice_detail):
        self.cursor.execute(
            "DELETE FROM invoice_details WHERE id = ?", (id_invoice_detail,)
        )
        self.conn.commit()

    def delete_all_data(self):
        """Borra todos los registros de todas las tablas (para test)."""
        self.cursor.executescript(
            """
            DELETE FROM invoice_details;
            DELETE FROM invoices;
            DELETE FROM products;
            DELETE FROM clients;
            DELETE FROM sender;
            DELETE FROM sqlite_sequence;
        """
        )
        self.conn.commit()

    # ===============================
    # Métodos de update
    # ===============================
    def update_sender(self, id_sender, name, ruc, user, password):
        self.cursor.execute(
            """
            UPDATE sender
            SET name = ?, ruc = ?, user = ?, password = ?
            WHERE id = ?
        """,
            (name, ruc, user, password, id_sender),
        )
        self.conn.commit()

    def update_client(self, id_client, name, dni, ruc):
        self.cursor.execute(
            """
            UPDATE clients
            SET name = ?, dni = ?, ruc = ?
            WHERE id = ?
        """,
            (name, dni, ruc, id_client),
        )
        self.conn.commit()

    def update_product(self, id_product, id_sender, name, unit, price, igv):
        self.cursor.execute(
            """
            UPDATE products
            SET id_sender = ?, name = ?, unit = ?, price = ?, igv = ?
            WHERE id = ?
        """,
            (id_sender, name, unit, price, igv, id_product),
        )
        self.conn.commit()

    def test_data_user(self):
        """Prueba de conexión a la base de datos."""
        self.insert_sender


if __name__ == "__main__":
    db_manager = DatabaseManager()
    """
    from dotenv import load_dotenv
    import os

    load_dotenv()

    # Obtener usuarios de prueba
    user1 = {
        "name": os.getenv("TEST_USER_1_NAME"),
        "ruc": os.getenv("TEST_USER_1_RUC"),
        "user": os.getenv("TEST_USER_1_USER"),
        "password": os.getenv("TEST_USER_1_PASSWORD")
    }
    user2 = {
        "name": os.getenv("TEST_USER_2_NAME"),
        "ruc": os.getenv("TEST_USER_2_RUC"),
        "user": os.getenv("TEST_USER_2_USER"),
        "password": os.getenv("TEST_USER_2_PASSWORD")
    }

    db_manager.insert_sender(
        user1["name"], user1["ruc"], user1["user"], user1["password"]
    )
    db_manager.insert_sender(
        user2["name"], user2["ruc"], user2["user"], user2["password"]
    )
    """

    # db_manager.delete_all_data()  # Limpia la base de datos para pruebas
    db_manager.create_tables()  # Crea las tablas nuevamente
    db_manager.close()
    print(" tablas creadas correctamente.")
