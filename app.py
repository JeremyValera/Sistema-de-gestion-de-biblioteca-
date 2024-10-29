import os
from flask import Flask, session, render_template, flash, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps
from sqlalchemy import or_
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import Book

# Configura la carpeta de subida de archivos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:12345678j@localhost/bdbiblioteca'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key'  # Necesario para usar sesiones
db = SQLAlchemy(app)

# Inicializa Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Especifica la vista para redirigir cuando el usuario no esté autenticado
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."

class Usuario(db.Model, UserMixin):
    idusuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario')

    def get_id(self):
        return self.idusuario

class Book(db.Model):
    idbook = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(255), nullable=True)
    imagen_path = db.Column(db.String(255), nullable=True)
    
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # Ej. "Venta" o "Alquiler"
    categoria = db.Column(db.String(50), nullable=False)  # Nuevo campo para la categoría de propiedad
    imagen_path = db.Column(db.String(255), nullable=True)
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('book.idbook'), nullable=True)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref=db.backref('comentarios', lazy=True))
    libro = db.relationship('Book', backref=db.backref('comentarios', lazy=True))
    propiedad = db.relationship('Property', backref=db.backref('comentarios', lazy=True))

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('book.idbook'), nullable=False)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref=db.backref('favoritos', lazy=True))
    libro = db.relationship('Book', backref=db.backref('favoritos', lazy=True))

class CommentForm(FlaskForm):
    texto = TextAreaField('Comentario', validators=[DataRequired()])
    submit = SubmitField('Enviar Comentario')
    
    
class RatingForm(FlaskForm):
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Enviar')

    # Definir la función de carga del usuario
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def get_book_by_id(idbook):
    return Book.query.get_or_404(idbook)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/books/comment/<int:idbook>', methods=['POST'])
@login_required
def add_comment_book(idbook):
    libro = Book.query.get_or_404(idbook)
    form = CommentForm()
    if form.validate_on_submit():
        texto = form.texto.data
        comentario = Comment(texto=texto, usuario_id=current_user.idusuario, libro_id=libro.idbook)
        db.session.add(comentario)
        db.session.commit()
        return redirect(url_for('book_details', idbook=libro.idbook))
    return render_template('book_details.html', libro=libro, form=form)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.route('/propiedades/comment/<int:idpropiedad>', methods=['POST'])
@login_required
def add_comment_property(idpropiedad):
    propiedad = Property.query.get_or_404(idpropiedad)
    form = CommentForm()
    if form.validate_on_submit():
        texto = form.texto.data
        comentario = Comment(texto=texto, usuario_id=current_user.idusuario, propiedad_id=propiedad.id)
        db.session.add(comentario)
        db.session.commit()
        return redirect(url_for('property_details', idpropiedad=propiedad.id))
    return render_template('property_details.html', propiedad=propiedad, form=form)

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('q')
    if not query:
        return render_template('main.html', libros=[])

    libros = Book.query.filter(
        or_(
            Book.titulo.ilike(f'%{query}%'),
            Book.autor.ilike(f'%{query}%'),
            Book.categoria.ilike(f'%{query}%')
        )
    ).all()

    resultados = [
        {
            'idbook': libro.idbook,
            'titulo': libro.titulo,
            'autor': libro.autor,
            'descripcion': libro.descripcion,
            'pdf_path': libro.pdf_path,
            'categoria': libro.categoria
        }
        for libro in libros
    ]
    
    return jsonify(resultados), 200

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.rol != 'admin':
            return "Acceso denegado"
        return f(*args, **kwargs)
    return decorated_function

@app.route('/books/favorite/<int:idbook>', methods=['POST'])
@login_required
def add_favorite(idbook):
    libro = Book.query.get_or_404(idbook)
    if not Favorite.query.filter_by(usuario_id=current_user.idusuario, libro_id=libro.idbook).first():
        nuevo_favorito = Favorite(usuario_id=current_user.idusuario, libro_id=libro.idbook)
        db.session.add(nuevo_favorito)
        db.session.commit()
    return redirect(url_for('book_details', idbook=libro.idbook))

@app.route('/books/unfavorite/<int:idbook>', methods=['POST'])
@login_required
def remove_favorite(idbook):
    libro = Book.query.get_or_404(idbook)
    favorito = Favorite.query.filter_by(usuario_id=current_user.idusuario, libro_id=libro.idbook).first()
    if favorito:
        db.session.delete(favorito)
        db.session.commit()
    return redirect(url_for('book_details', idbook=libro.idbook))

@app.route('/favorites')
@login_required
def favorites():
    # Lógica para obtener los libros favoritos del usuario
    libros = current_user.favoritos  
    return render_template('favorites.html', libros=libros)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    usuario = Usuario.query.get_or_404(current_user.idusuario)
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.apellido = request.form['apellido']
        usuario.email = request.form['email']
        db.session.commit()
        return redirect(url_for('perfil'))
    return render_template('perfil.html', usuario=usuario)

@login_manager.user_loader
def load_user(usuario):
    return Usuario.query.get(int(usuario))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['correo']
        contraseña = request.form['contraseña']
        nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, email=email, contraseña=contraseña)
        db.session.add(nuevo_usuario)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']
        usuario = Usuario.query.filter_by(email=email, contraseña=contraseña).first()
        if usuario:
            login_user(usuario)
            flash('Inicio de sesión exitoso', 'success')
            next_page = session.get('next')  # Obtener la URL guardada
            session.pop('next', None)  # Limpiar la URL guardada
            return redirect(next_page or url_for('main'))  # Redirigir a la URL guardada o a la página principal
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
    else:
        session['next'] = request.args.get('next')  # Guardar la URL original
    return render_template('login.html')

