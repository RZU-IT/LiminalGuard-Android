import argparse
import errno
import shutil
import subprocess
import sys
import threading

from . import __version__
from .checks import check_server
from .network import detect_ip
from .server import Server, local_address
from .terminal import Terminal
from .upstream import AdGuardDNS


def wait_for_shutdown(server, thread):
    while thread.is_alive():
        thread.join(0.5)
    if not server.stopped.is_set():
        raise RuntimeError("Le serveur DNS s'est arrêté")


def main():
    parser = argparse.ArgumentParser(description="Relais DNS Android — RZU Informatique")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--ip", help="choisir l'IPv4 Wi-Fi du téléphone")
    parser.add_argument("--check", action="store_true", help="vérifier un relais déjà démarré")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    parser.add_argument("--details", action="store_true", help="afficher les détails du démarrage")
    args = parser.parse_args()
    terminal = Terminal(args.color, details=args.details)
    terminal.banner()
    server = thread = None
    wake = False
    try:
        terminal.start()
        terminal.stage(5, "Recherche du téléphone")
        host, source = (args.ip, "manual") if args.ip else detect_ip()
        if not local_address(host):
            raise ValueError("Adresse locale invalide. Connectez le téléphone au Wi-Fi.")
        terminal.stage(20, "Adresse locale détectée")
        if args.check:
            check_server(host, 53, progress=terminal.stage)
        else:
            server = Server(host, 53, AdGuardDNS())
            server.bind()
            terminal.stage(40, "Service DNS démarré")
            thread = threading.Thread(target=server.serve, daemon=True)
            thread.start()
            check_server(host, 53, progress=terminal.stage)
            if shutil.which("termux-wake-lock"):
                try:
                    wake = subprocess.run(["termux-wake-lock"], timeout=3,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
                except (OSError, subprocess.TimeoutExpired):
                    pass
        terminal.stage(100, "Prêt" if not args.check else "Contrôle terminé")
        terminal.finish()
        terminal.identity(host, source, checking=args.check)
        if args.check:
            if args.details:
                print("Contrôle terminé ; cette commande n'a pas lancé de nouveau serveur.")
            return 0
        if not wake and args.details:
            print("Veille non verrouillée : autorisez l'activité en arrière-plan dans Android.", flush=True)
        wait_for_shutdown(server, thread)
    except KeyboardInterrupt:
        terminal.finish()
        print("\nRelais arrêté.")
    except (OSError, ValueError, RuntimeError) as error:
        terminal.finish()
        if isinstance(error, OSError) and error.errno in (errno.EACCES, errno.EPERM):
            message = "Android refuse le port 53 sur ce téléphone."
        elif isinstance(error, OSError) and error.errno == errno.EADDRINUSE:
            message = "Le port 53 est déjà utilisé."
        elif isinstance(error, OSError):
            message = "Connexion impossible. Vérifiez le Wi-Fi et l'accès Internet."
        else:
            message = str(error) if args.details else "Démarrage impossible. Vérifiez le Wi-Fi et Internet."
        print(f"\n{message}", file=sys.stderr)
        if args.details:
            print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    finally:
        terminal.finish()
        if server:
            server.close()
        if thread:
            thread.join(timeout=2)
        if wake and shutil.which("termux-wake-unlock"):
            try:
                subprocess.run(["termux-wake-unlock"], timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.TimeoutExpired):
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
