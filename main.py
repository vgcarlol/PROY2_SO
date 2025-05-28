from utils import leer_procesos, imprimir_gantt, calcular_avg_waiting
from scheduler import fifo, sjf, srtf, rr, priority

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