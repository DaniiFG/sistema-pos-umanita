from app import create_app, db
from app.models import Producto, ConceptoGasto

app = create_app()

def agregar_datos():
    with app.app_context():
        print("--- 🛠️ AGREGANDO ITEMS FALTANTES ---")
        
        # 1. Producto Fantasma
        fantasma = Producto.query.filter_by(nombre="Producto Fantasma").first()
        if not fantasma:
            # Precio 0 es la señal para que el POS pregunte el valor
            nuevo_p = Producto(
                nombre="Producto Fantasma", 
                precio=0, 
                categoria="Otros", 
                costo_referencia=0,
                activo=True
            )
            db.session.add(nuevo_p)
            print("✅ 'Producto Fantasma' agregado al menú (Categoría: Otros).")
        else:
            print("ℹ️ 'Producto Fantasma' ya existía.")

        # 2. Concepto Bienestar Laboral
        concepto = ConceptoGasto.query.filter_by(nombre="Bienestar Laboral").first()
        if not concepto:
            nuevo_c = ConceptoGasto(
                nombre="Bienestar Laboral",
                categoria="Obligaciones Laborales",
                es_compra_insumo=False
            )
            db.session.add(nuevo_c)
            print("✅ Concepto 'Bienestar Laboral' agregado a Obligaciones Laborales.")
        else:
            print("ℹ️ 'Bienestar Laboral' ya existía.")
            
        db.session.commit()
        print("\n¡Listo! Datos actualizados.")

if __name__ == "__main__":
    agregar_datos()