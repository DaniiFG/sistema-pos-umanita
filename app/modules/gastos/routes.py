from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Gasto, ConceptoGasto, Proveedor, Insumo, MovimientoInventario
from app.decorators import admin_required
from datetime import datetime

gastos_bp = Blueprint('gastos', __name__, template_folder='templates')

@gastos_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Cargar datos para los selects
    conceptos = ConceptoGasto.query.order_by(ConceptoGasto.categoria, ConceptoGasto.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).all()
    # Insumos para vincular gasto con inventario (Solo Materia Prima y Desechables)
    insumos = Insumo.query.filter(Insumo.categoria.in_(['Materia Prima', 'Desechables', 'Aseo'])).order_by(Insumo.nombre).all()

    if request.method == 'POST':
        concepto_id = request.form.get('concepto_id')
        concepto = ConceptoGasto.query.get(concepto_id)
        
        monto = int(request.form.get('monto'))
        cantidad = float(request.form.get('cantidad')) if request.form.get('cantidad') else None
        unidad = request.form.get('unidad')
        observacion = request.form.get('observacion')
        
        # Nuevos Campos
        proveedor_id = request.form.get('proveedor_id')
        metodo_pago = request.form.get('metodo_pago')
        
        # Lógica de Vinculación con Inventario
        insumo_relacionado_id = request.form.get('insumo_relacionado_id')
        
        nuevo_gasto = Gasto(
            categoria=concepto.categoria,
            descripcion=concepto.nombre,
            monto=monto,
            cantidad=cantidad,
            unidad=unidad,
            observacion=observacion,
            metodo_pago=metodo_pago,
            proveedor_id=proveedor_id if proveedor_id else None,
            usuario_id=current_user.id
        )
        
        db.session.add(nuevo_gasto)
        
        # SI SE SELECCIONÓ UN INSUMO, ACTUALIZAMOS EL INVENTARIO AUTOMÁTICAMENTE
        if insumo_relacionado_id and cantidad:
            insumo = Insumo.query.get(insumo_relacionado_id)
            if insumo:
                insumo.cantidad_actual += cantidad
                # Registramos el movimiento en el Kardex
                mov = MovimientoInventario(
                    insumo_id=insumo.id,
                    tipo='ENTRADA',
                    cantidad=cantidad,
                    costo_unitario=monto, # Asumimos que el monto total es el costo del lote
                    observacion=f"Compra registrada desde Gastos (Ref: {concepto.nombre})",
                    usuario_id=current_user.id
                )
                db.session.add(mov)
                flash(f'Se actualizó el inventario de {insumo.nombre} (+{cantidad})', 'info')

        db.session.commit()
        flash('Gasto registrado correctamente', 'success')
        return redirect(url_for('gastos.index'))

    # Mostrar historial
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).limit(50).all()
    return render_template('gastos.html', gastos=gastos, conceptos=conceptos, proveedores=proveedores, insumos=insumos)

@gastos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    gasto = Gasto.query.get_or_404(id)
    if request.method == 'POST':
        gasto.descripcion = request.form.get('descripcion_texto')
        gasto.monto = int(request.form.get('monto'))
        gasto.observacion = request.form.get('observacion')
        db.session.commit()
        flash('Gasto actualizado', 'info')
        return redirect(url_for('gastos.index'))
    return render_template('gastos_editar.html', gasto=gasto)

@gastos_bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto eliminado', 'warning')
    return redirect(url_for('gastos.index'))

@gastos_bp.route('/conceptos', methods=['GET', 'POST'])
@login_required
@admin_required
def conceptos():
    if request.method == 'POST':
        nuevo = ConceptoGasto(
            nombre=request.form.get('nombre'),
            categoria=request.form.get('categoria'),
            es_compra_insumo='es_compra_insumo' in request.form
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Nuevo concepto agregado', 'success')
        return redirect(url_for('gastos.conceptos'))
    lista = ConceptoGasto.query.order_by(ConceptoGasto.categoria).all()
    return render_template('gastos_conceptos.html', conceptos=lista)