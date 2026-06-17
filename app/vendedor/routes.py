from flask import render_template, redirect, request, url_for, jsonify, send_from_directory, current_app, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from app.models import Usuario, Departamento, Ciudad, Propiedad, Provincia, Imagen
from app.vendedor import vendedor_bp
from app.extensions import db
from app.utils.uploads import save_image, delete_image, get_image_url, allowed_file

# ============================================
# FUNCIONES PRINCIPALES DE PROPIEDADES
# ============================================

@vendedor_bp.route("/")
@login_required
def index():
    """Panel principal del vendedor - Muestra sus propiedades"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    # Obtener propiedades del vendedor actual
    propiedades = Propiedad.query.filter_by(id_usuario=current_user.id_usuario).all()
    
    # Contar propiedades por estado
    total_propiedades = len(propiedades)
    disponibles = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='disponible').count()
    vendidas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='vendido').count()
    alquiladas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='alquilado').count()
    
    # ====== CONVERTIR A DICCIONARIOS PARA JSON ======
    propiedades_dict = []
    for prop in propiedades:
        prop_dict = prop.to_dict()
        # Agregar imágenes
        imagenes = Imagen.query.filter_by(id_propiedad=prop.id_propiedad).all()
        prop_dict['imagenes'] = [img.to_dict() for img in imagenes]
        propiedades_dict.append(prop_dict)
    # ==============================================
    
    return render_template(
        "vendedor/index.html",
        propiedades=propiedades,  # Para el renderizado del template
        propiedades_json=propiedades_dict,  # Para el JavaScript
        total_propiedades=total_propiedades,
        disponibles=disponibles,
        vendidas=vendidas,
        alquiladas=alquiladas
    )

@vendedor_bp.route("/publicar", methods=['GET', 'POST'])
@login_required
def publicar():
    """Publicar una nueva propiedad con imágenes"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion')
            tipo = request.form.get('tipo')
            superficie = request.form.get('superficie')
            direccion = request.form.get('direccion')
            precio = request.form.get('precio')
            estado = request.form.get('estado')
            id_departamento = request.form.get('id_departamento')
            id_provincia = request.form.get('id_provincia')
            id_ciudad = request.form.get('id_ciudad')
            
            # Validar campos obligatorios
            if not all([titulo, descripcion, tipo, superficie, direccion, precio, estado, id_departamento, id_provincia, id_ciudad]):
                return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
            
            # Crear la propiedad
            propiedad = Propiedad(
                titulo=titulo,
                descripcion=descripcion,
                tipo=tipo,
                superficie=float(superficie),
                direccion=direccion,
                precio=float(precio),
                estado=estado,
                id_departamento=int(id_departamento),
                id_provincia=int(id_provincia),
                id_ciudad=int(id_ciudad),
                id_usuario=current_user.id_usuario,
                fecha_publicacion=datetime.now().date()
            )
            
            db.session.add(propiedad)
            db.session.flush()  # Para obtener el ID de la propiedad
            
            # Procesar imágenes
            archivos = request.files.getlist('imagenes')
            imagenes_guardadas = []
            
            for archivo in archivos:
                if archivo and archivo.filename != '':
                    nombre_imagen = save_image(archivo)
                    if nombre_imagen:
                        imagen = Imagen(
                            imagen=nombre_imagen,
                            id_propiedad=propiedad.id_propiedad
                        )
                        db.session.add(imagen)
                        imagenes_guardadas.append(nombre_imagen)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Propiedad publicada correctamente',
                'id_propiedad': propiedad.id_propiedad,
                'imagenes': imagenes_guardadas
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    # GET - Mostrar formulario
    departamentos = Departamento.query.all()
    provincias = Provincia.query.all()
    ciudades = Ciudad.query.all()
    
    return render_template(
        "vendedor/publicar.html",
        departamentos=departamentos,
        provincias=provincias,
        ciudades=ciudades
    )

