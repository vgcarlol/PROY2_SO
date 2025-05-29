import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import scheduler
import utils
import random

# Paleta de colores para Gantt y sincronización
PALETTE = ["#6fa8dc", "#93c47d", "#e06666", "#f6b26b", "#8e7cc3"]
SYNC_COLORS = {"ACCESED": "lightgreen", "WAITING": "lightcoral"}

class SimuladorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador SO")
        self.geometry("900x600")

        # Variables de carga
        self.proc_path   = tk.StringVar()
        self.res_path    = tk.StringVar()
        self.act_path    = tk.StringVar()
        self.proc_manual = tk.BooleanVar(value=False)
        self.res_manual  = tk.BooleanVar(value=False)
        self.act_manual  = tk.BooleanVar(value=False)

        # Variables de simulación
        self.alg_vars  = {name: tk.BooleanVar(value=False) for name in ["FIFO","SJF","SRT","RR","Priority"]}
        self.quantum   = tk.IntVar(value=2)
        self.sync_mode = tk.StringVar(value="mutex")

        # Estado interno para animación
        self.colors      = {}
        self.scale_x     = 30
        self.margin_x    = 500  # espacio para etiqueta con avg
        self.row_height  = 60
        self.cal_events  = []
        self.cal_index   = 0
        self.sync_events = []
        self.sync_index  = 0
        self.max_cycle   = 0

        # Construcción de la UI
        self._build_notebook()
        self._build_canvas()
        self._build_cycle_label()

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.tab_calc = ttk.Frame(self.nb)
        self.tab_sync = ttk.Frame(self.nb)
        self.nb.add(self.tab_calc, text="Calendarización")
        self.nb.add(self.tab_sync, text="Sincronización")
        self.nb.pack(fill=tk.BOTH, expand=True)

        # Calendarización
        frame1 = ttk.Frame(self.tab_calc, padding=5)
        frame1.pack(fill=tk.X)
        ttk.Button(frame1, text="Cargar Procesos", command=self._load_processes).grid(row=0, column=0, sticky="w")
        ttk.Entry(frame1, textvariable=self.proc_path, state="readonly", width=40).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(frame1, text="Ingresar manualmente", variable=self.proc_manual,
                        command=self._toggle_proc_input).grid(row=0, column=2)
        self.proc_preview = tk.Text(self.tab_calc, height=5, state=tk.DISABLED)
        self.proc_preview.pack(fill=tk.X, padx=5, pady=2)

        alg_frame = ttk.LabelFrame(self.tab_calc, text="Algoritmos")
        alg_frame.pack(fill=tk.X, padx=5, pady=5)
        for i,(name,var) in enumerate(self.alg_vars.items()):
            ttk.Checkbutton(alg_frame, text=name, variable=var).grid(row=i, column=0, sticky="w")
        ttk.Label(alg_frame, text="Quantum (RR):").grid(row=0, column=1, padx=10)
        ttk.Entry(alg_frame, textvariable=self.quantum, width=5).grid(row=0, column=2)

        btn1 = ttk.Frame(self.tab_calc, padding=5)
        btn1.pack(fill=tk.X)
        ttk.Button(btn1, text="Iniciar Simulación", command=self._on_execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn1, text="Limpiar Canvas", command=self._on_clear).pack(side=tk.LEFT)

        # Sincronización
        frame2 = ttk.Frame(self.tab_sync, padding=5)
        frame2.pack(fill=tk.X)
        ttk.Button(frame2, text="Cargar Recursos", command=self._load_resources).grid(row=0, column=0, sticky="w")
        ttk.Entry(frame2, textvariable=self.res_path, state="readonly", width=30).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(frame2, text="Manual", variable=self.res_manual,
                        command=self._toggle_res_input).grid(row=0, column=2)
        self.res_preview = tk.Text(self.tab_sync, height=3, state=tk.DISABLED)
        self.res_preview.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(frame2, text="Cargar Acciones", command=self._load_actions).grid(row=1, column=0, sticky="w")
        ttk.Entry(frame2, textvariable=self.act_path, state="readonly", width=30).grid(row=1, column=1, padx=5)
        ttk.Checkbutton(frame2, text="Manual", variable=self.act_manual,
                        command=self._toggle_act_input).grid(row=1, column=2)
        self.act_preview = tk.Text(self.tab_sync, height=5, state=tk.DISABLED)
        self.act_preview.pack(fill=tk.X, padx=5, pady=2)

        mode_frame = ttk.LabelFrame(self.tab_sync, text="Modo de Sincronización")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Mutex", variable=self.sync_mode, value="mutex").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(mode_frame, text="Semáforo", variable=self.sync_mode, value="semaphore").grid(row=0, column=1, padx=5)

        btn2 = ttk.Frame(self.tab_sync, padding=5)
        btn2.pack(fill=tk.X)
        ttk.Button(btn2, text="Iniciar Simulación", command=self._on_execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn2, text="Limpiar Canvas", command=self._on_clear).pack(side=tk.LEFT)

    def _build_canvas(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(container, bg="white")
        hbar = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = ttk.Scrollbar(container, orient=tk.VERTICAL,   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

    def _build_cycle_label(self):
        self.cycle_label = ttk.Label(self, text="Ciclo: 0", font=(None, 12, 'bold'))
        self.cycle_label.pack(side=tk.BOTTOM, pady=5)

    def _toggle_proc_input(self):
        self.proc_preview.config(state=tk.NORMAL if self.proc_manual.get() else tk.DISABLED)

    def _toggle_res_input(self):
        self.res_preview.config(state=tk.NORMAL if self.res_manual.get() else tk.DISABLED)

    def _toggle_act_input(self):
        self.act_preview.config(state=tk.NORMAL if self.act_manual.get() else tk.DISABLED)

    def _load_processes(self):
        """Carga procesos desde archivo y asigna colores + guarda en self.procs."""
        path = filedialog.askopenfilename(filetypes=[("TXT","*.txt")])
        if not path:
            return
        procs = utils.leer_procesos(path)
        self.colors.clear()
        for i, p in enumerate(procs):
            self.colors[p.pid] = PALETTE[i % len(PALETTE)]
        self.procs = procs
        self.proc_path.set(path)
        self.proc_preview.config(state=tk.NORMAL)
        self.proc_preview.delete("1.0", tk.END)
        self.proc_preview.insert(tk.END, "".join(open(path).readlines()[:10]))
        if not self.proc_manual.get():
            self.proc_preview.config(state=tk.DISABLED)

    def _load_resources(self):
        path = filedialog.askopenfilename(filetypes=[("TXT","*.txt")])
        if not path: return
        self.res_path.set(path)
        self.res_preview.config(state=tk.NORMAL)
        self.res_preview.delete("1.0", tk.END)
        self.res_preview.insert(tk.END, "".join(open(path).readlines()[:5]))
        if not self.res_manual.get():
            self.res_preview.config(state=tk.DISABLED)

    def _load_actions(self):
        path = filedialog.askopenfilename(filetypes=[("TXT","*.txt")])
        if not path: return
        self.act_path.set(path)
        self.act_preview.config(state=tk.NORMAL)
        self.act_preview.delete("1.0", tk.END)
        self.act_preview.insert(tk.END, "".join(open(path).readlines()[:10]))
        if not self.act_manual.get():
            self.act_preview.config(state=tk.DISABLED)

    def _on_execute(self):
        self.canvas.delete("all")
        self.cal_index  = 0
        self.sync_index = 0
        self.max_cycle  = 0
        if self.nb.index(self.nb.select()) == 0:
            self._prepare_calendar()
        else:
            self._prepare_sync()

    def _on_clear(self):
        self.canvas.delete("all")
        self.cycle_label.config(text="Ciclo: 0")

    def _draw_axis(self):
        self.canvas.delete('axis')
        y = 30
        step = max(1, self.max_cycle // 20)
        for c in range(0, self.max_cycle + 1, step):
            x = self.margin_x + c * self.scale_x
            self.canvas.create_line(x, y-5, x, y+5, tags='axis')
            self.canvas.create_text(x, y-15, text=str(c), tags='axis')
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def _draw_legend(self, pids):
        self.canvas.delete('legend')
        x0, y0 = self.margin_x, 10
        for pid in pids:
            color = self.colors.get(pid, "gray")
            # cuadrito de color
            self.canvas.create_rectangle(
                x0, y0, x0+15, y0+15,
                fill=color, outline="black",
                tags="legend"
            )
            # texto al lado
            self.canvas.create_text(
                x0+20, y0+7,
                text=pid, anchor="w",
                font=("Arial", 8),
                tags="legend"
            )
            x0 += 60



    def _prepare_calendar(self):
        try:
            if self.proc_manual.get():
                lines = self.proc_preview.get("1.0", tk.END).strip().splitlines()
                procs = []
                for l in lines:
                    pid, bt, at, prio = map(str.strip, l.split(","))
                    procs.append(scheduler.Process(pid, int(bt), int(at), int(prio)))
            else:
                procs = utils.leer_procesos(self.proc_path.get())

        except Exception as e:
            return messagebox.showerror("Error", f"No se pudo leer procesos:\n{e}")

        algs = [name for name,var in self.alg_vars.items() if var.get()]
        if not algs:
            return messagebox.showwarning("Atención", "Selecciona al menos un algoritmo.")

        self.cal_events.clear()
        for idx, name in enumerate(algs):
            # Hacemos copia limpia de los procesos
            cp = [p.copy() for p in procs]

            if name == "SRT":
                # Preemptivo (alias de srtf)
                done, gantt = scheduler.srt(cp)

            elif name == "RR":
                # Ahora rr devuelve (done, gantt_segments)
                done, gantt = scheduler.rr(cp, self.quantum.get())

            else:
                # FIFO, SJF, Priority (no preemptivos)
                done = getattr(scheduler, name.lower())(cp)
                gantt = [(p.pid, p.start, p.end) for p in done]

            # ——— Calcular métricas adicionales ———
            avg_wt     = utils.calcular_avg_waiting(done)
            avg_tat    = utils.calcular_avg_turnaround(done)
            throughput = utils.calcular_throughput(done)
            label = (
                f"{name}  •  Avg WT: {avg_wt}  •  "
                f"Avg TAT: {avg_tat}  •  "
                f"Throughput: {throughput} proc/ciclo"
            )

            # Etiqueta en Gantt
            self.cal_events.append(('label', label, idx))

            # Cada segmento para animar
            for pid, s, e in gantt:
                self.cal_events.append((idx, pid, s, e))
                self.max_cycle = max(self.max_cycle, e)

        self._draw_axis()
        self._animate_calendar()

    def _animate_calendar(self):
        if self.cal_index >= len(self.cal_events):
            return
        evt = self.cal_events[self.cal_index]
        if evt[0] == 'label':
            _, text, row = evt
            y = 40 + row * self.row_height
            self.canvas.create_text(10, y+15, text=text, anchor='w', font=('Arial',10,'bold'), tags='label')
        else:
            row,pid,s,e = evt
            y0 = 40 + row * self.row_height
            x0 = self.margin_x + s * self.scale_x
            x1 = self.margin_x + e * self.scale_x
            col = self.colors.get(pid, random.choice(PALETTE))
            self.canvas.create_rectangle(x0,y0,x1,y0+30, fill=col, outline='black')
            self.canvas.create_text((x0+x1)//2, y0+15, text=pid, fill='white')
            self.cycle_label.config(text=f"Ciclo: {e}")
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.cal_index += 1
        self.after(300, self._animate_calendar)

    def _prepare_sync(self):
        if not hasattr(self, 'procs') or not self.procs:
            return messagebox.showwarning(
                "Atención",
                "Antes de simular sincronización debes cargar el archivo de procesos en la pestaña Calendarización."
            )

        try:
            if self.res_manual.get():
                lines = self.res_preview.get("1.0", tk.END).strip().splitlines()
                resources = {l.split(",")[0].strip(): int(l.split(",")[1]) for l in lines}
            else:
                resources = utils.leer_recursos(self.res_path.get())

            if self.act_manual.get():
                lines = self.act_preview.get("1.0", tk.END).strip().splitlines()
                actions = []
                for l in lines:
                    pid, act, res, cyc = map(str.strip, l.split(","))
                    actions.append(utils.Action(pid, act, res, int(cyc)))
            else:
                actions = utils.leer_acciones(self.act_path.get())

        except Exception as e:
            return messagebox.showerror("Error", f"No se pudo leer recursos/acciones:\n{e}")

        self.sync_events, self.process_states = scheduler.simulate_sync(
             resources,
             actions,
             self.procs,
             mode=self.sync_mode.get()
        )


        pids = []
        for cycle, pid, _, _, _ in self.sync_events:
            if pid not in pids:
                pids.append(pid)

        self._draw_legend(pids)

        self.max_cycle = max((c for c, *_ in self.sync_events), default=0)

        self.pid_rows = { pid: idx for idx, pid in enumerate(pids) }

        self._draw_axis()
        self._animate_sync()

    def _animate_sync(self):
        # Antes de animar evento a evento, pinta TODO el grid:
        for pid, states in self.process_states.items():
            row = self.pid_rows[pid]
            y0  = 40 + row*self.row_height
            for c, st in enumerate(states):
                x0  = self.margin_x + c*self.scale_x
                col = "lightgrey" if st=="IDLE" else SYNC_COLORS[st]
                self.canvas.create_rectangle(
                    x0, y0, x0+self.scale_x, y0+30,
                    fill=col, outline="black"
                )
                self.canvas.create_text(
                    (x0 + x0+self.scale_x)//2, y0+15,
                    text=pid, fill="white"
                )

        # (Opcional) actualizar etiqueta de ciclo al final:
        self.cycle_label.config(text=f"Simulación lista: ciclos 0–{len(states)-1}")


if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()
