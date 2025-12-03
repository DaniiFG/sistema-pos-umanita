from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Producto, Venta, DetalleVenta, IngresoOcasional
from app.decorators import admin_required
from sqlalchemy import desc

ventas_bp = Blueprint('ventas', __name__, template_folder='templates')

@ventas_bp.route('/')
@login_required
def pos():
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('pos.html', productos=productos)

@ventas_bp.route('/guardar_venta', methods=['POST'])
@login_required
def guardar_venta():
    data = request.json
    cliente = data.get('cliente', {})
    es_domicilio = data.get('es_domicilio', False)
    
    nueva_venta = Venta(
        total_venta=data['total'],
        pago_efectivo=data['pagos']['efectivo'],
        pago_nequi=data['pagos']['nequi'],
        pago_daviplata=data['pagos']['daviplata'],
        tipo_venta=data['tipo'],
        usuario_id=current_user.id,
        es_domicilio=es_domicilio,
        cliente_nombre=cliente.get('nombre', 'Consumidor Final'),
        cliente_nit=cliente.get('nit', '222222222222'),
        cliente_direccion=cliente.get('direccion', ''),
        cliente_telefono=cliente.get('telefono', ''),
        cliente_email=cliente.get('email', '') # NUEVO
    )
    db.session.add(nueva_venta)
    db.session.flush()
    
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
    return jsonify({'status': 'ok', 'mensaje': 'Venta registrada', 'venta_id': nueva_venta.id})

@ventas_bp.route('/historial')
@login_required
def historial():
    # Mostrar últimas 50 ventas con detalles
    ventas = Venta.query.order_by(desc(Venta.fecha)).limit(50).all()
    return render_template('ventas_historial.html', ventas=ventas)

@ventas_bp.route('/ingresos_otros', methods=['GET', 'POST'])
@login_required
@admin_required
def ingresos_otros():
    if request.method == 'POST':
        nuevo_ingreso = IngresoOcasional(
            descripcion=request.form.get('descripcion'),
            monto=int(request.form.get('monto')),
            origen=request.form.get('origen'),
            metodo_pago=request.form.get('metodo_pago'), # NUEVO
            usuario_id=current_user.id
        )
        db.session.add(nuevo_ingreso)
        db.session.commit()
        flash('Ingreso registrado correctamente', 'success')
        return redirect(url_for('ventas.ingresos_otros'))
        
    historial = IngresoOcasional.query.order_by(IngresoOcasional.fecha.desc()).limit(50).all()
    return render_template('ingresos_otros.html', historial=historial)