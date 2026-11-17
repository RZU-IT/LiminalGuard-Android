# LiminalGuard Android — expérimental

![LiminalGuard](https://raw.githubusercontent.com/RZU-IT/LiminalGuard-Android/main/assets/logo.svg)

Relais DNS antipub expérimental sur Android, utilisable depuis les appareils du même Wi-Fi.

**Version expérimentale 0.1.0-alpha.2 — en cours de test, pas encore validée sur un téléphone Android physique.** Le premier essai sert à vérifier le port 53 et l'accès depuis la console. Certains téléphones refuseront ce port sans privilèges supplémentaires ; le script s'arrête alors sans annoncer un DNS prêt.

Pour Ubuntu et Raspberry Pi OS : [LiminalGuard Linux — version bêta](https://github.com/RZU-IT/LiminalGuard). Les deux versions ont des fonctionnements et des validations distincts.

## Essai sur téléphone

Installer [Termux depuis Google Play](https://play.google.com/store/apps/details?id=com.termux), sur Android 11 ou supérieur. Connecter le téléphone au même Wi-Fi que la console. Ouvrir Termux, puis exécuter ces deux commandes séparément :

```bash
pkg install -y git python && git clone https://github.com/RZU-IT/LiminalGuard-Android.git
```

```bash
bash LiminalGuard-Android/installer.sh
```

Accepter les permissions réseau ou d'arrière-plan proposées par Android si nécessaires. Les paquets proviennent des dépôts de Termux ; aucune application Linux supplémentaire n'est requise.

Une porte en ASCII, le titre LiminalGuard et la signature by RZU Informatique accompagnent une progression colorée liée aux étapes réelles. Le programme vérifie le port 53 UDP/TCP, une résolution normale et un domaine publicitaire de contrôle. Il affiche ensuite **Identifiant du téléphone : adresse IP**. Cet identifiant est simplement l'IPv4 locale du téléphone, pas un identifiant matériel ou personnel.

Dans les réglages réseau de la console, utiliser cette adresse comme DNS principal. Ne pas ajouter un DNS public non filtrant en secondaire : la console pourrait l'utiliser et contourner le relais. Si un second champ est obligatoire et accepte la même adresse, recopier celle du téléphone.

Si le test réseau de la console échoue, remettre son DNS en automatique. Le contrôle réalisé depuis le téléphone ne prouve pas l'accès depuis un autre appareil. Un Wi-Fi invité ou l'isolation des clients peut bloquer cet accès.

## Pendant l'essai

Laisser Termux actif. Autoriser son fonctionnement en arrière-plan et désactiver son optimisation de batterie si nécessaire. Un verrou de veille est demandé lorsqu'il est disponible ; il ne garantit pas qu'Android conservera le processus. Cette version ne configure pas de lancement automatique après redémarrage. Un téléphone utilisé en permanence comme serveur consomme de la batterie.

Le programme cherche d'abord l'IPv4 des interfaces Wi-Fi Android sans dépendre de `ifconfig`, de netlink ou de Termux:API. Si Android ne permet pas cette lecture, il utilise la route réseau active et signale que le Wi-Fi n'a pas été identifié. Désactiver le VPN et vérifier alors que l'adresse correspond au Wi-Fi. Pour la choisir explicitement :

```bash
bash LiminalGuard-Android/installer.sh --ip 192.168.1.25
```

Aucune manipulation de la box n'est obligatoire pour le premier essai. Termux partage l'adresse réseau d'Android : ce n'est pas une machine virtuelle avec une adresse séparée. L'outil relit l'adresse à chaque lancement et ne la rend pas statique. Si Android change cette adresse, mettre à jour les appareils qui l'utilisent. Une réservation DHCP dans la box reste une option pour un serveur permanent, pas une étape imposée par cet installateur. Aucune redirection de port vers Internet n'est nécessaire.

Ctrl+C arrête le relais. Remettre la console en DNS automatique dès que le téléphone ou le relais est arrêté. Pour relancer, réexécuter la deuxième commande.

## Fonctionnement

Le filtrage est fourni par le DNS public AdGuard, appelé en HTTPS avec vérification des certificats. Le téléphone sert de relais DNS IPv4 local ; ce prototype n'installe pas AdGuard Home et n'offre pas son tableau de bord ni ses listes personnalisées.

Les requêtes console → téléphone utilisent le DNS classique sur le réseau local. Les requêtes téléphone → AdGuard passent par HTTPS. AdGuard reçoit les noms demandés et l'adresse de connexion du téléphone. Aucun journal de requêtes ni historique n'est enregistré par cet outil. Le DNS de l'hôte, le pare-feu et la box ne sont pas modifiés.

Écoute sur une IPv4 privée explicite, accès limité aux clients IPv4 privés, nombre de traitements et débit bornés. Réponses UDP volumineuses renvoyées avec le drapeau de troncature pour permettre une reprise TCP. En cas de panne du fournisseur, le relais renvoie une erreur ; aucun DNS non filtrant n'est utilisé en secours.

## Limites

La présence de Termux sur le Play Store ne garantit pas la disponibilité du port 53. Ni PRoot ni un terminal affichant « root » ne donnent automatiquement les privilèges Android. Cette version ne roote pas le téléphone et ne contourne pas ses restrictions.

Le filtrage DNS ne bloque pas toutes les publicités, notamment celles diffusées depuis les mêmes domaines que les vidéos. Les applications utilisant leur propre DNS chiffré peuvent contourner celui configuré sur la console. Le contrôle parental n'est pas activé par ce profil.

IPv6, partage de connexion mobile, interface de gestion, démarrage automatique et fonctionnement prolongé écran éteint ne sont pas validés. Ne pas présenter cette alpha comme un remplacement garanti d'un serveur permanent.

## Vérification et développement

Les couleurs suivent le terminal ; `--color always`, `--color never` et `NO_COLOR` permettent de les régler. La progression reste textuelle lorsqu'elle est redirigée vers un fichier.

Dans une autre session Termux, pour contrôler le serveur déjà lancé :

```bash
bash LiminalGuard-Android/installer.sh --check --ip 192.168.1.25
```

Python 3.10+ et sa bibliothèque standard suffisent. Les sources sont séparées entre protocole DNS, transport HTTPS, serveur et interface terminal. Les tests utilisent des sockets loopback sur des ports temporaires ; ils ne changent pas le DNS du PC.

```bash
python -m unittest discover -s tests -v
```

Voir [les validations et les essais à faire sur Android](https://github.com/RZU-IT/LiminalGuard-Android/blob/main/docs/validation.md).

## Crédits

Développé par RZU Informatique avec l'assistance d'OpenAI Codex. [Licence MIT](https://github.com/RZU-IT/LiminalGuard-Android/blob/main/LICENSE) : conserver le copyright et la licence lors d'une réutilisation. Une mention de LiminalGuard et de RZU Informatique est appréciée.

Projet indépendant, sans affiliation avec AdGuard ou Termux. Le service distant reste soumis à ses propres conditions : [AdGuard DNS](https://adguard-dns.io/en/public-dns.html). La [version Raspberry Pi](https://github.com/RZU-IT/LiminalGuard) reste un projet séparé.
