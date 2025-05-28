class Process:
    def __init__(self, pid, bt, at, prio):
        self.pid = pid
        self.bt = bt
        self.at = at
        self.prio = prio
        self.rt = bt
        self.start = None
        self.end = None

    def copy(self):
        return Process(self.pid, self.bt, self.at, self.prio)

# FIFO
def fifo(procs):
    procs.sort(key=lambda p: p.at)
    t = 0
    gantt = []
    for p in procs:
        if t < p.at:
            t = p.at
        p.start = t
        t += p.bt
        p.end = t
        gantt.append(p)
    return gantt

# SJF (no preemptivo)
def sjf(procs):
    t = 0
    ready, done = [], []
    while procs or ready:
        ready += [p for p in procs if p.at <= t]
        procs = [p for p in procs if p.at > t]
        if ready:
            p = min(ready, key=lambda x: x.bt)
            ready.remove(p)
            p.start = t
            t += p.bt
            p.end = t
            done.append(p)
        else:
            t += 1
    return done

# SRTF (preemptivo)
def srtf(procs):
    t = 0
    ready = []
    done = []
    exec_order = []

    # Usamos dict para guardar primera vez que un proceso empieza
    start_times = {}

    while procs or ready:
        # Añadir los procesos que han llegado a la cola
        ready += [p for p in procs if p.at <= t]
        procs = [p for p in procs if p.at > t]

        if ready:
            # Elegir proceso con menor tiempo restante
            p = min(ready, key=lambda x: x.rt)

            if p.pid not in start_times:
                p.start = t
                start_times[p.pid] = True

            # Ejecutar 1 ciclo
            p.rt -= 1
            exec_order.append((p.pid, t))
            t += 1

            if p.rt == 0:
                p.end = t
                done.append(p)
                ready.remove(p)
        else:
            t += 1

    # Reasignar ejecución total en bloques contiguos para imprimir Gantt
    gantt = []
    if exec_order:
        last_pid, start = exec_order[0]
        for i in range(1, len(exec_order)):
            pid, current_time = exec_order[i]
            if pid != last_pid:
                gantt.append((last_pid, start, current_time))
                last_pid = pid
                start = current_time
        gantt.append((last_pid, start, exec_order[-1][1] + 1))  # Último bloque

    # Actualizar tiempos reales de los procesos
    for p in done:
        p.waiting_time = p.end - p.at - p.bt
        p.turnaround_time = p.end - p.at

    return done, gantt


# RR
def rr(procs, quantum):
    t = 0
    ready, queue, done = [], [], []
    while procs or queue or ready:
        ready += [p for p in procs if p.at <= t]
        procs = [p for p in procs if p.at > t]
        queue += ready
        ready = []
        if queue:
            p = queue.pop(0)
            if p.start is None:
                p.start = t
            exec_time = min(quantum, p.rt)
            p.rt -= exec_time
            t += exec_time
            if p.rt == 0:
                p.end = t
                done.append(p)
            else:
                queue += [p]
        else:
            t += 1
    return done

# PRIORITY (no preemptivo)
def priority(procs):
    t = 0
    ready, done = [], []
    while procs or ready:
        ready += [p for p in procs if p.at <= t]
        procs = [p for p in procs if p.at > t]
        if ready:
            p = min(ready, key=lambda x: x.prio)
            ready.remove(p)
            p.start = t
            t += p.bt
            p.end = t
            done.append(p)
        else:
            t += 1
    return done

def simulate_sync(resources, actions, mode="mutex"):
    # Agrupar acciones por ciclo
    by_cycle = {}
    for act in actions:
        by_cycle.setdefault(act.cycle, []).append(act)

    events = []
    max_cycle = max(by_cycle.keys(), default=-1)

    for cycle in range(max_cycle + 1):
        # para cada recurso, resetear capacidad al inicio del ciclo
        caps = resources.copy()
        for act in by_cycle.get(cycle, []):
            cap = caps.get(act.resource, 0)
            if mode == "mutex":
                if cap > 0:
                    state = "ACCESED"
                    caps[act.resource] = 0
                else:
                    state = "WAITING"
            else:  # semáforo
                if cap > 0:
                    state = "ACCESED"
                    caps[act.resource] = cap - 1
                else:
                    state = "WAITING"
            events.append((cycle, act.pid, act.action, act.resource, state))

    return events