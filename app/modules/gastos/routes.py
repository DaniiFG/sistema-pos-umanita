from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Gasto, ConceptoGasto
from app.decorators import admin_required
from datetime import datetime

gastos_bp = Blueprint('gastos', __name__, template_folder='templates')

@gastos_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Cargar conceptos para el select
    conceptos = ConceptoGasto.query.order_by(ConceptoGasto.categoria, ConceptoGasto.nombre).all()

    if request.method == 'POST':
        concepto_id = request.form.get('concepto_id')
        concepto = ConceptoGasto.query.get(concepto_id)
        
        monto = int(request.form.get('monto'))
        cantidad = request.form.get('cantidad')
        unidad = request.form.get('unidad')
        observacion = request.form.get('observacion')
        
        nuevo_gasto = Gasto(
            categoria=concepto.categoria,
            descripcion=concepto.nombre, # Guardamos el nombre
            monto=monto,
            cantidad=float(cantidad) if cantidad else None,
            unidad=unidad,
            observacion=observacion,
            usuario_id=current_user.id
        )
        
        db.session.add(nuevo_gasto)
        db.session.commit()
        flash('Gasto registrado correctamente', 'success')
        return redirect(url_for('gastos.index'))

    # Mostrar historial (más recientes primero)
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).limit(50).all()
    return render_template('gastos.html', gastos=gastos, conceptos=conceptos)

@gastos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    gasto = Gasto.query.get_or_404(id)
    conceptos = ConceptoGasto.query.all()
    
    if request.method == 'POST':
        gasto.descripcion = request.form.get('descripcion_texto') # Permitir edición manual al corregir
        gasto.monto = int(request.form.get('monto'))
        gasto.cantidad = float(request.form.get('cantidad')) if request.form.get('cantidad') else None
        gasto.unidad = request.form.get('unidad')
        gasto.observacion = request.form.get('observacion')
        
        db.session.commit()
        flash('Gasto actualizado', 'info')
        return redirect(url_for('gastos.index'))
        
    return render_template('gastos_editar.html', gasto=gasto, conceptos=conceptos)

@gastos_bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto eliminado', 'warning')
    return redirect(url_for('gastos.index'))

# --- GESTIÓN DE CONCEPTOS (Para agregar nuevos tipos de gasto) ---
@gastos_bp.route('/conceptos', methods=['GET', 'POST'])
@login_required
@admin_required
def conceptos():
    if request.method == 'POST':
        nuevo = ConceptoGasto(
            nombre=request.form.get('nombre'),
            categoria=request.form.get('categoria')
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Nuevo concepto agregado', 'success')
        return redirect(url_for('gastos.conceptos'))
        
    lista = ConceptoGasto.query.order_by(ConceptoGasto.categoria).all()
    return render_template('gastos_conceptos.html', conceptos=lista)