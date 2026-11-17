# Validation — 0.1.0-alpha.1

Vérifications du 17 novembre 2026 sur Windows et Ubuntu sous WSL. Android physique et console non testés.

## Exécuté

- Dix-neuf tests Python réussis sur chaque environnement : protocole, paquets invalides, port occupé, permission refusée, refus d'adresse publique, débit limité, DNS UDP/TCP, domaine bloqué, panne amont, réponse inattendue, troncature UDP et arrêt du serveur.
- Sockets réels loopback sur des ports temporaires avec fournisseur simulé pour la suite déterministe. Les erreurs des threads de service font échouer les tests.
- Essai réseau avec le vrai service AdGuard DNS en HTTPS : example.org résolu via UDP et TCP locaux ; ad.doubleclick.net bloqué. Cet essai passe sous Windows et sous WSL. Aucun réglage DNS système modifié.
- Syntaxe Bash, ShellCheck, aide et version du lanceur contrôlés sous WSL.

Les refus de permission sont simulés dans les tests de l'interface. Ils ne prouvent pas les autorisations d'un téléphone. Aucun essai du port 53 d'un Android n'a été réalisé. Aucun résultat PC/WSL ne vaut validation du Wi-Fi ou de la gestion des processus Android.

## Premier essai Android

Utiliser Termux du Play Store sur Android 11+, téléphone et console sur le même Wi-Fi, sans VPN. Lancer les deux commandes du README. Si Android refuse le port 53, conserver le message affiché : c'est un résultat de compatibilité, pas une installation réussie.

Si le contrôle local réussit, configurer le DNS de la console avec l'IP affichée et lancer son test de connexion. Vérifier ensuite le comportement écran éteint pendant plusieurs minutes et après le retour dans Termux. Une connexion normale réussie prouve la disponibilité DNS à cet instant, pas le blocage de toutes les publicités.

Pour un contrôle indépendant depuis un PC du même Wi-Fi disposant de dig :

```bash
dig @IP_DU_TELEPHONE example.org A
dig +tcp @IP_DU_TELEPHONE example.org A
dig @IP_DU_TELEPHONE ad.doubleclick.net A
```

Le dernier domaine doit donner une adresse nulle ou NXDOMAIN selon la politique du fournisseur. Répéter écran éteint. Ne pas exposer ce serveur sur Internet.

Arrêter avec Ctrl+C et remettre le DNS de la console en automatique. Le redémarrage automatique n'est pas implémenté. Remonter le modèle du téléphone, la version Android/Termux et le message d'erreur éventuel, sans compte, mot de passe ou jeton.

## Reproduction sur PC de développement

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 tests/live.py
bash -n installer.sh
shellcheck installer.sh
```

La suite automatique ne requiert ni administrateur ni port privilégié. Le contrôle live contacte un service tiers et dépend de son accessibilité et de ses listes actuelles.