@app.before_request
def check_login():
    if not current_user.is_authenticated:
        if request.endpoint not in ['login', 'static']:
            session['next'] = request.url
            return redirect(url_for('login', next=request.url))

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario
    return redirect(url_for('login'))

def es_admin():
    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = Usuario.query.get(usuario_id)
        if usuario and usuario.rol == 'admin':
            return True
    return False

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/books')
def books():
    libros = Book.query.all()
    return render_template('books.html', libros=libros)

@app.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        
 # Maneja la carga del archivo PDF
        pdf_path = None
        if 'pdf' in request.files:
            pdf = request.files['pdf']
            if pdf.filename != '':
                filename = secure_filename(pdf.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf.save(pdf_path)

        # Maneja la carga de la imagen
        imagen_path = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename != '':
                imagen_filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                imagen.save(imagen_path)

        # Crea un nuevo objeto Book con los detalles proporcionados
        new_book = Book(titulo=titulo, autor=autor, descripcion=descripcion, pdf_path=pdf_path, categoria=categoria, imagen_path=os.path.join('uploads', imagen_filename))
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('books'))
    return render_template('add_book.html')

@app.route('/books/edit/<int:idbook>', methods=['GET', 'POST'])
@admin_required
def edit_book(idbook):
    book = Book.query.get_or_404(idbook)
    if request.method == 'POST':
        book.titulo = request.form['titulo']
        book.autor = request.form['autor']
        book.descripcion = request.form['descripcion']
        book.categoria = request.form['categoria']

        # Maneja la carga del archivo PDF
        if 'pdf' in request.files:
            pdf = request.files['pdf']
            if pdf.filename != '':
                filename = secure_filename(pdf.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf.save(pdf_path)
                book.pdf_path = os.path.join('uploads', filename)
  
        # Maneja la carga de la imagen
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename != '':
                imagen_filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                imagen.save(imagen_path)
                book.imagen_path = os.path.join('uploads', imagen_filename)

        db.session.commit()
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)

@app.route('/books/delete/<int:idbook>')
@admin_required
def delete_book(idbook):
    book = Book.query.get_or_404(idbook)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('books'))

@app.route('/books/<int:idbook>')
def book_details(idbook):
    libro = get_book_by_id(idbook)  # Asegúrate de tener esta función o algo similar
    
    form = CommentForm()
    rating_form = RatingForm()
    
    favoritos_ids = [f.libro_id for f in current_user.favoritos] if current_user.is_authenticated else []
    
    return render_template('book_details.html', libro=libro, form=form, rating_form=rating_form, favoritos_ids=favoritos_ids)


# Ruta para Editar Propiedad
@app.route('/propiedades/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_propiedad(id):
    if current_user.rol != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('propiedades'))

    propiedad = Property.query.get_or_404(id)

    if request.method == 'POST':
        propiedad.nombre = request.form['nombre']
        propiedad.direccion = request.form['direccion']
        propiedad.descripcion = request.form['descripcion']
        propiedad.precio = request.form['precio']
        propiedad.tipo = request.form['tipo']
        db.session.commit()
        return redirect(url_for('propiedades'))

    return render_template('edit_propiedad.html', propiedad=propiedad)

# Ruta para Eliminar Propiedad
@app.route('/propiedades/delete/<int:id>', methods=['GET'])
@login_required
def delete_propiedad(id):
    if current_user.rol != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('propiedades'))
    
    propiedad = Property.query.get_or_404(id)
    db.session.delete(propiedad)
    db.session.commit()
    return redirect(url_for('propiedades'))

@app.route('/propiedades')
def propiedades():
    propiedades = Property.query.all()
    return render_template('propiedades.html', propiedades=propiedades)

@app.route('/propiedades/add', methods=['GET', 'POST'])
@admin_required
def add_propiedad():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        tipo = request.form['tipo']
        categoria = request.form['categoria']  # Nuevo campo para la categoría
        
        # Manejo de la imagen
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename != '':
                filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(imagen_path)
            else:
                imagen_path = None
        else:
            imagen_path = None

        new_propiedad = Property(nombre=nombre, direccion=direccion, descripcion=descripcion, precio=precio, tipo=tipo, imagen_path=imagen_path)
        db.session.add(new_propiedad)
        db.session.commit()
        return redirect(url_for('propiedades'))
    return render_template('add_propiedad.html')

@app.route('/buscar_propiedades', methods=['GET'])
def buscar_propiedades():
    query = request.args.get('q')
    if not query:
        return render_template('propiedades.html', propiedades=[])

    propiedades = Property.query.filter(
        or_(
            Property.nombre.ilike(f'%{query}%'),
            Property.direccion.ilike(f'%{query}%'),
            Property.tipo.ilike(f'%{query}%')
        )
    ).all()

    return render_template('propiedades.html', propiedades=propiedades)

@app.route('/')
def index():
    return render_template('main.html', libros=[])

@app.route('/main')
def main():
    return render_template('main.html', libros=[])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
