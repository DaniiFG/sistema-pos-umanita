# app/modules/ventas/routes.py
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

@ventas_bp.route('/guardar_mesa', methods=['POST'])
@login_required
def guardar_mesa():
    data = request.json
    mesa = data.get('mesa')
    carrito = data.get('carrito')
    
    # Buscar si ya existe una orden abierta para esa mesa
    venta_existente = Venta.query.filter_by(mesa=mesa, estado='Abierta').first()
    
    if venta_existente:
        # Actualizar: Borrar detalles anteriores y poner los nuevos (estrategia simple)
        DetalleVenta.query.filter_by(venta_id=venta_existente.id).delete()
        venta_existente.total_venta = sum(i['precio']*i['cantidad'] for i in carrito)
    else:
        # Crear nueva venta abierta
        venta_existente = Venta(
            mesa=mesa,
            estado='Abierta',
            total_venta=sum(i['precio']*i['cantidad'] for i in carrito),
            usuario_id=current_user.id
        )
        db.session.add(venta_existente)
    
    db.session.flush() # Para tener ID
    
    for item in carrito:
        det = DetalleVenta(
            venta_id=venta_existente.id,
            producto_id=item['id'],
            producto_nombre=item['nombre'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio'],
            subtotal=item['cantidad'] * item['precio']
        )
        db.session.add(det)
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@ventas_bp.route('/obtener_mesa/<mesa>')
@login_required
def obtener_mesa(mesa):
    venta = Venta.query.filter_by(mesa=mesa, estado='Abierta').first()
    if not venta:
        return jsonify({'carrito': []})
    
    carrito = []
    for d in venta.detalles:
        # Recuperar nombre actualizado si es posible
        nombre_prod = d.producto.nombre if d.producto else d.producto_nombre
        carrito.append({
            'id': d.producto_id,
            'nombre': nombre_prod,
            'cantidad': d.cantidad,
            'precio': d.precio_unitario
        })
    return jsonify({'carrito': carrito})

@ventas_bp.route('/mesas_ocupadas')
@login_required
def mesas_ocupadas():
    ventas = Venta.query.filter_by(estado='Abierta').all()
    mesas = [v.mesa for v in ventas]
    return jsonify({'mesas': mesas})

@ventas_bp.route('/cobrar', methods=['POST'])
@login_required
def cobrar():
    data = request.json
    mesa = data.get('mesa')
    cliente = data.get('cliente', {})
    
    # Buscar la venta abierta o crear una nueva si es mostrador inmediato
    venta = Venta.query.filter_by(mesa=mesa, estado='Abierta').first()
    if not venta:
        venta = Venta(mesa=mesa, usuario_id=current_user.id)
        db.session.add(venta)
    
    # Actualizar datos finales
    venta.estado = 'Cerrada'
    venta.total_venta = data['total']
    venta.descuento = data.get('descuento', 0)
    venta.pago_efectivo = data['pagos']['efectivo']
    venta.pago_nequi = data['pagos']['nequi']
    venta.pago_daviplata = data['pagos']['daviplata']
    venta.cambio_dado = data.get('cambio', 0)
    venta.es_fantasma = data.get('es_fantasma', False)
    
    venta.cliente_nombre = cliente.get('nombre', 'Consumidor Final')
    venta.cliente_nit = cliente.get('nit', '222222222222')
    venta.cliente_telefono = cliente.get('telefono', '')
    venta.cliente_direccion = cliente.get('direccion', '')
    
    # Re-guardar detalles para asegurar consistencia final
    DetalleVenta.query.filter_by(venta_id=venta.id).delete()
    for item in data['carrito']:
        det = DetalleVenta(
            venta_id=venta.id,
            producto_id=item['id'],
            producto_nombre=item['nombre'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio'],
            subtotal=item['cantidad'] * item['precio']
        )
        db.session.add(det)
        
    db.session.commit()
    return jsonify({'status': 'ok'})

@ventas_bp.route('/historial')
@login_required
def historial():
    ventas = Venta.query.filter_by(estado='Cerrada').order_by(desc(Venta.fecha)).limit(50).all()
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
            metodo_pago=request.form.get('metodo_pago'), 
            usuario_id=current_user.id
        )
        db.session.add(nuevo_ingreso)
        db.session.commit()
        flash('Ingreso registrado correctamente', 'success')
        return redirect(url_for('ventas.ingresos_otros'))
        
    historial = IngresoOcasional.query.order_by(IngresoOcasional.fecha.desc()).limit(50).all()
    return render_template('ingresos_otros.html', historial=historial)