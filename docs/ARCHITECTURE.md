# Architektur

## Zielbild

AI Management Hub ist eine eigene Steuerzentrale fuer mehrere AI-Modelle. Das
System verwaltet, welche Modelle welche Rollen uebernehmen, welche Agents
existieren, welche Skills sie nutzen, und ob neue Bausteine bereits vorhandene
Funktionalitaet doppeln.

## Schichten

### 1. Workspace

Der Workspace liegt in einem Git-Repo. Alle portablen Definitionen liegen in
Textformaten:

- `configs/*.yaml` fuer Modelle und Geraeteprofile
- `.ai-management/registry.json` fuer Agents, Skills und Fingerprints
- `.ai-management/projects.json` fuer Projekte, Repos und gemeinsame Bausteine
- `.ai-management/users.local.json` fuer lokale Webbenutzer ohne Git-Sync
- spaeter `agents/`, `skills/`, `runs/` fuer konkrete Artefakte

### 2. Registry

Die Registry ist die zentrale Wahrheit fuer:

- Modelle
- Agents
- Skills
- Aufgabenmuster
- Herkunft und Aenderungshistorie

Jeder Eintrag erhaelt einen normalisierten Fingerprint. Dadurch kann das System
erkennen, wenn z.B. `LegeStall deploy`, `stall deploy workflow` und
`Stall-Control deployment` dieselbe Absicht haben.

### 2b. Projektkatalog

Der Projektkatalog verbindet mehrere Repos. Er speichert:

- Projektname
- Git-Repo
- optionaler lokaler Pfad je Geraet
- Tags und Status
- gemeinsame Themen zwischen Projekten

Gemeinsamkeiten sind eigenstaendige Eintraege, damit z.B. `Docker Deploy ueber
UGREEN NAS`, `FastAPI Login`, `Traefik Routing` oder `Buchhaltungs-Kontenlogik`
nicht in jedem Repo neu erfunden werden.

### 3. Model Router

Modelle werden nicht nur als Provider-Namen gespeichert, sondern als Rollen:

- `planner`: zerlegt Arbeit und erstellt Plaene
- `coder`: setzt Code um
- `reviewer`: prueft Risiken, Tests und Doppelungen
- `researcher`: sucht externes Wissen oder Doku

Ein Modell kann mehrere Rollen haben, und eine Rolle kann Fallbacks besitzen.

### 4. Agent Layer

Agents sind langlebige Rollen mit Zustaendigkeit. Beispiele:

- `repo-maintainer`
- `skill-curator`
- `deployment-operator`
- `documentation-writer`

Agents duerfen Skills nutzen, sollen aber nicht selbst neue Parallelwelten
erfinden. Vor jeder Agent- oder Skill-Erstellung laeuft eine Registry-Pruefung.

### 5. Skill Layer

Skills sind wiederverwendbare Arbeitsanweisungen, Skripte oder Integrationen.
Der Skill-Generator muss immer:

1. existierende Skills suchen
2. Aehnlichkeit bewerten
3. erweitern statt neu erstellen, wenn die Ueberschneidung hoch ist
4. nur bei klar neuer Funktion einen neuen Skill anlegen

## Plattformstrategie

Win11, WSL und Linux Mint nutzen dieselbe Repo-Struktur. Unterschiede werden in
Geraeteprofilen abgelegt:

- Shell: PowerShell, bash
- Pfade: Windows-Pfade vs. Linux-Pfade
- Runtime: lokale Python-Version, Docker, WSL
- Secret-Quelle: `.env`, Keychain, pass, 1Password oder System-ENV

## Weboberflaeche

Die Startversion nutzt FastAPI mit serverseitiger Session. Ohne Anmeldung leiten
geschuetzte Seiten auf `/login` um. Der lokale User-Store verwendet
PBKDF2-SHA256-Hashes und wird bewusst nicht versioniert.

Erste Seiten:

- `/` Dashboard mit Modell-, Agent-, Skill- und Duplikatstatus
- `/projects` Projekt- und Gemeinsamkeitenverwaltung
- `/registry` Pruefung und Anlage von Agents/Skills
- `/models` Modellrollen und Routing-Auszug

## Docker/NAS Betrieb

Die Anwendung kann in einem Container laufen. Das Datenverzeichnis ist ueber
`AIM_DATA_DIR` konfigurierbar und wird im Compose-Setup nach `/data` gelegt.

Auf einem UGREEN NAS gilt:

- Compose/Build-Kontext muss auf dem NAS sichtbar sein.
- Windows-Mappings wie `Z:\` sind fuer den NAS-Docker nicht direkt gueltig.
- Benutzer, Sessions, Registry und Projekte sollten ueber ein Volume persistiert
  werden.
- Oeffentlicher Zugriff sollte spaeter ueber HTTPS/Reverse Proxy laufen.

## Grundregel gegen Doppelgleisigkeit

Neue Agents und Skills werden niemals direkt erzeugt. Der Ablauf ist:

```text
Beschreibung -> Normalisieren -> Registry-Suche -> Aehnlichkeit -> Entscheidung
```

Entscheidung:

- `reuse`: vorhandenen Eintrag nutzen
- `extend`: vorhandenen Eintrag erweitern
- `create`: neuen Eintrag erzeugen
- `reject`: absichtlich nicht aufnehmen
