import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from sistema_archivos import control_archivos as fs
from memoria import administrador_memoria as mem
from procesos import gestor_procesos as gp
import threading

class SistemaOperativoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Prototipo Sistema Operativo")
        self.root.geometry("900x520")

        # ==== PANELES ====
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo → Explorador de archivos
        self.frame_explorador = ttk.Frame(self.paned, padding=6)
        self.paned.add(self.frame_explorador, weight=1)

        # Panel derecho → Consola de mensajes
        self.frame_consola = ttk.Frame(self.paned, padding=6)
        self.paned.add(self.frame_consola, weight=2)

        # ==== EXPLORADOR ====
        self.tree = ttk.Treeview(self.frame_explorador)
        self.tree.pack(fill=tk.BOTH, expand=True, side="top")
        self.tree.bind("<Double-1>", self.explorar)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        vsb = ttk.Scrollbar(self.frame_explorador, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Contenedor de botones
        self.frame_botones = ttk.Frame(self.frame_explorador, padding=4)
        self.frame_botones.pack(fill=tk.X, side="bottom")

        self.btn_newdir = ttk.Button(self.frame_botones, text="Nueva Carpeta", command=self.crear_carpeta)
        self.btn_newdir.pack(fill=tk.X, pady=2)
        self.btn_newfile = ttk.Button(self.frame_botones, text="Nuevo Archivo", command=self.crear_archivo)
        self.btn_newfile.pack(fill=tk.X, pady=2)
        self.btn_rename = ttk.Button(self.frame_botones, text="Renombrar", command=self.renombrar)
        self.btn_rename.pack(fill=tk.X, pady=2)
        self.btn_delete = ttk.Button(self.frame_botones, text="Eliminar", command=self.eliminar)
        self.btn_delete.pack(fill=tk.X, pady=2)


        self.ruta_actual = "/root"
        self.refrescar_tree()

        # ==== CONSOLA DE MENSAJES ====
        self.text_console = tk.Text(self.frame_consola, bg="black", fg="white", insertbackground="white")
        self.text_console.pack(fill=tk.BOTH, expand=True)

        # Conectar callbacks de módulos
        try:
            fs.set_output_callback(self.mostrar_mensaje)
        except Exception:
            try:
                fs.output_callback = self.mostrar_mensaje
            except Exception:
                pass

        if hasattr(mem, "set_output_callback"):
            mem.set_output_callback(self.mostrar_mensaje)
        else:
            try:
                mem.output_callback = self.mostrar_mensaje
            except Exception:
                pass

        if hasattr(gp, "set_output_callback"):
            gp.set_output_callback(self.mostrar_mensaje)
        else:
            try:
                gp.output_callback = self.mostrar_mensaje
            except Exception:
                pass

        # ==== Hotkey para abrir consola de comandos ====
        self.root.bind("<Control-h>", self.abrir_comandos)

    # ------------------ Explorador ------------------
    def refrescar_tree(self):
        self.tree.delete(*self.tree.get_children())
        try:
            root_node = fs.get_file_system()
        except Exception as e:
            self.mostrar_mensaje(f"[ERROR] No se pudo cargar disco: {e}")
            return

        root_id = self.tree.insert("", "end", text="root", open=True, values=["/root"])
        self._llenar_tree_from_node(root_node, "/root", root_id)
        self._select_path_in_tree(self.ruta_actual)

    def _llenar_tree_from_node(self, nodo, ruta_actual, parent_id):
        contenido = nodo.get("contenido", {})
        carpetas = sorted([name for name, info in contenido.items() if info.get("tipo") == "dir"])
        archivos = sorted([name for name, info in contenido.items() if info.get("tipo") == "file"])

        for nombre in carpetas:
            path = f"{ruta_actual}/{nombre}"
            child_id = self.tree.insert(parent_id, "end", text=nombre + "/", open=False, values=[path])
            self._llenar_tree_from_node(contenido[nombre], path, child_id)

        for nombre in archivos:
            path = f"{ruta_actual}/{nombre}"
            self.tree.insert(parent_id, "end", text=nombre, values=[path])

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        values = self.tree.item(item_id, "values")
        if values:
            ruta = values[0]
        else:
            ruta = self._path_from_item(item_id)
        self.ruta_actual = ruta
        self.mostrar_mensaje(f"[INFO] Ruta actual: {self.ruta_actual}")

    def _path_from_item(self, item_id):
        parts = []
        cur = item_id
        while cur:
            text = self.tree.item(cur, "text")
            if text.endswith("/"):
                text = text[:-1]
            parts.append(text)
            cur = self.tree.parent(cur)
        parts.reverse()
        return "/" + "/".join(parts)

    def _select_path_in_tree(self, path):
        if not path:
            return False
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            return False
        top_children = self.tree.get_children("")
        if not top_children:
            return False
        cur_id = top_children[0]
        if parts == ["root"]:
            self.tree.selection_set(cur_id)
            self.tree.focus(cur_id)
            self.tree.see(cur_id)
            return True
        for part in parts[1:]:
            found = None
            for child in self.tree.get_children(cur_id):
                text = self.tree.item(child, "text")
                text_cmp = text[:-1] if text.endswith("/") else text
                if text_cmp == part:
                    found = child
                    break
            if not found:
                return False
            self.tree.item(found, open=True)
            cur_id = found
        self.tree.selection_set(cur_id)
        self.tree.focus(cur_id)
        self.tree.see(cur_id)
        return True

    def explorar(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if values:
            ruta = values[0]
            self.ruta_actual = ruta
            self.mostrar_mensaje(f"[INFO] Ruta actual: {ruta}")

    # ------------------ Crear/Eliminar/Renombrar ------------------
    def crear_carpeta(self):
        nombre = simpledialog.askstring("Nueva Carpeta", f"Crear en: {self.ruta_actual}\nNombre de la carpeta:")
        if not nombre:
            return
        try:
            fs.newdir(self.ruta_actual, nombre)
            self.refrescar_tree()
            self._select_path_in_tree(self.ruta_actual)
        except Exception as e:
            messagebox.showerror("Error al crear carpeta", str(e))

    def crear_archivo(self):
        nombre = simpledialog.askstring("Nuevo Archivo", f"Crear en: {self.ruta_actual}\nNombre del archivo:")
        if not nombre:
            return
        try:
            fs.createdoc(self.ruta_actual, nombre, "Contenido inicial")
            self.refrescar_tree()
            self._select_path_in_tree(self.ruta_actual)
        except Exception as e:
            messagebox.showerror("Error al crear archivo", str(e))

    def eliminar(self):
        try:
            parent_path = "/".join(self.ruta_actual.split("/")[:-1]) or "/root"
            fs.del_file(self.ruta_actual)
            self.ruta_actual = parent_path
            self.refrescar_tree()
            self._select_path_in_tree(self.ruta_actual)
        except Exception as e:
            messagebox.showerror("Error al eliminar", str(e))

    def renombrar(self):
        nuevo_nombre = simpledialog.askstring("Renombrar", f"Nuevo nombre para: {self.ruta_actual}")
        if not nuevo_nombre:
            return
        try:
            fs.rename(self.ruta_actual, nuevo_nombre)
            parent_path = "/".join(self.ruta_actual.split("/")[:-1]) or "/root"
            self.ruta_actual = parent_path
            self.refrescar_tree()
            self._select_path_in_tree(self.ruta_actual)
        except Exception as e:
            messagebox.showerror("Error al renombrar", str(e))

    # ------------------ Consola de comandos ------------------
    def mostrar_mensaje(self, mensaje):
        self.text_console.insert(tk.END, str(mensaje) + "\n")
        self.text_console.see(tk.END)

    def abrir_comandos(self, event=None):
        ventana_cmd = tk.Toplevel(self.root)
        ventana_cmd.title("Consola de Comandos")
        ventana_cmd.geometry("520x200")

        self.text_cmd = tk.Text(ventana_cmd, bg="black", fg="white", insertbackground="white", height=6)
        self.text_cmd.pack(fill=tk.BOTH, expand=True)

        ayuda = (
            "Comandos: mkdir <nombre>, touch <archivo>, ls, tree\n"
            "Procesos: proc <id> <mem>, mem <id> <tam>, run, help\n"
            "Enter para ejecutar el comando."
        )
        self.mostrar_mensaje("[HELP] " + ayuda)

        def ejecutar_cmd(event=None):
            if event and (event.state & 0x0001):
                return None
            cmd = self.text_cmd.get("1.0", "end-1c").strip()
            if cmd:
                self.mostrar_mensaje(f"$ {cmd}")
                self.procesar_comando(cmd)
                self.text_cmd.delete("1.0", "end")
            return "break"

        # Enter normal ejecuta, Shift+Enter no
        self.text_cmd.bind("<Return>", ejecutar_cmd)
        self.text_cmd.focus_set()

        for i, cmd in enumerate(["mkdir ", "touch ", "ls", "tree", "mem ", "proc "], start=1):
            ventana_cmd.bind(f"<Control-{i}>", lambda e, c=cmd: self._insert_cmd(c))

        ventana_cmd.focus_set()

    def _insert_cmd(self, cmd):
        """Inserta un comando base en la consola de comandos"""
        if hasattr(self, "text_cmd"):
            self.text_cmd.delete("1.0", "end")   
            self.text_cmd.insert("1.0", cmd)     
            self.text_cmd.focus_set()

    def procesar_comando(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        partes = cmd.split()
        comando = partes[0].lower()

        try:
            if comando == "mkdir":
                if len(partes) < 2:
                    self.mostrar_mensaje("[ERROR] Uso: mkdir <nombre>")
                else:
                    fs.newdir(self.ruta_actual, partes[1])
                    self.refrescar_tree()
                    self._select_path_in_tree(self.ruta_actual)

            elif comando == "touch":
                if len(partes) < 2:
                    self.mostrar_mensaje("[ERROR] Uso: touch <archivo>")
                else:
                    fs.createdoc(self.ruta_actual, partes[1], "")
                    self.refrescar_tree()
                    self._select_path_in_tree(self.ruta_actual)

            elif comando == "ls":
                try:
                    archivos = fs.list_dir(self.ruta_actual)
                    self.mostrar_mensaje("  ".join(archivos))
                except Exception as e:
                    self.mostrar_mensaje(f"[ERROR] {e}")


            elif comando == "tree":
                fs.tree(self.ruta_actual)

            elif comando == "mem":
                if len(partes) < 3:
                    self.mostrar_mensaje("[ERROR] Uso: mem <id> <tamaño>")
                else:
                    mem.asignar_memoria(partes[1], int(partes[2]))

            elif comando == "proc":
                if len(partes) < 3:
                    self.mostrar_mensaje("[ERROR] Uso: proc <id> <mem>")
                else:
                    gp.crear_proceso(partes[1], int(partes[2]))

            elif comando == "run":
                t = threading.Thread(target=gp.scheduler, daemon=True)
                t.start()
                self.mostrar_mensaje("[INFO] Scheduler iniciado (hilo).")

            elif comando == "help":
                self.mostrar_mensaje(
                    "Comandos: mkdir <nombre>, touch <archivo>, ls, tree\n"
                    "Procesos: proc <id> <mem>, mem <id> <tam>, run, help\n"
                    "Enter para ejecutar el comando."
                )

            else:
                self.mostrar_mensaje(f"[ERROR] Comando no reconocido: {comando}")

        except Exception as e:
            self.mostrar_mensaje(f"[ERROR] {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaOperativoUI(root)
    root.mainloop()
