from app import create_app, db
from app.models import IngresoOcasional

app = create_app()

def sumar_a_nequi():
    with app.app_context():
        print("--- 📱 CORRECCIÓN DE SALDO NEQUI (BASE) ---")
        
        # 1. Buscamos el registro específico de la Base en Nequi
        # Usamos la descripción y método exactos del seeder
        base_nequi = IngresoOcasional.query.filter_by(
            descripcion="Saldo Inicial Nequi",
            metodo_pago="Nequi"
        ).first()
        
        if not base_nequi:
            print("❌ No se encontró el registro automático de 'Saldo Inicial Nequi'.")
            print("   ¿Quizás le cambiaste el nombre o lo borraste?")
            return

        print(f"\n✅ Base Nequi actual encontrada:")
        print(f"   - ID: {base_nequi.id}")
        print(f"   - Descripción: {base_nequi.descripcion}")
        print(f"   - Monto actual: ${base_nequi.monto:,.0f}")
        
        # 2. Preguntar y confirmar la suma de $1.000
        monto_a_sumar = 1000
        nuevo_total = base_nequi.monto + monto_a_sumar
        
        print(f"\n¿Deseas sumar ${monto_a_sumar:,.0f} a este valor?")
        print(f"   Nuevo valor sería: ${nuevo_total:,.0f}")
        confirmacion = input("Escribe 'si' para confirmar: ")
        
        if confirmacion.lower() == 'si':
            try:
                # 3. Realizar la suma
                base_nequi.monto += monto_a_sumar
                db.session.commit()
                print("\n✅ ¡Saldo de Nequi actualizado correctamente!")
                print(f"   Ahora tu base en Nequi es: ${base_nequi.monto:,.0f}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al guardar: {e}")
        else:
            print("\nOperación cancelada. No se hicieron cambios.")

if __name__ == "__main__":
    sumar_a_nequi()