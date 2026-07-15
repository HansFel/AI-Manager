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
aim models --config configs/models.example.yaml
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
```

## Repo-Struktur

```text
configs/                  Beispielkonfigurationen
docs/                     Architektur und Entscheidungen
src/ai_management/        CLI und Kernlogik
.ai-management/           Lokale Registry, wird per CLI erzeugt
```

## Naechste Ausbaustufen

1. Web-UI fuer Agenten, Skills und Modell-Routing.
2. Provider-Adapter fuer die vier genutzten Modelle.
3. Task-Router, der Aufgaben an passende Agents verteilt.
4. GitHub-Sync und Geraeteprofile.
5. Skill-Generator mit Review-Schritt gegen vorhandene Registry.
