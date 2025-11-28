from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Gasto
from datetime import datetime

# Definimos el blueprint apuntando a SU carpeta de templates
gastos_bp = Blueprint('gastos', __name__, template_folder='templates')

@gastos_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Capturamos datos del formulario
        categoria = request.form.get('categoria')
        descripcion = request.form.get('descripcion')
        monto = int(request.form.get('monto'))
        
        # Datos opcionales
        cantidad = request.form.get('cantidad')
        unidad = request.form.get('unidad')
        
        # Validación simple
        if not cantidad: cantidad = 0
        
        nuevo_gasto = Gasto(
            categoria=categoria,
            descripcion=descripcion,
            monto=monto,
            cantidad=int(cantidad) if cantidad else None,
            unidad=unidad
        )
        
        db.session.add(nuevo_gasto)
        db.session.commit()
        # En producción usaríamos flash messages, aquí recargamos simple
        return redirect(url_for('gastos.index'))

    # Ordenamos por fecha descendente (lo más nuevo arriba)
    gastos = Gasto.query.order_by(Gasto.fecha.desc()).all()
    return render_template('gastos.html', gastos=gastos)

@gastos_bp.route('/eliminar/<int:id>')
def eliminar(id):
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    return redirect(url_for('gastos.index'))