# AI Management Hub

Lokale AI-Management-Umgebung fuer mehrere Modelle, Agents und Skills.

Ziel: Vier oder mehr AI-Modelle sollen zusammenarbeiten, ohne dass Skills,
Agents, Prompts oder Automationen mehrfach und widerspruechlich gepflegt
werden. Das Projekt ist local-first gebaut und soll auf Win11, WSL und Linux
Mint gleich funktionieren.

## Kernideen

- Eine gemeinsame Registry fuer Modelle, Agents, Skills und Aufgabenmuster.
- Skills und Agents bekommen Fingerprints, damit Doppelgleisigkeiten frueh
  sichtbar werden.
- Repos und Projekte werden zentral gepflegt, damit Gemeinsamkeiten wie
  Deployment, Auth, Datenmodelle und Skills nicht mehrfach entstehen.
- Modelle werden nach Rollen eingebunden, z.B. Planner, Coder, Reviewer,
  Researcher.
- Konfiguration bleibt in YAML/JSON und ist Git-freundlich.
- Secrets bleiben ausserhalb des Repos in `.env`, OS-Keychain oder lokalen
  Profilen.

## Schnellstart lokal

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
aim init
aim create-user --username admin
aim web --host 127.0.0.1 --port 8765
```

Falls `aim.exe` unter Windows noch nicht im PATH liegt, funktionieren dieselben
Befehle direkt ueber Python:

```powershell
python -m ai_management.cli init
python -m ai_management.cli create-user --username admin
python -m ai_management.cli web --host 127.0.0.1 --port 8765
```

Danach die Weboberflaeche oeffnen:

```text
http://127.0.0.1:8765
```

Weitere CLI-Beispiele:

```powershell
aim models --config configs/models.example.yaml
aim register-project "AI Manager" --repo-url "https://github.com/HansFel/AI-Manager.git" --tag fastapi --tag docker
aim register-skill "lege stall deploy" --description "Deploy workflow fuer Stall-Control"
aim register-skill "LegeStall deployment" --description "Deployment workflow for stall control"
aim duplicates
```

Unter WSL/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
aim init
aim create-user --username admin
aim web --host 127.0.0.1 --port 8765
```

## Repo-Struktur

```text
configs/                  Beispielkonfigurationen
docs/                     Architektur und Entscheidungen
src/ai_management/        CLI und Kernlogik
.ai-management/           Lokale Registry, wird per CLI erzeugt
```

## Projekte und Gemeinsamkeiten

Die Weboberflaeche hat eine Projektseite. Dort koennen Repos und Projekte
eingetragen werden, z.B. AgroBetrieb, LegeStallKontrolle, AI-Manager oder
MGRSoftware. Dazu koennen gemeinsame Bausteine gepflegt werden:

- Deployment-Wege
- Auth-/Login-Muster
- Datenmodelle
- gemeinsame Skills
- Docker/NAS/Traefik-Runtime
- wiederverwendbare Entscheidungen

Diese Informationen landen in `.ai-management/projects.json` und koennen ueber
Git synchronisiert werden. Lokale Benutzer und Session-Schluessel bleiben in
`.local` Dateien und werden nicht gepusht.

## Anmeldung

Die Weboberflaeche nutzt lokale Sessions. Benutzer werden nicht ins GitHub-Repo
geschrieben, sondern in `.ai-management/users.local.json` gespeichert. Diese
Datei ist absichtlich ignoriert.

```powershell
python -m ai_management.cli create-user --username admin
```

Damit kann der lokale Admin spaeter auch ein neues Passwort bekommen.

## Docker

Lokal:

```powershell
docker compose up -d --build
```

Beim ersten Containerstart kann ein Admin automatisch angelegt werden:

```powershell
$env:AIM_BOOTSTRAP_ADMIN_PASSWORD="bitte-aendern"
docker compose up -d --build
```

Danach:

```text
http://127.0.0.1:8765
```

Das Compose-Volume `./.ai-management:/data` speichert Registry, Projekte,
Benutzer und Sessions persistent.

## UGREEN NAS

Ja, die Anwendung kann auf einem UGREEN NAS laufen, wenn Docker bzw. Container
Manager verfuegbar ist. Wichtig: Das NAS muss den Projektordner selbst sehen;
Windows-Pfade wie `Z:\...` oder OneDrive-Pfade sind fuer den NAS-Docker kein
gueltiger Build-Kontext.

Siehe [docs/UGREEN_NAS.md](docs/UGREEN_NAS.md).

## Naechste Ausbaustufen

1. Repo-Scanner fuer lokale Pfade und GitHub-Remotes.
2. Provider-Adapter fuer die vier genutzten Modelle.
3. Task-Router, der Aufgaben an passende Agents verteilt.
4. GitHub-Sync und Geraeteprofile.
5. Skill-Generator mit Review-Schritt gegen vorhandene Registry.
6. Rollen/Rechte fuer mehrere Benutzer.
