from app import create_app, db
from app.models import IngresoOcasional

app = create_app()

def sumar_a_la_base():
    with app.app_context():
        print("--- 💰 CORRECCIÓN DE BASE DE CAJA ---")
        
        # 1. Buscamos el registro específico de la Base en Efectivo
        # Usamos la descripción que pusimos en el seeder para encontrarlo
        base_efectivo = IngresoOcasional.query.filter_by(
            descripcion="Base Inicial de Caja (Arranque)",
            metodo_pago="Efectivo Caja"
        ).first()
        
        if not base_efectivo:
            print("❌ No se encontró el registro automático de 'Base Inicial de Caja'.")
            print("   ¿Quizás le cambiaste el nombre o lo borraste?")
            return

        print(f"\n✅ Base actual encontrada:")
        print(f"   - ID: {base_efectivo.id}")
        print(f"   - Descripción: {base_efectivo.descripcion}")
        print(f"   - Monto actual: ${base_efectivo.monto:,.0f}")
        
        # 2. Preguntar y confirmar
        print("\n¿Deseas sumar $50.000 a este valor?")
        print(f"   Nuevo valor sería: ${base_efectivo.monto + 50000:,.0f}")
        confirmacion = input("Escribe 'si' para confirmar: ")
        
        if confirmacion.lower() == 'si':
            try:
                # 3. Realizar la suma
                base_efectivo.monto += 50000
                db.session.commit()
                print("\n✅ ¡Base actualizada correctamente!")
                print(f"   Ahora tu efectivo inicial es: ${base_efectivo.monto:,.0f}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al guardar: {e}")
        else:
            print("\nOperación cancelada. No se hicieron cambios.")

if __name__ == "__main__":
    sumar_a_la_base()