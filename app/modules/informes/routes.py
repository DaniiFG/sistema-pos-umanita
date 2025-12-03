from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_required
from app.models import db, Venta, DetalleVenta, Gasto, Producto, IngresoOcasional, ConceptoGasto, Proveedor
from app.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, date
from collections import defaultdict

informes_bp = Blueprint('informes', __name__, template_folder='templates')

def _obtener_data_informes(fecha_inicio, fecha_fin, filtro_metodo, filtro_cat_prod, filtro_prod_especifico, filtro_cat_gasto, filtro_concepto, filtro_proveedor):
    f_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    f_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    # --- 1. VENTAS ---
    q_detalles = db.session.query(DetalleVenta, Venta).join(Venta).join(Producto, DetalleVenta.producto_nombre == Producto.nombre)
    q_detalles = q_detalles.filter(Venta.fecha.between(f_ini, f_fin))

    if filtro_cat_prod: q_detalles = q_detalles.filter(Producto.categoria == filtro_cat_prod)
    
    if filtro_prod_especifico:
        if isinstance(filtro_prod_especifico, str):
            filtro_prod_especifico = [filtro_prod_especifico]
        filtro_prod_especifico = [x for x in filtro_prod_especifico if x]
        if filtro_prod_especifico:
            q_detalles = q_detalles.filter(DetalleVenta.producto_nombre.in_(filtro_prod_especifico))

    if filtro_metodo:
        if filtro_metodo == 'Efectivo': q_detalles = q_detalles.filter(Venta.pago_efectivo > 0)
        elif filtro_metodo == 'Nequi': q_detalles = q_detalles.filter(Venta.pago_nequi > 0)
        elif filtro_metodo == 'Daviplata': q_detalles = q_detalles.filter(Venta.pago_daviplata > 0)

    resultados_detalles = q_detalles.all()
    total_ventas = sum([d.subtotal for d, v in resultados_detalles])
    
    prod_stats = defaultdict(lambda: {'cant': 0, 'dinero': 0, 'categoria': ''})
    for d, v in resultados_detalles:
        prod = Producto.query.filter_by(nombre=d.producto_nombre).first()
        prod_stats[d.producto_nombre]['cant'] += d.cantidad
        prod_stats[d.producto_nombre]['dinero'] += d.subtotal
        if prod: prod_stats[d.producto_nombre]['categoria'] = prod.categoria
    
    productos_vendidos = [{'nombre': k, 'cant': v['cant'], 'dinero': v['dinero'], 'categoria': v['categoria']} for k,v in prod_stats.items()]
    productos_vendidos.sort(key=lambda x: x['dinero'], reverse=True)
    
    cat_stats_ventas = defaultdict(int)
    for p in productos_vendidos:
        cat_stats_ventas[p['categoria']] += p['dinero']

    # Gráfico
    q_graf = db.session.query(Producto.categoria, func.sum(DetalleVenta.subtotal)).join(Venta).join(Producto, DetalleVenta.producto_nombre==Producto.nombre).filter(Venta.fecha.between(f_ini, f_fin))
    if filtro_cat_prod: q_graf = q_graf.filter(Producto.categoria == filtro_cat_prod)
    if filtro_prod_especifico: q_graf = q_graf.filter(DetalleVenta.producto_nombre.in_(filtro_prod_especifico))
    if filtro_metodo == 'Efectivo': q_graf = q_graf.filter(Venta.pago_efectivo > 0)
    elif filtro_metodo == 'Nequi': q_graf = q_graf.filter(Venta.pago_nequi > 0)
    elif filtro_metodo == 'Daviplata': q_graf = q_graf.filter(Venta.pago_daviplata > 0)
    
    res_graf = q_graf.group_by(Producto.categoria).all()
    labels_ventas = [r[0] for r in res_graf]
    data_ventas = [r[1] for r in res_graf]

    # --- 2. GASTOS ---
    q_gastos = Gasto.query.filter(Gasto.fecha.between(f_ini, f_fin))
    if filtro_cat_gasto: q_gastos = q_gastos.filter(Gasto.categoria == filtro_cat_gasto)
    if filtro_concepto: q_gastos = q_gastos.filter(Gasto.descripcion == filtro_concepto)
    if filtro_proveedor: q_gastos = q_gastos.filter(Gasto.proveedor_id == filtro_proveedor)
    if filtro_metodo: 
        match = 'Efectivo' if filtro_metodo == 'Efectivo' else filtro_metodo
        q_gastos = q_gastos.filter(Gasto.metodo_pago.contains(match))

    lista_gastos = q_gastos.order_by(Gasto.fecha.desc()).all()
    total_gastos = sum([g.monto for g in lista_gastos])

    g_stats = defaultdict(lambda: {'monto': 0, 'detalles': defaultdict(int)})
    for g in lista_gastos:
        g_stats[g.categoria]['monto'] += g.monto
        g_stats[g.categoria]['detalles'][g.descripcion] += g.monto
        
    labels_gastos = list(g_stats.keys())
    data_gastos = [v['monto'] for v in g_stats.values()]

    # --- 3. BALANCE ---
    q_ventas_caja = Venta.query.filter(Venta.fecha.between(f_ini, f_fin))
    q_gastos_caja = Gasto.query.filter(Gasto.fecha.between(f_ini, f_fin))
    q_otros_caja = IngresoOcasional.query.filter(IngresoOcasional.fecha.between(f_ini, f_fin))

    detalles_ventas = q_ventas_caja.all()
    detalles_gastos = q_gastos_caja.all()
    detalles_otros = q_otros_caja.all()

    sum_v_efec = sum(v.pago_efectivo for v in detalles_ventas)
    sum_v_nequi = sum(v.pago_nequi for v in detalles_ventas)
    sum_v_davi = sum(v.pago_daviplata for v in detalles_ventas)
    
    sum_g_efec = sum(g.monto for g in detalles_gastos if 'Efectivo' in (g.metodo_pago or ''))
    sum_g_nequi = sum(g.monto for g in detalles_gastos if 'Nequi' in (g.metodo_pago or ''))
    sum_g_davi = sum(g.monto for g in detalles_gastos if 'Daviplata' in (g.metodo_pago or ''))
    
    sum_o_efec = sum(o.monto for o in detalles_otros if 'Efectivo' in (o.metodo_pago or ''))
    sum_o_nequi = sum(o.monto for o in detalles_otros if 'Nequi' in (o.metodo_pago or ''))
    sum_o_davi = sum(o.monto for o in detalles_otros if 'Daviplata' in (o.metodo_pago or ''))

    cierre_efectivo = (sum_v_efec + sum_o_efec) - sum_g_efec
    cierre_nequi = (sum_v_nequi + sum_o_nequi) - sum_g_nequi
    cierre_davi = (sum_v_davi + sum_o_davi) - sum_g_davi 
    balance_total = cierre_efectivo + cierre_nequi + cierre_davi

    # --- 4. P & G ---
    costo_ventas = 0
    for d, v in resultados_detalles:
        prod = Producto.query.filter_by(nombre=d.producto_nombre).first()
        if prod: costo_ventas += (d.cantidad * prod.costo_referencia)

    utilidad_bruta = total_ventas - costo_ventas
    utilidad_neta = utilidad_bruta - total_gastos

    return {
        'f_ini_dt': f_ini, 'f_fin_dt': f_fin, 
        'total_ventas': total_ventas, 
        'productos': productos_vendidos, # CORREGIDO: Se llama 'productos' para coincidir con el HTML
        'cat_stats_ventas': cat_stats_ventas,
        'labels_ventas': labels_ventas, 'data_ventas': data_ventas,
        'total_gastos': total_gastos, 'lista_gastos': lista_gastos, 'cat_stats_gastos': g_stats,
        'labels_gastos': labels_gastos, 'data_gastos': data_gastos,
        'cierre_efectivo': cierre_efectivo, 'cierre_nequi': cierre_nequi, 'cierre_davi': cierre_davi,
        'detalles_ventas': detalles_ventas, 'detalles_gastos': detalles_gastos, 'detalles_otros': detalles_otros,
        'balance_total': balance_total,
        'costo_ventas': costo_ventas, 'utilidad_bruta': utilidad_bruta, 'utilidad_neta': utilidad_neta
    }

