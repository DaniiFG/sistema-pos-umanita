from app import create_app, db
from app.models import Usuario, Producto, Insumo, ConceptoGasto, Proveedor, IngresoOcasional

app = create_app()

def cargar_datos():
    with app.app_context():
        print("🗑️  BORRANDO DATOS ANTIGUOS Y REINICIANDO SISTEMA...")
        db.drop_all() # Esto borra absolutamente todo
        db.create_all() # Esto crea las tablas vacías

        # --- 1. USUARIOS ---
        print("👤 Creando Usuarios (Admin y Cajero)...")
        admin = Usuario(username='admin', rol='admin')
        admin.set_password('admin123') 
        
        cajero = Usuario(username='cajero', rol='cajero')
        cajero.set_password('cajero123')
        
        db.session.add_all([admin, cajero])
        db.session.commit() # Guardamos para tener el ID del admin disponible

        # --- 2. PROVEEDORES ---
        print("🚚 Creando Proveedores...")
        prov1 = Proveedor(nombre="Avicola El Galpón", nit="900123456", telefono="3101234567", direccion="Central de Abastos")
        prov2 = Proveedor(nombre="Salsamentaria La Mejor", nit="900987654", telefono="3209876543")
        prov3 = Proveedor(nombre="Desechables del Centro", nit="800111222")
        prov4 = Proveedor(nombre="Empresa de Energía", nit="899999999")
        db.session.add_all([prov1, prov2, prov3, prov4])

        # --- 3. MENÚ DE PRODUCTOS ---
        print("🍗 Cargando Menú...")
        productos = [
            # PRESAS INDIVIDUALES
            Producto(nombre="Ala Broaster (+Papa/Arepa)", precio=3500, categoria="Presas Individuales", costo_referencia=2000),
            Producto(nombre="Pierna Broaster (+Papa/Arepa)", precio=4500, categoria="Presas Individuales", costo_referencia=2500),
            Producto(nombre="Cuadro Broaster (+Papa/Arepa)", precio=4500, categoria="Presas Individuales", costo_referencia=2500),
            Producto(nombre="Pechuga Broaster (+Papa/Arepa)", precio=5500, categoria="Presas Individuales", costo_referencia=3500),

            # POLLO AGRUPADO
            Producto(nombre="Medio Pollo (4 presas)", precio=18000, categoria="Medio Pollo", costo_referencia=10000),
            Producto(nombre="Pollo Entero (8 presas)", precio=36000, categoria="Pollo Entero", costo_referencia=20000),
            Producto(nombre="Pollo y Medio (12 presas)", precio=54000, categoria="Pollo y Medio", costo_referencia=30000),

            # COMIDA RÁPIDA / COMBOS
            Producto(nombre="Hamburguesa Sencilla", precio=15000, categoria="Comida Rápida", costo_referencia=8000),
            Producto(nombre="Salchipapa", precio=20000, categoria="Comida Rápida", costo_referencia=11000),
            Producto(nombre="Combo Sencillo (Ham+Gas+Papa)", precio=20000, categoria="Combos", es_combo=True, costo_referencia=12000),

            # ADICIONES
            Producto(nombre="Adición Papa Salada", precio=2000, categoria="Adiciones", costo_referencia=800),
            Producto(nombre="Adición Arepa Frita", precio=2000, categoria="Adiciones", costo_referencia=800),

            # BEBIDAS
            Producto(nombre="Gaseosa 350ml", precio=2500, categoria="Bebidas", costo_referencia=1200),
            Producto(nombre="Coca-Cola 1.5L", precio=8000, categoria="Bebidas", costo_referencia=5000),
        ]
        db.session.add_all(productos)

        # --- 4. INSUMOS BÁSICOS ---
        print("📦 Cargando Bodega Inicial...")
        insumos = [
            Insumo(nombre="Pollo Crudo", categoria="Materia Prima", unidad="Unidades"),
            Insumo(nombre="Papa Sabanera", categoria="Materia Prima", unidad="Bultos"),
            Insumo(nombre="Aceite", categoria="Materia Prima", unidad="Galones"),
            Insumo(nombre="Cajas Pollo", categoria="Desechables", unidad="Paquetes"),
            Insumo(nombre="Jabón Liquido", categoria="Aseo", unidad="Litros"),
            Insumo(nombre="Freidora", categoria="Activos", unidad="Unidades"),
        ]
        db.session.add_all(insumos)

        # --- 5. CONCEPTOS DE GASTO ---
        print("💸 Configurando Tipos de Gastos...")
        conceptos = [
            # MATERIA PRIMA
            ConceptoGasto(nombre="Compra de Pollo Crudo", categoria="Materia Prima", es_compra_insumo=True),
            ConceptoGasto(nombre="Compra de Papa", categoria="Materia Prima", es_compra_insumo=True),
            ConceptoGasto(nombre="Compra de Aceite", categoria="Materia Prima", es_compra_insumo=True),
            ConceptoGasto(nombre="Compra de Bebidas", categoria="Materia Prima", es_compra_insumo=True),
            ConceptoGasto(nombre="Compra de Desechables", categoria="Materia Prima", es_compra_insumo=True),
            ConceptoGasto(nombre="Compra de Aseo", categoria="Materia Prima", es_compra_insumo=True),

            # OBLIGACIONES LABORALES
            ConceptoGasto(nombre="Pago Nómina", categoria="Obligaciones Laborales"),
            ConceptoGasto(nombre="Compra Dotación", categoria="Obligaciones Laborales"),
            ConceptoGasto(nombre="Alimentación Personal", categoria="Obligaciones Laborales"),

            # OPERATIVOS
            ConceptoGasto(nombre="Pago de Arriendo Local", categoria="Arriendo"),
            ConceptoGasto(nombre="Pago Luz", categoria="Servicios"),
            ConceptoGasto(nombre="Pago Agua", categoria="Servicios"),
            ConceptoGasto(nombre="Pago Gas", categoria="Servicios"),
            ConceptoGasto(nombre="Pago Internet/Plan", categoria="Servicios"),

            # OTROS GASTOS
            ConceptoGasto(nombre="Mantenimiento y Mejoras", categoria="Otros Gastos"),
            ConceptoGasto(nombre="Publicidad y Marketing", categoria="Otros Gastos"),
            ConceptoGasto(nombre="Gastos Personales", categoria="Otros Gastos"),
            ConceptoGasto(nombre="Transporte / Taxis", categoria="Otros Gastos"),
            
            # ACTIVOS
            ConceptoGasto(nombre="Compra de Equipos (Freidora, nevera)", categoria="Activos"),
            ConceptoGasto(nombre="Mejoras Locales", categoria="Activos"),
        ]
        db.session.add_all(conceptos)

        # --- 6. BASES INICIALES DE DINERO (AQUÍ ESTÁ TU SOLICITUD) ---
        print("💰 Estableciendo Bases de Caja (Saldos Iniciales)...")
        # Usamos 'IngresoOcasional' para que cuente en el saldo pero no como venta de producto
        bases = [
            # Efectivo
            IngresoOcasional(
                descripcion="Base Inicial de Caja (Arranque)", 
                monto=1500000, 
                origen="Base Inicial", 
                metodo_pago="Efectivo Caja", 
                usuario_id=admin.id
            ),
            # Nequi
            IngresoOcasional(
                descripcion="Saldo Inicial Nequi", 
                monto=184300, 
                origen="Base Inicial", 
                metodo_pago="Nequi", 
                usuario_id=admin.id
            ),
            # Daviplata
            IngresoOcasional(
                descripcion="Saldo Inicial Daviplata", 
                monto=161845, 
                origen="Base Inicial", 
                metodo_pago="Daviplata", 
                usuario_id=admin.id
            ),
        ]
        db.session.add_all(bases)

        db.session.commit()
        print("✅ ¡SISTEMA REINICIADO Y LISTO!")
        print("   - Ventas y Gastos antiguos: BORRADOS")
        print("   - Base Efectivo: $1,500,000")
        print("   - Base Nequi: $184,300")
        print("   - Base Daviplata: $161,845")

if __name__ == "__main__":
    cargar_datos()