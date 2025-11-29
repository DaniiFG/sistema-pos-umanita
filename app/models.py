from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# --- 1. SEGURIDAD Y USUARIOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False) # 'admin' o 'cajero'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- 2. MÓDULO DE INGRESOS (VENTAS) ---
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    costo_referencia = db.Column(db.Integer, default=0) # Para informe P&G
    categoria = db.Column(db.String(50)) # 'Pollo', 'Comida Rapida', 'Bebidas', 'Adiciones'
    es_combo = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True) # Borrado lógico

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    total_venta = db.Column(db.Integer, nullable=False)
    
    # Desglose de pagos
    pago_efectivo = db.Column(db.Integer, default=0)
    pago_nequi = db.Column(db.Integer, default=0)
    pago_daviplata = db.Column(db.Integer, default=0)
    cambio_dado = db.Column(db.Integer, default=0)
    
    tipo_venta = db.Column(db.String(20), default='Directa') # 'Directa', 'Fiado', 'Ocasional'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_nombre = db.Column(db.String(100))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

# --- 3. MÓDULO DE EGRESOS (GASTOS) ---
class ConceptoGasto(db.Model):
    """Lista predefinida de tipos de gasto para evitar errores de escritura"""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) # Ej: "Compra de Pollo"
    categoria = db.Column(db.String(50), nullable=False) # 'Materia Prima', 'Nomina', etc.

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    categoria = db.Column(db.String(50), nullable=False) 
    descripcion = db.Column(db.String(200), nullable=False) # Nombre tomado del ConceptoGasto
    monto = db.Column(db.Integer, nullable=False)
    
    # Detalles físicos
    cantidad = db.Column(db.Float, nullable=True)
    unidad = db.Column(db.String(20), nullable=True)
    
    # Nota adicional opcional
    observacion = db.Column(db.String(200), nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

# --- 4. MÓDULO DE INVENTARIO ---
class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50)) # 'Materia Prima', 'Desechables', 'Aseo', 'Activos'
    cantidad_actual = db.Column(db.Float, default=0)
    unidad = db.Column(db.String(20), nullable=False) 
    minimo_alerta = db.Column(db.Float, default=5)
    
    movimientos = db.relationship('MovimientoInventario', backref='insumo', lazy=True)

class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'ENTRADA', 'SALIDA'
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Integer, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    observacion = db.Column(db.String(200))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))