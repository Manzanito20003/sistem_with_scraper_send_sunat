import json
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Ruta al archivo JSON
JSON_FILE_PATH = '../DataBase/response.json'


def save_json(data):
    """Guarda los datos en el archivo JSON."""
    try:
        with open(JSON_FILE_PATH, 'w', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        print("JSON actualizado correctamente.")
    except Exception as e:
        print(f"Error al guardar el JSON: {e}")

def open_image(filepath=None):
    """Abre una imagen y devuelve su ruta."""
    filepath = filepath or filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg;*.png;*.jpeg;*.bmp;*.gif")]
    )
    return filepath

def display_image(label, filepath):
    """Carga y muestra una imagen en un label."""
    img = Image.open(filepath)
    img.thumbnail((300, 300), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    label.config(image=img_tk)
    label.image = img_tk

def get_senders():
    """Carga remitentes desde un archivo JSON."""
    try:
        with open("../Scraping/clients.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return [(client["name"], client["id"]) for client in data if "name" in client and "id" in client]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        messagebox.showerror("Error", f"No se pudo cargar la lista de remitentes.\n{e}")
        return []

def process_product_data(product):
    """Procesa los datos de un producto y devuelve un diccionario con los valores."""
    return {
        'cantidad': int(product.get('cantidad', 0)),
        'unidad_medida': product.get('unidad_medida', 'Kilo'),
        'descripcion': product.get('descripcion', ''),
        'importe_de_item': float(product.get('importe_de_item', 0)),
        'Igv': 1 if product.get('Igv', 0) == "Sí" else 0
    }



