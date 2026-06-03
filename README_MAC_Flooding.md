# 🛡️ Ataque MAC Flooding — Documentación Técnica

**Autor:** Junior Javier Santos Perez  
**Matrícula:** 2024-1599  
**Fecha:** 03 de junio de 2026  
**Herramienta:** Script MAC Flooding (Python + Scapy)  
**Plataforma de laboratorio:** GNS3 + Kali Linux 2025.3

---

## 📋 Tabla de Contenidos

1. [Objetivo del Laboratorio](#objetivo-del-laboratorio)
2. [Objetivo del Script](#objetivo-del-script)
3. [Parámetros Utilizados](#parámetros-utilizados)
4. [Requisitos para el Uso de la Herramienta](#requisitos-para-el-uso-de-la-herramienta)
5. [Descripción del Funcionamiento del Script](#descripción-del-funcionamiento-del-script)
6. [Documentación de la Red](#documentación-de-la-red)
7. [Topología](#topología)
8. [Capturas de Pantalla](#capturas-de-pantalla)
9. [Medidas de Mitigación / Contramedidas](#medidas-de-mitigación--contramedidas)

---

## 🎯 Objetivo del Laboratorio

Demostrar de forma práctica y controlada la ejecución de un ataque de **MAC Flooding** sobre un switch Cisco simulado en GNS3, con el fin de:

- Comprender cómo el desbordamiento de la tabla CAM de un switch puede degradar su comportamiento.
- Observar cómo el switch pasa de operar en modo switching a modo hub (flooding de todos los puertos).
- Verificar la saturación de la tabla MAC con entradas falsas dinámicas.
- Proponer e implementar contramedidas efectivas para mitigar el ataque.

---

## 🐍 Objetivo del Script

El script de MAC Flooding tiene como objetivo saturar la **tabla CAM (Content Addressable Memory)** del switch Cisco enviando masivamente tramas Ethernet con direcciones MAC de origen falsas y aleatorias, con el fin de:

- Desbordar la capacidad de la tabla MAC del switch (generalmente limitada a miles de entradas).
- Forzar al switch a operar en modo **fail-open**, enviando todas las tramas a todos los puertos (comportamiento de hub).
- Permitir que el atacante capture tráfico destinado a otros hosts al recibir todas las tramas en su interfaz.
- Demostrar la ausencia de mecanismos de autenticación o límite en el aprendizaje de MACs por defecto.

---

## ⚙️ Parámetros Utilizados

| Parámetro         | Valor              | Descripción                                                     |
|-------------------|--------------------|-----------------------------------------------------------------|
| Interfaz          | `eth0`             | Interfaz de red del atacante usada para el envío                |
| MAC origen        | Aleatoria          | Cada trama usa una MAC de origen distinta y aleatoria           |
| MAC destino       | `ff:ff:ff:ff:ff:ff`| Broadcast Ethernet para maximizar el impacto en la red          |
| Ethertype         | `0x9000` (Loopback)| Tipo de trama utilizado en los frames generados                 |
| Paquetes enviados | 145,000            | Total de tramas MAC falsas inyectadas durante el ataque         |
| Tiempo total      | 34.50 s            | Duración total del ataque                                       |
| Velocidad media   | 4,203 pkt/s        | Paquetes por segundo promedio durante el ataque                 |
| Velocidad pico    | ~4,188 pkt/s       | Velocidad observada en las métricas en tiempo real              |

---

## 🖥️ Requisitos para el Uso de la Herramienta

### Sistema Operativo
- Kali Linux 2025.3 (o cualquier distribución Linux con soporte a raw sockets)

### Privilegios
- Ejecución como `root` o con `sudo` (necesario para enviar tramas a nivel de capa 2)

### Dependencias Python
```bash
# Requiere Scapy para generación y envío de tramas Ethernet
pip install scapy

# Módulos de la librería estándar utilizados:
import random
import threading
import time
```

### Hardware / Red
- Interfaz de red activa conectada al mismo segmento L2 que el switch objetivo
- Conectividad directa al switch víctima (mismo dominio de broadcast)

### Entorno de Laboratorio
- GNS3 con imagen Cisco IOS IOSv Layer 2 Switch
- Kali Linux como nodo atacante conectado al switch
- Solar-PuTTY para monitoreo del switch en tiempo real

---

## 🔬 Descripción del Funcionamiento del Script

El script opera en las siguientes fases:

### Fase 1 — Generación de Tramas Falsas
Para cada trama enviada, el script genera una **dirección MAC de origen completamente aleatoria** de 6 bytes, garantizando que cada trama sea única y sea aprendida como una nueva entrada en la tabla CAM del switch:
```python
src_mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
```

### Fase 2 — Construcción de la Trama Ethernet
Cada trama se construye con:
- **MAC destino**: `ff:ff:ff:ff:ff:ff` (broadcast)
- **MAC origen**: aleatoria (nueva en cada trama)
- **Ethertype**: `0x9000` (Ethernet Loopback)
- **Payload**: mínimo para maximizar la tasa de envío

### Fase 3 — Envío Masivo Multihilo
El script utiliza múltiples hilos para maximizar la tasa de envío a través de un socket `AF_PACKET` de tipo crudo (`SOCK_RAW`), inyectando las tramas directamente en la interfaz `eth0` sin pasar por el stack de red del sistema operativo.

### Fase 4 — Saturación de la Tabla CAM
A medida que el switch recibe las tramas, intenta aprender cada MAC origen y asociarla a un puerto. Al superar la capacidad máxima de la tabla CAM, el switch entra en modo **fail-open** y comienza a enviar todas las tramas por todos los puertos (comportamiento de hub), exponiendo el tráfico de todos los hosts.

### Fase 5 — Monitoreo en Tiempo Real
El script muestra métricas actualizadas continuamente:
```
[*] Enviados: 143,000 | Velocidad: 4,188 pkt/s | Tiempo: 34.1s
```

### Fase 6 — Finalización y Resumen
Al presionar `Ctrl+C` el ataque se detiene y muestra el resumen final:
```
[v] Ataque finalizado.
    Paquetes enviados : 145,000
    Tiempo total      : 34.50s
    Velocidad media   : 4,203 pkt/s
```

---

## 🌐 Documentación de la Red

### Tabla de Direccionamiento IP

| Nodo                              | Rol       | Interfaz    | Dirección IP  | Notas                        |
|-----------------------------------|-----------|-------------|---------------|------------------------------|
| kali-linux-2025.3-vmware-amd64-1  | Atacante  | eth0 / e1   | 10.0.99.100   | Genera tramas MAC falsas     |
| Clonekali-1                       | Víctima   | e0 / e3     | 10.0.99.50    | Host cuyo tráfico se expone  |
| SERVIDOR-KALI-1                   | Servidor  | e0          | 10.0.99.150   | Nodo de la red objetivo      |
| Switch-1                          | Switch L2 | e0/e1/e3    | N/A (L2)      | Cisco IOS IOSv Switch        |
| R1                                | Router    | f0/0        | N/A           | Gateway de la red            |

### Protocolo / Capa Explotada

| Capa | Protocolo  | Descripción                                                                    |
|------|------------|--------------------------------------------------------------------------------|
| L2   | Ethernet   | Sin límite de aprendizaje MAC por defecto — tabla CAM desbordable              |
| L2   | Tabla CAM  | Capacidad finita — al desbordarse el switch opera como hub (fail-open)         |

### Evidencia de la Saturación

| Momento       | Entradas en tabla MAC | Comportamiento del switch              |
|---------------|-----------------------|----------------------------------------|
| Antes          | 3–4 MACs legítimas    | Switching normal — tráfico unicast     |
| Durante/Después | Miles de MACs falsas  | Fail-open — flooding a todos los puertos |

---

## 🗺️ Topología

La topología fue diseñada e implementada en **GNS3** con los siguientes componentes:

```
    [SERVIDOR-KALI-1]
    10.0.99.150 / e0
          |
          | (e0 - Switch-1)
     [Switch-1]────────────────[R1]
      e3 |  e0                     f0/0
         |
     (e3 - Clonekali-1)
    [Clonekali-1 / Víctima]
    10.0.99.50

     (e1 - Switch-1)
          |
    [kali-linux-2025.3 / Atacante]
    10.0.99.100
```

> 📁 La imagen de la topología se encuentra en la carpeta `/images/` del repositorio.

---

## 📸 Capturas de Pantalla

Las capturas de pantalla se encuentran almacenadas en la carpeta **`/images/`** del repositorio.

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `imagen_01_topologia.png` | Topología del laboratorio en GNS3 con nombre y matrícula del estudiante |
| 2 | `imagen_02_tabla_mac_antes.png` | Tabla MAC del switch antes del ataque — 3 a 4 entradas legítimas dinámicas |
| 3 | `imagen_03_ataque_en_curso.png` | Script en ejecución — 32,000 tramas enviadas a 3,969 pkt/s con warnings de Scapy |
| 4 | `imagen_04_tcpdump_tramas_falsas.png` | Captura tcpdump mostrando tramas broadcast con MACs de origen falsas y aleatorias |
| 5 | `imagen_05_ataque_finalizado.png` | Resumen del ataque — 145,000 paquetes en 34.50s a 4,203 pkt/s promedio |
| 6 | `imagen_06_tabla_mac_saturada.png` | Tabla CAM del switch saturada con miles de entradas MAC falsas dinámicas |
| 7 | `imagen_07_contramedida_port_security.png` | Contramedida aplicada: Port Security con `maximum 2`, `violation shutdown` y `mac-address sticky` |

---

## 🛡️ Medidas de Mitigación / Contramedidas

### 1. Port Security en el Switch Cisco (Contramedida Principal)
```cisco
Switch# configure terminal
Switch(config)# interface g0/0
Switch(config-if)# switchport mode access
Switch(config-if)# switchport port-security
Switch(config-if)# switchport port-security maximum 2
Switch(config-if)# switchport port-security violation shutdown
Switch(config-if)# switchport port-security mac-address sticky
Switch(config-if)# ^Z
Switch# write
```
> Port Security limita el número de MACs aprendidas por puerto. Al superar el límite, el puerto entra en estado `err-disabled` (shutdown). Con `sticky`, las MACs legítimas se memorizan automáticamente en la configuración. **Es la contramedida más efectiva contra MAC Flooding.**

### 2. Limitar el Tamaño de la Tabla MAC por Puerto
```cisco
Switch(config-if)# switchport port-security maximum 1
```
> Reducir a 1 el máximo de MACs por puerto de acceso impide completamente el aprendizaje de MACs falsas adicionales.

### 3. Recuperación Automática de Puertos en err-disabled
```cisco
Switch(config)# errdisable recovery cause psecure-violation
Switch(config)# errdisable recovery interval 300
```
> Permite que el puerto se recupere automáticamente tras un período de tiempo después de una violación de Port Security.

### 4. Monitoreo de la Tabla CAM
```cisco
! Verificar número de entradas en la tabla MAC
Switch# show mac address-table count
! Ver entradas por interfaz
Switch# show mac address-table interface g0/0
! Verificar estado de Port Security
Switch# show port-security interface g0/0
Switch# show port-security address
```

### 5. VLANs para Segmentación
> Segmentar la red en VLANs reduce el dominio de broadcast y limita el impacto del ataque MAC Flooding a un único segmento, protegiendo el resto de la red.

### 6. 802.1X — Autenticación de Puerto
```cisco
Switch(config)# aaa new-model
Switch(config)# aaa authentication dot1x default group radius
Switch(config)# dot1x system-auth-control
Switch(config)# interface g0/0
Switch(config-if)# dot1x port-control auto
```
> La autenticación 802.1X requiere que cada dispositivo se autentique antes de poder enviar tráfico por el puerto, impidiendo que un atacante inyecte tramas sin credenciales válidas.

---

## 📁 Estructura del Repositorio

```
mac-flooding-attack/
├── README.md                              ← Este archivo
├── mac_flooding.py                        ← Script del ataque
├── images/
│   ├── imagen_01_topologia.png
│   ├── imagen_02_tabla_mac_antes.png
│   ├── imagen_03_ataque_en_curso.png
│   ├── imagen_04_tcpdump_tramas_falsas.png
│   ├── imagen_05_ataque_finalizado.png
│   ├── imagen_06_tabla_mac_saturada.png
│   └── imagen_07_contramedida_port_security.png
└── video/
    └── mac_flooding_demo.mp4              ← Video de demostración (máx. 5 min)
```

---

## ⚠️ Aviso Legal / Disclaimer

> Este laboratorio fue realizado en un entorno **completamente controlado y simulado** con fines académicos y de investigación en seguridad informática. El uso de estas técnicas fuera de entornos autorizados es ilegal y contrario a la ética profesional. El autor no se hace responsable del uso indebido de este material.

---

*Documentación generada para entrega académica — Seguridad en Redes | 2026*