@vendedor_bp.route("/propiedad/<int:id_propiedad>")
@login_required
def ver_propiedad(id_propiedad):
    """Ver detalles de una propiedad específica con todos los datos del vendedor"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return render_template("main/index.html")
    
    # Obtener datos relacionados
    vendedor = Usuario.query.get(propiedad.id_usuario)
    departamento = Departamento.query.get(propiedad.id_departamento)
    provincia = Provincia.query.get(propiedad.id_provincia)
    ciudad = Ciudad.query.get(propiedad.id_ciudad)
    imagenes = Imagen.query.filter_by(id_propiedad=id_propiedad).all()
    
    # Datos del vendedor (sin password)
    datos_vendedor = vendedor.to_dict() if vendedor else None
    if datos_vendedor and 'password' in datos_vendedor:
        del datos_vendedor['password']
    
    return render_template(
        "vendedor/propiedad.html",
        propiedad=propiedad,
        vendedor=datos_vendedor,
        departamento=departamento,
        provincia=provincia,
        ciudad=ciudad,
        imagenes=imagenes
    )

@vendedor_bp.route("/propiedad/editar/<int:id_propiedad>", methods=['GET', 'POST'])
@login_required
def editar_propiedad(id_propiedad):
    """Editar una propiedad existente"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return render_template("main/index.html")
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            propiedad.titulo = request.form.get('titulo', propiedad.titulo)
            propiedad.descripcion = request.form.get('descripcion', propiedad.descripcion)
            propiedad.tipo = request.form.get('tipo', propiedad.tipo)
            propiedad.superficie = float(request.form.get('superficie', propiedad.superficie))
            propiedad.direccion = request.form.get('direccion', propiedad.direccion)
            propiedad.precio = float(request.form.get('precio', propiedad.precio))
            propiedad.estado = request.form.get('estado', propiedad.estado)
            
            if request.form.get('id_departamento'):
                propiedad.id_departamento = int(request.form.get('id_departamento'))
            if request.form.get('id_provincia'):
                propiedad.id_provincia = int(request.form.get('id_provincia'))
            if request.form.get('id_ciudad'):
                propiedad.id_ciudad = int(request.form.get('id_ciudad'))
            
            db.session.commit()
            
            # Redirigir a la vista de la propiedad
            return redirect(url_for('vendedor.ver_propiedad', id_propiedad=propiedad.id_propiedad))
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    # GET - Mostrar formulario con datos actuales
    departamentos = Departamento.query.all()
    provincias = Provincia.query.all()
    ciudades = Ciudad.query.all()
    
    return render_template(
        "vendedor/editar.html",
        propiedad=propiedad,
        departamentos=departamentos,
        provincias=provincias,
        ciudades=ciudades
    )

