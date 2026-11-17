#!/data/data/com.termux/files/usr/bin/bash
set -eu

project_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    if command -v pkg >/dev/null 2>&1; then
        printf 'Installation de Python via les paquets Termux…\n'
        pkg install -y python
    else
        printf 'Python 3.10+ requis. Lancez cet outil dans Termux.\n' >&2
        exit 1
    fi
fi
python_bin=python3
command -v "$python_bin" >/dev/null 2>&1 || python_bin=python
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    printf 'Mettez Python à jour : pkg upgrade python\n' >&2
    exit 1
}
cd -- "$project_dir"
exec "$python_bin" -m liminalguard "$@"
