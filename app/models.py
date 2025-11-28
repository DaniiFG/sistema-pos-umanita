from datetime import datetime
from app import db

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(50)) # Ej: "Pollo", "Bebida"
    imagen = db.Column(db.String(100), default='default.jpg') # Nombre archivo

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    total_venta = db.Column(db.Integer, nullable=False)
    
    # Desglose de pagos (Vital para arqueo de caja)
    pago_efectivo = db.Column(db.Integer, default=0)
    pago_nequi = db.Column(db.Integer, default=0)
    pago_daviplata = db.Column(db.Integer, default=0)
    
    # Tipo: 'Directa', 'Fiado', 'Ocasional'
    tipo_venta = db.Column(db.String(20), default='Directa') 
    
    # Relación con items (Uno a Muchos)
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_nombre = db.Column(db.String(100)) # Guardamos nombre por si borran el producto original
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    
    # Categoría: 'Materia Prima', 'Nomina', 'Servicios', 'Otros'
    categoria = db.Column(db.String(50), nullable=False) 
    
    descripcion = db.Column(db.String(200), nullable=False) # Ej: "Pago turno María", "2 Bultos de Papa"
    monto = db.Column(db.Integer, nullable=False)
    
    # Campos específicos para Materia Prima (Vital para inventario futuro)
    cantidad = db.Column(db.Integer, nullable=True) # Ej: 2
    unidad = db.Column(db.String(20), nullable=True) # Ej: "Bultos", "Cajas", "Libras"
    

class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad_actual = db.Column(db.Integer, default=0)
    unidad = db.Column(db.String(20), nullable=False) # Ej: Bultos, Botellas, Litros
    minimo_alerta = db.Column(db.Integer, default=5) # Para avisar si se acaba
    
    # Relación con movimientos (Historial)
    movimientos = db.relationship('MovimientoInventario', backref='insumo', lazy=True)

class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'ENTRADA' o 'SALIDA'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    nota = db.Column(db.String(200)) # Ej: "Compra semanal" o "Se rompió una botella"