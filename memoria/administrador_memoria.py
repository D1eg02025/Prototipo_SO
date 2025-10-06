import threading
from colorama import init, Fore
init(autoreset=True)

MEMORIA_TOTAL = 50
memoria = [None] * MEMORIA_TOTAL
memoria_virtual = {}
lock = threading.Lock()

# Callback de salida
output_callback = None

def log(msg):
    if output_callback:
        output_callback(msg)
    else:
        print(msg)

def asignar_memoria(nombre_proceso, tamaño):
    with lock:
        libres_totales = memoria.count(None)
        if libres_totales < tamaño:
            log(Fore.BLUE + f"[MEMORIA] No hay suficiente memoria para '{nombre_proceso}'. Necesita {tamaño}, disponible {libres_totales}.")
            return False

        indices_asignados = []
        asignadas = 0
        for i in range(MEMORIA_TOTAL):
            if memoria[i] is None:
                memoria[i] = nombre_proceso
                indices_asignados.append(i)
                asignadas += 1
                if asignadas == tamaño:
                    break

        memoria_virtual.setdefault(nombre_proceso, []).extend(indices_asignados)
        log(Fore.BLUE + f"[MEMORIA] Asignadas {asignadas} unidades a '{nombre_proceso}' (índices {indices_asignados}).")
        return True

def liberar_memoria(nombre_proceso, indices=None):
    with lock:
        if indices is None:
            indices = [i for i, p in enumerate(memoria) if p == nombre_proceso]

        liberado = 0
        for i in indices:
            if memoria[i] == nombre_proceso:
                memoria[i] = None
                liberado += 1

        if nombre_proceso in memoria_virtual:
            memoria_virtual[nombre_proceso] = [i for i in memoria_virtual[nombre_proceso] if i not in indices]
            if not memoria_virtual[nombre_proceso]:
                memoria_virtual.pop(nombre_proceso)

        if liberado > 0:
            log(Fore.BLUE + f"[MEMORIA] Liberadas {liberado} unidades de '{nombre_proceso}' (física y virtual).")
        else:
            log(Fore.BLUE + f"[MEMORIA] No se encontró memoria asignada a '{nombre_proceso}'.")

def tiene_memoria(nombre_proceso):
    with lock:
        return bool(memoria_virtual.get(nombre_proceso, []))

def memoria_disponible():
    with lock:
        return memoria.count(None)
