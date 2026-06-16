from flask import redirect, request, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.admin import admin_bp
from app.models import Usuario, Propiedad, Provincia, Departamento, Ciudad, Auditoria, Imagen
from datetime import date, datetime
from sqlalchemy import func

# ============================================
# FUNCIONES PARA USUARIOS
# ============================================

@admin_bp.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    """Listar todos los usuarios con campos: id, nombre, correo"""
    try:
        # Verificar que sea administrador
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        usuarios = Usuario.query.all()
        
        # Datos básicos para la lista
        data = []
        for usuario in usuarios:
            data.append({
                "id": usuario.id_usuario,
                "nombre": usuario.nombre,
                "email": usuario.email
            })
        
        return jsonify({
            "success": True,
            "data": data,
            "total": len(data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al listar usuarios: {str(e)}"
        }), 500


@admin_bp.route('/usuarios/<int:id_usuario>', methods=['GET'])
@login_required
def ver_usuario(id_usuario):
    """Ver información completa de un usuario (sin password)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({
                "success": False,
                "message": "Usuario no encontrado"
            }), 404
        
        # Obtener datos del usuario sin password
        data = usuario.to_dict()
        # Asegurar que no se incluya el password
        if 'password' in data:
            del data['password']
        
        # Contar propiedades del usuario
        total_propiedades = Propiedad.query.filter_by(id_usuario=id_usuario).count()
        data['total_propiedades'] = total_propiedades
        
        return jsonify({
            "success": True,
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al obtener usuario: {str(e)}"
        }), 500


@admin_bp.route('/usuarios/<int:id_usuario>', methods=['DELETE'])
@login_required
def eliminar_usuario(id_usuario):
    """Eliminar un usuario (con todas sus propiedades en cascada)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        # No permitir eliminar al propio administrador
        if id_usuario == current_user.id_usuario:
            return jsonify({
                "success": False,
                "message": "No puedes eliminar tu propia cuenta"
            }), 400
        
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({
                "success": False,
                "message": "Usuario no encontrado"
            }), 404
        
        # Guardar datos para auditoría
        datos_usuario = usuario.to_dict()
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Usuario {usuario.nombre} eliminado correctamente",
            "data": datos_usuario
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al eliminar usuario: {str(e)}"
        }), 500


# ============================================
# FUNCIONES PARA PROPIEDADES
# ============================================

@admin_bp.route('/propiedades', methods=['GET'])
@login_required
def listar_propiedades():
    """Listar propiedades con: id, nombre_vendedor, propiedad (título)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        propiedades = Propiedad.query.all()
        
        data = []
        for prop in propiedades:
            vendedor = Usuario.query.get(prop.id_usuario)
            data.append({
                "id": prop.id_propiedad,
                "nombre_vendedor": vendedor.nombre if vendedor else "Desconocido",
                "propiedad": prop.titulo,
                "estado": prop.estado,
                "precio": prop.precio,
                "fecha_publicacion": prop.fecha_publicacion.strftime('%d/%m/%Y') if prop.fecha_publicacion else None
            })
        
        return jsonify({
            "success": True,
            "data": data,
            "total": len(data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al listar propiedades: {str(e)}"
        }), 500


@admin_bp.route('/propiedades/<int:id_propiedad>', methods=['GET'])
@login_required
def ver_propiedad(id_propiedad):
    """Ver todos los datos de una propiedad y su vendedor (sin password)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        propiedad = Propiedad.query.get(id_propiedad)
        if not propiedad:
            return jsonify({
                "success": False,
                "message": "Propiedad no encontrada"
            }), 404
        
        # Obtener datos del vendedor
        vendedor = Usuario.query.get(propiedad.id_usuario)
        datos_vendedor = vendedor.to_dict() if vendedor else None
        if datos_vendedor and 'password' in datos_vendedor:
            del datos_vendedor['password']
        
        # Obtener datos de ubicación
        departamento = Departamento.query.get(propiedad.id_departamento)
        provincia = Provincia.query.get(propiedad.id_provincia)
        ciudad = Ciudad.query.get(propiedad.id_ciudad)
        
        # Obtener imágenes
        imagenes = Imagen.query.filter_by(id_propiedad=id_propiedad).all()
        
        data = propiedad.to_dict()
        data['vendedor'] = datos_vendedor
        data['ubicacion'] = {
            "departamento": departamento.departamento if departamento else None,
            "provincia": provincia.provincia if provincia else None,
            "ciudad": ciudad.ciudad if ciudad else None
        }
        data['imagenes'] = [img.to_dict() for img in imagenes]
        
        return jsonify({
            "success": True,
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al obtener propiedad: {str(e)}"
        }), 500


