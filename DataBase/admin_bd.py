import sqlite3
import sys
db_path="./billing_system.db"
def modo_consola_sqlite():
    print(f"[MODO ADMIN] Consola interactiva SQLite abierta: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    while True:
        try:
            comando = input("sqlite> ")
            if comando.strip().lower() in ["exit", "quit"]:
                break
            cursor.execute(comando)
            resultados = cursor.fetchall()
            for fila in resultados:
                print(fila)
            conn.commit()
        except Exception as e:
            print(f"[ERROR] ", e)

    conn.close()
    print("Cerrando consola SQLite...")
