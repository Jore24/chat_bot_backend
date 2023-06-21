from pymongo import MongoClient

# Conexión a la base de datos MongoDB
client = MongoClient("mongodb+srv://jore24:jore24@olva1.3g92oyt.mongodb.net/")
db = client["olva1"]  # Reemplaza "nombre_base_de_datos" con el nombre de tu base de datos

# Definición del modelo Usuario
class Usuario:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def guardar(self):
        # Obtener la colección de usuarios
        coleccion = db["user"]  # Nombre de la colección, en este caso "user"

        # Crear el documento de usuario
        usuario_doc = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }

        # Insertar el documento en la colección
        coleccion.insert_one(usuario_doc)

# Ejemplo de uso
usuario = Usuario("ejemplo", "ejemplo@example.com", "contraseña123")
usuario.guardar()
