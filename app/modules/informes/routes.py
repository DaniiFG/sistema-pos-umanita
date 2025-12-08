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
    # Excluimos las ventas fantasma para que no alteren las estadísticas de producto
    # ==============================================================================
    
    # Base de la consulta: Detalles unidos a Ventas
    q_detalles = db.session.query(DetalleVenta, Venta).join(Venta).filter(
        Venta.fecha.between(f_ini, f_fin),
        Venta.es_fantasma == False,  # EXCLUIR FANTASMAS
        Venta.estado == 'Cerrada'    # Solo ventas cobradas
    )

    # Aplicar filtros de Productos si existen
    if filtro_cat_prod:
        # Nota: Esto filtra por la categoría ACTUAL del producto
        q_detalles = q_detalles.join(Producto, DetalleVenta.producto_id == Producto.id).filter(Producto.categoria == filtro_cat_prod)
    
    if filtro_prod_especifico:
        # Manejo de lista o string único
        if isinstance(filtro_prod_especifico, str):
            filtro_prod_especifico = [filtro_prod_especifico]
        # Filtramos por nombre histórico o actual
        q_detalles = q_detalles.filter(DetalleVenta.producto_nombre.in_(filtro_prod_especifico))

    # Filtro por método de pago (solo afecta qué ventas se suman)
    if filtro_metodo:
        if filtro_metodo == 'Efectivo': q_detalles = q_detalles.filter(Venta.pago_efectivo > 0)
        elif filtro_metodo == 'Nequi': q_detalles = q_detalles.filter(Venta.pago_nequi > 0)
        elif filtro_metodo == 'Daviplata': q_detalles = q_detalles.filter(Venta.pago_daviplata > 0)

    resultados_detalles = q_detalles.all()
    
    # Calcular Total Ventas (Comercial)
    total_ventas = sum([d.subtotal for d, v in resultados_detalles])
    
    # Agrupación inteligente de productos (Por ID para soportar cambios de nombre)
    prod_stats = defaultdict(lambda: {'cant': 0, 'dinero': 0, 'categoria': '', 'nombre': ''})
    
    for d, v in resultados_detalles:
        # Clave de agrupación: ID si existe, si no Nombre (para compatibilidad con datos viejos)
        key = d.producto_id if d.producto_id else d.producto_nombre
        
        # Determinar nombre y categoría actuales
        nombre_mostrar = d.producto_nombre
        cat_mostrar = "Sin Categoría"
        
        # Intentamos obtener datos frescos del producto
        if d.producto: # Si hay relación
            nombre_mostrar = d.producto.nombre
            cat_mostrar = d.producto.categoria
        elif d.producto_id: # Si hay ID pero no cargó relación (raro, pero por seguridad)
            p = Producto.query.get(d.producto_id)
            if p: 
                nombre_mostrar = p.nombre
                cat_mostrar = p.categoria
        else:
            # Fallback legacy: buscar por nombre string antiguo
            p_legacy = Producto.query.filter_by(nombre=d.producto_nombre).first()
            if p_legacy:
                cat_mostrar = p_legacy.categoria

        prod_stats[key]['nombre'] = nombre_mostrar
        prod_stats[key]['categoria'] = cat_mostrar
        prod_stats[key]['cant'] += d.cantidad
        prod_stats[key]['dinero'] += d.subtotal

    # Convertir a lista y ordenar por dinero generado
    productos_vendidos = list(prod_stats.values())
    productos_vendidos.sort(key=lambda x: x['dinero'], reverse=True)
    
    # Estadísticas por Categoría (Para Gráficos)
    cat_stats_ventas = defaultdict(int)
    for p in productos_vendidos:
        cat_stats_ventas[p['categoria']] += p['dinero']

    # ==============================================================================
    # 2. GASTOS (Operativos y P&G)
    # Excluimos gastos fantasma de los informes gerenciales
    # ==============================================================================
    q_gastos = Gasto.query.filter(
        Gasto.fecha.between(f_ini, f_fin),
        Gasto.es_fantasma == False # EXCLUIR FANTASMAS DEL REPORTE
    )
    
    if filtro_cat_gasto: q_gastos = q_gastos.filter(Gasto.categoria == filtro_cat_gasto)
    if filtro_concepto: q_gastos = q_gastos.filter(Gasto.descripcion == filtro_concepto)
    if filtro_proveedor: q_gastos = q_gastos.filter(Gasto.proveedor_id == filtro_proveedor)
    
    lista_gastos = q_gastos.order_by(Gasto.fecha.desc()).all()
    total_gastos = sum([g.monto for g in lista_gastos])

    # Agrupación por categoría para gráficos
    cat_stats_gastos = defaultdict(lambda: {'monto': 0, 'detalles': defaultdict(int)})
    for g in lista_gastos:
        cat_stats_gastos[g.categoria]['monto'] += g.monto
        cat_stats_gastos[g.categoria]['detalles'][g.descripcion] += g.monto

    # ==============================================================================
    # 3. CIERRE DE CAJA (REALIDAD FINANCIERA)
    # Aquí INCLUIMOS FANTASMAS porque el dinero real sí se movió de la caja
    # ==============================================================================
    
    # Traer TODO lo del rango
    todas_ventas = Venta.query.filter(Venta.fecha.between(f_ini, f_fin), Venta.estado == 'Cerrada').all()
    todos_gastos = Gasto.query.filter(Gasto.fecha.between(f_ini, f_fin)).all()
    todos_ingresos = IngresoOcasional.query.filter(IngresoOcasional.fecha.between(f_ini, f_fin)).all()

    # --- INGRESOS (VENTAS) ---
    # Corrección Clave: Efectivo Real = (Billete Entregado - Cambio)
    v_efec_neto = sum((v.pago_efectivo - v.cambio_dado) for v in todas_ventas if v.pago_efectivo > 0)
    v_nequi = sum(v.pago_nequi for v in todas_ventas)
    v_davi = sum(v.pago_daviplata for v in todas_ventas)
    
    # --- EGRESOS (GASTOS) ---
    # Detectamos método por string (ej: "Efectivo Caja", "Nequi", etc.)
    g_efec = sum(g.monto for g in todos_gastos if 'Efectivo' in (g.metodo_pago or ''))
    g_nequi = sum(g.monto for g in todos_gastos if 'Nequi' in (g.metodo_pago or ''))
    g_davi = sum(g.monto for g in todos_gastos if 'Daviplata' in (g.metodo_pago or ''))
    
    # --- OTROS INGRESOS (BASE, APORTES) ---
    i_efec = sum(i.monto for i in todos_ingresos if 'Efectivo' in (i.metodo_pago or ''))
    i_nequi = sum(i.monto for i in todos_ingresos if 'Nequi' in (i.metodo_pago or ''))
    i_davi = sum(i.monto for i in todos_ingresos if 'Davi' in (i.metodo_pago or ''))

    # --- CÁLCULO FINAL DE SALDOS ---
    cierre_efectivo = (v_efec_neto + i_efec) - g_efec
    cierre_nequi = (v_nequi + i_nequi) - g_nequi
    cierre_davi = (v_davi + i_davi) - g_davi
    
    # Nuevo Requerimiento: Total Unificado
    total_caja_unificado = cierre_efectivo + cierre_nequi + cierre_davi

    # Detalles para mostrar en acordeón (solo los relevantes)
    detalles_ventas = todas_ventas # Se envían todas para auditoría de caja
    detalles_gastos = todos_gastos
    detalles_otros = todos_ingresos

    # ==============================================================================
    # 4. P & G (Estado de Resultados Aproximado)
    # ==============================================================================
    costo_ventas = 0
    # Usamos la lista 'resultados_detalles' que ya excluye fantasmas
    for d, v in resultados_detalles:
        # Calcular costo basado en el producto
        costo_unitario = 0
        if d.producto:
            costo_unitario = d.producto.costo_referencia
        elif d.producto_id:
            p = Producto.query.get(d.producto_id)
            if p: costo_unitario = p.costo_referencia
        else:
            # Legacy
            p_leg = Producto.query.filter_by(nombre=d.producto_nombre).first()
            if p_leg: costo_unitario = p_leg.costo_referencia
            
        costo_ventas += (d.cantidad * costo_unitario)

    utilidad_bruta = total_ventas - costo_ventas
    utilidad_neta = utilidad_bruta - total_gastos
    
    # Nuevo Requerimiento: Neto del día (Ventas Reales - Gastos Reales del periodo seleccionado)
    neto_dia = total_ventas - total_gastos

    return {
        'f_ini_dt': f_ini, 'f_fin_dt': f_fin, 
        'total_ventas': total_ventas, 
        'productos': productos_vendidos,
        'cat_stats_ventas': cat_stats_ventas,
        'total_gastos': total_gastos, 
        'lista_gastos': lista_gastos, # Lista filtrada (sin fantasmas) para informe visual
        'cat_stats_gastos': cat_stats_gastos,
        'cierre_efectivo': cierre_efectivo, 
        'cierre_nequi': cierre_nequi, 
        'cierre_davi': cierre_davi,
        'total_caja_unificado': total_caja_unificado, 
        'balance_total': total_caja_unificado, # <--- RESTAURADO PARA COMPATIBILIDAD CON INFORME CONTABLE
        'detalles_ventas': detalles_ventas, 
        'detalles_gastos': detalles_gastos, 
        'detalles_otros': detalles_otros,
        'costo_ventas': costo_ventas, 
        'utilidad_bruta': utilidad_bruta, 
        'utilidad_neta': utilidad_neta,
        'neto_dia': neto_dia,
        'ventas_dia': total_ventas # Alias para claridad en template
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

    # Datos para selects de filtros
    cats_prod = [c[0] for c in db.session.query(Producto.categoria).distinct()]
    list_prod = [p[0] for p in db.session.query(Producto.nombre).distinct().order_by(Producto.nombre)]
    cats_gasto = [c[0] for c in db.session.query(ConceptoGasto.categoria).distinct()]
    list_conceptos = [c[0] for c in db.session.query(ConceptoGasto.nombre).distinct()]
    proveedores = Proveedor.query.filter_by(activo=True).all()

    # Obtener toda la data procesada
    data = _obtener_data_informes(fecha_inicio, fecha_fin, **filtros)

    # Preparar datos para Gráficos JS (listas simples)
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
    # Recuperar filtros del form para regenerar data
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
    # Recalcular todo con los filtros actuales para imprimir P&G
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