from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_required
from app.models import db, Venta, DetalleVenta, Gasto, Producto, IngresoOcasional, ConceptoGasto, Proveedor
from app.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, date
from collections import defaultdict

informes_bp = Blueprint('informes', __name__, template_folder='templates')

def _obtener_data_informes(fecha_inicio, fecha_fin, **kwargs):
    # Convertir fechas (el final del día se ajusta a 23:59:59)
    f_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    f_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    # Filtros opcionales que vienen en kwargs
    filtro_cat_prod = kwargs.get('filtro_cat_prod')
    filtro_prod_especifico = kwargs.get('filtro_prod_especifico')
    filtro_metodo = kwargs.get('filtro_metodo')
    filtro_cat_gasto = kwargs.get('filtro_cat_gasto')
    filtro_concepto = kwargs.get('filtro_concepto')
    filtro_proveedor = kwargs.get('filtro_proveedor')

    # ==============================================================================
    # 1. VENTAS (Informe Comercial y P&G)
    # ==============================================================================
    q_detalles = db.session.query(DetalleVenta, Venta).join(Venta).filter(
        Venta.fecha.between(f_ini, f_fin),
        Venta.es_fantasma == False,
        Venta.estado == 'Cerrada'
    )

    if filtro_cat_prod:
        q_detalles = q_detalles.join(Producto, DetalleVenta.producto_id == Producto.id).filter(Producto.categoria == filtro_cat_prod)
    
    if filtro_prod_especifico:
        if isinstance(filtro_prod_especifico, str):
            filtro_prod_especifico = [filtro_prod_especifico]
        q_detalles = q_detalles.filter(DetalleVenta.producto_nombre.in_(filtro_prod_especifico))

    # Filtro de método de pago para VENTAS
    if filtro_metodo:
        if filtro_metodo == 'Efectivo': q_detalles = q_detalles.filter(Venta.pago_efectivo > 0)
        elif filtro_metodo == 'Nequi': q_detalles = q_detalles.filter(Venta.pago_nequi > 0)
        elif filtro_metodo == 'Daviplata': q_detalles = q_detalles.filter(Venta.pago_daviplata > 0)

    resultados_detalles = q_detalles.all()
    
    total_ventas = sum([d.subtotal for d, v in resultados_detalles])
    
    prod_stats = defaultdict(lambda: {'cant': 0, 'dinero': 0, 'categoria': '', 'nombre': ''})
    
    for d, v in resultados_detalles:
        key = d.producto_id if d.producto_id else d.producto_nombre
        nombre_mostrar = d.producto_nombre
        cat_mostrar = "Sin Categoría"
        
        if d.producto:
            nombre_mostrar = d.producto.nombre
            cat_mostrar = d.producto.categoria
        elif d.producto_id:
            p = Producto.query.get(d.producto_id)
            if p: 
                nombre_mostrar = p.nombre
                cat_mostrar = p.categoria
        else:
            p_legacy = Producto.query.filter_by(nombre=d.producto_nombre).first()
            if p_legacy:
                cat_mostrar = p_legacy.categoria

        prod_stats[key]['nombre'] = nombre_mostrar
        prod_stats[key]['categoria'] = cat_mostrar
        prod_stats[key]['cant'] += d.cantidad
        prod_stats[key]['dinero'] += d.subtotal

    productos_vendidos = list(prod_stats.values())
    productos_vendidos.sort(key=lambda x: x['dinero'], reverse=True)
    
    cat_stats_ventas = defaultdict(int)
    for p in productos_vendidos:
        cat_stats_ventas[p['categoria']] += p['dinero']

    # Tendencia Ventas
    trend_ventas_dict = defaultdict(int)
    ids_procesados = set()
    for d, v in resultados_detalles:
        if v.id not in ids_procesados:
            fecha_str = v.fecha.strftime('%Y-%m-%d')
            trend_ventas_dict[fecha_str] += v.total_venta
            ids_procesados.add(v.id)
            
    fechas_ordenadas_ventas = sorted(trend_ventas_dict.keys())
    data_trend_ventas = [trend_ventas_dict[f] for f in fechas_ordenadas_ventas]

    # ==============================================================================
    # 2. GASTOS
    # ==============================================================================
    q_gastos = Gasto.query.filter(
        Gasto.fecha.between(f_ini, f_fin),
        Gasto.es_fantasma == False
    )
    
    # --- CORRECCIÓN: Filtro de método de pago para GASTOS ---
    if filtro_metodo:
        # Usamos 'like' para el efectivo porque en BD se guarda como "Efectivo Caja"
        if filtro_metodo == 'Efectivo': 
            q_gastos = q_gastos.filter(Gasto.metodo_pago.like('%Efectivo%'))
        elif filtro_metodo == 'Nequi': 
            q_gastos = q_gastos.filter(Gasto.metodo_pago == 'Nequi')
        elif filtro_metodo == 'Daviplata': 
            q_gastos = q_gastos.filter(Gasto.metodo_pago == 'Daviplata')

    if filtro_cat_gasto: q_gastos = q_gastos.filter(Gasto.categoria == filtro_cat_gasto)
    if filtro_concepto: q_gastos = q_gastos.filter(Gasto.descripcion == filtro_concepto)
    if filtro_proveedor: q_gastos = q_gastos.filter(Gasto.proveedor_id == filtro_proveedor)
    
    lista_gastos = q_gastos.order_by(Gasto.fecha.desc()).all()
    total_gastos = sum([g.monto for g in lista_gastos])

    cat_stats_gastos = defaultdict(lambda: {'monto': 0, 'detalles': defaultdict(int)})
    for g in lista_gastos:
        cat_stats_gastos[g.categoria]['monto'] += g.monto
        # Ahora usamos la observación real si existe, o el concepto base
        detalle_mostrar = g.descripcion
        if g.observacion:
            detalle_mostrar += f" ({g.observacion})"
        cat_stats_gastos[g.categoria]['detalles'][detalle_mostrar] += g.monto

    # Tendencia Gastos
    trend_gastos_dict = defaultdict(int)
    for g in lista_gastos:
        fecha_str = g.fecha.strftime('%Y-%m-%d')
        trend_gastos_dict[fecha_str] += g.monto
        
    fechas_ordenadas_gastos = sorted(trend_gastos_dict.keys())
    data_trend_gastos = [trend_gastos_dict[f] for f in fechas_ordenadas_gastos]

    # ==============================================================================
    # 3. CIERRE DE CAJA
    # ==============================================================================
    todas_ventas = Venta.query.filter(Venta.fecha.between(f_ini, f_fin), Venta.estado == 'Cerrada').all()
    todos_gastos = Gasto.query.filter(Gasto.fecha.between(f_ini, f_fin)).all()
    todos_ingresos = IngresoOcasional.query.filter(IngresoOcasional.fecha.between(f_ini, f_fin)).all()

    v_efec_neto = sum((v.pago_efectivo - v.cambio_dado) for v in todas_ventas if v.pago_efectivo > 0)
    v_nequi = sum(v.pago_nequi for v in todas_ventas)
    v_davi = sum(v.pago_daviplata for v in todas_ventas)
    
    g_efec = sum(g.monto for g in todos_gastos if 'Efectivo' in (g.metodo_pago or ''))
    g_nequi = sum(g.monto for g in todos_gastos if 'Nequi' in (g.metodo_pago or ''))
    g_davi = sum(g.monto for g in todos_gastos if 'Daviplata' in (g.metodo_pago or ''))
    
    i_efec = sum(i.monto for i in todos_ingresos if 'Efectivo' in (i.metodo_pago or ''))
    i_nequi = sum(i.monto for i in todos_ingresos if 'Nequi' in (i.metodo_pago or ''))
    i_davi = sum(i.monto for i in todos_ingresos if 'Davi' in (i.metodo_pago or ''))

    cierre_efectivo = (v_efec_neto + i_efec) - g_efec
    cierre_nequi = (v_nequi + i_nequi) - g_nequi
    cierre_davi = (v_davi + i_davi) - g_davi
    total_caja_unificado = cierre_efectivo + cierre_nequi + cierre_davi

    detalles_ventas = todas_ventas
    detalles_gastos = todos_gastos
    detalles_otros = todos_ingresos

    # ==============================================================================
    # 4. P & G
    # ==============================================================================
    costo_ventas = 0
    for d, v in resultados_detalles:
        costo_unitario = 0
        if d.producto:
            costo_unitario = d.producto.costo_referencia
        elif d.producto_id:
            p = Producto.query.get(d.producto_id)
            if p: costo_unitario = p.costo_referencia
        else:
            p_leg = Producto.query.filter_by(nombre=d.producto_nombre).first()
            if p_leg: costo_unitario = p_leg.costo_referencia
            
        costo_ventas += (d.cantidad * costo_unitario)

    utilidad_bruta = total_ventas - costo_ventas
    utilidad_neta = utilidad_bruta - total_gastos
    neto_dia = total_ventas - total_gastos

    return {
        'f_ini_dt': f_ini, 'f_fin_dt': f_fin, 
        'total_ventas': total_ventas, 
        'productos': productos_vendidos,
        'cat_stats_ventas': cat_stats_ventas,
        'total_gastos': total_gastos, 
        'lista_gastos': lista_gastos,
        'cat_stats_gastos': cat_stats_gastos,
        'cierre_efectivo': cierre_efectivo, 
        'cierre_nequi': cierre_nequi, 
        'cierre_davi': cierre_davi,
        'total_caja_unificado': total_caja_unificado, 
        'balance_total': total_caja_unificado,
        'detalles_ventas': detalles_ventas, 
        'detalles_gastos': detalles_gastos, 
        'detalles_otros': detalles_otros,
        'costo_ventas': costo_ventas, 
        'utilidad_bruta': utilidad_bruta, 
        'utilidad_neta': utilidad_neta,
        'neto_dia': neto_dia,
        'ventas_dia': total_ventas,
        'labels_trend_ventas': fechas_ordenadas_ventas,
        'data_trend_ventas': data_trend_ventas,
        'labels_trend_gastos': fechas_ordenadas_gastos,
        'data_trend_gastos': data_trend_gastos
    }

