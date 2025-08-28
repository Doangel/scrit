#!/usr/bin/env python3
# bloquear_whatsapp.py

import argparse
import os
import platform
import time
import subprocess

DOMINIOS = [
    "whatsapp.com",
    "www.whatsapp.com",
    "web.whatsapp.com",
    "static.whatsapp.net",
    "whatsapp.net",
    "mmg.whatsapp.net",
    "whatsapp-cdn.net",
    "whatsapp.net.edgesuite.net",
]

MARCADOR_INICIO = "# >>> BLOQUEO_WHATSAPP_INICIO >>>"
MARCADOR_FIN = "# <<< BLOQUEO_WHATSAPP_FIN <<<"

def ruta_hosts():
    so = platform.system().lower()
    if "windows" in so:
        return r"C:\Windows\System32\drivers\etc\hosts"
    # macOS y Linux
    return "/etc/hosts"

def leer_hosts(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def escribir_hosts(path, contenido):
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(contenido)

def ya_bloqueado(texto):
    return MARCADOR_INICIO in texto and MARCADOR_FIN in texto

def construir_bloque():
    lineas = [MARCADOR_INICIO]
    for d in DOMINIOS:
        # Redirige a 0.0.0.0 para bloquear
        lineas.append(f"0.0.0.0 {d}")
        lineas.append(f"0.0.0.0 www.{d}")  # por si acaso
    lineas.append(MARCADOR_FIN)
    return "\n".join(lineas) + "\n"

def activar_bloqueo():
    hpath = ruta_hosts()
    contenido = leer_hosts(hpath)
    if ya_bloqueado(contenido):
        print("Ya estaba bloqueado.")
        return
    nuevo = contenido
    if not contenido.endswith("\n"):
        nuevo += "\n"
    nuevo += construir_bloque()
    escribir_hosts(hpath, nuevo)
    print("Bloqueo de WhatsApp ACTIVADO en hosts.")

def desactivar_bloqueo():
    hpath = ruta_hosts()
    contenido = leer_hosts(hpath)
    if not ya_bloqueado(contenido):
        print("No había bloqueo previo.")
        return
    # Elimina la sección marcada
    partes = []
    dentro = False
    for linea in contenido.splitlines():
        if linea.strip() == MARCADOR_INICIO:
            dentro = True
            continue
        if linea.strip() == MARCADOR_FIN:
            dentro = False
            continue
        if not dentro:
            partes.append(linea)
    escribir_hosts(hpath, "\n".join(partes) + "\n")
    print("Bloqueo de WhatsApp DESACTIVADO en hosts.")

def matar_procesos_whatsapp():
    """
    Intenta cerrar la app de WhatsApp si está abierta (Windows/macOS/Linux).
    Primero usa psutil si está disponible; si no, recurre a comandos del sistema.
    """
    nombres = ["WhatsApp.exe", "WhatsApp", "WhatsApp.app"]
    try:
        import psutil  # opcional
        matados = 0
        for p in psutil.process_iter(attrs=["name"]):
            try:
                if p.info["name"] in nombres:
                    p.terminate()
                    matados += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if matados:
            print(f"Procesos de WhatsApp terminados: {matados}")
    except ImportError:
        # Sin psutil: usar taskkill/pkill
        so = platform.system().lower()
        try:
            if "windows" in so:
                subprocess.run(["taskkill", "/F", "/IM", "WhatsApp.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "WhatsApp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Intento de cierre de WhatsApp realizado.")
        except Exception as e:
            print(f"No se pudo cerrar WhatsApp: {e}")

def vigilar(intervalo=5):
    """
    Mantiene el bloqueo y cierra WhatsApp si se abre.
    Pulsa Ctrl+C para terminar.
    """
    print("Vigilando apertura de WhatsApp (Ctrl+C para salir)...")
    while True:
        matar_procesos_whatsapp()
        time.sleep(intervalo)

def requiere_admin():
    so = platform.system().lower()
    try:
        if "windows" in so:
            # Windows: comprobar privilegios con whoami /groups no es fiable aquí;
            # probamos abrir hosts en modo append.
            with open(ruta_hosts(), "a"):
                return True
        else:
            return os.geteuid() == 0
    except PermissionError:
        return False
    except Exception:
        # Si no sabemos, seguimos y que falle al escribir
        return True

def main():
    parser = argparse.ArgumentParser(description="Bloquear/Desbloquear WhatsApp (hosts) y vigilar procesos.")
    parser.add_argument("--activar", action="store_true", help="Añade dominios de WhatsApp al archivo hosts.")
    parser.add_argument("--desactivar", action="store_true", help="Elimina el bloqueo del archivo hosts.")
    parser.add_argument("--vigilar", action="store_true", help="Cierra la app de WhatsApp si se abre.")
    parser.add_argument("--intervalo", type=int, default=5, help="Segundos entre revisiones en modo vigilar (default: 5).")
    args = parser.parse_args()

    if (args.activar or args.desactivar) and not requiere_admin():
        print("⚠️ Ejecuta este script con privilegios de administrador (sudo) para modificar el archivo hosts.")
        return

    if args.activar:
        activar_bloqueo()
    if args.desactivar:
        desactivar_bloqueo()
    if args.vigilar:
        try:
            vigilar(args.intervalo)
        except KeyboardInterrupt:
            print("\nVigilancia detenida.")

    if not (args.activar or args.desactivar or args.vigilar):
        parser.print_help()

if __name__ == "__main__":
    main()