@admin_bp.route('/propiedades/<int:id_propiedad>', methods=['DELETE'])
@login_required
def eliminar_propiedad(id_propiedad):
    """Eliminar una propiedad"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        propiedad = Propiedad.query.get(id_propiedad)
        if not propiedad:
            return jsonify({
                "success": False,
                "message": "Propiedad no encontrada"
            }), 404
        
        datos_propiedad = propiedad.to_dict()
        
        db.session.delete(propiedad)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Propiedad '{propiedad.titulo}' eliminada correctamente",
            "data": datos_propiedad
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al eliminar propiedad: {str(e)}"
        }), 500


# ============================================
# FUNCIONES PARA DEPARTAMENTOS
# ============================================

@admin_bp.route('/departamentos', methods=['GET'])
@login_required
def listar_departamentos():
    """Listar todos los departamentos"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        departamentos = Departamento.query.all()
        data = [dep.to_dict() for dep in departamentos]
        
        return jsonify({
            "success": True,
            "data": data,
            "total": len(data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al listar departamentos: {str(e)}"
        }), 500


@admin_bp.route('/departamentos', methods=['POST'])
@login_required
def crear_departamento():
    """Crear un nuevo departamento"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('departamento'):
            return jsonify({
                "success": False,
                "message": "El nombre del departamento es obligatorio"
            }), 400
        
        # Verificar si ya existe
        existente = Departamento.query.filter_by(departamento=data['departamento']).first()
        if existente:
            return jsonify({
                "success": False,
                "message": "El departamento ya existe"
            }), 409
        
        nuevo = Departamento(departamento=data['departamento'])
        db.session.add(nuevo)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Departamento creado correctamente",
            "data": nuevo.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al crear departamento: {str(e)}"
        }), 500


@admin_bp.route('/departamentos/<int:id_departamento>', methods=['PUT'])
@login_required
def editar_departamento(id_departamento):
    """Editar un departamento"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        departamento = Departamento.query.get(id_departamento)
        if not departamento:
            return jsonify({
                "success": False,
                "message": "Departamento no encontrado"
            }), 404
        
        data = request.get_json()
        if not data or not data.get('departamento'):
            return jsonify({
                "success": False,
                "message": "El nombre del departamento es obligatorio"
            }), 400
        
        # Verificar si ya existe otro con el mismo nombre
        existente = Departamento.query.filter(
            Departamento.departamento == data['departamento'],
            Departamento.id_departamento != id_departamento
        ).first()
        if existente:
            return jsonify({
                "success": False,
                "message": "Ya existe otro departamento con ese nombre"
            }), 409
        
        departamento.departamento = data['departamento']
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Departamento actualizado correctamente",
            "data": departamento.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al editar departamento: {str(e)}"
        }), 500


