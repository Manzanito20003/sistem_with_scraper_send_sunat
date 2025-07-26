import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()


def process_image_to_json(image_path):

    api_key = os.getenv("API_KEY")

    if not api_key:
        logging.error("API_KEY no encontrada en el archivo .env.")
        return

    # Configurar API
    genai.configure(api_key=api_key)

    try:
        # Subir la imagen a través de la API de Gemini
        uploaded_file = genai.upload_file(
            path=image_path, display_name=os.path.basename(image_path)
        )
        logging.info(
            f"Archivo subido '{uploaded_file.display_name}' con URI: {uploaded_file.uri}"
        )
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        prompt = """
         Convierte la información de la imagen proporcionada en un JSON con la siguiente estructura con tipo UTF-8:
         {
             "cliente":{
             "fecha": "dd/mm/yy" (opcional tipo DATE),
             "cliente": "Nombre del cliente (tipo STRING)",
             "dni": "DNI del comprador" (opcional 8 digitos , tipo string),
             "ruc": "ruc del cliente" (opcional, debe comenzar con '10',tipo string),
             }
             "productos": [
                 {
                     "cantidad": X (Tipo float o int),
                     "unidad_medida": "CAJA" (si es otro producto) o "KILOGRAMO" (si es menestra tipo STRING)
                     "descripcion": "Descripción del producto (tipo STRING)",
                     "precio_base": X.XX,   (precio base del producto opcional tipo FLOAT)
                     "igv": 1 (si incluye IGV) o 0 (si no incluye IGV, debes considerar que las menestras Peruanas no incluyen IGV)
                    "precio_total": x.xx (precio total del producto a pagar tipo FLOAT)

                 }
             ],
             "total": X.XX (total a pagar por el cliente  tipo FLOAT)
         }
         Utiliza los valores exactos de la imagen para cada campo y coloca un valor vacío segun tipo de dato  (no uses None , int => 0 ,string="") corresponda en los campos opcionales si no están presentes,ademas pasa a mayuscual los datos.
         """

        # Realizar la solicitud al modelo con la imagen y el prompt
        response = model.generate_content([uploaded_file, prompt])

        # Limpiar el texto generado
        lines = response.text.splitlines()
        cleaned_text = "\n".join(lines[1:-1])
        # Intentar convertir la respuesta en un objeto JSON
        try:
            python_obj = json.loads(cleaned_text)  # convierte de str a dict
            logging.info("Objeto JSON convertido exitosamente:", python_obj)
            return json.dumps(python_obj, indent=4)

        except json.JSONDecodeError as e:
            logging.error("al convertir la respuesta en JSON: %s", e)

    except Exception as e:
        logging.error(f"al procesar la imagen: {e}")


def process_pdf_to_json(pdf_path):
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        logging.error("API_KEY no encontrada en el archivo .env.")
        return None

    # Configurar API
    genai.configure(api_key=api_key)

    try:
        logging.info(f"Enviando PDF '{pdf_path}' a Gemini...")
        uploaded_file = genai.upload_file(
            path=pdf_path, display_name=os.path.basename(pdf_path)
        )
        logging.info(f"PDF subido correctamente: {uploaded_file.uri}")

        # Procesar el PDF con el prompt dado
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt_text = """
                 Convierte la información del pdf proporcionada en un JSON con la siguiente estructura con tipo UTF-8:
                 {
                     "cliente":{
                     "fecha": "dd/mm/yy" (opcional tipo DATE),
                     "cliente": "Nombre del cliente (tipo STRING)",
                     "dni": "DNI del comprador" (opcional 8 digitos , tipo string),
                     "ruc": "ruc del cliente" (opcional, debe comenzar con '10',tipo string),
                     }
                     "productos": [
                         {
                             "cantidad": X (Tipo float o int),
                             "unidad_medida": "CAJA" (si es otro producto) o "KILOGRAMO" (si es menestra tipo STRING)
                             "descripcion": "Descripción del producto (tipo STRING)",
                             "precio_base": X.XX,   (precio base del producto opcional tipo FLOAT)
                             "igv": 1 (si incluye IGV) o 0 (si no incluye IGV, debes considerar que las menestras Peruanas no incluyen IGV)
                            "precio_total": x.xx (precio total del producto a pagar tipo FLOAT)

                         }
                     ],
                     "total": X.XX (total a pagar por el cliente  tipo FLOAT)
                 }
                 Utiliza los valores exactos de la imagen para cada campo y coloca un valor vacío segun tipo de dato  (no uses None , int => 0 ,string="") corresponda en los campos opcionales si no están presentes,ademas pasa a mayuscual los datos.
                 """

        response = model.generate_content([prompt_text, uploaded_file])

        # Limpiar el texto generado
        lines = response.text.splitlines()
        cleaned_text = "\n".join(lines[1:-1])
        try:
            python_obj = json.loads(cleaned_text)
            logging.info("Objeto JSON convertido exitosamente:", python_obj)
            return json.dumps(python_obj, indent=4)

        except json.JSONDecodeError as e:
            logging.error("al convertir la respuesta en JSON: %s", e)

    except Exception as e:
        logging.error(f"Error al procesar el PDF: {e}")
        return None


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    prompt = "Extrae todos los datos del PDF y conviértelos a JSON estructurado."
    resultado = process_pdf_to_json(
        "C:\\Users\\jefersson\\Downloads\\___ Factura Electronica - Impresion ___.pdf"
    )

    if resultado:
        print("Resultado:\n", resultado)
    else:
        print("No se obtuvo respuesta.")
