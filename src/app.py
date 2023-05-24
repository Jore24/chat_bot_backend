from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from chatbot import get_response
from user import User
from user import DiscountCode
from db import db
import bcrypt
import smtplib
from email.mime.text import MIMEText
import secrets
from itsdangerous import URLSafeTimedSerializer
from flask_cors import CORS



app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socket_io = SocketIO(app, cors_allowed_origins="*")

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/bot'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)



# Definición del modelo de usuario

# Ruta para el registro de usuarios
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Generar el hash de la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Crear una instancia del modelo de usuario con la contraseña encriptada
        new_user = User(username=username, password=hashed_password, email=email)

        # Guardar el nuevo usuario en la base de datos
        db.session.add(new_user)
        db.session.commit()
        discount_code = secrets.token_hex(4)
        new_discount_code = DiscountCode(code=discount_code, user_id=new_user.id)
        db.session.add(new_discount_code)
        db.session.commit()

        sender_email = 'jore24@autonoma.edu.pe'  # Reemplaza con tu dirección de correo electrónico
        receiver_email = email  # Usar la dirección de correo electrónico proporcionada por el usuario
        subject = 'Bienvenido a nuestra aplicación'  # Asunto del correo electrónico
        message = 'Hola {},\n\nGracias por registrarte en nuestra aplicación. Tu código de descuento es: {}'.format(username, discount_code)  # Cuerpo del correo electrónico
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email
       
        smtp_server = 'smtp.gmail.com'  # Servidor SMTP de Gmail (puedes usar otro si prefieres)
        smtp_port = 587  # Puerto SMTP de Gmail

        smtp_username = 'jore24@autonoma.edu.pe'  # Tu dirección de correo electrónico
        smtp_password = 'xd'  # Tu contraseña de correo electrónico
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
    if request.method == 'GET':
        print('GET request received XD')
    elif request.method == 'POST':
        print('POST request received')

    # Obtener los datos del JSON enviado en la solicitud
    data = request.get_json()

    # Extraer los datos necesarios del JSON
    username = data.get('username')
    password = data.get('password')

    # Lógica de inicio de sesión aquí
    # ...
    user = User.query.filter_by(username=username).first()

    if user:
        # Verificar si la contraseña es correcta
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id

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




@app.route('/chat', methods=['POST'])
def handle_http_message():
    data = request.json
    message = {
        'socket_id': 'user',
        'message': data['message']
    }
    print('Received message:', message)
    
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
    print('Client connected')
    socket_id = request.sid


@socket_io.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socket_io.on('message')
def handle_socket_message(data):
    message = {
        'socket_id': request.sid,
        'message': data
    }
    print('Received message:', message)
    
    # Enviar el mensaje al chatbot y obtener la respuesta
    response = get_response(data)
    
    # Crear un mensaje con la respuesta del chatbot
    bot_message = {
        'socket_id': 'bot',
        'message': response
    }
    
    # Emitir el mensaje del bot a todos los clientes conectados
    emit('message', bot_message, broadcast=True)  # Emitir el mensaje a todos los clientes conectados





if __name__ == "__main__":
    socket_io.run(app, host="0.0.0.0", port=5000)
