# actualizar_bd.py
import sqlite3
from app import create_app, db
from app.models import Producto, DetalleVenta

# Configuración manual de conexión para alteraciones crudas
DB_PATH = 'umanita.db'

def agregar_columna(cursor, tabla, columna, tipo):
    try:
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
        print(f"✅ Columna '{columna}' agregada a tabla '{tabla}'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"ℹ️ La columna '{columna}' ya existe en '{tabla}'.")
        else:
            print(f"❌ Error agregando '{columna}' a '{tabla}': {e}")

def actualizar_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- 🛠️ ACTUALIZANDO ESQUEMA DE BASE DE DATOS ---")

    # 1. MODIFICACIONES EN VENTAS
    agregar_columna(cursor, 'venta', 'mesa', 'VARCHAR(50)')
    agregar_columna(cursor, 'venta', 'estado', "VARCHAR(20) DEFAULT 'Cerrada'") # Abierta (para mesas) o Cerrada
    agregar_columna(cursor, 'venta', 'descuento', 'INTEGER DEFAULT 0')
    agregar_columna(cursor, 'venta', 'es_fantasma', 'BOOLEAN DEFAULT 0')

    # 2. MODIFICACIONES EN DETALLES DE VENTA (Para corregir error de nombres)
    agregar_columna(cursor, 'detalle_venta', 'producto_id', 'INTEGER')

    # 3. MODIFICACIONES EN PRODUCTOS
    agregar_columna(cursor, 'producto', 'imagen_local', 'VARCHAR(255)') # Para subida local

    # 4. MODIFICACIONES EN GASTOS
    agregar_columna(cursor, 'gasto', 'iva', 'INTEGER DEFAULT 0')
    agregar_columna(cursor, 'gasto', 'es_fantasma', 'BOOLEAN DEFAULT 0')
    agregar_columna(cursor, 'gasto', 'origen_dinero', "VARCHAR(20) DEFAULT 'Caja Menor'") # Menor o Mayor
    agregar_columna(cursor, 'gasto', 'subtotal_base', 'INTEGER') # Antes de IVA

    conn.commit()
    conn.close()
    
    # 5. REPARACIÓN DE HISTORIAL DE NOMBRES (VINCULAR IDs)
    print("\n--- 🔄 VINCULANDO HISTORIAL DE VENTAS CON IDs DE PRODUCTOS ---")
    app = create_app()
    with app.app_context():
        # Recorremos todos los detalles que no tengan producto_id
        detalles = DetalleVenta.query.filter(DetalleVenta.producto_id == None).all()
        contador = 0
        for det in detalles:
            # Buscamos el producto por nombre exacto
            prod = Producto.query.filter_by(nombre=det.producto_nombre).first()
            if prod:
                det.producto_id = prod.id
                contador += 1
        
        db.session.commit()
        print(f"✅ Se actualizaron {contador} registros antiguos para que no pierdan referencia si cambias el nombre.")

if __name__ == "__main__":
    actualizar_schema()