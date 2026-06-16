from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app.main import main_bp
from app.models import Usuario, Propiedad, Imagen, Departamento, Provincia, Ciudad, Auditoria
from app.extensions import db


@main_bp.route("/")
def index():
    return render_template("main/index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard principal con estadísticas reales"""
    
    # Verificar que sea administrador
    if current_user.rol.lower() != 'administrador':
        return render_template("main/index.html")
    
    # Estadísticas básicas
    total_propiedades = Propiedad.query.count()
    total_usuarios = Usuario.query.count()
    
    # Propiedades por estado
    propiedades_activas = Propiedad.query.filter_by(estado='disponible').count()
    propiedades_vendidas = Propiedad.query.filter_by(estado='vendido').count()
    propiedades_alquiladas = Propiedad.query.filter_by(estado='alquilado').count()
    
    # Usuarios por rol
    administradores = Usuario.query.filter_by(rol='administrador').count()
    vendedores = Usuario.query.filter_by(rol='vendedor').count()
    clientes = Usuario.query.filter_by(rol='cliente').count()
    
    # Propiedades por tipo
    tipos = db.session.query(
        Propiedad.tipo, 
        func.count(Propiedad.id_propiedad).label('total')
    ).group_by(Propiedad.tipo).all()
    
    # Propiedades recientes (últimos 7 días)
    fecha_limite = datetime.now().date() - timedelta(days=7)
    propiedades_recientes = Propiedad.query.filter(
        Propiedad.fecha_publicacion >= fecha_limite
    ).order_by(Propiedad.fecha_publicacion.desc()).limit(10).all()
    
    # Últimos usuarios registrados
    usuarios_recientes = Usuario.query.order_by(
        Usuario.fecha_registro.desc()
    ).limit(10).all()
    
    # Actividad de auditoría reciente
    auditoria_reciente = Auditoria.query.order_by(
        Auditoria.fecha_actividad.desc(),
        Auditoria.hora_actividad.desc()
    ).limit(10).all()
    
    # Estadísticas por mes (últimos 6 meses)
    meses = []
    ventas_mensuales = []
    
    for i in range(6):
        mes = datetime.now().date().replace(day=1) - timedelta(days=30*i)
        inicio_mes = mes.replace(day=1)
        fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Propiedad.query.filter(
            Propiedad.fecha_publicacion >= inicio_mes,
            Propiedad.fecha_publicacion <= fin_mes
        ).count()
        
        meses.append(inicio_mes.strftime('%b'))
        ventas_mensuales.append(count)
    
    # Calcular alturas para las barras
    max_ventas = max(ventas_mensuales) if ventas_mensuales else 1
    alturas_barras = []
    for venta in ventas_mensuales:
        if max_ventas > 0:
            altura = (venta / (max_ventas + 1)) * 100
        else:
            altura = 10
        alturas_barras.append(altura)
    
    # Datos para gráfico de distribución por tipo
    tipos_data = [{'tipo': t.tipo, 'total': t.total} for t in tipos]
    
    return render_template(
        'main/dashboard.html',
        # Métricas principales
        total_propiedades=total_propiedades,
        total_usuarios=total_usuarios,
        propiedades_activas=propiedades_activas,
        propiedades_vendidas=propiedades_vendidas,
        propiedades_alquiladas=propiedades_alquiladas,
        administradores=administradores,
        vendedores=vendedores,
        clientes=clientes,
        # Datos para tablas
        propiedades_recientes=propiedades_recientes,
        usuarios_recientes=usuarios_recientes,
        auditoria_reciente=auditoria_reciente,
        # Datos para gráficos
        tipos_data=tipos_data,
        meses=meses,
        ventas_mensuales=ventas_mensuales,
        alturas_barras=alturas_barras
    )

@main_bp.route("/api/auditoria/reciente")
@login_required
def api_auditoria_reciente():
    """API para obtener auditoría reciente"""
    if current_user.rol.lower() != 'administrador':
        return jsonify({"success": False, "message": "No autorizado"}), 403
    
    auditoria = Auditoria.query.order_by(
        Auditoria.fecha_actividad.desc(),
        Auditoria.hora_actividad.desc()
    ).limit(20).all()
    
    data = [audit.to_dict() for audit in auditoria]
    return jsonify({"success": True, "data": data})