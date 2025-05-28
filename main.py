from utils import leer_procesos, imprimir_gantt, calcular_avg_waiting, leer_recursos, leer_acciones
from scheduler import fifo, sjf, srtf, rr, priority, simulate_sync

if __name__ == "__main__":
    archivo = "data/procesos.txt"  
    quantum = 2               

    procesos = leer_procesos(archivo)

    print("\n[ FIFO ]")
    gantt = fifo([p.copy() for p in procesos])
    imprimir_gantt(gantt)
    print("Avg WT:", calcular_avg_waiting(gantt))

    print("\n[ SJF ]")
    gantt = sjf([p.copy() for p in procesos])
    imprimir_gantt(gantt)
    print("Avg WT:", calcular_avg_waiting(gantt))

    print("\n[ SRTF ]")
    procesos_srtf, gantt_srtf = srtf([p.copy() for p in procesos])
    imprimir_gantt(gantt_srtf)
    print("Avg WT:", calcular_avg_waiting(procesos_srtf))


    print("\n[ Round Robin ]")
    gantt = rr([p.copy() for p in procesos], quantum)
    imprimir_gantt(gantt)
    print("Avg WT:", calcular_avg_waiting(gantt))

    print("\n[ Priority ]")
    gantt = priority([p.copy() for p in procesos])
    imprimir_gantt(gantt)
    print("Avg WT:", calcular_avg_waiting(gantt))


    # --- Simulación de Sincronización ---
    print("\n[ SIMULACIÓN DE SINCRONIZACIÓN (MUTEX) ]")
    recs = leer_recursos("data/recursos.txt")
    acts = leer_acciones("data/acciones.txt")
    events = simulate_sync(recs, acts, mode="mutex")
    for cycle, pid, action, res, state in events:
        print(f"Ciclo {cycle}: {pid} {action} {res} -> {state}")

    print("\n[ SIMULACIÓN DE SINCRONIZACIÓN (SEMAPHORE) ]")
    events = simulate_sync(recs, acts, mode="semaphore")
    for cycle, pid, action, res, state in events:
        print(f"Ciclo {cycle}: {pid} {action} {res} -> {state}")