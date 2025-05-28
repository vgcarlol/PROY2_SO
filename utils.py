from scheduler import Process

def leer_procesos(path):
    lista = []
    with open(path) as f:
        for linea in f:
            if not linea.strip(): continue
            pid, bt, at, prio = map(str.strip, linea.strip().split(","))
            lista.append(Process(pid, int(bt), int(at), int(prio)))
    return lista

def imprimir_gantt(lista):
    print("[Gantt]")
    for p in lista:
        if isinstance(p, tuple):
            pid, start, end = p
        else:
            pid, start, end = p.pid, p.start, p.end
        print(f"| {pid} ({start}-{end}) ", end='')
    print("|")

def calcular_avg_waiting(lista):
    total_wait = 0
    for p in lista:
        if hasattr(p, "waiting_time"):
            wt = p.waiting_time
        else:
            wt = p.start - p.at
        total_wait += wt
    return round(total_wait / len(lista), 2)

def leer_recursos(path):
    recursos = {}
    with open(path) as f:
        for linea in f:
            if not linea.strip(): continue
            name, cnt = map(str.strip, linea.strip().split(","))
            recursos[name] = int(cnt)
    return recursos

class Action:
    def __init__(self, pid, action, resource, cycle):
        self.pid = pid
        self.action = action   # e.g. "READ" o "WRITE"
        self.resource = resource
        self.cycle = cycle

def leer_acciones(path):
    acciones = []
    with open(path) as f:
        for linea in f:
            if not linea.strip(): continue
            pid, act, res, cyc = map(str.strip, linea.strip().split(","))
            acciones.append(Action(pid, act, res, int(cyc)))
    return acciones