@vendedor_bp.route("/propiedad/eliminar/<int:id_propiedad>", methods=['POST'])
@login_required
def eliminar_propiedad(id_propiedad):
    """Eliminar una propiedad y todas sus imágenes"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        # Eliminar imágenes del sistema de archivos
        imagenes = Imagen.query.filter_by(id_propiedad=id_propiedad).all()
        for imagen in imagenes:
            delete_image(imagen.imagen)
        
        # Eliminar propiedad (las imágenes se eliminan por cascade en BD)
        db.session.delete(propiedad)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Propiedad eliminada correctamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================
# FUNCIONES PARA IMÁGENES
# ============================================

@vendedor_bp.route("/propiedad/<int:id_propiedad>/imagenes", methods=['POST'])
@login_required
def agregar_imagenes(id_propiedad):
    """Agregar imágenes a una propiedad existente"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        archivos = request.files.getlist('imagenes')
        imagenes_guardadas = []
        
        for archivo in archivos:
            if archivo and archivo.filename != '':
                nombre_imagen = save_image(archivo)
                if nombre_imagen:
                    imagen = Imagen(
                        imagen=nombre_imagen,
                        id_propiedad=id_propiedad
                    )
                    db.session.add(imagen)
                    imagenes_guardadas.append(nombre_imagen)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(imagenes_guardadas)} imagen(es) agregada(s) correctamente',
            'imagenes': imagenes_guardadas
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@vendedor_bp.route("/imagen/<int:id_imagen>", methods=['DELETE'])
@login_required
def eliminar_imagen(id_imagen):
    """Eliminar una imagen específica"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    imagen = Imagen.query.get_or_404(id_imagen)
    propiedad = Propiedad.query.get(imagen.id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        # Eliminar archivo del sistema
        delete_image(imagen.imagen)
        
        # Eliminar registro de la base de datos
        db.session.delete(imagen)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Imagen eliminada correctamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@vendedor_bp.route("/imagen/<int:id_imagen>/editar", methods=['POST'])
@login_required
def editar_imagen(id_imagen):
    """Reemplazar una imagen existente con una nueva"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    imagen = Imagen.query.get_or_404(id_imagen)
    propiedad = Propiedad.query.get(imagen.id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        archivo = request.files.get('imagen')
        if not archivo or archivo.filename == '':
            return jsonify({'success': False, 'message': 'No se ha enviado ninguna imagen'}), 400
        
        # Guardar nueva imagen
        nuevo_nombre = save_image(archivo)
        if not nuevo_nombre:
            return jsonify({'success': False, 'message': 'Formato de imagen no válido'}), 400
        
        # Eliminar imagen antigua
        delete_image(imagen.imagen)
        
        # Actualizar registro
        imagen.imagen = nuevo_nombre
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Imagen actualizada correctamente',
            'nueva_imagen': nuevo_nombre
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@vendedor_bp.route("/propiedad/<int:id_propiedad>/imagenes/orden", methods=['PUT'])
@login_required
def reordenar_imagenes(id_propiedad):
    """Reordenar las imágenes de una propiedad"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    try:
        # Esta es una funcionalidad más avanzada, se puede implementar con un campo 'orden'
        data = request.get_json()
        if not data or 'orden' not in data:
            return jsonify({'success': False, 'message': 'Datos inválidos'}), 400
        
        # Aquí iría la lógica para reordenar imágenes
        # Por ahora solo respondemos éxito
        return jsonify({'success': True, 'message': 'Orden actualizado correctamente'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================
# FUNCIONES PARA SERVIR IMÁGENES
# ============================================

@vendedor_bp.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    """Servir archivos de uploads para usuarios autenticados"""
    upload_folder = os.path.join(current_app.root_path, 'utils', 'uploads')
    return send_from_directory(upload_folder, filename)


# ============================================
# FUNCIONES PARA DEPARTAMENTOS, PROVINCIAS Y CIUDADES (API)
# ============================================

@vendedor_bp.route("/api/departamentos", methods=['GET'])
@login_required
def api_departamentos():
    """API para obtener departamentos"""
    departamentos = Departamento.query.all()
    return jsonify({
        'success': True,
        'data': [dep.to_dict() for dep in departamentos]
    })

@vendedor_bp.route("/api/provincias/<int:id_departamento>", methods=['GET'])
@login_required
def api_provincias(id_departamento):
    """API para obtener provincias por departamento"""
    provincias = Provincia.query.filter_by(id_departamento=id_departamento).all()
    return jsonify({
        'success': True,
        'data': [prov.to_dict() for prov in provincias]
    })

@vendedor_bp.route("/api/ciudades/<int:id_provincia>", methods=['GET'])
@login_required
def api_ciudades(id_provincia):
    """API para obtener ciudades por provincia"""
    ciudades = Ciudad.query.filter_by(id_provincia=id_provincia).all()
    return jsonify({
        'success': True,
        'data': [ciu.to_dict() for ciu in ciudades]
    })


@vendedor_bp.route("/api/propiedad/<int:id_propiedad>/imagenes", methods=['GET'])
@login_required
def api_obtener_imagenes(id_propiedad):
    """API para obtener todas las imágenes de una propiedad"""
    propiedad = Propiedad.query.get_or_404(id_propiedad)
    
    if propiedad.id_usuario != current_user.id_usuario:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    imagenes = Imagen.query.filter_by(id_propiedad=id_propiedad).all()
    
    data = []
    for img in imagenes:
        data.append({
            'id_imagen': img.id_imagen,
            'imagen': img.imagen,
            'url': url_for('vendedor.serve_upload', filename=img.imagen)
        })
    
    return jsonify({'success': True, 'data': data})





from datetime import datetime, timedelta
from sqlalchemy import func

# Agregar esta función después de las otras rutas
@vendedor_bp.route("/mis_ventas")
@login_required
def mis_ventas():
    """Panel de ventas del vendedor con gráficos"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    # Obtener todas las propiedades del vendedor
    propiedades = Propiedad.query.filter_by(id_usuario=current_user.id_usuario).all()
    
    # Estadísticas de ventas
    total_propiedades = len(propiedades)
    vendidas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='vendido').count()
    alquiladas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='alquilado').count()
    disponibles = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='disponible').count()
    
    # Calcular ingresos totales (propiedades vendidas)
    propiedades_vendidas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='vendido').all()
    ingresos_totales = sum([prop.precio for prop in propiedades_vendidas])
    
    # Ventas por mes (últimos 12 meses)
    meses = []
    ventas_mensuales = []
    ingresos_mensuales = []
    
    for i in range(12):
        mes = datetime.now().date().replace(day=1) - timedelta(days=30*i)
        inicio_mes = mes.replace(day=1)
        fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Propiedades vendidas en este mes
        ventas_mes = Propiedad.query.filter(
            Propiedad.id_usuario == current_user.id_usuario,
            Propiedad.estado == 'vendido',
            Propiedad.fecha_publicacion >= inicio_mes,
            Propiedad.fecha_publicacion <= fin_mes
        ).count()
        
        # Ingresos del mes
        ingresos_mes = db.session.query(func.sum(Propiedad.precio)).filter(
            Propiedad.id_usuario == current_user.id_usuario,
            Propiedad.estado == 'vendido',
            Propiedad.fecha_publicacion >= inicio_mes,
            Propiedad.fecha_publicacion <= fin_mes
        ).scalar() or 0
        
        meses.append(inicio_mes.strftime('%b %Y'))
        ventas_mensuales.append(ventas_mes)
        ingresos_mensuales.append(float(ingresos_mes))
    
    # Ventas por tipo de propiedad
    ventas_por_tipo = db.session.query(
        Propiedad.tipo,
        func.count(Propiedad.id_propiedad).label('total')
    ).filter(
        Propiedad.id_usuario == current_user.id_usuario,
        Propiedad.estado == 'vendido'
    ).group_by(Propiedad.tipo).all()
    
    # Datos para gráfico de tipo
    tipos = [t.tipo.capitalize() for t in ventas_por_tipo] if ventas_por_tipo else []
    cantidades = [t.total for t in ventas_por_tipo] if ventas_por_tipo else []
    
    # Propiedades recientes vendidas
    ventas_recientes = Propiedad.query.filter(
        Propiedad.id_usuario == current_user.id_usuario,
        Propiedad.estado == 'vendido'
    ).order_by(Propiedad.fecha_publicacion.desc()).limit(10).all()
    
    return render_template(
        "vendedor/mis_ventas.html",
        total_propiedades=total_propiedades,
        vendidas=vendidas,
        alquiladas=alquiladas,
        disponibles=disponibles,
        ingresos_totales=ingresos_totales,
        meses=meses,
        ventas_mensuales=ventas_mensuales,
        ingresos_mensuales=ingresos_mensuales,
        tipos=tipos,
        cantidades=cantidades,
        ventas_recientes=ventas_recientes
    )


