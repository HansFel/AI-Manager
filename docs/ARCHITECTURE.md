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
- `/registry` Pruefung und Anlage von Agents/Skills
- `/models` Modellrollen und Routing-Auszug

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
