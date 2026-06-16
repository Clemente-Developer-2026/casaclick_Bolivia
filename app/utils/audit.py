from app.extensions import db
from app.models import Auditoria
from flask import request, has_request_context
from flask_login import current_user
from datetime import datetime
import json
import getpass
import os

class AuditSystem:
    """Sistema de auditoría para registrar todas las operaciones"""
    
    @staticmethod
    def get_current_user_info():
        """Obtener información del usuario actual"""
        if has_request_context() and current_user.is_authenticated:
            return {
                'id': current_user.id_usuario,
                'nombre': current_user.nombre,
                'email': current_user.email
            }
        return {
            'id': None,
            'nombre': 'SISTEMA',
            'email': 'sistema@audit.local'
        }
    
    @staticmethod
    def get_request_info():
        """Obtener información de la petición actual"""
        if has_request_context():
            return {
                'ip': request.remote_addr,
                'endpoint': request.endpoint,
                'method': request.method
            }
        return {
            'ip': None,
            'endpoint': 'script_externo',
            'method': 'UNKNOWN'
        }
    
    @staticmethod
    def registrar_auditoria(tabla, registro_id, accion, datos_anteriores=None, datos_nuevos=None):
        """Registrar una acción en la tabla de auditoría"""
        try:
            user_info = AuditSystem.get_current_user_info()
            request_info = AuditSystem.get_request_info()
            
            # Crear el objeto de auditoría pero NO hacer commit aquí
            auditoria = Auditoria(
                id_usuario=user_info['id'],
                nombre_usuario=user_info['nombre'],
                email_usuario=user_info['email'],
                tabla_afectada=tabla,
                registro_id=registro_id,
                accion=accion.upper(),
                datos_anteriores=json.dumps(datos_anteriores, default=str) if datos_anteriores else None,
                datos_nuevos=json.dumps(datos_nuevos, default=str) if datos_nuevos else None,
                ip_usuario=request_info['ip'],
                endpoint=request_info['endpoint']
            )
            
            # Agregar a la sesión sin commit
            db.session.add(auditoria)
            # No hacer commit aquí - la transacción principal se encargará
            print(f"✅ Auditoría registrada: {accion} en {tabla} ID:{registro_id}")
            
        except Exception as e:
            print(f"❌ Error al registrar auditoría: {str(e)}")
            # No hacer rollback aquí

# Funciones helper para registrar operaciones específicas
def audit_insert(modelo, instancia):
    """Registrar inserción de un registro"""
    AuditSystem.registrar_auditoria(
        tabla=modelo.__tablename__,
        registro_id=instancia.id_propiedad if hasattr(instancia, 'id_propiedad') 
                    else getattr(instancia, list(instancia.__table__.primary_key.columns)[0].name),
        accion='INSERT',
        datos_nuevos=instancia.to_dict() if hasattr(instancia, 'to_dict') else None
    )

def audit_update(modelo, instancia, datos_anteriores):
    """Registrar actualización de un registro"""
    AuditSystem.registrar_auditoria(
        tabla=modelo.__tablename__,
        registro_id=instancia.id_propiedad if hasattr(instancia, 'id_propiedad') 
                    else getattr(instancia, list(instancia.__table__.primary_key.columns)[0].name),
        accion='UPDATE',
        datos_anteriores=datos_anteriores,
        datos_nuevos=instancia.to_dict() if hasattr(instancia, 'to_dict') else None
    )

def audit_delete(modelo, id_registro, datos_eliminados):
    """Registrar eliminación de un registro"""
    AuditSystem.registrar_auditoria(
        tabla=modelo.__tablename__,
        registro_id=id_registro,
        accion='DELETE',
        datos_anteriores=datos_eliminados
    )