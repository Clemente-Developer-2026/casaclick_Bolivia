from flask import render_template
from flask_login import login_required,current_user
from app.models import Usuario
from app.cliente import cliente_bp

@cliente_bp.route("/")
def index():
    return render_template("main/index.html")

@cliente_bp.route("/cliente")
@login_required
def dashboard():
    return render_template("cliente/cliente.html")