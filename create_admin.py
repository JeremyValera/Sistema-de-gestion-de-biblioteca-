from app import db, Usuario, app

# Crear un usuario administrador
email_admin = ''
existing_user = None

# Comprobar si el usuario ya existe
with app.app_context():
    existing_user = Usuario.query.filter_by(email=email_admin).first()

if existing_user is None:
    admin_usuario = Usuario(nombre='Admin', apellido='User', email=email_admin, contraseña='123b', rol='admin')

    # Añadir el usuario a la sesión y confirmar los cambios dentro del contexto de la aplicación
    with app.app_context():
        db.session.add(admin_usuario)
        db.session.commit()
        print("Usuario administrador creado con éxito")
else:
    print("El usuario con el correo ya existe.")
