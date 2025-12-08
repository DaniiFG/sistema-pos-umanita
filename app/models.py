# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# --- 1. SEGURIDAD Y USUARIOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- 2. TERCEROS ---
class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(20))
    direccion = db.Column(db.String(150))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    gastos = db.relationship('Gasto', backref='proveedor', lazy=True)

# --- 3. VENTAS ---
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    costo_referencia = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50)) 
    es_combo = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    foto_url = db.Column(db.String(255), nullable=True) # Link externo (Legacy)
    imagen_local = db.Column(db.String(255), nullable=True) # Archivo local (Nuevo)

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    
    # Estados: 'Abierta' (Mesa ocupada), 'Cerrada' (Pagada)
    estado = db.Column(db.String(20), default='Cerrada') 
    mesa = db.Column(db.String(50), nullable=True) # Identificador de mesa
    
    total_venta = db.Column(db.Integer, nullable=False)
    descuento = db.Column(db.Integer, default=0) # Nuevo campo descuento
    
    pago_efectivo = db.Column(db.Integer, default=0)
    pago_nequi = db.Column(db.Integer, default=0)
    pago_daviplata = db.Column(db.Integer, default=0)
    pago_otros = db.Column(db.Integer, default=0)
    cambio_dado = db.Column(db.Integer, default=0)
    
    es_fantasma = db.Column(db.Boolean, default=False) # No sale en informes, solo afecta caja
    
    cliente_nombre = db.Column(db.String(100), default="Consumidor Final")
    cliente_nit = db.Column(db.String(20), default="222222222222")
    cliente_direccion = db.Column(db.String(150))
    cliente_telefono = db.Column(db.String(20))
    cliente_email = db.Column(db.String(100), nullable=True)
    
    es_domicilio = db.Column(db.Boolean, default=False)
    tipo_venta = db.Column(db.String(20), default='Directa') 
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True) # Nuevo: Vinculación real
    producto_nombre = db.Column(db.String(100)) # Backup del nombre
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    
    producto = db.relationship('Producto') # Relación para acceder a categoría actual

class IngresoOcasional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    descripcion = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Integer, nullable=False)
    origen = db.Column(db.String(50)) 
    metodo_pago = db.Column(db.String(20), default='Efectivo Caja') 
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

# --- 4. GASTOS ---
class ConceptoGasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False) 
    es_compra_insumo = db.Column(db.Boolean, default=False) 

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    categoria = db.Column(db.String(50), nullable=False) 
    descripcion = db.Column(db.String(200), nullable=False) 
    
    subtotal_base = db.Column(db.Integer, nullable=True) # Valor antes de IVA
    iva = db.Column(db.Integer, default=0)
    monto = db.Column(db.Integer, nullable=False) # Total final
    
    metodo_pago = db.Column(db.String(20), default='Efectivo de Caja')
    origen_dinero = db.Column(db.String(20), default='Caja Menor') # 'Caja Menor' o 'Caja Mayor'
    es_fantasma = db.Column(db.Boolean, default=False) # Oculto en informes
    
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=True)
    cantidad = db.Column(db.Float, nullable=True)
    unidad = db.Column(db.String(20), nullable=True)
    observacion = db.Column(db.String(200), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

# --- 5. INVENTARIO ---
class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50)) 
    cantidad_actual = db.Column(db.Float, default=0)
    unidad = db.Column(db.String(20), nullable=False) 
    minimo_alerta = db.Column(db.Float, default=5)
    movimientos = db.relationship('MovimientoInventario', backref='insumo', lazy=True)

class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) 
    cantidad = db.Column(db.Float, nullable=False)
    costo_unitario = db.Column(db.Integer, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    observacion = db.Column(db.String(200))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))