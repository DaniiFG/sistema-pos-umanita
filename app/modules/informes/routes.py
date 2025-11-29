from flask import Blueprint, render_template, request
from app.models import db, Venta, DetalleVenta, Gasto, Producto
from sqlalchemy import func
from datetime import datetime, date

informes_bp = Blueprint('informes', __name__, template_folder='templates')

@informes_bp.route('/', methods=['GET', 'POST'])
def index():
    # Fechas por defecto: Día actual
    hoy = date.today()
    fecha_inicio = request.form.get('fecha_inicio', default=hoy.strftime('%Y-%m-%d'))
    fecha_fin = request.form.get('fecha_fin', default=hoy.strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime para las consultas (Inicio 00:00 - Fin 23:59)
    f_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    f_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    # --- 1. INFORME DE VENTAS ---
    # Ventas totales en el rango (Dinero que entró)
    total_ventas = db.session.query(func.sum(Venta.total_venta))\
        .filter(Venta.fecha.between(f_ini, f_fin)).scalar() or 0
        
    # Desglose por Método de Pago
    pagos = db.session.query(
        func.sum(Venta.pago_efectivo),
        func.sum(Venta.pago_nequi),
        func.sum(Venta.pago_daviplata)
    ).filter(Venta.fecha.between(f_ini, f_fin)).first()
    
    pago_efectivo = pagos[0] or 0
    pago_nequi = pagos[1] or 0
    pago_davi = pagos[2] or 0
    
    # Top Productos Vendidos (Detallado)
    productos_vendidos = db.session.query(
        DetalleVenta.producto_nombre,
        func.sum(DetalleVenta.cantidad).label('cantidad'),
        func.sum(DetalleVenta.subtotal).label('dinero')
    ).join(Venta).filter(Venta.fecha.between(f_ini, f_fin))\
    .group_by(DetalleVenta.producto_nombre)\
    .order_by(func.sum(DetalleVenta.subtotal).desc()).all()

    # --- 2. INFORME DE GASTOS ---
    # Total de Egresos
    total_gastos = db.session.query(func.sum(Gasto.monto))\
        .filter(Gasto.fecha.between(f_ini, f_fin)).scalar() or 0
        
    # Gastos Agrupados por Categoría (Para gráfica o resumen)
    gastos_por_cat = db.session.query(
        Gasto.categoria,
        func.sum(Gasto.monto)
    ).filter(Gasto.fecha.between(f_ini, f_fin))\
    .group_by(Gasto.categoria).all()
    
    # Lista Detallada de Gastos (Tabla)
    lista_gastos = Gasto.query.filter(Gasto.fecha.between(f_ini, f_fin))\
        .order_by(Gasto.fecha.desc()).all()

    # --- 3. BALANCE (FLUJO DE CAJA) ---
    # Dinero Entrante vs Dinero Saliente
    balance_caja = total_ventas - total_gastos

    # --- 4. ESTADO DE RESULTADOS (P&G ESTIMADO) ---
    # Calculamos el Costo de la Mercancía Vendida (CMV)
    # Sumamos (Cantidad Vendida * Costo Referencia del Producto)
    # Nota: Cruzamos por nombre de producto.
    
    costo_ventas = db.session.query(
        func.sum(DetalleVenta.cantidad * Producto.costo_referencia)
    ).select_from(DetalleVenta)\
     .join(Producto, DetalleVenta.producto_nombre == Producto.nombre)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .filter(Venta.fecha.between(f_ini, f_fin)).scalar() or 0
     
    utilidad_bruta = total_ventas - costo_ventas
    utilidad_neta = utilidad_bruta - total_gastos

    return render_template('informes.html',
                           f_inicio=fecha_inicio,
                           f_fin=fecha_fin,
                           # Datos Ventas
                           total_ventas=total_ventas,
                           efectivo=pago_efectivo,
                           nequi=pago_nequi,
                           davi=pago_davi,
                           productos=productos_vendidos,
                           # Datos Gastos
                           total_gastos=total_gastos,
                           gastos_cat=gastos_por_cat,
                           lista_gastos=lista_gastos,
                           # Balance
                           balance=balance_caja,
                           # P&G
                           costo_ventas=costo_ventas,
                           utilidad_bruta=utilidad_bruta,
                           utilidad_neta=utilidad_neta)