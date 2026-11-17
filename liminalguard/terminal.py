import os
import shutil
import sys
import threading

from . import __version__

DOOR = """
    +--------+
    |        |   LIMINALGUARD
    |       .|   ANDROID
    |        |
    +--------+"""

RZU = r"""    ___  ____  _   _
   | _ \|_  / | | | |
   |   / / /_ | |_| |
   |_|_\/____| \___/
       INFORMATIQUE"""


class Terminal:
    def __init__(self, color="auto", stream=None):
        self.stream = stream or sys.stdout
        self.interactive = self.stream.isatty()
        self.color = color == "always" or (color == "auto" and self.interactive and "NO_COLOR" not in os.environ)
        self.columns = shutil.get_terminal_size((72, 24)).columns
        self.percent = 0
        self.label = "Préparation"
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.finished = False

    def paint(self, text, code="150"):
        return f"\033[38;5;{code}m{text}\033[0m" if self.color else text

    def banner(self):
        print(self.paint(DOOR), file=self.stream)
        print(self.paint(RZU, "109"), file=self.stream)
        print(f"    by RZU Informatique · {__version__}\n    Version expérimentale\n", file=self.stream, flush=True)

    def render(self, frame=0):
        width = max(8, min(24, self.columns // 3))
        filled = width * self.percent // 100
        bar = "=" * filled + " " * (width - filled)
        spinner = "|/-\\"[frame % 4] if self.percent < 100 else "+"
        available = max(0, self.columns - width - 11)
        return f"{spinner} [{bar}] {self.percent:3d}% {self.label[:available]}".rstrip()

    def start(self):
        if self.interactive:
            self.thread = threading.Thread(target=self.animate, daemon=True)
            self.thread.start()

    def animate(self):
        frame = 0
        while not self.stop.is_set():
            with self.lock:
                self.stream.write("\r" + self.paint(self.render(frame)) + " " * 2)
                self.stream.flush()
            frame += 1
            self.stop.wait(0.12)

    def stage(self, percent, label):
        with self.lock:
            self.percent, self.label = percent, label
            if self.interactive:
                self.stream.write("\r" + " " * max(0, self.columns - 1) + "\r" + self.paint(self.render()))
                self.stream.flush()
            else:
                print(self.render(), file=self.stream, flush=True)

    def finish(self):
        if self.finished:
            return
        self.stop.set()
        if self.thread:
            self.thread.join(1)
        if self.interactive:
            print(file=self.stream, flush=True)
        self.finished = True

    def identity(self, host, source, checking=False):
        print("\n" + self.paint(f"Identifiant du téléphone : {host}"), file=self.stream)
        if not checking:
            print("Filtrage actif. Gardez Termux ouvert. Ctrl+C pour arrêter.", file=self.stream)
        if source == "route":
            print("Wi-Fi non identifié : vérifiez que cette adresse est celle du Wi-Fi, sans VPN.", file=self.stream)
        print("L'adresse est relue à chaque lancement ; elle n'est pas rendue statique.", file=self.stream, flush=True)