@admin_bp.route('/departamentos/<int:id_departamento>', methods=['DELETE'])
@login_required
def eliminar_departamento(id_departamento):
    """Eliminar un departamento (con sus provincias en cascada)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        departamento = Departamento.query.get(id_departamento)
        if not departamento:
            return jsonify({
                "success": False,
                "message": "Departamento no encontrado"
            }), 404
        
        # Verificar si tiene propiedades asociadas
        propiedades = Propiedad.query.filter_by(id_departamento=id_departamento).first()
        if propiedades:
            return jsonify({
                "success": False,
                "message": "No se puede eliminar el departamento porque tiene propiedades asociadas"
            }), 409
        
        datos = departamento.to_dict()
        db.session.delete(departamento)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Departamento eliminado correctamente",
            "data": datos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al eliminar departamento: {str(e)}"
        }), 500


# ============================================
# FUNCIONES PARA PROVINCIAS
# ============================================

@admin_bp.route('/provincias', methods=['GET'])
@login_required
def listar_provincias():
    """Listar todas las provincias"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        provincias = Provincia.query.all()
        data = [prov.to_dict() for prov in provincias]
        
        # Agregar nombre del departamento
        for item in data:
            dep = Departamento.query.get(item['id_departamento'])
            item['departamento_nombre'] = dep.departamento if dep else None
        
        return jsonify({
            "success": True,
            "data": data,
            "total": len(data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al listar provincias: {str(e)}"
        }), 500


@admin_bp.route('/provincias', methods=['POST'])
@login_required
def crear_provincia():
    """Crear una nueva provincia"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('provincia') or not data.get('id_departamento'):
            return jsonify({
                "success": False,
                "message": "Provincia y departamento son obligatorios"
            }), 400
        
        # Verificar que el departamento existe
        departamento = Departamento.query.get(data['id_departamento'])
        if not departamento:
            return jsonify({
                "success": False,
                "message": "Departamento no encontrado"
            }), 404
        
        # Verificar si ya existe
        existente = Provincia.query.filter_by(
            provincia=data['provincia'],
            id_departamento=data['id_departamento']
        ).first()
        if existente:
            return jsonify({
                "success": False,
                "message": "La provincia ya existe en este departamento"
            }), 409
        
        nueva = Provincia(
            provincia=data['provincia'],
            id_departamento=data['id_departamento']
        )
        db.session.add(nueva)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Provincia creada correctamente",
            "data": nueva.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al crear provincia: {str(e)}"
        }), 500


@admin_bp.route('/provincias/<int:id_provincia>', methods=['PUT'])
@login_required
def editar_provincia(id_provincia):
    """Editar una provincia"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        provincia = Provincia.query.get(id_provincia)
        if not provincia:
            return jsonify({
                "success": False,
                "message": "Provincia no encontrada"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Datos requeridos"
            }), 400
        
        if 'provincia' in data:
            provincia.provincia = data['provincia']
        
        if 'id_departamento' in data:
            # Verificar que el departamento existe
            departamento = Departamento.query.get(data['id_departamento'])
            if not departamento:
                return jsonify({
                    "success": False,
                    "message": "Departamento no encontrado"
                }), 404
            provincia.id_departamento = data['id_departamento']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Provincia actualizada correctamente",
            "data": provincia.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al editar provincia: {str(e)}"
        }), 500


@admin_bp.route('/provincias/<int:id_provincia>', methods=['DELETE'])
@login_required
def eliminar_provincia(id_provincia):
    """Eliminar una provincia (con sus ciudades en cascada)"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        provincia = Provincia.query.get(id_provincia)
        if not provincia:
            return jsonify({
                "success": False,
                "message": "Provincia no encontrada"
            }), 404
        
        # Verificar si tiene propiedades asociadas
        propiedades = Propiedad.query.filter_by(id_provincia=id_provincia).first()
        if propiedades:
            return jsonify({
                "success": False,
                "message": "No se puede eliminar la provincia porque tiene propiedades asociadas"
            }), 409
        
        datos = provincia.to_dict()
        db.session.delete(provincia)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Provincia eliminada correctamente",
            "data": datos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al eliminar provincia: {str(e)}"
        }), 500


# ============================================
# FUNCIONES PARA CIUDADES
# ============================================

@admin_bp.route('/ciudades', methods=['GET'])
@login_required
def listar_ciudades():
    """Listar todas las ciudades"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        ciudades = Ciudad.query.all()
        data = []
        for ciudad in ciudades:
            item = ciudad.to_dict()
            provincia = Provincia.query.get(ciudad.id_provincia)
            item['provincia_nombre'] = provincia.provincia if provincia else None
            if provincia:
                dep = Departamento.query.get(provincia.id_departamento)
                item['departamento_nombre'] = dep.departamento if dep else None
            data.append(item)
        
        return jsonify({
            "success": True,
            "data": data,
            "total": len(data)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al listar ciudades: {str(e)}"
        }), 500


