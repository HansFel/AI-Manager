# Betrieb auf UGREEN NAS

Ja, die Anwendung kann grundsaetzlich auf einem UGREEN NAS laufen, wenn dort
Docker bzw. Container Manager verfuegbar ist.

## Wichtige Regel

Der Docker-Daemon auf dem NAS sieht keine Windows-Pfade wie `C:\...`, `Z:\...`
oder OneDrive-Pfade. Das Repo oder die Compose-Datei muss in einem Ordner
liegen, den der NAS-Docker selbst sehen kann.

## Variante per SSH auf dem NAS

```bash
git clone https://github.com/HansFel/AI-Manager.git
cd AI-Manager
mkdir -p .ai-management
AIM_BOOTSTRAP_ADMIN_PASSWORD='neues-sicheres-passwort' docker compose up -d --build
```

Danach im LAN:

```text
http://NAS-IP:8765
```

Nach dem ersten erfolgreichen Login sollte das Bootstrap-Passwort aus der
Compose-Umgebung entfernt werden.

## Variante ueber UGREEN Container Manager

1. Repo oder Projektordner auf das NAS kopieren.
2. `docker-compose.yml` als Compose-Projekt importieren.
3. Port `8765` nach aussen freigeben.
4. Volume `./.ai-management:/data` beibehalten, damit Benutzer, Sessions,
   Registry und Projekte Neustarts ueberleben.

## Oeffentlicher Zugriff

Fuer den Anfang ist LAN/VPN-Zugriff besser als direkte Internetfreigabe. Wenn
die App spaeter oeffentlich erreichbar sein soll, dann nur hinter HTTPS und
einem Reverse Proxy wie Traefik.
