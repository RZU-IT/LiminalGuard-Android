# Validation — 0.1.0-alpha.2

Vérifications du 17 novembre 2026 sur Windows et Ubuntu sous WSL. Android physique et console non testés.

## Exécuté

- Trente-quatre tests Python : 32 réussis et deux contrôles ioctl Linux ignorés sous Windows ; 34 réussis sous WSL : protocole, paquets invalides, port occupé, permission refusée, refus d'adresse publique, débit limité, DNS UDP/TCP, domaine bloqué, panne amont, réponse inattendue, troncature UDP et arrêt du serveur.
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

## Recherche Android et évolution alpha.2

Le parcours ne dépend pas d'une application supplémentaire. Le Wi-Fi est recherché par interrogation de ses interfaces connues ; la route réseau est un secours explicitement identifié, pas une preuve de connexion Wi-Fi. Aucun appel ne change une adresse, une route ou une permission.

Les API Android de modification des réseaux configurés sont restreintes pour les applications ordinaires ciblant Android récent. Ajouter un Linux PRoot ne change ni ces permissions ni le réseau partagé. Aucune promesse d'IP statique automatique n'est faite. L'outil affiche l'adresse actuelle sous le libellé « Identifiant du téléphone » après les contrôles, sans supposer le type d'appareil client.

Références consultées le 17 novembre 2026 :

- [Android WifiManager : updateNetwork et ses restrictions](https://developer.android.com/reference/android/net/wifi/WifiManager#updateNetwork(android.net.wifi.WifiConfiguration)).
- [Termux : refus de netlink sur Android 13](https://github.com/termux/termux-packages/issues/16226).
- [Termux Play Store : fonctionnalités API disponibles](https://github.com/termux-play-store).
- [PRoot : pas de véritables privilèges root ni de réseau isolé](https://github.com/termux/proot-distro#proot-limitations).

Les tests ajoutés couvrent la préférence Wi-Fi, le secours par route, le refus d'adresse publique, l'absence de réseau, les refus ioctl, la progression sur 40 colonnes, les couleurs, l'arrêt du thread d'animation, les échecs avant 100 %, le contrôle sans lancement de service et un démarrage avec de vrais sockets suivi d'une interruption. Les permissions Android sont simulées ; les essais ioctl ciblés tournent sous Linux, pas sur Android physique.
