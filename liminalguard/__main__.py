import argparse
import errno
import os
import shutil
import socket
import subprocess
import sys
import threading

from . import __version__
from .checks import check_server
from .server import Server, local_address
from .upstream import AdGuardDNS


def detect_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.connect(("1.1.1.1", 443))
        return connection.getsockname()[0]


def main():
    parser = argparse.ArgumentParser(description="DNS Wi-Fi expérimental pour console — RZU Informatique")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--ip", help="IPv4 Wi-Fi du téléphone")
    parser.add_argument("--check", action="store_true", help="tester un relais déjà démarré")
    args = parser.parse_args()
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    accent, reset = ("\033[38;5;150m", "\033[0m") if color else ("", "")
    print(f"{accent}  +---+  LiminalGuard Android {__version__}\n  |   |  by RZU Informatique\n  |  .|  EXPÉRIMENTAL\n  +---+{reset}", flush=True)
    server = None
    thread = None
    wake = False
    try:
        host = args.ip or detect_ip()
        if not local_address(host):
            raise ValueError("Aucune IPv4 privée détectée. Connectez le téléphone au Wi-Fi et utilisez --ip si nécessaire.")
        if args.check:
            check_server(host, 53)
            print("DNS UDP/TCP et domaine publicitaire : vérifications locales réussies.")
            return 0
        server = Server(host, 53, AdGuardDNS())
        server.bind()
        thread = threading.Thread(target=server.serve, daemon=True)
        thread.start()
        print("Vérification DNS UDP/TCP et filtrage…", flush=True)
        check_server(host, 53)
        if shutil.which("termux-wake-lock"):
            wake = subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        print(f"\n{accent}DNS de votre console : {host}{reset}", flush=True)
        print("Même Wi-Fi pour le téléphone et la console. Désactivez le VPN pendant cet essai.")
        print("Laissez Termux actif et autorisez son activité en arrière-plan dans Android.")
        print("Contrôle local réussi ; l'accès depuis la console reste à tester.")
        print("AdGuard DNS assure le filtrage à distance. Aucun historique de requêtes local.")
        print("Ctrl+C arrête le DNS. Remettez alors la console en DNS automatique.", flush=True)
        while thread.is_alive():
            thread.join(0.5)
        if not server.stopped.is_set():
            raise RuntimeError("Le serveur DNS s'est arrêté")
    except KeyboardInterrupt:
        print("\nDNS arrêté. Remettez la console en DNS automatique.")
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EPERM):
            print("\nAndroid refuse le port DNS 53. Ce téléphone ne permet pas ce mode avec les droits actuels.\nAucun DNS prêt pour la console ; aucune modification système effectuée.", file=sys.stderr)
        elif error.errno == errno.EADDRINUSE:
            print("\nLe port 53 est déjà utilisé. Aucune installation existante n'a été arrêtée.", file=sys.stderr)
        else:
            print(f"\nÉchec réseau ({type(error).__name__}). Vérifiez le Wi-Fi et l'accès Internet.", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError) as error:
        print(f"\n{error}\nLe DNS n'est pas annoncé prêt.", file=sys.stderr)
        return 1
    finally:
        if server:
            server.close()
        if thread:
            thread.join(timeout=2)
        if wake and shutil.which("termux-wake-unlock"):
            subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
