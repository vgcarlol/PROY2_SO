import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import scheduler
import utils

# Paleta de colores básica para Gantt
PALETTE = ["#6fa8dc", "#93c47d", "#e06666", "#f6b26b", "#8e7cc3"]

class SimuladorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador SO")
        self.geometry("900x600")

        # Notebook y pestañas
        self.nb = ttk.Notebook(self)
        self.tab_calc = ttk.Frame(self.nb)
        self.tab_sync = ttk.Frame(self.nb)
        self.nb.add(self.tab_calc, text="Calendarización")
        self.nb.add(self.tab_sync, text="Sincronización")
        self.nb.pack(fill=tk.BOTH, expand=True)

        self._create_variables()
        self._build_tab_calendarizacion()
        self._build_tab_sincronizacion()
        self._build_canvas()
        self._build_bottom_buttons()

    def _create_variables(self):
        # Paths
        self.proc_path = tk.StringVar()
        self.res_path  = tk.StringVar()
        self.act_path  = tk.StringVar()
        # Manual input toggles
        self.proc_manual = tk.BooleanVar(value=False)
        self.res_manual  = tk.BooleanVar(value=False)
        self.act_manual  = tk.BooleanVar(value=False)
        # Calendar vars
        self.alg_vars = { name: tk.BooleanVar() for name in ["FIFO","SJF","SRTF","RR","Priority"] }
        self.quantum  = tk.IntVar(value=2)
        # Sync vars
        self.sync_mode = tk.StringVar(value="mutex")

    def _build_tab_calendarizacion(self):
        frame = ttk.Frame(self.tab_calc, padding=5)
        frame.pack(fill=tk.X)

        # Carga de procesos
        ttk.Button(frame, text="Cargar Procesos", command=self._load_processes).grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.proc_path, state="readonly", width=40).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(frame, text="Ingresar manualmente", variable=self.proc_manual,
                        command=self._toggle_proc_input).grid(row=0, column=2)

        # Preview o input
        self.proc_preview = tk.Text(self.tab_calc, height=5, state=tk.DISABLED)
        self.proc_preview.pack(fill=tk.X, padx=5, pady=2)

        # Algoritmos y quantum
        alg_frame = ttk.LabelFrame(self.tab_calc, text="Algoritmos")
        alg_frame.pack(fill=tk.X, padx=5, pady=5)
        for i,(name,var) in enumerate(self.alg_vars.items()):
            ttk.Checkbutton(alg_frame, text=name, variable=var).grid(row=i, column=0, sticky="w")
        ttk.Label(alg_frame, text="Quantum (RR):").grid(row=0, column=1, padx=10)
        ttk.Entry(alg_frame, textvariable=self.quantum, width=5).grid(row=0, column=2)

        # Botón iniciar simulación
        btn_frame = ttk.Frame(self.tab_calc, padding=5)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Iniciar Simulación", command=self._on_execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar Canvas",  command=self._on_clear).pack(side=tk.LEFT)

    def _build_tab_sincronizacion(self):
        frame = ttk.Frame(self.tab_sync, padding=5)
        frame.pack(fill=tk.X)

        # Carga de recursos
        ttk.Button(frame, text="Cargar Recursos", command=self._load_resources).grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.res_path, state="readonly", width=30).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(frame, text="Manual", variable=self.res_manual,
                        command=self._toggle_res_input).grid(row=0, column=2)
        self.res_preview = tk.Text(self.tab_sync, height=3, state=tk.DISABLED)
        self.res_preview.pack(fill=tk.X, padx=5, pady=2)

        # Carga de acciones
        ttk.Button(frame, text="Cargar Acciones", command=self._load_actions).grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.act_path, state="readonly", width=30).grid(row=1, column=1, padx=5)
        ttk.Checkbutton(frame, text="Manual", variable=self.act_manual,
                        command=self._toggle_act_input).grid(row=1, column=2)
        self.act_preview = tk.Text(self.tab_sync, height=5, state=tk.DISABLED)
        self.act_preview.pack(fill=tk.X, padx=5, pady=2)

        # Modo mutex/semaforo
        mode_frame = ttk.LabelFrame(self.tab_sync, text="Modo de Sincronización")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Mutex",     variable=self.sync_mode, value="mutex").grid(row=0,column=0,padx=5)
        ttk.Radiobutton(mode_frame, text="Semáforo", variable=self.sync_mode, value="semaphore").grid(row=0,column=1,padx=5)

        # Botón iniciar simulación
        btn_frame2 = ttk.Frame(self.tab_sync, padding=5)
        btn_frame2.pack(fill=tk.X)
        ttk.Button(btn_frame2, text="Iniciar Simulación", command=self._on_execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Limpiar Canvas",      command=self._on_clear).pack(side=tk.LEFT)

    def _build_canvas(self):
        # Contenedor con scrollbars
        cframe = ttk.Frame(self)
        cframe.pack(fill=tk.BOTH, expand=True)
        # Canvas
        self.canvas = tk.Canvas(cframe, background="white")
        # Scrollbars
        hbar = ttk.Scrollbar(cframe, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = ttk.Scrollbar(cframe, orient=tk.VERTICAL,   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid( row=0, column=1, sticky="ns" )
        hbar.grid( row=1, column=0, sticky="ew" )
        cframe.rowconfigure(0, weight=1)
        cframe.columnconfigure(0, weight=1)

    def _build_bottom_buttons(self):
        # No usado, botones en cada pestaña
        pass

    # — Carga y toggles —
    def _load_processes(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files","*.txt")])
        if not path: return
        self.proc_path.set(path)
        self.proc_preview.config(state=tk.NORMAL)
        self.proc_preview.delete("1.0", tk.END)
        preview = "".join(open(path).readlines()[:10])
        self.proc_preview.insert(tk.END, preview)
        if not self.proc_manual.get():
            self.proc_preview.config(state=tk.DISABLED)

    def _load_resources(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files","*.txt")])
        if not path: return
        self.res_path.set(path)
        self.res_preview.config(state=tk.NORMAL)
        self.res_preview.delete("1.0", tk.END)
        preview = "".join(open(path).readlines()[:5])
        self.res_preview.insert(tk.END, preview)
        if not self.res_manual.get():
            self.res_preview.config(state=tk.DISABLED)

    def _load_actions(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files","*.txt")])
        if not path: return
        self.act_path.set(path)
        self.act_preview.config(state=tk.NORMAL)
        self.act_preview.delete("1.0", tk.END)
        preview = "".join(open(path).readlines()[:10])
        self.act_preview.insert(tk.END, preview)
        if not self.act_manual.get():
            self.act_preview.config(state=tk.DISABLED)

    def _toggle_proc_input(self):
        state = tk.NORMAL if self.proc_manual.get() else tk.DISABLED
        self.proc_preview.config(state=state)

    def _toggle_res_input(self):
        state = tk.NORMAL if self.res_manual.get() else tk.DISABLED
        self.res_preview.config(state=state)

    def _toggle_act_input(self):
        state = tk.NORMAL if self.act_manual.get() else tk.DISABLED
        self.act_preview.config(state=state)

    # — Lógica de simulación —
    def _on_execute(self):
        self.canvas.delete("all")
        current = self.nb.index(self.nb.select())
        if current == 0:
            self._run_calendarizacion()
        else:
            self._run_sincronizacion()

    def _on_clear(self):
        self.canvas.delete("all")

    def _run_calendarizacion(self):
        # Leer procesos
        try:
            if self.proc_manual.get():
                lines = self.proc_preview.get("1.0", tk.END).strip().splitlines()
                procs = [scheduler.Process(*map(str.strip, line.split(","))) for line in lines if line.strip()]
                procs = [scheduler.Process(p.pid, int(p.bt), int(p.at), int(p.prio)) for p in procs]
            else:
                procs = utils.leer_procesos(self.proc_path.get())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer procesos:\n{e}")
            return

        selected = [name for name,var in self.alg_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Atención", "Selecciona al menos un algoritmo.")
            return

        max_end = 0
        for idx, name in enumerate(selected):
            procs_copy = [p.copy() for p in procs]
            if name == "SRTF":
                done, gantt = scheduler.srtf(procs_copy)
            elif name == "RR":
                done = scheduler.rr(procs_copy, self.quantum.get())
                gantt = [(p.pid, p.start, p.end) for p in done]
            else:
                func = getattr(scheduler, name.lower())
                done = func(procs_copy)
                gantt = [(p.pid, p.start, p.end) for p in done]
            avg = utils.calcular_avg_waiting(done)

            # Etiqueta
            self.canvas.create_text(10, 20 + idx*80,
                                    text=f"{name} (Avg WT: {avg})", anchor="w",
                                    font=("Arial", 10, "bold"))
            # Gantt
            for pid, start, end in gantt:
                color = PALETTE[idx % len(PALETTE)]
                y = 40 + idx*80
                x1 = 10 + start*30
                x2 = 10 + end*30
                self.canvas.create_rectangle(x1, y, x2, y+30, fill=color, outline="black")
                self.canvas.create_text((x1+x2)//2, y+15, text=pid)
                max_end = max(max_end, end)

        # Ajustar scrollregion
        width = 10 + max_end*30 + 50
        height = 40 + len(selected)*80 + 20
        self.canvas.config(scrollregion=(0,0,width,height))

    def _run_sincronizacion(self):
        try:
            if self.res_manual.get():
                lines = self.res_preview.get("1.0", tk.END).strip().splitlines()
                resources = {l.split(",")[0].strip(): int(l.split(",")[1]) for l in lines}
            else:
                resources = utils.leer_recursos(self.res_path.get())
            if self.act_manual.get():
                lines = self.act_preview.get("1.0", tk.END).strip().splitlines()
                actions = [utils.Action(*map(str.strip, l.split(","))) for l in lines]
            else:
                actions = utils.leer_acciones(self.act_path.get())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer recursos/acciones:\n{e}")
            return

        events = scheduler.simulate_sync(resources, actions, mode=self.sync_mode.get())
        y = 10
        for cycle, pid, act, res, state in events:
            txt = f"Ciclo {cycle}: {pid} {act} {res} -> {state}"
            self.canvas.create_text(10, y, text=txt, anchor="w", font=("Arial", 9))
            y += 20
        self.canvas.config(scrollregion=(0,0,800,y+20))

if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()
