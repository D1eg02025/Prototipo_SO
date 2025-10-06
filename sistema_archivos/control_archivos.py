import json
import os
from colorama import init, Fore
init(autoreset=True)

# Archivo disco relativo
BASE_DIR = os.path.dirname(__file__)
DISCO_VIRTUAL = os.path.join(BASE_DIR, "disco_virtual.json")

# Inicializar disco
if not os.path.exists(DISCO_VIRTUAL):
    with open(DISCO_VIRTUAL, "w", encoding="utf-8") as f:
        json.dump({"root": {"tipo": "dir", "contenido": {}}}, f, indent=4, ensure_ascii=False)

# Callback para la consola
output_callback = None
def set_output_callback(cb):
    global output_callback
    output_callback = cb

def log(msg):
    if output_callback:
        try:
            output_callback(str(msg))
        except Exception:
            print(msg)
    else:
        print(msg)

# ----------------------------
# Utilidades internas
# ----------------------------
def cargar_disco():
    with open(DISCO_VIRTUAL, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_disco(disco):
    with open(DISCO_VIRTUAL, "w", encoding="utf-8") as f:
        json.dump(disco, f, indent=4, ensure_ascii=False)

def recorrer_ruta(ruta):
    partes = [p for p in ruta.strip("/").split("/") if p]
    disco = cargar_disco()
    nodo = disco.get("root")

    if partes == ["root"]:
        return nodo, disco

    for parte in partes[1:]:
        if nodo and nodo["tipo"] == "dir" and parte in nodo["contenido"]:
            nodo = nodo["contenido"][parte]
        else:
            return None, disco
    return nodo, disco

# ----------------------------
# Operaciones del sistema de archivos
# ----------------------------
def newdir(ruta, nombre):
    nodo, disco = recorrer_ruta(ruta)
    if nodo is None or nodo.get("tipo") != "dir":
        raise Exception(f"Ruta no encontrada: {ruta}")
    if nombre in nodo["contenido"]:
        raise Exception(f"El directorio '{nombre}' ya existe en {ruta}")
    nodo["contenido"][nombre] = {"tipo": "dir", "contenido": {}}
    guardar_disco(disco)
    log(Fore.GREEN + f"Directorio '{nombre}' creado en '{ruta}'")

def createdoc(ruta, archivo, contenido=""):
    nodo, disco = recorrer_ruta(ruta)
    if nodo is None or nodo.get("tipo") != "dir":
        raise Exception(f"Ruta no encontrada: {ruta}")
    if archivo in nodo["contenido"]:
        raise Exception(f"El archivo '{archivo}' ya existe en {ruta}")
    nodo["contenido"][archivo] = {"tipo": "file", "contenido": contenido}
    guardar_disco(disco)
    log(Fore.GREEN + f"Archivo '{archivo}' creado en '{ruta}'")

def read(ruta_archivo):
    partes = ruta_archivo.strip("/").split("/")
    archivo = partes[-1]
    dir_ruta = "/" + "/".join(partes[:-1]) if partes[:-1] else "/"
    nodo, _ = recorrer_ruta(dir_ruta)
    if nodo and archivo in nodo["contenido"] and nodo["contenido"][archivo]["tipo"] == "file":
        return nodo["contenido"][archivo]["contenido"]
    raise Exception(f"Archivo no encontrado: {ruta_archivo}")

def update(ruta_archivo, nuevo_contenido):
    partes = ruta_archivo.strip("/").split("/")
    archivo = partes[-1]
    dir_ruta = "/" + "/".join(partes[:-1]) if partes[:-1] else "/"
    nodo, disco = recorrer_ruta(dir_ruta)
    if nodo and archivo in nodo["contenido"] and nodo["contenido"][archivo]["tipo"] == "file":
        nodo["contenido"][archivo]["contenido"] = nuevo_contenido
        guardar_disco(disco)
        log(Fore.GREEN + f"Archivo '{archivo}' actualizado")
    else:
        raise Exception(f"Archivo no encontrado: {ruta_archivo}")

def del_file(ruta):
    partes = ruta.strip("/").split("/")
    nombre = partes[-1]
    dir_ruta = "/" + "/".join(partes[:-1]) if partes[:-1] else "/"
    nodo, disco = recorrer_ruta(dir_ruta)
    if nodo and nombre in nodo["contenido"]:
        nodo["contenido"].pop(nombre)
        guardar_disco(disco)
        log(Fore.GREEN + f"'{nombre}' eliminado de {dir_ruta}")
    else:
        raise Exception(f"Archivo o directorio no encontrado: {ruta}")

# función rename
def rename(ruta, nuevo_nombre):
    partes = ruta.strip("/").split("/")
    viejo_nombre = partes[-1]
    dir_ruta = "/" + "/".join(partes[:-1]) if partes[:-1] else "/"
    nodo, disco = recorrer_ruta(dir_ruta)
    if nodo and viejo_nombre in nodo["contenido"]:
        nodo["contenido"][nuevo_nombre] = nodo["contenido"].pop(viejo_nombre)
        guardar_disco(disco)
        log(Fore.GREEN + f"'{viejo_nombre}' renombrado a '{nuevo_nombre}'")
    else:
        raise Exception(f"Archivo o directorio no encontrado: {ruta}")

def list_dir(ruta):
    nodo, _ = recorrer_ruta(ruta)
    if nodo and nodo.get("tipo") == "dir":
        return list(nodo["contenido"].keys())
    raise Exception(f"Directorio no encontrado: {ruta}")

def tree(ruta="/", indent=""):
    nodo, _ = recorrer_ruta(ruta)
    if nodo is None or nodo.get("tipo") != "dir":
        raise Exception(f"Directorio no encontrado: {ruta}")
    for nombre, info in nodo["contenido"].items():
        log(f"{indent}|-- {nombre}/" if info["tipo"] == "dir" else f"{indent}|-- {nombre}")
        if info["tipo"] == "dir":
            tree(f"{ruta.rstrip('/')}/{nombre}", indent + "    ")

# ----------------------------
#  integración con main
# ----------------------------
def get_file_system():
    disco = cargar_disco()
    return disco["root"]
