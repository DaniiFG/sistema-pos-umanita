from flask import Blueprint, render_template, request, jsonify
from app.models import db, Producto, Venta, DetalleVenta
from datetime import datetime

ventas_bp = Blueprint('ventas', __name__, template_folder='templates')

@ventas_bp.route('/')
def pos():
    # Obtenemos productos para mostrar en el Kiosco
    productos = Producto.query.all()
    # Si no hay productos (primera vez), creamos unos falsos para probar
    if not productos:
        p1 = Producto(nombre="Presa Broaster", precio=4500, categoria="Pollo")
        p2 = Producto(nombre="Gaseosa 350ml", precio=2500, categoria="Bebidas")
        p3 = Producto(nombre="Combo Personal", precio=12000, categoria="Combos")
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        productos = Producto.query.all()
        
    return render_template('pos.html', productos=productos)

@ventas_bp.route('/guardar_venta', methods=['POST'])
def guardar_venta():
    data = request.json
    
    # 1. Crear cabecera de venta
    nueva_venta = Venta(
        total_venta=data['total'],
        pago_efectivo=data['pagos']['efectivo'],
        pago_nequi=data['pagos']['nequi'],
        pago_daviplata=data['pagos']['daviplata'],
        tipo_venta=data['tipo']
    )
    db.session.add(nueva_venta)
    db.session.flush() # Para obtener el ID de la venta antes de commit
    
    # 2. Guardar detalles
    for item in data['carrito']:
        detalle = DetalleVenta(
            venta_id=nueva_venta.id,
            producto_nombre=item['nombre'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio'],
            subtotal=item['cantidad'] * item['precio']
        )
        db.session.add(detalle)
        
    db.session.commit()
    return jsonify({'status': 'ok', 'mensaje': 'Venta registrada con éxito'})