@admin_bp.route('/ciudades', methods=['POST'])
@login_required
def crear_ciudad():
    """Crear una nueva ciudad"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        data = request.get_json()
        if not data or not data.get('ciudad') or not data.get('id_provincia'):
            return jsonify({
                "success": False,
                "message": "Ciudad y provincia son obligatorios"
            }), 400
        
        # Verificar que la provincia existe
        provincia = Provincia.query.get(data['id_provincia'])
        if not provincia:
            return jsonify({
                "success": False,
                "message": "Provincia no encontrada"
            }), 404
        
        # Verificar si ya existe
        existente = Ciudad.query.filter_by(
            ciudad=data['ciudad'],
            id_provincia=data['id_provincia']
        ).first()
        if existente:
            return jsonify({
                "success": False,
                "message": "La ciudad ya existe en esta provincia"
            }), 409
        
        nueva = Ciudad(
            ciudad=data['ciudad'],
            id_provincia=data['id_provincia']
        )
        db.session.add(nueva)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Ciudad creada correctamente",
            "data": nueva.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al crear ciudad: {str(e)}"
        }), 500


@admin_bp.route('/ciudades/<int:id_ciudad>', methods=['PUT'])
@login_required
def editar_ciudad(id_ciudad):
    """Editar una ciudad"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        ciudad = Ciudad.query.get(id_ciudad)
        if not ciudad:
            return jsonify({
                "success": False,
                "message": "Ciudad no encontrada"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Datos requeridos"
            }), 400
        
        if 'ciudad' in data:
            ciudad.ciudad = data['ciudad']
        
        if 'id_provincia' in data:
            provincia = Provincia.query.get(data['id_provincia'])
            if not provincia:
                return jsonify({
                    "success": False,
                    "message": "Provincia no encontrada"
                }), 404
            ciudad.id_provincia = data['id_provincia']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Ciudad actualizada correctamente",
            "data": ciudad.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al editar ciudad: {str(e)}"
        }), 500


@admin_bp.route('/ciudades/<int:id_ciudad>', methods=['DELETE'])
@login_required
def eliminar_ciudad(id_ciudad):
    """Eliminar una ciudad"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        ciudad = Ciudad.query.get(id_ciudad)
        if not ciudad:
            return jsonify({
                "success": False,
                "message": "Ciudad no encontrada"
            }), 404
        
        # Verificar si tiene propiedades asociadas
        propiedades = Propiedad.query.filter_by(id_ciudad=id_ciudad).first()
        if propiedades:
            return jsonify({
                "success": False,
                "message": "No se puede eliminar la ciudad porque tiene propiedades asociadas"
            }), 409
        
        datos = ciudad.to_dict()
        db.session.delete(ciudad)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Ciudad eliminada correctamente",
            "data": datos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error al eliminar ciudad: {str(e)}"
        }), 500


# ============================================
# FUNCIONES PARA ESTADÍSTICAS DEL ADMIN
# ============================================

@admin_bp.route('/estadisticas', methods=['GET'])
@login_required
def obtener_estadisticas():
    """Obtener estadísticas generales para el admin"""
    try:
        if current_user.rol.lower() != 'administrador':
            return jsonify({
                "success": False,
                "message": "No tienes permisos para realizar esta acción"
            }), 403
        
        total_usuarios = Usuario.query.count()
        total_propiedades = Propiedad.query.count()
        total_departamentos = Departamento.query.count()
        total_provincias = Provincia.query.count()
        total_ciudades = Ciudad.query.count()
        
        # Propiedades por estado
        disponibles = Propiedad.query.filter_by(estado='disponible').count()
        vendidos = Propiedad.query.filter_by(estado='vendido').count()
        alquilados = Propiedad.query.filter_by(estado='alquilado').count()
        
        # Usuarios por rol
        administradores = Usuario.query.filter_by(rol='administrador').count()
        vendedores = Usuario.query.filter_by(rol='vendedor').count()
        clientes = Usuario.query.filter_by(rol='cliente').count()
        
        return jsonify({
            "success": True,
            "data": {
                "usuarios": {
                    "total": total_usuarios,
                    "administradores": administradores,
                    "vendedores": vendedores,
                    "clientes": clientes
                },
                "propiedades": {
                    "total": total_propiedades,
                    "disponibles": disponibles,
                    "vendidos": vendidos,
                    "alquilados": alquilados
                },
                "ubicaciones": {
                    "departamentos": total_departamentos,
                    "provincias": total_provincias,
                    "ciudades": total_ciudades
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error al obtener estadísticas: {str(e)}"
        }), 500
    
