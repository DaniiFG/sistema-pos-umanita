from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Insumo, MovimientoInventario, ConceptoGasto
from app.decorators import admin_required
from sqlalchemy import desc

inventario_bp = Blueprint('inventario', __name__, template_folder='templates')

@inventario_bp.route('/')
@login_required
@admin_required
def index():
    insumos = Insumo.query.order_by(Insumo.nombre).all()
    # Enviamos una lista de categorías única para generar las pestañas dinámicamente si se quisiera, 
    # pero tu HTML ya las tiene fijas, así que nos aseguramos que el ID coincida.
    return render_template('inventario.html', insumos=insumos)

@inventario_bp.route('/crear', methods=['POST'])
@login_required
@admin_required
def crear_insumo():
    categoria = request.form.get('categoria')
    nombre_insumo = request.form.get('nombre')
    
    nuevo = Insumo(
        nombre=nombre_insumo,
        categoria=categoria,
        unidad=request.form.get('unidad'),
        minimo_alerta=float(request.form.get('minimo'))
    )
    db.session.add(nuevo)

    # NUEVA LÓGICA: CREAR CONCEPTO DE GASTO ASOCIADO PARA FACILITAR EL REGISTRO DE COMPRAS
    if categoria in ['Materia Prima', 'Desechables', 'Aseo', 'Activos']:
        nombre_concepto = f"Compra de {nombre_insumo}"
        
        # Verificar si ya existe un concepto con ese nombre para evitar duplicados
        concepto_existente = ConceptoGasto.query.filter_by(nombre=nombre_concepto).first()
        
        if not concepto_existente:
            # Los activos no afectan el inventario de insumos automáticamente con el gasto normal
            es_compra_insumo = True if categoria in ['Materia Prima', 'Desechables', 'Aseo'] else False
            
            nuevo_concepto = ConceptoGasto(
                nombre=nombre_concepto,
                categoria=categoria,
                es_compra_insumo=es_compra_insumo
            )
            db.session.add(nuevo_concepto)
            flash(f'Concepto de Gasto "{nombre_concepto}" creado automáticamente.', 'info')

    db.session.commit()
    flash(f'Producto "{nuevo.nombre}" creado.', 'success')
    # Redirección corregida: Reemplaza espacios por guiones bajos para el ID del HTML
    anchor = categoria.replace(" ", "_")
    return redirect(url_for('inventario.index') + f'#{anchor}')

@inventario_bp.route('/editar/<int:id>', methods=['POST'])
@login_required
@admin_required
def editar_insumo(id):
    insumo = Insumo.query.get_or_404(id)
    insumo.nombre = request.form.get('nombre')
    insumo.categoria = request.form.get('categoria')
    insumo.unidad = request.form.get('unidad')
    insumo.minimo_alerta = float(request.form.get('minimo'))
    
    db.session.commit()
    flash('Insumo actualizado correctamente.', 'info')
    anchor = insumo.categoria.replace(" ", "_")
    return redirect(url_for('inventario.index') + f'#{anchor}')

@inventario_bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar_insumo(id):
    insumo = Insumo.query.get_or_404(id)
    # Verificar si tiene historial para no romper integridad
    if insumo.movimientos:
        flash('No se puede eliminar: El insumo tiene historial de movimientos. Edítalo o desactívalo.', 'danger')
    else:
        cat_original = insumo.categoria
        # Opcional: Eliminar ConceptoGasto asociado
        nombre_concepto = f"Compra de {insumo.nombre}"
        concepto = ConceptoGasto.query.filter_by(nombre=nombre_concepto).first()
        if concepto:
            db.session.delete(concepto)
            
        db.session.delete(insumo)
        db.session.commit()
        flash('Insumo eliminado.', 'warning')
        anchor = cat_original.replace(" ", "_")
        return redirect(url_for('inventario.index') + f'#{anchor}')
    
    return redirect(url_for('inventario.index'))

@inventario_bp.route('/movimiento', methods=['POST'])
@login_required
@admin_required
def movimiento():
    insumo_id = request.form.get('insumo_id')
    tipo = request.form.get('tipo')
    cantidad = float(request.form.get('cantidad'))
    observacion = request.form.get('observacion')
    
    insumo = Insumo.query.get_or_404(insumo_id)
    
    if tipo == 'SALIDA' and insumo.cantidad_actual < cantidad:
        flash(f'Error: Stock insuficiente de {insumo.nombre}.', 'danger')
        anchor = insumo.categoria.replace(" ", "_")
        return redirect(url_for('inventario.index') + f'#{anchor}')

    # Actualizar Stock
    costo = 0
    if tipo == 'ENTRADA':
        insumo.cantidad_actual += cantidad
        costo = int(request.form.get('costo_unitario')) if request.form.get('costo_unitario') else 0
    else:
        insumo.cantidad_actual -= cantidad

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
    
    flash('Movimiento registrado.', 'success')
    # Corrección de ancla
    anchor = insumo.categoria.replace(" ", "_")
    return redirect(url_for('inventario.index') + f'#{anchor}')

@inventario_bp.route('/historial')
@login_required
@admin_required
def historial():
    movimientos = MovimientoInventario.query.order_by(desc(MovimientoInventario.fecha)).limit(100).all()
    return render_template('historial.html', movimientos=movimientos)