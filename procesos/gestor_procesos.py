import threading, time, os
from queue import Queue
from memoria.administrador_memoria import memoria_virtual, tiene_memoria, liberar_memoria, asignar_memoria
from colorama import init, Fore
init(autoreset=True)

procesos = []
cola_procesos = Queue()
scheduler_evento = threading.Event()
scheduler_evento.set()
lock = threading.Lock()

# Callback de salida
output_callback = None
def log(msg):
    if output_callback:
        output_callback(msg)
    else:
        print(msg)

class Proceso:
    def __init__(self, nombre, memoria_necesaria=5, quantum=1):
        self.nombre = nombre
        self.memoria_necesaria = memoria_necesaria
        self.pasos_totales = memoria_necesaria
        self.pasos = 0
        self.thread = threading.Thread(target=self.run)
        self.terminado = False
        self.quantum = quantum
        self.evento = threading.Event()
        self.evento.clear()
        self.activo_en_scheduler = True

    def run(self):
        while self.pasos < self.pasos_totales and not self.terminado:
            self.evento.wait()
            with lock:
                indices = memoria_virtual.get(self.nombre, [])
                if indices:
                    idx = indices.pop(0)
                    self.pasos += 1
                    log(Fore.GREEN + f"[{self.nombre}] Ejecutando paso {self.pasos}/{self.pasos_totales} (usando memoria índice {idx})")
                    liberar_memoria(self.nombre, [idx])
                else:
                    log(Fore.YELLOW + f"[{self.nombre}] Memoria insuficiente, esperando...")
            time.sleep(1)
        self.terminado = True
        liberar_memoria(self.nombre)
        log(Fore.GREEN + f"[{self.nombre}] Proceso terminado.")

# ----------------------------
# Funciones del gestor
# ----------------------------
def crear_proceso(nombre, memoria_necesaria=5):
    if not asignar_memoria(nombre, memoria_necesaria):
        log(Fore.RED + f"[GESTOR] No se pudo crear el proceso '{nombre}'. Falta de memoria.")
        return None
    p = Proceso(nombre, memoria_necesaria)
    procesos.append(p)
    cola_procesos.put(p)
    log(Fore.GREEN + f"[GESTOR] Proceso '{nombre}' creado con {memoria_necesaria} pasos y en cola.")
    return p

def listar_procesos():
    lista = []
    log("=== Procesos ===")
    for p in procesos:
        estado = "Terminado" if p.terminado else "En ejecución"
        activo = "Sí" if p.activo_en_scheduler else "No"
        info = f"Proceso: {p.nombre}, Estado: {estado}, Activo: {activo}, Pasos: {p.pasos}/{p.pasos_totales}"
        log(Fore.GREEN + info)
        lista.append(info)
    return lista

def terminar_proceso(nombre):
    for p in procesos:
        if p.nombre == nombre and not p.terminado:
            p.terminado = True
            liberar_memoria(p.nombre)
            log(Fore.GREEN + f"[GESTOR] Proceso '{nombre}' terminado.")
            return True
    log(Fore.YELLOW + f"[GESTOR] Proceso '{nombre}' no encontrado o ya terminado.")
    return False

def pause_scheduler():
    scheduler_evento.clear()

def resume_scheduler():
    scheduler_evento.set()

def scheduler(procesos_a_ejecutar=None, on_finish=None):
    while True:
        scheduler_evento.wait()
        procesos_activos = [p for p in procesos if not p.terminado and (procesos_a_ejecutar is None or p.nombre in procesos_a_ejecutar)]
        if not procesos_activos and cola_procesos.empty():
            log(Fore.GREEN + "[SCHEDULER] Todos los procesos han terminado. Scheduler finalizando...")
            if on_finish: on_finish()
            break
        if not cola_procesos.empty():
            p = cola_procesos.get()
            if p.terminado:
                continue
            if p.activo_en_scheduler and (procesos_a_ejecutar is None or p.nombre in procesos_a_ejecutar):
                if not p.thread.is_alive():
                    p.thread.start()
                p.evento.set()
                time.sleep(p.quantum)
                p.evento.clear()
                if not p.terminado:
                    cola_procesos.put(p)
        else:
            time.sleep(0.1)

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')
