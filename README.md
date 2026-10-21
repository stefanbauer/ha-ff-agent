# FF Agent für Home Assistant

Lokale Entwicklungsbasis für eine Home-Assistant-Custom-Integration mit der Domain
`ff_agent`. **Noch keine FF-Agent-Funktionalität und keine Dashboard-Karte.** Es
gibt keine externen Anfragen, Webhooks, Zugangsdaten, Entitäten, Aktionen oder
Einrichtungsdialoge. Version `0.0.0` kennzeichnet ausschließlich das Gerüst.

## Voraussetzungen und Struktur

- Docker Desktop mit laufender Engine und Docker Compose v2.
- Git; kein lokales Python oder virtuelles Environment erforderlich.
- Freier lokaler TCP-Port `8124`.

```text
custom_components/ff_agent/   Installierbare Integration (Manifest + No-op-Setup)
dev/configuration.yaml       Minimale, versionierte HA-Testkonfiguration
tests/                       Integrationstest mit echtem Home Assistant
compose.yaml                 Separate Testinstanz und Ruff-Werkzeug
hacs.json                    HACS-Metadaten
pyproject.toml               Ruff-Konfiguration (Python 3.14)
.github/workflows/           Prüfungen bei Push und Pull Request
```

Die Struktur folgt den offiziellen [Home-Assistant-Konventionen](https://developers.home-assistant.io/docs/creating_integration_file_structure/)
und dem [HACS-Integrationslayout](https://www.hacs.xyz/docs/publish/integration/).
**Das Repository ist privat und deshalb nicht über HACS installierbar.** HACS wird
für die lokale Entwicklung weder installiert noch benötigt. Dies ist noch kein
veröffentlichungsfertiges HACS-Paket: Brand-Assets, eine bewusste Lizenzentscheidung,
vollständige Funktionalität und Release-Validierung stehen vor einer späteren
Veröffentlichung an. Es werden keine Releases oder Images veröffentlicht.

## Lokale Testinstanz

Alle folgenden Befehle im Zielrepository ausführen:

```sh
cd /Users/stefanbauer/Herd/ha-ff-agent
docker compose up -d --wait --wait-timeout 240
```

Öffnen: **http://localhost:8124**. Beim ersten Start einen eigenen lokalen
Home-Assistant-Benutzer über das Onboarding anlegen. Es werden bewusst weder ein
Standardpasswort noch Tokens erzeugt oder im Repository gespeichert. Keine
produktiven Zugangsdaten verwenden. Das Onboarding darf zunächst offen bleiben;
die Integration wird trotzdem bereits beim Start geladen.

Die Instanz verwendet exakt `ghcr.io/home-assistant/home-assistant:2026.10.2`
(inklusive Python 3.14). Compose-Projekt: `ha-ff-agent-dev`. Der Port ist nur an
`127.0.0.1` gebunden, nicht ans LAN. Kein Host-Netzwerk, kein privilegierter Modus,
keine Gerätefreigaben und keine automatische Geräteerkennung. Dies ist Home
Assistant Container, kein Home Assistant OS mit Supervisor/Apps.

### Änderungen ohne Commit oder Push testen

`./custom_components/ff_agent` ist direkt und schreibgeschützt nach
`/config/custom_components/ff_agent` eingebunden. Änderungen im Editor sind sofort
im Container sichtbar; **Python-Code wird erst nach einem HA-Neustart neu geladen**:

```sh
docker compose restart homeassistant
docker compose ps
docker compose logs --tail=100 homeassistant
```

Auch `dev/configuration.yaml` ist direkt schreibgeschützt eingebunden. Dieser
Bootstrap lädt `ff_agent:` nur zur Gerüstprüfung; das ist keine Zusage einer
späteren YAML-Konfigurationsschnittstelle. FF Agent erscheint ohne Config Flow
noch nicht unter „Integration hinzufügen“. Keine leeren Plattform-, Übersetzungs-
oder Dashboard-Dateien sind nötig, bevor es entsprechende Funktionalität gibt.

### Betrieb

```sh
# Starten (auch nach stop/down); wartet auf den HTTP-Healthcheck
docker compose up -d --wait --wait-timeout 240

# Stoppen, Daten und Container behalten
docker compose stop

# Neustarten, etwa nach Python-Änderungen
docker compose restart homeassistant

# Status / HTTP-Healthcheck
docker compose ps
curl -I http://localhost:8124/

# Logs verfolgen (Ctrl+C beendet nur die Logansicht)
docker compose logs -f --tail=100 homeassistant

# Container und Projektnetzwerk entfernen, Daten behalten
docker compose down
```

Kein automatischer Start nach einem Docker-/Mac-Neustart (`restart: "no"`). Die
Testinstanz bei Bedarf mit `up` starten. Konto, Einstellungen, Datenbank und Tokens
liegen nur im Docker-Volume `ha-ff-agent-dev_ha_config`, nicht im Git-Arbeitsordner.

### Vollständiger Reset — destruktiv

**Löscht alle lokalen Testbenutzer, Tokens, Einstellungen, Historie und übrigen
HA-Laufzeitdaten dieser Instanz unwiederbringlich.** Vorher bei Bedarf ein Backup
anlegen. Quellcode und versionierte Testkonfiguration bleiben unverändert. Andere
Docker-Projekte werden nicht angefasst. Kein `docker system prune` verwenden.

```sh
docker compose down --volumes --remove-orphans
docker compose up -d --wait --wait-timeout 240
```

Danach beginnt das Onboarding erneut. Das Image bleibt im Docker-Cache.

## Prüfungen

Die gleichen Befehle laufen in GitHub Actions. Ruff wird separat und gepinnt im
Werkzeugcontainer ausgeführt, Tests dagegen im exakten HA-Laufzeitimage:

```sh
docker compose config --quiet
docker compose run --rm ruff
docker compose run --rm ruff format --check --no-cache .
docker compose run --rm --no-deps --entrypoint python homeassistant -m unittest discover -s /tests -v
docker compose run --rm --no-deps --entrypoint python homeassistant -m homeassistant --script check_config --config /config
```

Der Smoke-Test lädt die gemountete Integration über Home Assistants Setup-API in
einem temporären Konfigurationsordner und prüft das erfolgreiche Laden ohne
FF-Agent-Entitäten oder -Aktionen. Er verwendet keine persönlichen Daten und
sendet keine FF-Agent-Anfragen. `check_config` prüft die echte Dev-Konfiguration;
es startet keinen zweiten HTTP-Server. Die Befehle benötigen keinen Commit/Push.

Zum automatischen Formatieren den Quellordner einmal explizit schreibbar mounten
(der Standardmount des Werkzeugs bleibt absichtlich read-only):

```sh
docker compose run --rm --volume "$PWD:/work:rw" ruff format --no-cache .
```

Für spätere HA-Upgrades Image-Tag, Python-Zielversion und Mindestversion in
`hacs.json` gemeinsam prüfen. Keine produktiven Daten oder echten FF-Agent-Links
für automatisierte Tests verwenden.
