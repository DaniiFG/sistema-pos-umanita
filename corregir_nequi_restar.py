from app import create_app, db
from app.models import IngresoOcasional

app = create_app()

def restar_a_nequi():
    with app.app_context():
        print("--- 📱 CORRECCIÓN: RESTAR SALDO NEQUI (BASE) ---")
        
        # 1. Buscamos el registro específico de la Base en Nequi
        base_nequi = IngresoOcasional.query.filter_by(
            descripcion="Saldo Inicial Nequi",
            metodo_pago="Nequi"
        ).first()
        
        if not base_nequi:
            print("❌ No se encontró el registro automático de 'Saldo Inicial Nequi'.")
            return

        print(f"\n✅ Base Nequi actual encontrada:")
        print(f"   - Monto actual: ${base_nequi.monto:,.0f}")
        
        # ---------------------------------------------------------
        # AQUÍ DEFINES CUÁNTO QUIERES QUITAR
        monto_a_restar = 11000  
        # ---------------------------------------------------------

        nuevo_total = base_nequi.monto - monto_a_restar
        
        print(f"\n¿Deseas RESTAR ${monto_a_restar:,.0f} a este valor?")
        print(f"   Nuevo valor sería: ${nuevo_total:,.0f}")
        confirmacion = input("Escribe 'si' para confirmar: ")
        
        if confirmacion.lower() == 'si':
            try:
                # 3. EL CAMBIO CLAVE: Usamos -= para restar
                base_nequi.monto -= monto_a_restar
                
                db.session.commit()
                print("\n✅ ¡Saldo de Nequi disminuido correctamente!")
                print(f"   Ahora tu base en Nequi es: ${base_nequi.monto:,.0f}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al guardar: {e}")
        else:
            print("\nOperación cancelada.")

if __name__ == "__main__":
    restar_a_nequi()