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

## 0) Prérequis
- Une distribution Debian de mise en place sur votre machine avec accès `sudo`
- Accès réseau local recommandé pour tester le ban (évite de se bannir en loopback, ça serait dommage...)

## 1) Installation des paquets
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip caddy fail2ban
```

Lancer votre terminal et copier coller ces commandes, cela installera toutes les dépendances nécessaire au bon fonctionnement