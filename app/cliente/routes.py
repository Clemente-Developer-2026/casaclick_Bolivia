from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

from app.models import Usuario, Propiedad, Imagen, Departamento, Provincia, Ciudad
from app.cliente import cliente_bp
from app.extensions import db


@cliente_bp.route("/")
@login_required
def index():
    """Página principal del cliente - Listado de todas las propiedades"""
    if current_user.rol.lower() != 'cliente':
        return render_template("main/index.html")
    
    # Obtener todas las propiedades disponibles
    propiedades = Propiedad.query.filter_by(estado='disponible').all()
    
    # Convertir a diccionario para el template
    propiedades_dict = []
    for prop in propiedades:
        prop_dict = prop.to_dict()
        # Agregar imágenes
        imagenes = Imagen.query.filter_by(id_propiedad=prop.id_propiedad).all()
        prop_dict['imagenes'] = [img.to_dict() for img in imagenes]
        # Agregar nombre del vendedor
        vendedor = Usuario.query.get(prop.id_usuario)
        prop_dict['vendedor_nombre'] = vendedor.nombre if vendedor else 'Desconocido'
        # Agregar ubicación
        departamento = Departamento.query.get(prop.id_departamento)
        provincia = Provincia.query.get(prop.id_provincia)
        ciudad = Ciudad.query.get(prop.id_ciudad)
        prop_dict['ubicacion'] = {
            'departamento': departamento.departamento if departamento else 'N/A',
            'provincia': provincia.provincia if provincia else 'N/A',
            'ciudad': ciudad.ciudad if ciudad else 'N/A'
        }
        propiedades_dict.append(prop_dict)
    
    # Estadísticas
    total_propiedades = Propiedad.query.filter_by(estado='disponible').count()
    total_vendedores = db.session.query(func.count(Usuario.id_usuario.distinct())).filter(
        Usuario.rol == 'vendedor'
    ).scalar()
    
    return render_template(
        "cliente/index.html",
        propiedades=propiedades,
        propiedades_json=propiedades_dict,
        total_propiedades=total_propiedades,
        total_vendedores=total_vendedores
    )


@cliente_bp.route("/propiedad/<int:id_propiedad>")
@login_required
def ver_propiedad(id_propiedad):
    """Ver detalles de una propiedad con datos del vendedor"""
    if current_user.rol.lower() != 'cliente':
        return render_template("main/index.html")
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    # Verificar que la propiedad esté disponible
    if propiedad.estado != 'disponible':
        return render_template("main/index.html")
    
    # Obtener datos del vendedor (sin password)
    vendedor = Usuario.query.get(propiedad.id_usuario)
    datos_vendedor = vendedor.to_dict() if vendedor else None
    if datos_vendedor and 'password' in datos_vendedor:
        del datos_vendedor['password']
    
    # Obtener ubicación
    departamento = Departamento.query.get(propiedad.id_departamento)
    provincia = Provincia.query.get(propiedad.id_provincia)
    ciudad = Ciudad.query.get(propiedad.id_ciudad)
    
    # Obtener imágenes
    imagenes = Imagen.query.filter_by(id_propiedad=id_propiedad).all()
    
    return render_template(
        "cliente/propiedad.html",
        propiedad=propiedad,
        vendedor=datos_vendedor,
        departamento=departamento,
        provincia=provincia,
        ciudad=ciudad,
        imagenes=imagenes
    )


@cliente_bp.route("/perfil")
@login_required
def perfil():
    """Perfil del cliente con toda su información (sin password)"""
    if current_user.rol.lower() != 'cliente':
        return render_template("main/index.html")
    
    # Datos del usuario (sin password)
    usuario_data = current_user.to_dict()
    if 'password' in usuario_data:
        del usuario_data['password']
    
    # Fecha de registro formateada
    fecha_registro = current_user.fecha_registro.strftime('%d/%m/%Y') if current_user.fecha_registro else 'No disponible'
    
    # Calcular antigüedad
    from datetime import date
    if current_user.fecha_registro:
        dias = (date.today() - current_user.fecha_registro).days
        if dias < 30:
            antiguedad = f"{dias} días"
        elif dias < 365:
            antiguedad = f"{dias // 30} meses"
        else:
            antiguedad = f"{dias // 365} años"
    else:
        antiguedad = "N/A"
    
    return render_template(
        "cliente/perfil.html",
        usuario=current_user,
        usuario_data=usuario_data,
        fecha_registro=fecha_registro,
        antiguedad=antiguedad
    )


@cliente_bp.route("/api/propiedades")
@login_required
def api_propiedades():
    """API para obtener propiedades con filtros"""
    if current_user.rol.lower() != 'cliente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    # Obtener parámetros de filtro
    tipo = request.args.get('tipo', 'all')
    departamento_id = request.args.get('departamento', 'all')
    precio_min = request.args.get('precio_min', 0, type=float)
    precio_max = request.args.get('precio_max', float('inf'), type=float)
    
    # Construir query
    query = Propiedad.query.filter_by(estado='disponible')
    
    if tipo != 'all':
        query = query.filter_by(tipo=tipo)
    if departamento_id != 'all':
        query = query.filter_by(id_departamento=departamento_id)
    if precio_min > 0:
        query = query.filter(Propiedad.precio >= precio_min)
    if precio_max != float('inf'):
        query = query.filter(Propiedad.precio <= precio_max)
    
    propiedades = query.all()
    
    # Convertir a JSON
    data = []
    for prop in propiedades:
        prop_dict = prop.to_dict()
        imagenes = Imagen.query.filter_by(id_propiedad=prop.id_propiedad).all()
        prop_dict['imagenes'] = [img.to_dict() for img in imagenes]
        vendedor = Usuario.query.get(prop.id_usuario)
        prop_dict['vendedor_nombre'] = vendedor.nombre if vendedor else 'Desconocido'
        data.append(prop_dict)
    
    return jsonify({
        'success': True,
        'data': data,
        'total': len(data)
    })


@cliente_bp.route("/api/departamentos")
@login_required
def api_departamentos():
    """API para obtener departamentos"""
    departamentos = Departamento.query.all()
    return jsonify({
        'success': True,
        'data': [dep.to_dict() for dep in departamentos]
    })


@cliente_bp.route("/api/tipos")
@login_required
def api_tipos():
    """API para obtener tipos de propiedades únicos"""
    tipos = db.session.query(Propiedad.tipo).distinct().all()
    return jsonify({
        'success': True,
        'data': [t[0] for t in tipos if t[0]]
    })