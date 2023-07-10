from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from user import User
from user import DiscountCode
from db import db
from email.mime.multipart import MIMEMultipart
import bcrypt
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS
import openai
from flask_pymongo import PyMongo
from flask_cors import CORS
import random
import string
from email.mime.image import MIMEImage
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socket_io = SocketIO(app, cors_allowed_origins="*")



# MongoDb Prueba de Login
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

CORS(app)

dbcolec = mongo.db.usuario
# dbcolec = mongo.db.messages

for document in dbcolec.find():
    print(document)

def generate_discount_code(length=8):
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choices(characters, k=length))
    return code



def send_email(sender_email, receiver_email, subject, message, image_path, smtp_username, smtp_password):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Agregar el mensaje de texto
    text = MIMEText(message)
    msg.attach(text)

    # Adjuntar la imagen
    with open(image_path, 'rb') as image_file:
        image = MIMEImage(image_file.read())
        image.add_header('Content-ID', '<image>')
        msg.attach(image)

    # Crear el contenido del mensaje en HTML con la imagen incrustada
    html_content = f'''
        <html>
            <body>
                <p>{message}</p>
                <img src="cid:image" alt="Image">
            </body>
        </html>
    '''
    html = MIMEText(html_content, 'html')
    msg.attach(html)

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except smtplib.SMTPException as e:
        error_message = str(e)
        response = {
            'message': 'Error en el registro',
            'error': error_message
        }
        return jsonify(response), 500

@app.route('/register', methods=['POST'])
def register():
    image_path = 'img.jpg'
    
    dbcolec = mongo.db.usuario
    try:
        data = request.get_json()
        username = data['username']
        dni = data['dni']
        address = data['address']
        email = data['email']
        password = data['password']
    
        
        if 'role' in data:
            role = data['role']
        else:
            role = 'client'
        
        existing_user = dbcolec.find_one({'username': username})
        if existing_user:
            return jsonify({'message': 'El usuario ya está registrado'})

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        discount_code = generate_discount_code()

        result = dbcolec.insert_one({
            'username': username, 
            'password': hashed_password,
            'email': email,
            'dni': dni,
            'address': address,
            'role': role,
            'discount_code' : discount_code,
            'is_used': False

        })

        sender_email = os.getenv('SMTP_USERNAME')
        receiver_email = email
        subject = 'Bienvenido a nuestra aplicación'
        message = 'Hola {},\n\nGracias por registrarte en nuestra aplicación. Tu código de descuento es: {}'.format(username, discount_code)
        
       
        
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        send_email(sender_email, receiver_email, subject, message, image_path, smtp_username, smtp_password)

        user_id = str(result.inserted_id)  
        
        response = {
            'message': 'Registro exitoso',
            'username': username,
            'email': email,
            'user_id': user_id
        }
        
        return jsonify(response)
    except Exception as e:
        error_message = str(e)
        response = {
            'message': 'Error en el registro',
            'error': error_message
        }
        return jsonify(response), 500

@app.route('/apply_discount_code', methods=['POST'])
def apply_discount_code():
    data = request.get_json()
    discount_code = data.get('discount_code')

    # Buscar el código de descuento en la base de datos
    code = DiscountCode.query.filter_by(code=discount_code).first()

    if code:
        if not code.is_used:
            # El código de descuento no ha sido utilizado
            # Marcar el código como utilizado en la base de datos
            code.is_used = True
            db.session.commit()

            response = {
                'message': 'Código de descuento aplicado con éxito'
            }
        else:
            # El código de descuento ya ha sido utilizado
            response = {
                'message': 'El código de descuento ya ha sido utilizado'
            }
    else:
        # El código de descuento no existe
        response = {
            'message': 'Código de descuento inválido'
        }

    return jsonify(response)

@app.route('/login', methods=['POST', 'GET'])
def login():
    dbcolec = mongo.db.usuario
    # Obtener los datos del JSON enviado en la solicitud
    data = request.get_json()

    # Extraer los datos necesarios del JSON
    username = data.get('username')
    password = data.get('password')

    # Buscar el usuario en la base de datos
    user = dbcolec.find_one({'username': username})

    if user:
        hashed_password = user.get('password')
        # Verificar si la contraseña es correcta
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            session['user_id'] = str(user.get('_id'))
            print('ID del usuario logueado:', session['user_id'])
            print(user)

            response = {
                'message': 'Inicio de sesión exitoso',
                'username': username,
                'user_id': str(user.get('_id')),
                'role': user.get('role')
                
            }
            

        else:
            response = {
                'message': 'Contraseña incorrecta'
            }
    else:
        response = {
            'message': 'Usuario no encontrado'
        }

    # Devolver la respuesta en formato JSON
    return jsonify(response)

