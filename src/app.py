from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from user import User
from user import DiscountCode
from db import db
import bcrypt
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS
import openai
openai.api_key = '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'
from flask_pymongo import PyMongo
from flask_cors import CORS

app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socket_io = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)

# MongoDb Prueba de Login
app.config['MONGO_URI'] = 'mongodb+srv://jore24:jore24@olva1.3g92oyt.mongodb.net/olva1?retryWrites=true&w=majority'
mongo = PyMongo(app)

CORS(app)

dbcolec = mongo.db.usuario
# dbcolec = mongo.db.messages

for document in dbcolec.find():
    print(document)


# Ruta para el registro de usuarios
@app.route('/register', methods=['POST'])
def register():
    dbcolec = mongo.db.usuario
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']

        # Verificar si el usuario ya existe en la base de datos
        existing_user = dbcolec.find_one({'username': username})
        if existing_user:
            return jsonify({'message': 'El usuario ya está registrado'})

        # Generar el hash de la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insertar el nuevo usuario en la base de datos
        dbcolec.insert_one({
            'username': username, 
            'password': hashed_password,
            'email': email
        })

        # Enviar correo electrónico de bienvenida
        sender_email = 'jore24@autonoma.edu.pe'  # Reemplaza con tu dirección de correo electrónico
        receiver_email = email  # Usar la dirección de correo electrónico proporcionada por el usuario
        subject = 'Bienvenido a nuestra aplicación'  # Asunto del correo electrónico
        message = 'Hola {},\n\nGracias por registrarte en nuestra aplicación.'.format(username)  # Cuerpo del correo electrónico
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        smtp_server = 'smtp.gmail.com'  # Servidor SMTP de Gmail (puedes usar otro si prefieres)
        smtp_port = 587  # Puerto SMTP de Gmail

        smtp_username = 'jore24@autonoma.edu.pe'  # Tu dirección de correo electrónico
        smtp_password = 'x'  # Tu contraseña de correo electrónico
        
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

        response = {
            'message': 'Registro exitoso',
            'username': username,
            'email': email
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

            response = {
                'message': 'Inicio de sesión exitoso',
                'username': username
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




def get_response(user_input):
    dbcolec = mongo.db.messages
    message = user_input.get('message')
    user = user_input.get('user')
    if (user_input == 'Soporte'):
        print('Soporte ps')
        return
    with open('context.txt', 'r') as file:
        context = file.read()
    prompt = context + '\n' + message
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=15,
        temperature=0.7
    )
    #guardar el socket
    dbcolec.insert_one({'message': message, 'user' : user, 'bot_response': response.choices[0].text.strip()})

    return response.choices[0].text.strip()



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
    
    return jsonify(bot_message)

@socket_io.on('connect')
def handle_connect():
    socket_id = request.sid
    initial_message = '¡Hola! Soy un asistente virtual. ¿En qué puedo ayudarte hoy?'
    options = ['Soporte', 'Sucursal', 'Desconocido', 'asdsasd', 'awqeqwd']
    initial_bot_message = {
        'socket_id': 'bot',
        'message': initial_message,
        'options': options
    }
    emit('message', initial_bot_message, room=socket_id)


@socket_io.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


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
    socket_io.run(app, host="0.0.0.0", port=5000)