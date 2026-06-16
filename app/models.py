from flask_login import UserMixin
from app.extensions import db
from datetime import datetime
import getpass
import os

class Usuario(db.Model, UserMixin):
    __tablename__ = "users"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)  
    telefono = db.Column(db.String(20), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  
    password = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False)
    
    # Relación con Propiedad con CASCADE
    propiedades = db.relationship('Propiedad', back_populates='usuario', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.id_usuario)

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol,
            "fecha_registro": self.fecha_registro
        }
    


class Auditoria(db.Model):
    __tablename__ = "auditoria"
    
    id_auditoria = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('users.id_usuario'), nullable=True)  # Permitir NULL
    nombre_usuario = db.Column(db.String(100), nullable=True)
    email_usuario = db.Column(db.String(100), nullable=True)
    tabla_afectada = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    accion = db.Column(db.String(10), nullable=False)
    datos_anteriores = db.Column(db.Text, nullable=True)
    datos_nuevos = db.Column(db.Text, nullable=True)
    fecha_actividad = db.Column(db.Date, nullable=False)
    hora_actividad = db.Column(db.Time, nullable=False)
    user_sistema = db.Column(db.String(100), nullable=True)
    ip_usuario = db.Column(db.String(45), nullable=True)
    endpoint = db.Column(db.String(200), nullable=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import datetime
        ahora = datetime.now()
        self.fecha_actividad = ahora.date()
        self.hora_actividad = ahora.time()
        import getpass
        self.user_sistema = getpass.getuser()






class Departamento(db.Model):
    __tablename__ = "departamentos"
    id_departamento = db.Column(db.Integer, primary_key=True)
    departamento = db.Column(db.String(100), nullable=False)
    
    # Relación con Provincia con CASCADE
    provincias = db.relationship('Provincia', back_populates='departamento', lazy=True, cascade="all, delete-orphan")
    
    # Relación con Propiedad (SIN cascade para no eliminar propiedades al eliminar departamento)
    propiedades = db.relationship('Propiedad', back_populates='departamento', lazy=True)

    def to_dict(self):
        return {
            "id_departamento": self.id_departamento,
            "departamento": self.departamento
        }

class Provincia(db.Model):
    __tablename__ = "provincias"
    id_provincia = db.Column(db.Integer, primary_key=True)
    provincia = db.Column(db.String(100), nullable=False)
    
    # Clave foránea a Departamento
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id_departamento'), nullable=False)
    
    # Relaciones
    departamento = db.relationship('Departamento', back_populates='provincias')
    
    # Relación con Ciudad con CASCADE
    ciudades = db.relationship('Ciudad', back_populates='provincia', lazy=True, cascade="all, delete-orphan")
    
    # Relación con Propiedad (SIN cascade)
    propiedades = db.relationship('Propiedad', back_populates='provincia', lazy=True)

    def to_dict(self):
        return {
            "id_provincia": self.id_provincia,
            "provincia": self.provincia,
            "id_departamento": self.id_departamento
        }

class Ciudad(db.Model):
    __tablename__ = "ciudades"
    id_ciudad = db.Column(db.Integer, primary_key=True)  
    ciudad = db.Column(db.String(100), nullable=False)
    
    # Clave foránea a Provincia
    id_provincia = db.Column(db.Integer, db.ForeignKey('provincias.id_provincia'), nullable=False)
    
    # Relaciones
    provincia = db.relationship('Provincia', back_populates='ciudades')
    
    # Relación con Propiedad (SIN cascade)
    propiedades = db.relationship('Propiedad', back_populates='ciudad', lazy=True)

    def to_dict(self):
        return {
            "id_ciudad": self.id_ciudad,
            "ciudad": self.ciudad,
            "id_provincia": self.id_provincia
        }

class Propiedad(db.Model):
    __tablename__ = "propiedades"
    id_propiedad = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)  
    tipo = db.Column(db.String(50), nullable=False)  
    superficie = db.Column(db.Float, nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), nullable=False) 
    fecha_publicacion = db.Column(db.Date, nullable=False)
    
    # Claves foráneas
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id_departamento'), nullable=False)
    id_provincia = db.Column(db.Integer, db.ForeignKey('provincias.id_provincia'), nullable=False)
    id_ciudad = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('users.id_usuario'), nullable=False)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='propiedades')
    departamento = db.relationship('Departamento', back_populates='propiedades')
    provincia = db.relationship('Provincia', back_populates='propiedades')
    ciudad = db.relationship('Ciudad', back_populates='propiedades')
    
    # Relación con Imagen con CASCADE (ya lo tienes)
    imagenes = db.relationship('Imagen',back_populates='propiedad', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id_propiedad": self.id_propiedad,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "superficie": self.superficie,
            "direccion": self.direccion,
            "precio": self.precio,
            "estado": self.estado,
            "fecha_publicacion": self.fecha_publicacion,
            "id_departamento": self.id_departamento,
            "id_provincia": self.id_provincia,
            "id_ciudad": self.id_ciudad,  
            "id_usuario": self.id_usuario
        }

