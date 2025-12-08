import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from app.models import db, Producto, DetalleVenta
from app.decorators import admin_required

productos_bp = Blueprint('productos', __name__, template_folder='templates')

def guardar_imagen(archivo):
    if not archivo or archivo.filename == '':
        return None
    filename = secure_filename(archivo.filename)
    # Agregar timestamp para evitar cache o duplicados
    import time
    filename = f"{int(time.time())}_{filename}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    archivo.save(path)
    return filename

@productos_bp.route('/')
@login_required
@admin_required
def index():
    productos = Producto.query.order_by(Producto.categoria).all()
    return render_template('productos_lista.html', productos=productos)

@productos_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    if request.method == 'POST':
        imagen = guardar_imagen(request.files.get('imagen'))
        
        nuevo = Producto(
            nombre=request.form['nombre'],
            precio=int(request.form['precio']),
            categoria=request.form['categoria'],
            costo_referencia=int(request.form['costo']) if request.form['costo'] else 0,
            es_combo='es_combo' in request.form,
            imagen_local=imagen
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto creado.', 'success')
        return redirect(url_for('productos.index'))
    return render_template('productos_form.html', accion="Crear", producto=None)

@productos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    if request.method == 'POST':
        # Actualizar datos básicos
        nuevo_nombre = request.form['nombre']
        
        # IMPORTANTE: Si cambia el nombre, actualizar historial o confiar en producto_id
        # (El reporte ahora usa producto_id, así que el nombre antiguo en detalle_venta ya no afecta el agrupamiento)
        
        producto.nombre = nuevo_nombre
        producto.precio = int(request.form['precio'])
        producto.categoria = request.form['categoria']
        producto.costo_referencia = int(request.form['costo']) if request.form['costo'] else 0
        producto.es_combo = 'es_combo' in request.form
        producto.activo = 'activo' in request.form
        
        imagen = guardar_imagen(request.files.get('imagen'))
        if imagen:
            producto.imagen_local = imagen
        
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('productos.index'))
    return render_template('productos_form.html', accion="Editar", producto=producto)