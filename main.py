# Archivo principal

# Importamos las bibliotecas necesarias para la aplicación
from flask import Flask, jsonify, request  # Flask para crear la aplicación web, jsonify para retornar respuestas JSON, y request para manejar solicitudes HTTP.
import os  # Para acceder a variables del entorno.
import json  # Para manipular datos JSON.
from dotenv import load_dotenv  # Para cargar variables de entorno desde un archivo .env.
from epaycosdk.epayco import Epayco  # Importamos el SDK de ePayco para manejar pagos.

# Cargar variables del entorno definidas en el archivo .env
load_dotenv()

# Inicializamos la aplicación Flask
app = Flask(__name__)

# Inicializamos ePayco con las claves de tu cuenta, las cuales se cargan desde las variables de entorno
epayco = Epayco({
    'apiKey': os.getenv('PUBLIC_KEY'),  # Llave pública de ePayco
    'privateKey': os.getenv('PRIVATE_KEY'),  # Llave privada de ePayco
    'lenguage': 'ES',  # Definimos el lenguaje como español
    'test': os.getenv('EPAYCO_TEST') == 'true'  # Indicamos si el modo es de pruebas (test) o producción
})

# Método para crear el token de una tarjeta
def create_token(data):
    try:
        # Datos de la tarjeta proporcionados en la solicitud
        card_data = {
            "card[number]": data['card_number'],  # Número de tarjeta
            "card[exp_year]": data['exp_year'],  # Año de expiración
            "card[exp_month]": data['exp_month'],  # Mes de expiración
            "card[cvc]": data['cvc'],  # Código de seguridad (CVC)
            "hasCvv": True  # Indicamos que la tarjeta tiene CVC
        }
        # Creamos el token con la tarjeta
        token = epayco.token.create(card_data)
        return token  # Retornamos el token creado
    except Exception as e:
        # Si ocurre un error, retornamos el error en formato JSON
        print(f"Error creating token: {str(e)}")  # Agregar impresión del error
        return {'error': str(e)}

# Método para crear un cliente en ePayco
def create_customer(token, data):
    # Definimos los datos del cliente
    customer_data = {'name': data['name'], 'last_name': data['last_name'], 'email': data['email'],
                     'phone': data['phone'], 'default': True, 'token_card': token}
    # Añadimos el token de la tarjeta al cliente
    try:
        # Creamos el cliente en ePayco
        customer = epayco.customer.create(customer_data)
        return customer  # Retornamos el cliente creado
    except Exception as e:
        # Si ocurre un error, retornamos el error en formato JSON
        print(f"Error creating customer: {str(e)}")  # Agregar impresión del error
        return {'error': str(e)}

# Método para procesar un pago
def process_payment(data, customer_id, token_card):
    try:
        # Definimos los datos necesarios para el pago
        payment_data = {
            'token_card': token_card,  # Token de la tarjeta
            'customer_id': customer_id,  # ID del cliente
            'doc_type': 'CC',  # Tipo de documento del cliente
            'doc_number': data['doc_number'],  # Número del documento del cliente
            'name': data['name'],  # Nombre del cliente
            'last_name': data['last_name'],  # Apellido del cliente
            'email': data['email'],  # Email del cliente
            'city': data['city'],  # Ciudad del cliente
            'address': data['address'],  # Dirección del cliente
            'phone': data['phone'],  # Teléfono del cliente
            'cell_phone': data['cell_phone'],  # Teléfono celular del cliente
            'bill': data['bill'],  # Factura o referencia de pago
            'description': 'Pago de servicios',  # Descripción del pago
            'value': data['value'],  # Valor del pago
            'tax': '0',  # Impuesto (en este caso es 0)
            'tax_base': ['value'],  # Base imponible del impuesto
            'currency': 'COP'  # Moneda en la que se procesa el pago (Pesos colombianos)
        }
        # Procesamos el pago con ePayco
        response = epayco.charge.create(payment_data)
        return response  # Retornamos la respuesta del pago
    except Exception as e:
        # Si ocurre un error, retornamos el error en formato JSON
        print(f"Error processing payment: {str(e)}")  # Agregar impresión del error
        return {'error': str(e)}

# Endpoint que maneja todo el flujo del pago
@app.route('/payment', methods=['POST'])
def handle_payment_process():
    # Obtenemos los datos enviados en el cuerpo de la solicitud (JSON)
    data = request.json

    # Crear el token de la tarjeta
    token_response = create_token(data)
    print("token response:", json.dumps(token_response))

    # Verificamos si hubo un error al crear el token
    if token_response.get("status") is not True:
        return jsonify(token_response), 500

    # Extraemos el ID del token de la tarjeta
    token_card = token_response["id"]

    # Crear el cliente
    customer_response = create_customer(token_card, data)
    print("customer response:", json.dumps(customer_response))

    # Verificamos si hubo un error al crear el cliente
    if 'error' in customer_response:
        return jsonify(customer_response), 500

    # Extraemos el ID del cliente
    customer_id = customer_response['data']['customerId']

    # Procesamos el pago
    payment_response = process_payment(data, customer_id, token_card)
    print("payment response:", json.dumps(payment_response))

    # Verificamos si hubo un error al procesar el pago
    if 'error' in payment_response:
        return jsonify(payment_response), 500

    # Retornamos la respuesta exitosa del pago
    return jsonify(payment_response), 200

# Punto de entrada de la aplicación
if __name__ == '__main__':
    # Ejecutamos la aplicación en modo debug y en el puerto 5001
    app.run(debug=True, port=5001)
