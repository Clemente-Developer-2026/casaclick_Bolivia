from flask import render_template
from flask_login import login_required, current_user
from app.models import Usuario

from app.main import main_bp

@main_bp.route("/")
def index():
    return render_template("main/index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.rol.lower() == "administrador":
        return render_template("main/dashboard.html")
    elif current_user.rol.lower() == "vendedor":
        return render_template("vendedor/index.html")
    elif current_user.rol.lower() == "cliente":
        return render_template("cliente/cliente.html")
    else:
        return render_template("main/index.html")