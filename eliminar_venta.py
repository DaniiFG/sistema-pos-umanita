from app import create_app, db
from app.models import Venta, DetalleVenta

app = create_app()

def borrar_venta_por_id():
    with app.app_context():
        print("--- 🗑️ ELIMINAR VENTA MANUALMENTE ---")
        id_input = input("Ingresa el ID de la venta que quieres borrar: ")
        
        if not id_input.isdigit():
            print("❌ Error: Debes ingresar un número entero.")
            return

        venta_id = int(id_input)
        
        # 1. Buscar la venta
        venta = Venta.query.get(venta_id)
        
        if not venta:
            print(f"❌ No existe ninguna venta con el ID {venta_id}.")
            return

        # Mostrar resumen antes de borrar
        print(f"\n⚠️  Venta Encontrada:")
        print(f"   - Fecha: {venta.fecha}")
        print(f"   - Cliente: {venta.cliente_nombre}")
        print(f"   - Total: ${venta.total_venta:,.0f}")
        
        confirmacion = input("\n¿Estás SEGURO de eliminarla? (Escribe 'si' para confirmar): ")
        
        if confirmacion.lower() == 'si':
            try:
                # 2. Eliminar primero los detalles (los productos asociados a esa venta)
                num_detalles = DetalleVenta.query.filter_by(venta_id=venta.id).delete()
                print(f"   > Se eliminaron {num_detalles} registros de productos asociados.")

                # 3. Eliminar la venta principal
                db.session.delete(venta)
                db.session.commit()
                print("\n✅ ¡Venta eliminada exitosamente!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al borrar: {e}")
        else:
            print("\nOperación cancelada.")

if __name__ == "__main__":
    borrar_venta_por_id()