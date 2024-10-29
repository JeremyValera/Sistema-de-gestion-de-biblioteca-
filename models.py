
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Book(db.Model):
    idbook = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(100), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(255), nullable=True)  # Añadido el campo 'categoria'


class Usuario(db.Model):
    """
    Modelo para representar un usuario de la biblioteca.
    """
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.Enum('administrador', 'usuario'), default='usuario')

class Prestamo(db.Model):
    """
    Modelo para representar un préstamo de un libro.
    """
    id = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey('libro.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date)
