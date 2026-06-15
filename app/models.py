from flask_login import UserMixin
from app.extensions import db

class Usuario(db.Model,UserMixin):
    __tablename__ = "users"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    telefono = db.Column(db.String, nullable=False)
    rol = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False)

    def get_id(self):
        return str(self.id_usuario)

    def to_dict(self):
        return{
            "id" : self.id_usuario,
            "nombre" : self.nombre,
            "email" : self.email,
            "telefono" : self.telefono,
            "rol" : self.rol,
            "fecha_registro" : self.fecha_registro
        }