class Imagen(db.Model):
    __tablename__ = "imagenes"
    id_imagen = db.Column(db.Integer, primary_key=True)
    imagen = db.Column(db.String(255), nullable=False)
    id_propiedad = db.Column(db.Integer, db.ForeignKey('propiedades.id_propiedad'), nullable=False)
    
    # Relación con Propiedad
    propiedad = db.relationship('Propiedad', back_populates='imagenes')
    
    def to_dict(self):
        return {
            "id_imagen": self.id_imagen,
            "imagen": self.imagen,
            "id_propiedad": self.id_propiedad
        }
    



# ==================================================
# EVENTOS DE AUDITORÍA CORREGIDOS
# ==================================================

from sqlalchemy import event
import json
import sys

def after_insert_listener(mapper, connection, target):
    """Evento que se dispara después de INSERTAR un registro - VERSIÓN CORREGIDA"""
    try:
        # Obtener el ID del registro insertado
        id_registro = getattr(target, list(target.__table__.primary_key.columns)[0].name)
        
        # Obtener datos del objeto
        datos_nuevos = None
        if hasattr(target, 'to_dict'):
            datos_nuevos = target.to_dict()
        
        # Obtener información del usuario actual desde la conexión
        # Usar una conexión separada para evitar conflictos
        from app.utils.audit import AuditSystem
        
        # Crear el registro de auditoría
        user_info = AuditSystem.get_current_user_info()
        request_info = AuditSystem.get_request_info()
        
        from app.models import Auditoria
        from datetime import datetime
        
        auditoria = Auditoria(
            id_usuario=user_info['id'],
            nombre_usuario=user_info['nombre'],
            email_usuario=user_info['email'],
            tabla_afectada=target.__tablename__,
            registro_id=id_registro,
            accion='INSERT',
            datos_nuevos=json.dumps(datos_nuevos, default=str) if datos_nuevos else None,
            ip_usuario=request_info['ip'],
            endpoint=request_info['endpoint']
        )
        
        # Usar la conexión directamente para evitar conflictos con la sesión
        connection.execute(
            Auditoria.__table__.insert().values(
                id_usuario=auditoria.id_usuario,
                nombre_usuario=auditoria.nombre_usuario,
                email_usuario=auditoria.email_usuario,
                tabla_afectada=auditoria.tabla_afectada,
                registro_id=auditoria.registro_id,
                accion=auditoria.accion,
                datos_nuevos=auditoria.datos_nuevos,
                ip_usuario=auditoria.ip_usuario,
                endpoint=auditoria.endpoint,
                fecha_actividad=datetime.now().date(),
                hora_actividad=datetime.now().time(),
                user_sistema=auditoria.user_sistema
            )
        )
        print(f"✅ Auditoría INSERT registrada para {target.__tablename__} ID:{id_registro}")
        
    except Exception as e:
        print(f"❌ Error en after_insert: {str(e)}")
        # No interrumpir la operación principal