@informes_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    hoy = date.today()
    fecha_inicio = request.form.get('fecha_inicio', default=hoy.strftime('%Y-%m-%d'))
    fecha_fin = request.form.get('fecha_fin', default=hoy.strftime('%Y-%m-%d'))
    
    # Recoger filtros
    filtros = {
        'filtro_metodo': request.form.get('filtro_metodo', ''),
        'filtro_cat_prod': request.form.get('filtro_categoria_prod', ''),
        'filtro_prod_especifico': request.form.getlist('filtro_producto_especifico'),
        'filtro_cat_gasto': request.form.get('filtro_categoria_gasto', ''),
        'filtro_concepto': request.form.get('filtro_concepto', ''),
        'filtro_proveedor': request.form.get('filtro_proveedor', '')
    }
    
    tab_activa = request.form.get('tab_activa', 'ventas')

    # Datos para selects
    cats_prod = [c[0] for c in db.session.query(Producto.categoria).distinct()]
    list_prod = [p[0] for p in db.session.query(Producto.nombre).distinct().order_by(Producto.nombre)]
    cats_gasto = [c[0] for c in db.session.query(ConceptoGasto.categoria).distinct()]
    list_conceptos = [c[0] for c in db.session.query(ConceptoGasto.nombre).distinct()]
    proveedores = Proveedor.query.all()

    data = _obtener_data_informes(fecha_inicio, fecha_fin, **filtros)

    return render_template('informes.html',
                           f_inicio=fecha_inicio, f_fin=fecha_fin, tab_activa=tab_activa, 
                           cats_prod=cats_prod, list_prod=list_prod,
                           cats_gasto=cats_gasto, list_conceptos=list_conceptos,
                           list_prov=proveedores,
                           filtro_metodo=filtros['filtro_metodo'], filtro_cat_prod=filtros['filtro_cat_prod'], filtro_prod_esp=filtros['filtro_prod_especifico'],
                           filtro_cat_gasto=filtros['filtro_cat_gasto'], filtro_con=filtros['filtro_concepto'], filtro_prov=filtros['filtro_proveedor'],
                           **data)

