from app import create_app, db
from app.models import Venta

app = create_app()

def analizar_efectivo():
    with app.app_context():
        print("\n💰 --- ANALISIS DE DESCUADRE (SOLO EFECTIVO) ---")
        
        ventas = Venta.query.all()
        ventas_con_cambio = 0
        dinero_sobrante = 0
        
        for v in ventas:
            # 1. Calculamos cuánto efectivo debió entrar realmente
            # (Total Venta - Lo que pagaron por Nequi/Davi)
            otros_pagos = (v.pago_nequi or 0) + (v.pago_daviplata or 0)
            efectivo_real_venta = v.total_venta - otros_pagos
            
            # 2. Obtenemos lo que el sistema registró en efectivo (El billete que entregaron)
            efectivo_registrado = v.pago_efectivo or 0
            
            # 3. La diferencia es el cambio (vueltas) que se sumó incorrectamente a la caja
            # Solo si el registrado es mayor al real (hubo cambio)
            diferencia = efectivo_registrado - efectivo_real_venta
            
            if diferencia > 0:
                ventas_con_cambio += 1
                dinero_sobrante += diferencia
                # print(f" > Venta #{v.id}: Registrado ${efectivo_registrado} | Real ${efectivo_real_venta} | Sobran: ${diferencia}")

        print(f"\n📊 RESULTADO DEL DIAGNÓSTICO:")
        print(f"   ----------------------------------------------------")
        print(f"   Total Ventas analizadas:        {len(ventas)}")
        print(f"   Ventas donde se dio cambio:     {ventas_con_cambio}")
        print(f"   ----------------------------------------------------")
        print(f"   🛑 DINERO 'FANTASMA' EN CAJA:   ${dinero_sobrante:,.0f}")
        print(f"   ----------------------------------------------------")
        print("\n✅ SOLUCIÓN:")
        print("El informe de 'routes.py' corregido que te entregaré a continuación")
        print("restará automáticamente este valor para que tu cierre cuadre.")

if __name__ == "__main__":
    analizar_efectivo()