import difflib
import sqlite3
from difflib import get_close_matches,SequenceMatcher

# Ruta absoluta de la base de datos
DB_PATH = r"C:\Users\jefersson\Desktop\Sunat_boleta\DataBase\billing_system.db"

def connect():
    """Conecta a la base de datos con la ruta absoluta"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        return None, None

def create_tables():
    """Crea las tablas de la base de datos"""
    conn, cursor = connect()

    cursor.executescript("""
    -- Tabla de Remitentes (Usuarios del sistema)
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
        name TEXT NOT NULL,
        dni TEXT UNIQUE,
        ruc TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabla de Productos
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL
        name TEXT UNIQUE,
        unit TEXT CHECK (unit IN ('KILOGRAMO', 'CAJA', 'UNIDAD', 'BOLSA')),
        price REAL NOT NULL,
        igv INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabla de Boletas (Facturas)
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL,
        igv REAL NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES sender(id) ON DELETE CASCADE
    );

    -- Tabla Intermedia: Relación entre Boletas y Productos
    CREATE TABLE IF NOT EXISTS invoice_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("Tablas creadas correctamente.")

def insert_sender(name, ruc, user, password):
    """Inserta un nuevo remitente (usuario del sistema)"""
    conn, cursor = connect()
    try:
        cursor.execute("""
            INSERT INTO sender (name, ruc, user, password) 
            VALUES (?, ?, ?, ?)
        """, (name, ruc, user, password))
        conn.commit()
        print(f"Remitente '{name}' agregado correctamente.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

import sqlite3  # Asegúrate de importar sqlite3

def insert_client(name, dni, ruc):
    """Inserta un nuevo cliente en la base de datos si no existe otro con el mismo nombre, dni o ruc.
    Si el cliente ya existe, devuelve su ID existente."""
    try:
        conn, cursor = connect()

        # Verificar si el cliente ya existe (mismo name, dni o ruc)
        cursor.execute("""
            SELECT id FROM clients WHERE name = ? OR dni = ? OR ruc = ?
        """, (name, dni, ruc))
        existing_client = cursor.fetchone()

        if existing_client:
            print("Cliente ya existe ID:", existing_client[0])
            conn.close()
            return existing_client[0]  # Devuelve el ID del cliente ya existente

        # Insertar el nuevo cliente
        cursor.execute("""
            INSERT INTO clients (name, dni, ruc) 
            VALUES (?, ?, ?)
        """, (name, dni, ruc))
        conn.commit()
        conn.close()
        id_client = cursor.lastrowid  # Obtener el ID recién insertado
        return id_client  # Devuelve el nuevo ID

    except Exception as e:
        return f"Error al insertar el cliente: {e}"


import sqlite3  # Asegúrate de importar sqlite3

def insert_product(id_client, name, unit, price, igv):
    """Inserta un nuevo producto en la base de datos si no existe otro con el mismo nombre para el mismo cliente"""
    try:
        conn, cursor = connect()

        # Verificar si el producto ya existe para el mismo cliente
        cursor.execute("SELECT id FROM products WHERE name = ? AND id_client = ?", (name, id_client))
        existing_product = cursor.fetchone()

        if existing_product:  # Si existe, devolvemos su ID
            return f"Error: El producto '{name}' con el cliente '{id_client}' ya existe en la base de datos con ID {existing_product[0]}."

        # Insertar el nuevo producto
        cursor.execute("""
            INSERT INTO products (id_client, name, unit, price, igv) 
            VALUES (?, ?, ?, ?, ?)
        """, (id_client, name, unit, price, igv))

        conn.commit()
        conn.close()  # Asegurar que la conexión se cierre siempre

        return f"Producto '{name}' agregado correctamente."

    except Exception as e:
        return f"Error al insertar el producto: {e}"



def insert_invoice(client_id, sender_id, total, igv):
    """Inserta una nueva boleta (factura)"""
    conn, cursor = connect()
    cursor.execute("""
        INSERT INTO invoices (client_id, sender_id, total, igv) 
        VALUES (?, ?, ?, ?)
    """, (client_id, sender_id, total, igv))
    invoice_id = cursor.lastrowid  # Obtener el ID de la última boleta insertada
    conn.commit()
    conn.close()
    print(f"Factura ID {invoice_id} agregada correctamente.")
    return invoice_id



def insert_invoice_detail(invoice_id, product_id, quantity, subtotal):
    """Agrega un producto a una boleta"""
    conn, cursor = connect()
    cursor.execute("""
        INSERT INTO invoice_details (invoice_id, product_id, quantity, subtotal) 
        VALUES (?, ?, ?, ?)
    """, (invoice_id, product_id, quantity, subtotal))
    conn.commit()
    conn.close()
    print(f"Producto ID {product_id} agregado a la Factura ID {invoice_id}.")

def get_senders():
    """Obtiene todos los remitentes"""
    conn, cursor = connect()
    cursor.execute("SELECT * FROM sender")
    senders = cursor.fetchall()
    conn.close()
    return senders
def get_senders_and_id():
    """Obtiene todos los remitentes"""
    conn, cursor = connect()
    cursor.execute("SELECT id,name FROM sender")
    senders = cursor.fetchall()
    conn.close()
    return senders

def get_clients():
    """Obtiene todos los clientes"""
    conn, cursor = connect()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    conn.close()
    return clients

def get_products():
    """Obtiene todos los productos"""
    conn, cursor = connect()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def get_invoices():
    """Obtiene todas las boletas"""
    conn, cursor = connect()
    cursor.execute("""
        SELECT invoices.id, clients.name, sender.name AS remitente, invoices.date, invoices.total, invoices.igv 
        FROM invoices
        JOIN clients ON invoices.client_id = clients.id
        JOIN sender ON invoices.sender_id = sender.id
    """)
    invoices = cursor.fetchall()
    conn.close()
    return invoices
#tool to search for similar names

def calculate_similarity(a, b):
    """Calcula la similitud entre dos cadenas con más precisión"""
    similarity = SequenceMatcher(None, a.lower(), b.lower()).ratio()

    # Ajustamos el porcentaje realista
    length_factor = min(len(a), len(b)) / max(len(a), len(b))
    adjusted_similarity = similarity * length_factor  # Ajuste basado en longitud

    return round(adjusted_similarity * 100, 2)


def calculate_similarity(text1, text2):
    """
    Calcula la similitud entre dos cadenas de texto usando la métrica de Levenshtein.

    :param text1: Texto ingresado por el usuario
    :param text2: Texto de la BD
    :return: Porcentaje de similitud (0 - 100)
    """
    return round(difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100, 2)

def match_product_fuzzy(search_term):
    """
    Busca un producto en la base de datos con coincidencias exactas y aproximadas.

    :param search_term: Nombre parcial o con errores del producto
    :return: Lista de tuplas con (id, name, unit, price, confidence)
    """
    conn, cursor = connect()

    # 🔹 1️⃣ Obtener todos los productos disponibles en la BD
    cursor.execute("SELECT id, name, unit, price FROM products")
    products = cursor.fetchall()  # Lista completa de productos
    product_names = [row[1] for row in products]  # Solo los nombres de productos

    # 🔹 2️⃣ Intentar encontrar coincidencias exactas con `LIKE`
    query = """
    SELECT id, name, unit, price FROM products 
    WHERE name LIKE ? 
    ORDER BY LENGTH(name) ASC;
    """
    cursor.execute(query, (f"%{search_term}%",))
    exact_matches = cursor.fetchall()

    matches_with_confidence = []

    # 🔹 3️⃣ Si no hay coincidencias exactas, buscar con fuzzy matching
    if not exact_matches and product_names:
        close_matches = get_close_matches(search_term, product_names, n=5, cutoff=0.4)  # 5 sugerencias con 40%+ similitud

        for match in close_matches:
            confidence = calculate_similarity(search_term, match)

            # Buscar el producto completo en la BD
            cursor.execute(query, (f"%{match}%",))
            matched_product = cursor.fetchone()

            if matched_product:
                matches_with_confidence.append((*matched_product, confidence))

    conn.close()

    # 🔹 4️⃣ Retornar coincidencias exactas o aproximadas, ordenadas por confianza
    if exact_matches:
        return [(row[0], row[1], row[2], row[3], 100) for row in exact_matches]  # Exacto = 100%

    return sorted(matches_with_confidence, key=lambda x: x[4], reverse=True)


def match_client_fuzzy(search_term):
    """
    Busca un cliente por coincidencia exacta o aproximada y devuelve la confianza del match.

    :param search_term: Nombre parcial o con errores del cliente
    :return: Lista de tuplas con (id, name, dni, ruc, confidence)
    """
    conn, cursor = connect()

    # 1️⃣ Obtener todos los nombres de clientes de la base de datos
    cursor.execute("SELECT id, name, dni, ruc FROM clients")
    clients = cursor.fetchall()  # Lista de clientes completos
    client_names = [row[1] for row in clients]  # Solo los nombres de clientes

    # 2️⃣ Buscar coincidencias exactas con `LIKE`
    query = """
    SELECT id, name, dni, ruc FROM clients 
    WHERE name LIKE ?;
    """
    cursor.execute(query, (f"%{search_term}%",))
    exact_matches = cursor.fetchall()

    # 3️⃣ Si no hay coincidencias exactas, buscar coincidencias aproximadas
    matches_with_confidence = []
    if not exact_matches and client_names:
        close_matches = get_close_matches(search_term, client_names, n=5,
                                          cutoff=0.4)  # Baja el cutoff para más precisión

        for match in close_matches:
            confidence = calculate_similarity(search_term, match)

            # Evitar coincidencias con confianza baja
            if confidence > 50:
                cursor.execute(query, (f"%{match}%",))
                matched_client = cursor.fetchone()

                if matched_client:
                    matches_with_confidence.append((*matched_client, confidence))

    conn.close()

    # 4️⃣ Retornar coincidencias exactas con 100% de confianza, o aproximadas con % realista
    if exact_matches:
        return [(row[0], row[1], row[2], row[3], 100) for row in exact_matches]

    return matches_with_confidence  # Coincidencias aproximadas con porcentaje realist


def borrar_datos(tabla="all"):
    """Borra los datos de una tabla específica o de toda la base de datos."""
    conn, cursor = connect()

    try:
        if tabla == "all":
            cursor.execute("DELETE FROM invoice_details")
            cursor.execute("DELETE FROM invoices")
            cursor.execute("DELETE FROM clients")
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM sender")

            # 🔹 Reiniciar los IDs autoincrementales
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='invoice_details'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='invoices'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='clients'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='sender'")

            print("✅ Todos los datos de la base de datos han sido eliminados.")

        else:
            cursor.execute(f"DELETE FROM {tabla}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}'")
            print(f"✅ Datos eliminados de la tabla '{tabla}'.")

        conn.commit()

    except sqlite3.Error as e:
        print(f"[ERROR] No se pudieron borrar los datos de la tabla {tabla}: {e}")

    finally:
        conn.close()

def get_sender_by_id(id):
    """Obtiene un remitente por su ID"""
    conn, cursor = connect()
    cursor.execute("SELECT * FROM sender WHERE id = ?", (id,))
    sender = cursor.fetchone()
    conn.close()
    return sender

def get_next_invoice_number(sender_id):
    """Obtiene el siguiente número de boleta para un remitente."""
    conn, cursor = connect()
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE sender_id = ?", (sender_id,))
    num_boleta = cursor.fetchone()[0] +1  # 🔹 Siguiente número de boleta
    conn.close()
    return num_boleta
def mostrar_bd():
    print("\n📌 Lista de Remitentes:")

    print(get_senders_and_id())
    for sender in get_senders():
        print(sender)

    print("\n📌 Lista de Clientes:")
    for client in get_clients():
        print(client)

    print("\n📌 Lista de Productos:")
    for product in get_products():
        print(product)

    print("\n📌 Lista de Boletas:")
    for invoice in get_invoices():
        print(invoice)
# Ejecutar la creación de la base de datos y sus tablas


if __name__ == "__main__":
    create_tables()