@informes_bp.route('/reporte_ventas/<tipo>', methods=['POST'])
@login_required
@admin_required
def reporte_ventas(tipo):
    data = _obtener_data_informes(
        request.form.get('fecha_inicio'), request.form.get('fecha_fin'), 
        request.form.get('filtro_metodo'), request.form.get('filtro_categoria_prod'), 
        request.form.getlist('filtro_producto_especifico'), None, None, None
    )
    
    if tipo == 'general':
        reporte_data = [{'categoria': cat, 'total': total} for cat, total in data['cat_stats_ventas'].items()]
        reporte_data.sort(key=lambda x: x['total'], reverse=True)
        # CORRECCIÓN: 'tabla_datos' en lugar de 'data' para evitar conflicto
        return render_template('informe_ventas_general.html', 
                               tabla_datos=reporte_data, 
                               total_ventas=data['total_ventas'], 
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'detallado':
        ventas_por_categoria = defaultdict(list)
        for p in data['productos']: # Usamos la clave corregida 'productos'
            ventas_por_categoria[p['categoria']].append(p)
        sorted_categories = sorted(ventas_por_categoria.items(), key=lambda item: sum(p['dinero'] for p in item[1]), reverse=True)

        return render_template('informe_ventas_detallado.html', 
                               ventas_por_categoria=sorted_categories, 
                               total_ventas=data['total_ventas'], 
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'contable':
        return render_template('informe_contable.html', data=data, datetime=datetime)
        
    return redirect(url_for('informes.index'))

@informes_bp.route('/reporte_gastos/<tipo>', methods=['POST'])
@login_required
@admin_required
def reporte_gastos(tipo):
    data = _obtener_data_informes(
        request.form.get('fecha_inicio'), request.form.get('fecha_fin'), 
        request.form.get('filtro_metodo'), None, None, 
        request.form.get('filtro_categoria_gasto'), request.form.get('filtro_concepto'), request.form.get('filtro_proveedor')
    )
    
    if tipo == 'general':
        reporte_data = [{'categoria': cat, 'total': info['monto']} for cat, info in data['cat_stats_gastos'].items()]
        reporte_data.sort(key=lambda x: x['total'], reverse=True)
        # CORRECCIÓN: 'tabla_datos' en lugar de 'data'
        return render_template('informe_gastos_general.html', 
                               tabla_datos=reporte_data, 
                               total_gastos=data['total_gastos'], 
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'detallado':
        sorted_categories = sorted(data['cat_stats_gastos'].items(), key=lambda item: item[1]['monto'], reverse=True)
        return render_template('informe_gastos_detallado.html', 
                               gastos_por_categoria=sorted_categories, 
                               total_gastos=data['total_gastos'],
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'contable':
        return render_template('informe_contable.html', data=data, datetime=datetime)

    return redirect(url_for('informes.index'))
    
@informes_bp.route('/reporte_pyg', methods=['POST'])
@login_required
@admin_required
def reporte_pyg():
    data = _obtener_data_informes(
        request.form.get('fecha_inicio'), request.form.get('fecha_fin'), 
        request.form.get('filtro_metodo'), request.form.get('filtro_categoria_prod'), 
        request.form.getlist('filtro_producto_especifico'), 
        request.form.get('filtro_categoria_gasto'), request.form.get('filtro_concepto'), request.form.get('filtro_proveedor')
    )
    return render_template('informe_contable.html', data=data, datetime=datetime)