@vendedor_bp.route("/exportar-catalogo")
@login_required
def exportar_catalogo():
    """Exportar catálogo de productos a CSV"""
    if current_user.rol.lower() != 'vendedor':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    propiedades = Propiedad.query.filter_by(id_usuario=current_user.id_usuario).all()
    
    # Crear archivo CSV en memoria
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow([
        'ID', 'Título', 'Tipo', 'Descripción', 'Precio (USD)', 
        'Superficie (m²)', 'Dirección', 'Estado', 'Fecha Publicación'
    ])
    
    # Escribir datos
    for prop in propiedades:
        writer.writerow([
            f'PR-{prop.id_propiedad}',
            prop.titulo,
            prop.tipo.capitalize(),
            prop.descripcion,
            f'{prop.precio:.2f}',
            prop.superficie,
            prop.direccion,
            prop.estado.capitalize(),
            prop.fecha_publicacion.strftime('%d/%m/%Y')
        ])
    
    # Crear respuesta
    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=catalogo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )



@vendedor_bp.route("/perfil")
@login_required
def perfil():
    """Perfil del vendedor con toda su información"""
    if current_user.rol.lower() != 'vendedor':
        return render_template("main/index.html")
    
    # Obtener estadísticas del vendedor
    total_propiedades = Propiedad.query.filter_by(id_usuario=current_user.id_usuario).count()
    propiedades_vendidas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='vendido').count()
    propiedades_activas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='disponible').count()
    propiedades_alquiladas = Propiedad.query.filter_by(id_usuario=current_user.id_usuario, estado='alquilado').count()
    
    # Calcular ingresos totales
    ingresos_totales = db.session.query(func.sum(Propiedad.precio)).filter(
        Propiedad.id_usuario == current_user.id_usuario,
        Propiedad.estado == 'vendido'
    ).scalar() or 0
    
    # Propiedades recientes
    propiedades_recientes = Propiedad.query.filter_by(
        id_usuario=current_user.id_usuario
    ).order_by(Propiedad.fecha_publicacion.desc()).limit(5).all()
    
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
        "vendedor/vendedor.html",
        usuario=current_user,
        fecha_registro=fecha_registro,
        antiguedad=antiguedad,
        total_propiedades=total_propiedades,
        propiedades_vendidas=propiedades_vendidas,
        propiedades_activas=propiedades_activas,
        propiedades_alquiladas=propiedades_alquiladas,
        ingresos_totales=ingresos_totales,
        propiedades_recientes=propiedades_recientes
    )