#@app.route('/chat', methods=['POST'])
def get_response_validate_apply_discount_code(user_input):
    dbcolec = mongo.db.usuario  # Nombre de la colección de usuarios en tu base de datos
    code = user_input.get('message')

    # Realizar la consulta en la base de datos para encontrar un usuario con el código de descuento ingresado
    user_with_code = dbcolec.find_one({'discount_code': code})

    if user_with_code:
        
        return "¡Excelente! El código de descuento que ingresaste es válido. Ahora puedes disfrutar de los beneficios especiales que ofrecemos. Recuerda que puedes acercarte a nuestras tiendas Olva más cercanas para aprovechar tu descuento. Si tienes alguna pregunta adicional, no dudes en consultarnos. ¿En qué más puedo asistirte?"
        
    else:
 
        return "Lo siento, el código de descuento que ingresaste no es válido o ya está usado. Por favor, asegúrate de haber ingresado el código correcto. Si tienes alguna pregunta, no dudes en contactarnos. ¿Hay algo más en lo que pueda ayudarte?"
 

    




context = ""  # Variable para almacenar el contexto globalmente
context_initialized = False  # Bandera para indicar si el contexto se ha inicializado


    
def get_response(user_input):
    global context, context_initialized

    dbcolec = mongo.db.messages
    message = user_input.get('message')
    user = user_input.get('user')
    reasons_for_contact = ['Soporte', 'Sucursales y servicios', 'Reclamos', 'Envíos', 'Cupones y descuentos', 'Agente en línea']
    if message == 'Agente en línea':

        return "Pronto estaremos habilitando este canal en línea, por favor puedes contactarnos por llamada al número 917251229 o nuestra página de facebook www.facebook.com/Olva"
    
    if message == 'salir' and context_initialized is False:
        context = ""
        context_initialized = False
        form_link = "https://docs.google.com/forms/d/e/1FAIpQLSejir0c7S-vRyzc1SNu4Ko_138IzC740sE7JuYXe-KH2ufkVw/viewform"
        response = "Gracias por usar nuestro chatbot. Para finalizar, necesitamos tu opinión sobre mi funcionamiento. Por favor, completa este [cuestionario]( " + form_link + " ) para proporcionarnos tus comentarios."
        return response
    if message == 'opciones' and context_initialized is False:
        context = ""
        context_initialized = False
        
        response = "Selecciona nuevamente el motivo de tu contacto por favor 😀"
        return response

    elif message == 'salir' and context_initialized is True:
        context = ""
        context_initialized = False
        return "", get_response(user_input)
    
    if message == 'borrar' and context_initialized is False:
        context = ""
        context_initialized = False
        print("borrado")

        return "???"
    
    
    
    elif message == 'Cupones y descuentos' and context_initialized is False:
        print('Entra?')
        context_initialized = False  # Reiniciar la bandera de contexto
        context = "ValidarCupon"  # Establecer el contexto para validar el cupón
        return "Estaré encantado de ayudarte, por favor. Ingresa el código de descuento"
    
    elif context == "ValidarCupon":
        context = ""  # Reiniciar el contexto
        return get_response_validate_apply_discount_code(user_input)


    if not context_initialized:
        for reason in reasons_for_contact:
            if reason in message:
                filename = reason.lower().replace(" ", "_") + '.txt'
                with open(filename, 'r') as file:
                    print('Se abrió el archivo', filename)
                    context = file.read()
                    context_initialized = True
                    break

    prompt = context + '\n' + message
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )

    # Guardar el mensaje en la base de datos
    result= dbcolec.insert_one({'messageUser': message, 'user': user, 'reasons_for_contact' : reasons_for_contact, 'bot_response': response.choices[0].text.strip()})
    print('Se guardó el mensaje en la base de datos',result)

    return response.choices[0].text.strip()



    # Realiza la acción correspondiente con el mensaje recibido

@app.route('/chat', methods=['POST'])
def handle_http_message():
    data = request.json
    print(data, )
    message = {
        'socket_id': 'socket_id',
        'message': data['message']
    }
    
    
    # Enviar el mensaje al chatbot y obtener la respuesta
    response = get_response(data['message'])
    
    # Crear un mensaje con la respuesta del chatbot
    bot_message = {
        'socket_id': 'bot',
        'message': response
    }
    print('que acá?')
    return jsonify(bot_message)



@socket_io.on('connect')
def handle_connect():
    print('conectado')
# def handle_connect():
#     socket_id = request.sid
#     initial_message = '¡Hola! Soy un asistente virtual. ¿En qué puedo ayudarte hoy?'
#     options = ['Soporte', 'Sucursal', 'Reclamos', 'Envíos', 'Sucursales y servicios', 'Cotizaciones']
#     print('entras aca?')
#     initial_bot_message = {
#         'message': initial_message,
#         'options': options,
#         'socket_id': 'bot'
#     }
#     emit('message', initial_bot_message, room=socket_id)


@socket_io.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socket_io.on('connection')
def handle_connection():
    print('Client connected')





@socket_io.on('message')
def handle_socket_message(data):
    user = data['user']
    message = {
        'socket_id': request.sid,
        'message': data,
        'user': user
       
        
    }
    
    # Enviar el mensaje al chatbot y obtener la respuesta
    response = get_response(data)
    
    # Crear un mensaje con la respuesta del chatbot
    bot_message = {
        'socket_id': 'bot',
        'message': response,
    }
    
    # Emitir el mensaje del bot a todos los clientes conectados
    emit('message', bot_message, broadcast=True)  # Emitir el mensaje a todos los clientes conectados





if __name__ == "__main__":
    # Obtener el puerto desde las variables de entorno
   port = int(os.getenv("PORT", 5000))
socket_io.run(app, host="0.0.0.0", port=port)
