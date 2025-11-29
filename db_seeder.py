from app import create_app, db
from app.models import Usuario, Producto, Insumo, ConceptoGasto

app = create_app()

def cargar_datos():
    with app.app_context():
        print("🗑️  Reiniciando Base de Datos...")
        # Borramos todo para empezar limpio con la nueva estructura
        db.drop_all()
        db.create_all()

        # --- 1. USUARIOS ---
        print("👤 Creando Usuarios...")
        admin = Usuario(username='admin', rol='admin')
        admin.set_password('admin123') 
        
        cajero = Usuario(username='cajero', rol='cajero')
        cajero.set_password('cajero123')
        
        db.session.add_all([admin, cajero])

        # --- 2. PRODUCTOS (TU MENÚ REAL) ---
        print("🍗 Cargando Menú de Umañita...")
        productos = [
            # POLLO BROASTER
            Producto(nombre="Ala Broaster (+Papa/Arepa)", precio=3500, categoria="Pollo", costo_referencia=2000),
            Producto(nombre="Pierna Broaster (+Papa/Arepa)", precio=4500, categoria="Pollo", costo_referencia=2500),
            Producto(nombre="Cuadro Broaster (+Papa/Arepa)", precio=4500, categoria="Pollo", costo_referencia=2500),
            Producto(nombre="Pechuga Broaster (+Papa/Arepa)", precio=5500, categoria="Pollo", costo_referencia=3500),
            Producto(nombre="Medio Pollo (4 presas)", precio=18000, categoria="Pollo", costo_referencia=10000),
            Producto(nombre="Pollo Entero (8 presas)", precio=36000, categoria="Pollo", costo_referencia=20000),
            Producto(nombre="Pollo y Medio (12 presas)", precio=54000, categoria="Pollo", costo_referencia=30000),

            # COMIDA RÁPIDA
            Producto(nombre="Hamburguesa Sencilla", precio=15000, categoria="Comida Rápida", costo_referencia=8000),
            Producto(nombre="Hamburguesa Especial", precio=17000, categoria="Comida Rápida", costo_referencia=9500),
            Producto(nombre="Salchipapa", precio=20000, categoria="Comida Rápida", costo_referencia=11000),
            Producto(nombre="Salvajada", precio=30000, categoria="Comida Rápida", costo_referencia=16000),
            Producto(nombre="Combo Sencillo (Ham+Gas+Papa)", precio=20000, categoria="Combos", es_combo=True, costo_referencia=12000),
            Producto(nombre="Combo Especial (HamEsp+Gas+Papa)", precio=22000, categoria="Combos", es_combo=True, costo_referencia=13500),

            # ADICIONES
            Producto(nombre="Adición Papa Salada", precio=2000, categoria="Adiciones", costo_referencia=800),
            Producto(nombre="Adición Arepa Frita", precio=2000, categoria="Adiciones", costo_referencia=800),
            Producto(nombre="Porción Papa Francesa", precio=7000, categoria="Adiciones", costo_referencia=3000),
            Producto(nombre="Salsa de la Casa Extra", precio=1000, categoria="Adiciones", costo_referencia=200),

            # BEBIDAS
            Producto(nombre="Gaseosa 250ml (Vidrio/Plástico)", precio=2000, categoria="Bebidas", costo_referencia=1200),
            Producto(nombre="Bebida 400ml (Mega/Hit/Te)", precio=4000, categoria="Bebidas", costo_referencia=2500),
            Producto(nombre="Coca-Cola 1.5L", precio=8000, categoria="Bebidas", costo_referencia=5000),
            Producto(nombre="Postobon 1.5L", precio=7000, categoria="Bebidas", costo_referencia=4500),
        ]
        db.session.add_all(productos)

        # --- 3. INSUMOS BÁSICOS (BODEGA) ---
        print("📦 Creando Categorías de Bodega...")
        insumos = [
            # MATERIA PRIMA
            Insumo(nombre="Pollo Crudo", categoria="Materia Prima", unidad="Unidades"),
            Insumo(nombre="Papa Sabanera", categoria="Materia Prima", unidad="Bultos"),
            Insumo(nombre="Aceite", categoria="Materia Prima", unidad="Galones"),
            
            # DESECHABLES
            Insumo(nombre="Cajas Pollo Entero", categoria="Desechables", unidad="Paquetes"),
            Insumo(nombre="Bolsas J1", categoria="Desechables", unidad="Paquetes"),
            
            # ASEO
            Insumo(nombre="Cloro", categoria="Aseo", unidad="Galones"),
            Insumo(nombre="Jabón Loza", categoria="Aseo", unidad="Litros"),
            
            # ACTIVOS
            Insumo(nombre="Mesas Plásticas", categoria="Activos", unidad="Unidades"),
            Insumo(nombre="Nevera Coca-Cola", categoria="Activos", unidad="Unidades"),
        ]
        db.session.add_all(insumos)

        # --- 4. CONCEPTOS DE GASTO (Lista Desplegable) ---
        print("💸 Creando Lista de Gastos Predefinidos...")
        conceptos = [
            # MATERIA PRIMA
            ConceptoGasto(nombre="Compra de Pollo Crudo", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Papa", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Aceite", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Bebidas/Gaseosa", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Queso", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Carne/Jamón", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Salsas", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Verduras/Fruver", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Salchichas/Huevos", categoria="Materia Prima"),
            
            # DESECHABLES Y ASEO
            ConceptoGasto(nombre="Compra de Desechables (Cajas/Bolsas)", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Implementos de Aseo", categoria="Materia Prima"),
            ConceptoGasto(nombre="Compra de Gas (Cilindros)", categoria="Servicios"),

            # NÓMINA
            ConceptoGasto(nombre="Pago Turno / Día", categoria="Nomina"),
            ConceptoGasto(nombre="Pago Quincena", categoria="Nomina"),
            ConceptoGasto(nombre="Adelanto de Sueldo", categoria="Nomina"),
            ConceptoGasto(nombre="Compra de Dotación", categoria="Nomina"),
            ConceptoGasto(nombre="Almuerzos Personal", categoria="Nomina"),

            # OPERATIVOS
            ConceptoGasto(nombre="Pago de Arriendo", categoria="Operativos"),
            ConceptoGasto(nombre="Pago de Luz/Agua", categoria="Servicios"),
            ConceptoGasto(nombre="Mantenimiento/Reparaciones", categoria="Operativos"),
            ConceptoGasto(nombre="Publicidad", categoria="Operativos"),
            ConceptoGasto(nombre="Transporte/Domicilios", categoria="Operativos"),
        ]
        db.session.add_all(conceptos)

        db.session.commit()
        print("✅ ¡Sistema cargado con éxito! (Usuarios, Menú y Gastos listos)")

if __name__ == "__main__":
    cargar_datos()