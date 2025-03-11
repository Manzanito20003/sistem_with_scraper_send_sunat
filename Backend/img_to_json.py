import google.generativeai as genai
from dotenv import load_dotenv
import os
import PIL.Image
import json


def process_image_to_json(image_path):
    """
    load_dotenv()
    api_key = os.getenv("API_KEY")

    if not api_key:
        print("Error: API_KEY no encontrada en el archivo .env.")
        return

    # Configurar API
    genai.configure(api_key=api_key)

    try:
        # Abrir el archivo de imagen
        sample_file = PIL.Image.open(image_path)
        print(f"Imagen '{image_path}' abierta correctamente.")

        # Subir la imagen a través de la API de Gemini
        uploaded_file = genai.upload_file(path=image_path, display_name=os.path.basename(image_path))
        print(f"Archivo subido '{uploaded_file.display_name}' con URI: {uploaded_file.uri}")

        # Seleccionar un modelo Gemini
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")

        # Crear el prompt con la estructura JSON que esperas
        prompt = '''
        Convierte la información de la imagen proporcionada en un JSON con la siguiente estructura con tipo UTF-8:
        {
            "fecha": "dd/mm/yy" (opcional tipo DATE),
            "cliente": "Nombre del cliente (tipo STRING)",
            "dni": "DNI del comprador" (opcional 8 digitos , tipo string),
            "ruc": "ruc del cliente" (opcional, debe comenzar con '10',tipo string),

            "productos": [
                {
                    "cantidad": X (TIPO INT),
                    "unidad_medida": "CAJA" (si es otro producto) o "KILOGRAMO" (si es menestra tipo STRING) 
                    "descripcion": "Descripción del producto (tipo STRING)",
                    "precio_base": X.XX,   (precio base del producto opcional tipo FLOAT)
                    "Igv": 1 (si incluye IGV) o 0 (si no incluye IGV, debes considerar que las menestras Peruanas no incluyen IGV)
                    "precio_total": x.xx (precio total del producto a pagar tipo FLOAT)
                    
                }
            ],
            "total": X.XX (total a pagar por el cliente  tipo FLOAT)
        }
        Utiliza los valores exactos de la imagen para cada campo y coloca un valor vacío segun tipo de dato  (no uses None , int => 0 ,string="") corresponda en los campos opcionales si no están presentes,ademas pasa a mayuscual los datos.
        '''

        # Realizar la solicitud al modelo con la imagen y el prompt
        response = model.generate_content([uploaded_file, prompt])

        # Limpiar el texto generado
        lines = response.text.splitlines()  # Divide el texto en líneas
        cleaned_text = "\n".join(lines[1:-1])  # Ignorar la primera y la última línea

        # Intentar convertir la respuesta en un objeto JSON
        try:
            python_obj = json.loads(cleaned_text)
            print("Objeto JSON convertido exitosamente:")
            print(python_obj)

            return json.dumps(python_obj, indent=4)

        except json.JSONDecodeError as e:
            print("Error al convertir la respuesta en JSON:", e)

    except Exception as e:
        print(f"Error al procesar la imagen: {e}")
    """
    data={'fecha': '', 'cliente': '', 'dni': '', 'ruc': '', 'productos': [{'cantidad': 2, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'GUINDA ', 'precio_base': 6.0, 'Igv': 0, 'precio_total': 12.0}, {'cantidad': 5, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'LENTEJA RICHLI', 'precio_base': 5.5, 'Igv': 0, 'precio_total': 27.5}, {'cantidad': 3, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'CHULPI I', 'precio_base': 5.8, 'Igv': 0, 'precio_total': 17.4}, {'cantidad': 3, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'TRIGO AM', 'precio_base': 4.4, 'Igv': 0, 'precio_total': 13.2}, {'cantidad': 2, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'TRIGO RESB', 'precio_base': 4.0, 'Igv': 0, 'precio_total': 8.0}, {'cantidad': 5, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'CANCHA MONTANA', 'precio_base': 4.6, 'Igv': 0, 'precio_total': 23.0}, {'cantidad': 4, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'AVP RUMBA', 'precio_base': 4.6, 'Igv': 0, 'precio_total': 18.4}, {'cantidad': 2, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'MORON ENT', 'precio_base': 3.8, 'Igv': 0, 'precio_total': 7.6}, {'cantidad': 2, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'CANARIO NV', 'precio_base': 6.8, 'Igv': 0, 'precio_total': 13.6}, {'cantidad': 2, 'unidad_medida': 'KILOGRAMO', 'descripcion': 'PARDINA', 'precio_base': 6.2, 'Igv': 0, 'precio_total': 12.4}], 'total': 153.1}

    return json.dumps(data, indent=4)
