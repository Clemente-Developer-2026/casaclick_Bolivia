from flask import redirect, request, url_for, jsonify
from flask_login import login_user, logout_user, login_required

from app.extensions import db, bcrypt
from app.auth import auth_bp
from app.models import Usuario
from datetime import date

@auth_bp.route('/registros', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    telefono = data.get('telefono')
    rol = data.get('rol')
    password = data.get('password')
    if not all([nombre, email, telefono, rol, password]):
        return jsonify({
            "success": False,
            "message": "Todos los campos son obligatorios"
        }), 400
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return jsonify({
            "success": False,
            "message": "El correo ya está registrado"
        }), 409
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    usuario = Usuario(
        nombre=nombre,
        email=email,
        telefono=telefono,
        rol=rol.lower(),
        password=password_hash,
        fecha_registro=date.today()
    )

    db.session.add(usuario)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Usuario registrado correctamente",
        "usuario": usuario.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "No se recibieron datos"
        }), 400
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email y contraseña son obligatorios"
        }), 400
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({
            "success": False,
            "message": "Usuario no encontrado"
        }), 404
    if not bcrypt.check_password_hash(usuario.password, password):
        return jsonify({
            "success": False,
            "message": "Contraseña incorrecta"
        }), 401
    login_user(usuario)
    # Dashboard según rol
    if usuario.rol.lower() == "administrador":
        dashboard = "/dashboard"
    elif usuario.rol.lower() == "vendedor":
        dashboard = "/vendedor"
    elif usuario.rol.lower() == "cliente":
        dashboard = "/cliente/cliente"
    else:
        dashboard = "/main/index"
    return jsonify({
        "success": True,
        "message": "Inicio de sesión exitoso",
        "rol": usuario.rol,
        "dashboard": dashboard,
        "usuario": {
            "id": usuario.id_usuario,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "telefono": usuario.telefono
        }
    }), 200

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

