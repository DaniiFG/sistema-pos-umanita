from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Producto
from app.decorators import admin_required

productos_bp = Blueprint('productos', __name__, template_folder='templates')

@productos_bp.route('/')
@login_required
@admin_required
def index():
    # Solo el admin puede ver esta lista para editar
    productos = Producto.query.order_by(Producto.categoria).all()
    return render_template('productos_lista.html', productos=productos)

@productos_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    if request.method == 'POST':
        nuevo = Producto(
            nombre=request.form['nombre'],
            precio=int(request.form['precio']),
            categoria=request.form['categoria'],
            costo_referencia=int(request.form['costo']) if request.form['costo'] else 0,
            es_combo='es_combo' in request.form
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto creado correctamente', 'success')
        return redirect(url_for('productos.index'))
    return render_template('productos_form.html', accion="Crear", producto=None)

@productos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.precio = int(request.form['precio'])
        producto.categoria = request.form['categoria']
        producto.costo_referencia = int(request.form['costo']) if request.form['costo'] else 0
        producto.es_combo = 'es_combo' in request.form
        producto.activo = 'activo' in request.form
        
        db.session.commit()
        flash('Producto actualizado', 'success')
        return redirect(url_for('productos.index'))
    return render_template('productos_form.html', accion="Editar", producto=producto)