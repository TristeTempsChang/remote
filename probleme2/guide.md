# Guide d’installation — Problème 2

Ce guide décrit l’installation complète afin de mettre en place le serveur web et le reverse proxy qui permettront de servir l'application web

## Objectif
Déployer une application web  avec :
- `/login` : formulaire et vérification avec identifiants codés en dur
- `/private` : accessible uniquement si authentifié et renvoie exactement :
  **"Accès au contenu privé autorisé"**
- **Caddy** en reverse proxy sur le port 80
- **fail2ban** qui bannit une ip si trop d’échecs sur `/login` (brute force)

Le dossier contient les éléments suivants :
- Application Flask (auth + session)
- Caddyfile
- Deux fichier de conf caddy pour fail2ban

<br />

## 0) Prérequis
- Une distribution Debian de mise en place sur votre machine avec accès `sudo`
- Accès réseau local recommandé pour tester le ban (évite de se bannir en loopback, ça serait dommage...)

<br />

## 1) Installation des paquets
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip caddy fail2ban
```

Lancez votre terminal et copiez collez ces commandes, cela installera toutes les dépendances nécessaire au bon fonctionnement

<br />

## 2) Créer l'environnement virtuel et installer les dépendances

Afin de lancer une première fois l'application web, il va être nécessaire d'installer Flask et Gunicorn.

Dans votre terminal, dans le répertoire du projet copiez / collez la commande

```bash
cd probleme2/app
```
Ensuite faite :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask gunicorn
```

Cela créera et activera l'environnement virtuel qui contiendra les bibliothèques de Python puis installera flask et gunicorn pour servir l'application

### Test sans reverse proxy

Pour démarrer l'application, dans votre terminal faite :
```bash
gunicorn -w 2 -b 127.0.0.1:8000 app:app
```

<br />

## 3) Gestionnaire de processus (systemd user)

Nous allons ensuite faire en sorte que l’application tourne en service systemd user (sous l’utilisateur courant). L'objectif étant de garder notre application constamment lancée

Pour ce faire, il va falloir créer le fichier de service : `~/.config/systemd/user/probleme2.service`

> 💡 Pour le contenu du fichier de service, voir dans le dossier `systemd` pour le template.

Une fois le fichier de service créer, lancez ces commandes dans votre terminal :

```bash
systemctl --user daemon-reload
systemctl --user enable --now webapp
systemctl --user status webapp --no-pager
```

### Test pour voir si le service fonctionne

```bash
curl -i http://127.0.0.1:8000/login
```

<br />

## 4) Caddy (reverse proxy + logs)

Nous allons maintenant configurer le reverse proxy de l'application

Créez un fichier Caddyfile dans : `/etc/caddy/Caddyfile`

> 💡 Pour le contenu du fichier Caddyfile, voir dans le dossier `caddy` pour le template.

Ensuite nous allons créer le dossier de logs (qui servira aussi à fail2ban)

```bash
sudo mkdir -p /var/log/caddy
```

Ensuite redémarrez Caddy et vérifiez qu'il s'est bien lancé

```bash
sudo systemctl restart caddy
sudo systemctl status caddy --no-pager
```

### Test via Caddy

```bash
curl -i http://localhost/login
curl -i http://localhost/private
```

### Test échec login (doit renvoyer 401) :

```bash
curl -i -X POST http://localhost/login -d "username=nainportequoi&password=faux"
```

### Vérifier que les logs se remplissent :

```bash
sudo tail -n 10 /var/log/caddy/access.log
```

## 5) Fail2ban (ban brute force sur /login)

Maintenant il va falloir configurer Fail2Ban afin de bannir une ip si elle génère trop de réponses 401 sur `/login`.

Exemple de règle :
- **maxretry** = 5
- **findtime** = 600s (10 min)
- **bantime** = 3600s (1h)

Créer un filtre (fichier de conf) qui repère les échecs de login directement dans les logs de Caddy : `/etc/fail2ban/filter.d/caddy-login-401.conf`

> 💡 Pour le contenu du fichier de conf, voir dans le dossier `fail2ban` et le fichier `caddy-login-401.conf` pour le template.

Ensuite créer une jail qui va appliquer un ban : `/etc/fail2ban/jail.d/caddy-login.conf`

> 💡 Pour le contenu du fichier de conf, voir dans le dossier `fail2ban` et le fichier `caddy-login.conf` pour le template.

Une fois cela fait, redémarrez et vérifiez que fail2ban fonctionne :

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status
sudo fail2ban-client status caddy-login-401
```

## 6) Test de bannissement

Afin de s'assurer que tout fonctionne, nous allons procéder à des tests

 ⚠️ **Attention au test depuis localhost** : Tester uniquement `localhost` peut aboutir à bannir `127.0.0.1`. Idéalement, il serait recommandé de tester via l'ip LAN de la machine.

Pour trouver l'ip :

```bash
ip a | grep -E "inet " | grep -v 127.0.0.1
```

Exemple : `192.168.1.50`

Une fois l'ip trouvé, générez des échecs de login :

```bash
IP="192.168.1.50"  # remplacer par votre IP
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://$IP/login \
    -d "username=alice&password=wrong$i"
done
```

Vérifiez le ban :

```bash
sudo fail2ban-client status caddy-login-401
```

On doit voir l'ip dans `Banned IP list`.

Vérifiez ensuite que le ban soit effectif

```bash
curl -i http://$IP/login
```

Si vous souhaitez débannir vous pouvez taper cette commande :

```bash
sudo fail2ban-client set caddy-login-401 unbanip 192.168.1.50
```

<br />

### Diagnostic rapide si le ban ne marche pas :

Il est conseillé de regarder si la jail est active :

```bash
sudo fail2ban-client status caddy-login-401
```

Est ce que le filtre matche-t-il les logs ? :

```bash
sudo fail2ban-regex /var/log/caddy/access.log /etc/fail2ban/filter.d/caddy-login-401.conf
```

Les logs contiennent-ils bien /login + 401 ? :

```bash
sudo grep -n '"uri":"/login"' /var/log/caddy/access.log | tail -n 5
sudo grep -n '"status":401' /var/log/caddy/access.log | tail -n 5
```