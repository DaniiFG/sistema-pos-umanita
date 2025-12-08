# reparar_historial.py
from app import create_app, db
from app.models import Producto, DetalleVenta

app = create_app()

def reparar():
    with app.app_context():
        print("--- 🔄 VINCULANDO HISTORIAL DE VENTAS ANTIGUO ---")
        
        # Ahora que actualizaste models.py, Python sí reconocerá 'producto_id'
        detalles = DetalleVenta.query.filter(DetalleVenta.producto_id == None).all()
        
        count = 0
        for d in detalles:
            # Buscamos el producto original por su nombre
            prod = Producto.query.filter_by(nombre=d.producto_nombre).first()
            if prod:
                d.producto_id = prod.id
                count += 1
        
        db.session.commit()
        print(f"✅ ¡Listo! Se vincularon {count} ventas antiguas con sus productos.")
        print("   Ahora puedes cambiar nombres en el menú sin perder el historial.")

if __name__ == "__main__":
    reparar()