@informes_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    hoy = date.today()
    fecha_inicio = request.form.get('fecha_inicio', default=hoy.strftime('%Y-%m-%d'))
    fecha_fin = request.form.get('fecha_fin', default=hoy.strftime('%Y-%m-%d'))
    
    filtros = {
        'filtro_metodo': request.form.get('filtro_metodo', ''),
        'filtro_cat_prod': request.form.get('filtro_categoria_prod', ''),
        'filtro_prod_especifico': request.form.getlist('filtro_producto_especifico'),
        'filtro_cat_gasto': request.form.get('filtro_categoria_gasto', ''),
        'filtro_concepto': request.form.get('filtro_concepto', ''),
        'filtro_proveedor': request.form.get('filtro_proveedor', '')
    }
    
    tab_activa = request.form.get('tab_activa', 'ventas')

    cats_prod = [c[0] for c in db.session.query(Producto.categoria).distinct()]
    list_prod = [p[0] for p in db.session.query(Producto.nombre).distinct().order_by(Producto.nombre)]
    cats_gasto = [c[0] for c in db.session.query(ConceptoGasto.categoria).distinct()]
    list_conceptos = [c[0] for c in db.session.query(ConceptoGasto.nombre).distinct()]
    proveedores = Proveedor.query.filter_by(activo=True).all()

    data = _obtener_data_informes(fecha_inicio, fecha_fin, **filtros)

    labels_ventas = list(data['cat_stats_ventas'].keys())
    data_ventas = list(data['cat_stats_ventas'].values())
    
    labels_gastos = list(data['cat_stats_gastos'].keys())
    data_gastos = [v['monto'] for v in data['cat_stats_gastos'].values()]

    return render_template('informes.html',
                           f_inicio=fecha_inicio, f_fin=fecha_fin, tab_activa=tab_activa, 
                           cats_prod=cats_prod, list_prod=list_prod,
                           cats_gasto=cats_gasto, list_conceptos=list_conceptos,
                           list_prov=proveedores,
                           filtro_metodo=filtros['filtro_metodo'], 
                           filtro_cat_prod=filtros['filtro_cat_prod'], 
                           filtro_prod_esp=filtros['filtro_prod_especifico'],
                           filtro_cat_gasto=filtros['filtro_cat_gasto'], 
                           filtro_con=filtros['filtro_concepto'], 
                           filtro_prov=filtros['filtro_proveedor'],
                           labels_ventas=labels_ventas, data_ventas=data_ventas,
                           labels_gastos=labels_gastos, data_gastos=data_gastos,
                           **data)

