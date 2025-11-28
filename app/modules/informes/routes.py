from flask import Blueprint, render_template, request
from app.models import db, Venta, Gasto
from sqlalchemy import func
from datetime import datetime, date

informes_bp = Blueprint('informes', __name__, template_folder='templates')

@informes_bp.route('/', methods=['GET', 'POST'])
def index():
    # Por defecto, mostramos el informe de HOY
    fecha_filtro = date.today()
    
    # Si el usuario selecciona otra fecha en el calendario
    if request.method == 'POST' and request.form.get('fecha'):
        fecha_str = request.form.get('fecha')
        fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # --- CONSULTAS A LA BASE DE DATOS ---
    
    # 1. TOTAL VENTAS DEL DÍA
    # Filtramos donde la fecha de la venta (casting a date) sea igual al filtro
    total_ventas = db.session.query(func.sum(Venta.total_venta))\
        .filter(func.date(Venta.fecha) == fecha_filtro).scalar() or 0

    # 2. TOTAL GASTOS DEL DÍA
    total_gastos = db.session.query(func.sum(Gasto.monto))\
        .filter(func.date(Gasto.fecha) == fecha_filtro).scalar() or 0
        
    # 3. DESGLOSE POR MÉTODO DE PAGO (Para cuadrar caja)
    pagos = db.session.query(
        func.sum(Venta.pago_efectivo),
        func.sum(Venta.pago_nequi),
        func.sum(Venta.pago_daviplata)
    ).filter(func.date(Venta.fecha) == fecha_filtro).first()
    
    # Manejo de nulos si no hay ventas
    efectivo = pagos[0] or 0
    nequi = pagos[1] or 0
    davi = pagos[2] or 0
    
    # 4. BALANCE (Flujo de Caja)
    balance = total_ventas - total_gastos

    return render_template('informes.html', 
                           fecha=fecha_filtro,
                           ventas=total_ventas,
                           gastos=total_gastos,
                           balance=balance,
                           pagos={'efectivo': efectivo, 'nequi': nequi, 'davi': davi})