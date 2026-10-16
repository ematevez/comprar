"""
generar_codigos.py
Corré esto vos mismo por consola cuando necesites códigos de renovación de
un solo uso (para no tener que tipear siempre la clave maestra, o para dar
uno puntual a alguien sin darle la clave maestra en sí).

Uso:
    python generar_codigos.py           -> genera 5 códigos
    python generar_codigos.py 10        -> genera 10 códigos
"""
import sys
from licencia import generar_codigos

if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    codigos = generar_codigos(cantidad)

    print(f"\n✅ Se generaron {len(codigos)} códigos de renovación (un solo uso cada uno):\n")
    for c in codigos:
        print(f"   {c}")
    print(f"\nQuedaron guardados en codigos_renovacion.json junto con los que ya tenías.")
    print("Cada uno sirve UNA vez para renovar 15 días (o autorizar una máquina nueva).")
