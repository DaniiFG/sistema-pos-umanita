from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Gasto, ConceptoGasto, Proveedor, Insumo, MovimientoInventario
from app.decorators import admin_required

gastos_bp = Blueprint('gastos', __name__, template_folder='templates')

EMPLEADOS = ["Daniel García", "Daniela Garcia", "Camilo Melendrez", "Gladys Bravo", "Luis Garcia"]

@gastos_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    conceptos = ConceptoGasto.query.order_by(ConceptoGasto.categoria, ConceptoGasto.nombre).all()
    proveedores = Proveedor.query.filter_by(activo=True).all()
    # AHORA: Todos los insumos se pueden seleccionar para alimentar inventario
    insumos = Insumo.query.order_by(Insumo.nombre).all()

    if request.method == 'POST':
        # --- LÓGICA DE REGISTRO INDIVIDUAL ---
        concepto_id = request.form.get('concepto_id')
        concepto = ConceptoGasto.query.get(concepto_id)
        
        monto = int(request.form.get('monto'))
        descripcion_final = concepto.nombre
        
        # Si es nómina, agregar empleado
        if concepto.categoria == 'Obligaciones Laborales' and request.form.get('empleado_nomina'):
            descripcion_final += f" ({request.form.get('empleado_nomina')})"
            
        nuevo_gasto = Gasto(
            categoria=concepto.categoria,
            descripcion=descripcion_final,
            monto=monto,
            metodo_pago=request.form.get('metodo_pago'),
            origen_dinero=request.form.get('origen_dinero'),
            es_fantasma='es_fantasma' in request.form,
            proveedor_id=request.form.get('proveedor_id') or None,
            observacion=request.form.get('observacion'),
            usuario_id=current_user.id
        )
        db.session.add(nuevo_gasto)
        
        # Inventario
        insumo_id = request.form.get('insumo_relacionado_id')
        cantidad = float(request.form.get('cantidad')) if request.form.get('cantidad') else 0
        if insumo_id and cantidad > 0:
            insumo = Insumo.query.get(insumo_id)
            if insumo:
                insumo.cantidad_actual += cantidad
                mov = MovimientoInventario(
                    insumo_id=insumo.id,
                    tipo='ENTRADA',
                    cantidad=cantidad,
                    costo_unitario=monto,
                    observacion=f"Compra Gasto: {descripcion_final}",
                    usuario_id=current_user.id
                )
                db.session.add(mov)
                flash(f'Inventario actualizado: {insumo.nombre} (+{cantidad})', 'info')

        db.session.commit()
        flash('Gasto registrado.', 'success')
        return redirect(url_for('gastos.index'))

    # Listar últimos gastos (excluyendo fantasmas para la vista por defecto, o marcándolos)
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).limit(50).all()
    return render_template('gastos.html', gastos=gastos, conceptos=conceptos, proveedores=proveedores, insumos=insumos, empleados=EMPLEADOS)

@gastos_bp.route('/factura_masiva', methods=['POST'])
@login_required
@admin_required
def factura_masiva():
    # Procesar lista de items enviada por formulario
    # Se asume que los inputs se llaman item_concepto[], item_subtotal[], item_iva_pct[], etc.
    try:
        conceptos = request.form.getlist('item_concepto')
        subtotales = request.form.getlist('item_subtotal')
        ivas = request.form.getlist('item_iva_select') # 0, 5, 19
        descripciones = request.form.getlist('item_desc')
        
        origen = request.form.get('factura_origen')
        metodo = request.form.get('factura_metodo')
        prov = request.form.get('factura_proveedor') or None
        
        for i in range(len(conceptos)):
            con_id = conceptos[i]
            if not con_id: continue
            
            concepto_obj = ConceptoGasto.query.get(con_id)
            sub = int(subtotales[i])
            pct_iva = int(ivas[i])
            valor_iva = sub * pct_iva // 100
            total = sub + valor_iva
            desc = descripciones[i] or concepto_obj.nombre
            
            nuevo = Gasto(
                categoria=concepto_obj.categoria,
                descripcion=f"[Fac] {desc}",
                subtotal_base=sub,
                iva=valor_iva,
                monto=total,
                metodo_pago=metodo,
                origen_dinero=origen,
                proveedor_id=prov,
                usuario_id=current_user.id
            )
            db.session.add(nuevo)
            
        db.session.commit()
        flash('Factura masiva registrada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error registrando factura: {str(e)}', 'danger')
        
    return redirect(url_for('gastos.index'))

# --- CRUD PROVEEDORES ---
@gastos_bp.route('/proveedores', methods=['GET', 'POST'])
@login_required
@admin_required
def proveedores():
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'crear':
            p = Proveedor(
                nombre=request.form.get('nombre'),
                nit=request.form.get('nit'),
                telefono=request.form.get('telefono'),
                direccion=request.form.get('direccion')
            )
            db.session.add(p)
            flash('Proveedor creado', 'success')
        elif accion == 'editar':
            p = Proveedor.query.get(request.form.get('id'))
            p.nombre = request.form.get('nombre')
            p.nit = request.form.get('nit')
            p.telefono = request.form.get('telefono')
            p.direccion = request.form.get('direccion')
            flash('Proveedor actualizado', 'info')
        elif accion == 'eliminar':
            p = Proveedor.query.get(request.form.get('id'))
            # Soft delete mejor
            p.activo = False
            flash('Proveedor desactivado', 'warning')
            
        db.session.commit()
        return redirect(url_for('gastos.proveedores'))
        
    lista = Proveedor.query.filter_by(activo=True).all()
    return render_template('gastos_proveedores.html', proveedores=lista) # Necesitas crear este template simple

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
    # Lógica original...
    if request.method == 'POST':
        nuevo = ConceptoGasto(
            nombre=request.form.get('nombre'),
            categoria=request.form.get('categoria'),
            es_compra_insumo='es_compra_insumo' in request.form
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Concepto agregado', 'success')
        return redirect(url_for('gastos.conceptos'))
    lista = ConceptoGasto.query.order_by(ConceptoGasto.categoria).all()
    return render_template('gastos_conceptos.html', conceptos=lista)