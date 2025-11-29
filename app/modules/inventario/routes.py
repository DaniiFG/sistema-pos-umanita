from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Insumo, MovimientoInventario
from sqlalchemy import desc

inventario_bp = Blueprint('inventario', __name__, template_folder='templates')

@inventario_bp.route('/')
@login_required
def index():
    # Obtenemos todos los insumos ordenados por nombre
    # En el HTML los filtraremos por categorías usando Jinja para no hacer 4 consultas
    insumos = Insumo.query.order_by(Insumo.nombre).all()
    return render_template('inventario.html', insumos=insumos)

@inventario_bp.route('/crear', methods=['POST'])
@login_required
def crear_insumo():
    nuevo = Insumo(
        nombre=request.form.get('nombre'),
        categoria=request.form.get('categoria'),
        unidad=request.form.get('unidad'),
        minimo_alerta=float(request.form.get('minimo'))
    )
    db.session.add(nuevo)
    db.session.commit()
    flash(f'Producto "{nuevo.nombre}" creado en bodega.', 'success')
    return redirect(url_for('inventario.index'))

@inventario_bp.route('/movimiento', methods=['POST'])
@login_required
def movimiento():
    insumo_id = request.form.get('insumo_id')
    tipo = request.form.get('tipo') # 'ENTRADA' o 'SALIDA'
    cantidad = float(request.form.get('cantidad'))
    observacion = request.form.get('observacion')
    
    insumo = Insumo.query.get_or_404(insumo_id)
    
    # Validaciones
    if tipo == 'SALIDA' and insumo.cantidad_actual < cantidad:
        flash(f'Error: No hay suficiente stock de {insumo.nombre}.', 'danger')
        return redirect(url_for('inventario.index'))

    # Actualizamos Stock
    if tipo == 'ENTRADA':
        insumo.cantidad_actual += cantidad
        # Si es entrada, capturamos el costo para valorizar inventario
        costo = int(request.form.get('costo_unitario')) if request.form.get('costo_unitario') else 0
    else:
        insumo.cantidad_actual -= cantidad
        costo = 0 # En salida no registramos costo de compra

    # Guardamos en Historial (Kardex)
    mov = MovimientoInventario(
        insumo_id=insumo.id,
        tipo=tipo,
        cantidad=cantidad,
        costo_unitario=costo,
        observacion=observacion,
        usuario_id=current_user.id
    )
    
    db.session.add(mov)
    db.session.commit()
    
    flash('Movimiento registrado correctamente.', 'success')
    return redirect(url_for('inventario.index'))

@inventario_bp.route('/historial')
@login_required
def historial():
    # Traemos los últimos 100 movimientos ordenados del más reciente al más antiguo
    movimientos = MovimientoInventario.query.order_by(desc(MovimientoInventario.fecha)).limit(100).all()
    return render_template('historial.html', movimientos=movimientos)