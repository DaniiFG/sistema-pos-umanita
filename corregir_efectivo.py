from app import create_app, db
from app.models import IngresoOcasional

app = create_app()

def restar_a_la_base():
    with app.app_context():
        print("\n--- 📉 CORRECCIÓN: RESTAR A BASE DE CAJA ---")
        
        # 1. Buscamos el registro específico de la Base en Efectivo
        base_efectivo = IngresoOcasional.query.filter_by(
            descripcion="Base Inicial de Caja (Arranque)",
            metodo_pago="Efectivo Caja"
        ).first()
        
        if not base_efectivo:
            print("❌ No se encontró el registro 'Base Inicial de Caja (Arranque)'.")
            return

        print(f"✅ Base actual encontrada:")
        print(f"   - ID: {base_efectivo.id}")
        print(f"   - Descripción: {base_efectivo.descripcion}")
        print(f"   - Monto actual disponible: ${base_efectivo.monto:,.0f}")
        
        # 2. Pedir el valor a restar
        try:
            monto_a_restar = int(input("\n¿Cuánto dinero deseas RESTAR a la caja? (sin puntos): "))
        except ValueError:
            print("❌ Error: Debes ingresar un número válido.")
            return

        # Verificación básica para no quedar en negativo
        if monto_a_restar > base_efectivo.monto:
            print(f"⚠️  CUIDADO: Vas a restar más de lo que hay. La base quedaría negativa.")
        
        nuevo_total = base_efectivo.monto - monto_a_restar
        
        print(f"\n   Monto a restar: -${monto_a_restar:,.0f}")
        print(f"   Nuevo saldo final será: ${nuevo_total:,.0f}")
        confirmacion = input("Escribe 'si' para confirmar y guardar: ")
        
        if confirmacion.lower() == 'si':
            try:
                # 3. Realizar la resta (El cambio clave es el signo -=)
                base_efectivo.monto -= monto_a_restar
                db.session.commit()
                print("\n✅ ¡Base actualizada correctamente!")
                print(f"   Ahora tu efectivo inicial es: ${base_efectivo.monto:,.0f}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al guardar en base de datos: {e}")
        else:
            print("\nOperación cancelada. No se hicieron cambios.")

if __name__ == "__main__":
    restar_a_la_base()