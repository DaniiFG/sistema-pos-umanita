from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Insumo, MovimientoInventario

inventario_bp = Blueprint('inventario', __name__, template_folder='templates')

@inventario_bp.route('/')
def index():
    insumos = Insumo.query.all()
    return render_template('inventario.html', insumos=insumos)

@inventario_bp.route('/crear_insumo', methods=['POST'])
def crear_insumo():
    nombre = request.form.get('nombre')
    unidad = request.form.get('unidad')
    minimo = request.form.get('minimo')
    
    nuevo = Insumo(nombre=nombre, unidad=unidad, minimo_alerta=minimo)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('inventario.index'))

@inventario_bp.route('/movimiento', methods=['POST'])
def movimiento():
    # Esta función maneja tanto ENTRADAS (Compras) como SALIDAS (Uso/Cocina)
    insumo_id = request.form.get('insumo_id')
    tipo = request.form.get('tipo') # 'ENTRADA' o 'SALIDA'
    cantidad = int(request.form.get('cantidad'))
    nota = request.form.get('nota')
    
    insumo = Insumo.query.get_or_404(insumo_id)
    
    if tipo == 'SALIDA':
        if insumo.cantidad_actual < cantidad:
            # Aquí idealmente iría un flash message de error
            return "Error: No hay suficiente stock", 400
        insumo.cantidad_actual -= cantidad
    else: # ENTRADA
        insumo.cantidad_actual += cantidad
        
    # Guardamos el historial
    mov = MovimientoInventario(insumo_id=insumo.id, tipo=tipo, cantidad=cantidad, nota=nota)
    
    db.session.add(mov)
    db.session.commit()
    
    return redirect(url_for('inventario.index'))