@informes_bp.route('/reporte_ventas/<tipo>', methods=['POST'])
@login_required
@admin_required
def reporte_ventas(tipo):
    data = _obtener_data_informes(
        request.form.get('fecha_inicio'), request.form.get('fecha_fin'), 
        filtro_metodo=request.form.get('filtro_metodo'), 
        filtro_cat_prod=request.form.get('filtro_categoria_prod'), 
        filtro_prod_especifico=request.form.getlist('filtro_producto_especifico')
    )
    
    if tipo == 'general':
        reporte_data = [{'categoria': cat, 'total': total} for cat, total in data['cat_stats_ventas'].items()]
        reporte_data.sort(key=lambda x: x['total'], reverse=True)
        return render_template('informe_ventas_general.html', 
                               tabla_datos=reporte_data, 
                               total_ventas=data['total_ventas'], 
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'detallado':
        ventas_por_categoria = defaultdict(list)
        for p in data['productos']:
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
        filtro_metodo=request.form.get('filtro_metodo'), 
        filtro_cat_gasto=request.form.get('filtro_categoria_gasto'), 
        filtro_concepto=request.form.get('filtro_concepto'), 
        filtro_proveedor=request.form.get('filtro_proveedor')
    )
    
    if tipo == 'general':
        reporte_data = [{'categoria': cat, 'total': info['monto']} for cat, info in data['cat_stats_gastos'].items()]
        reporte_data.sort(key=lambda x: x['total'], reverse=True)
        return render_template('informe_gastos_general.html', 
                               tabla_datos=reporte_data, 
                               total_gastos=data['total_gastos'], 
                               f_ini_dt=data['f_ini_dt'], f_fin_dt=data['f_fin_dt'], 
                               datetime=datetime)

    elif tipo == 'detallado':
        gastos_por_categoria = defaultdict(list)
        for g in data['lista_gastos']:
            gastos_por_categoria[g.categoria].append(g)
            
        sorted_categories = sorted(gastos_por_categoria.items(), key=lambda item: sum(g.monto for g in item[1]), reverse=True)

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
        filtro_metodo=request.form.get('filtro_metodo'), 
        filtro_cat_prod=request.form.get('filtro_categoria_prod'), 
        filtro_prod_especifico=request.form.getlist('filtro_producto_especifico'), 
        filtro_cat_gasto=request.form.get('filtro_categoria_gasto'), 
        filtro_concepto=request.form.get('filtro_concepto'), 
        filtro_proveedor=request.form.get('filtro_proveedor')
    )
    return render_template('informe_contable.html', data=data, datetime=datetime)