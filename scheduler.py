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

# SRT (preemptivo)
def srt(procs):
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
    # Ordenar procesos por llegada
    procs.sort(key=lambda p: p.at)
    t = 0
    queue = []
    done = []
    gantt = []
    i = 0   # índice para insertar nuevos procesos al llegar

    while queue or i < len(procs):
        # Si no hay nadie en cola, saltamos al próximo arribo
        if not queue:
            t = max(t, procs[i].at)
            queue.append(procs[i])
            i += 1

        # Sacamos el siguiente de la cola
        p = queue.pop(0)
        if p.start is None:
            p.start = t

        # La porción de CPU que va a correr ahora
        porcion = min(quantum, p.rt)
        gantt.append((p.pid, t, t + porcion))

        # Avanzamos el tiempo y actualizamos restante
        t      += porcion
        p.rt   -= porcion

        # Insertamos en la cola los procesos que hayan llegado durante esta porción
        while i < len(procs) and procs[i].at <= t:
            queue.append(procs[i])
            i += 1

        # Si terminó, lo movemos a done; si no, vuelve al fondo de la cola
        if p.rt == 0:
            p.end = t
            done.append(p)
        else:
            queue.append(p)

    # Calculamos waiting_time y turnaround_time
    for p in done:
        p.waiting_time    = p.end - p.at - p.bt
        p.turnaround_time = p.end - p.at

    return done, gantt


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

def simulate_sync(resources, actions, procs, mode="mutex"):
    arrival   = {p.pid: p.at for p in procs}
    by_cycle  = {}
    for act in actions:
        by_cycle.setdefault(act.cycle, []).append(act)

    max_cycle = max(by_cycle.keys(), default=-1)
    caps      = resources.copy()
    events    = []
    # Inicializar también el historial completo por PID
    process_states = {
        p.pid: ["IDLE"] * (max_cycle+1)
        for p in procs
    }

    for cycle in range(max_cycle+1):
        for act in by_cycle.get(cycle, []):
            pid, res, op = act.pid, act.resource, act.action.upper()

            # 1) ¿Ha llegado el proceso?
            if cycle < arrival[pid]:
                state = "WAITING"
            else:
                if mode == "mutex":
                    # toma/bloquea un lock binario
                    if caps.get(res,0) > 0:
                        state       = "ACCESED"
                        caps[res]   = 0
                    else:
                        state = "WAITING"

                else:  # modo semáforo
                    if op == "READ":
                        # P
                        if caps.get(res,0) > 0:
                            state     = "ACCESED"
                            caps[res] = caps[res] - 1
                        else:
                            state = "WAITING"
                    elif op == "WRITE":
                        # V
                        state     = "ACCESED"
                        caps[res] = caps.get(res,0) + 1
                    else:
                        # Si hay otros ops, los tratamos como acceso neutro
                        state = "ACCESED"

            events.append((cycle, pid, op, res, state))
            process_states[pid][cycle] = state

    return events, process_states
