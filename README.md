# LiminalGuard Android

![LiminalGuard](assets/logo.svg)

Relais DNS antipub pour les appareils du même Wi-Fi. Version expérimentale, en cours de test sur téléphone.

## Lancer

Installer [Termux du Play Store](https://play.google.com/store/apps/details?id=com.termux), sur Android 11 ou supérieur. Ouvrir Termux, connecté au Wi-Fi sans VPN :

```bash
pkg install -y git python >/dev/null && git clone --quiet https://github.com/RZU-IT/LiminalGuard-Android.git
```

```bash
bash LiminalGuard-Android/installer.sh
```

L’écran est nettoyé au lancement. Seuls le logo et une barre de chargement restent visibles, puis :

```text
Identifiant du téléphone : adresse IP
```

Utiliser l’adresse affichée comme DNS sur l’appareil à filtrer. Garder Termux actif. Ctrl+C arrête le relais ; remettre alors les appareils en DNS automatique.

Android doit autoriser le port 53. L’adresse du téléphone n’est pas rendue statique. Le relais utilise AdGuard DNS en HTTPS ; il ne bloque pas toutes les publicités vidéo.

Pour afficher les détails en cas de problème : `bash LiminalGuard-Android/installer.sh --details`.

[Guide et dépannage](docs/reference.md) · [Validation](docs/validation.md) · [Version Linux](https://github.com/RZU-IT/LiminalGuard)

Développé par RZU Informatique avec l’assistance d’OpenAI Codex. [Licence MIT](LICENSE). Projet indépendant d’AdGuard et Termux.

## Mettre à jour

Dans Termux, arrêter l’outil avec Ctrl+C, puis lancer :

```bash
git -C ~/LiminalGuard-Android pull --ff-only
bash ~/LiminalGuard-Android/installer.sh
```

La première commande récupère la mise à jour, la seconde relance l’outil.