def after_update_listener(mapper, connection, target):
    """Evento que se dispara después de ACTUALIZAR un registro - VERSIÓN CORREGIDA"""
    try:
        id_registro = getattr(target, list(target.__table__.primary_key.columns)[0].name)
        
        # Obtener datos anteriores (no podemos obtenerlos fácilmente, así que omitimos por ahora)
        datos_nuevos = None
        if hasattr(target, 'to_dict'):
            datos_nuevos = target.to_dict()
        
        from app.utils.audit import AuditSystem
        
        user_info = AuditSystem.get_current_user_info()
        request_info = AuditSystem.get_request_info()
        
        from app.models import Auditoria
        from datetime import datetime
        
        auditoria = Auditoria(
            id_usuario=user_info['id'],
            nombre_usuario=user_info['nombre'],
            email_usuario=user_info['email'],
            tabla_afectada=target.__tablename__,
            registro_id=id_registro,
            accion='UPDATE',
            datos_nuevos=json.dumps(datos_nuevos, default=str) if datos_nuevos else None,
            ip_usuario=request_info['ip'],
            endpoint=request_info['endpoint']
        )
        
        connection.execute(
            Auditoria.__table__.insert().values(
                id_usuario=auditoria.id_usuario,
                nombre_usuario=auditoria.nombre_usuario,
                email_usuario=auditoria.email_usuario,
                tabla_afectada=auditoria.tabla_afectada,
                registro_id=auditoria.registro_id,
                accion=auditoria.accion,
                datos_nuevos=auditoria.datos_nuevos,
                ip_usuario=auditoria.ip_usuario,
                endpoint=auditoria.endpoint,
                fecha_actividad=datetime.now().date(),
                hora_actividad=datetime.now().time(),
                user_sistema=auditoria.user_sistema
            )
        )
        print(f"✅ Auditoría UPDATE registrada para {target.__tablename__} ID:{id_registro}")
        
    except Exception as e:
        print(f"❌ Error en after_update: {str(e)}")

def after_delete_listener(mapper, connection, target):
    """Evento que se dispara después de ELIMINAR un registro - VERSIÓN CORREGIDA"""
    try:
        id_registro = getattr(target, list(target.__table__.primary_key.columns)[0].name)
        
        # Obtener datos eliminados
        datos_anteriores = None
        if hasattr(target, 'to_dict'):
            datos_anteriores = target.to_dict()
        
        from app.utils.audit import AuditSystem
        
        user_info = AuditSystem.get_current_user_info()
        request_info = AuditSystem.get_request_info()
        
        from app.models import Auditoria
        from datetime import datetime
        
        auditoria = Auditoria(
            id_usuario=user_info['id'],
            nombre_usuario=user_info['nombre'],
            email_usuario=user_info['email'],
            tabla_afectada=target.__tablename__,
            registro_id=id_registro,
            accion='DELETE',
            datos_anteriores=json.dumps(datos_anteriores, default=str) if datos_anteriores else None,
            ip_usuario=request_info['ip'],
            endpoint=request_info['endpoint']
        )
        
        connection.execute(
            Auditoria.__table__.insert().values(
                id_usuario=auditoria.id_usuario,
                nombre_usuario=auditoria.nombre_usuario,
                email_usuario=auditoria.email_usuario,
                tabla_afectada=auditoria.tabla_afectada,
                registro_id=auditoria.registro_id,
                accion=auditoria.accion,
                datos_anteriores=auditoria.datos_anteriores,
                ip_usuario=auditoria.ip_usuario,
                endpoint=auditoria.endpoint,
                fecha_actividad=datetime.now().date(),
                hora_actividad=datetime.now().time(),
                user_sistema=auditoria.user_sistema
            )
        )
        print(f"✅ Auditoría DELETE registrada para {target.__tablename__} ID:{id_registro}")
        
    except Exception as e:
        print(f"❌ Error en after_delete: {str(e)}")

# Registrar los eventos para TODOS los modelos
def register_audit_events(model_class):
    """Registrar eventos de auditoría para un modelo"""
    event.listen(model_class, 'after_insert', after_insert_listener)
    event.listen(model_class, 'after_update', after_update_listener)
    event.listen(model_class, 'after_delete', after_delete_listener)

# Lista de modelos a auditar (excluir Auditoria para evitar bucles infinitos)
modelos_a_auditar = [Usuario, Propiedad, Imagen, Departamento, Provincia, Ciudad]

# Registrar eventos para cada modelo
for modelo in modelos_a_auditar:
    register_audit_events(modelo)
    print(f"✅ Eventos de auditoría registrados para {modelo.__name__}")