# Lokale Entwicklung

Die Bedienungsanleitung steht in der [README](../README.md).
Diese Seite richtet sich ausschließlich an Entwickler der Integration.

Lokale Entwicklungsbasis für eine Home-Assistant-Custom-Integration mit der Domain
`ff_agent`. Mehrere benannte Dienste lassen sich über die Oberfläche einrichten,
jeweils mit persönlicher Rückmelde-ID, Standard-Anreiseart und eigenem Alarm-Webhook.
Pro Dienst gibt es einen Einsatz-Binary-Sensor, einen Rückmeldestatus und die
Aktionen Einsatz zusagen, Einsatz absagen und Einsatz beenden. Nur ausdrückliche Zu-/Absagen
senden FF-Agent-Anfragen; automatisierte Tests verwenden ausschließlich Mock-HTTP.
**Noch keine Einsatzdetails oder eigene Dashboard-Karte.** Version `0.1.1` ist eine Entwicklungsversion;
`1.0.0` bleibt einer ersten vollständigen, stabilen Version vorbehalten.
Die Integrationsoberfläche ist standardmäßig Englisch, bei deutscher HA-Sprache Deutsch.

## Voraussetzungen und Struktur

- Docker Desktop mit laufender Engine und Docker Compose v2.
- Git; kein lokales Python oder virtuelles Environment erforderlich.
- Freier lokaler TCP-Port `8124`.

```text
custom_components/ff_agent/   Integration, Config Flow und Übersetzungen
dev/configuration.yaml       Minimale, versionierte HA-Testkonfiguration
tests/                       Integrationstest mit echtem Home Assistant
compose.yaml                 Separate Testinstanz und Ruff-Werkzeug
hacs.json                    HACS-Metadaten
pyproject.toml               Ruff-Konfiguration (Python 3.14)
.github/workflows/           Prüfungen bei Push und Pull Request
```

Die Struktur folgt den offiziellen [Home-Assistant-Konventionen](https://developers.home-assistant.io/docs/creating_integration_file_structure/)
und dem [HACS-Integrationslayout](https://www.hacs.xyz/docs/publish/integration/).
Das öffentliche Repository kann als benutzerdefiniertes HACS-Repository installiert
werden; eine Aufnahme in den Standardkatalog ist nicht erfolgt. HACS wird für die
lokale Entwicklung weder installiert noch benötigt. Code und eigene Dokumentation
stehen unter der [MIT-Lizenz](../LICENSE); das Logo ist davon ausgenommen, siehe
[Rechtehinweise](../NOTICES.md). Eine Namensnennung ersetzt keine Nutzungserlaubnis.
Version 0.1.1 ist zum kontrollierten Praxistest vorgesehen. Neue Versionen werden
nach erfolgreicher Prüfung als reguläres GitHub-Release veröffentlicht. Tag und
Manifest-Version stimmen überein und tragen kein `v`-Präfix, zum Beispiel `0.1.1`.
HACS nutzt diese Releases für versionierte Updates, auch bei Custom-Repositories.
Es werden keine Container-Images veröffentlicht und keine HACS-Katalogeinreichung
vorgenommen.
Lokale Brand-Icons liegen unter `custom_components/ff_agent/brand/`.
Die [Endnutzeranleitung](../README.md) enthält die vorbereiteten offiziellen
My-Home-Assistant-Buttons für HACS und den Config Flow. Der HACS-Link nutzt
`owner=stefanbauer`, `repository=ha-ff-agent` und `category=integration` und kann
ein öffentliches Custom-Repository hinzufügen oder ein vorhandenes öffnen.
Er veröffentlicht nichts und umgeht keine Zugriffsrechte. Der Setup-Link mit
`domain=ff_agent` setzt die lokale Installation und einen Neustart voraus.
Das native `my:` ist in der minimalen Testkonfiguration aktiviert, damit solche
Links auch ohne `default_config:` auf die lokale Oberfläche weiterleiten können.

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
späteren YAML-Konfigurationsschnittstelle. Die Dienste selbst werden über die
Oberfläche eingerichtet; HACS ist dafür nicht erforderlich.

### FF-Agent-Dienste einrichten

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → FF Agent**
   (oder „Dienst hinzufügen“ auf der vorhandenen FF-Agent-Seite).
2. Organisationsnamen eingeben, zum Beispiel **Feuerwehr Berglern**.
3. In **FF-Agent → Persönliches Profil → Weblinks für Einsatzmeldung** den
   persönlichen Zusage-/Absage-Link suchen. **Nur die UUID** zwischen
   `/missionreplies/` und `/accept` bzw. `/reject` eingeben, im Format
   `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`, keine vollständige URL oder Parameter.
   Die ID ist ein
   Geheimnis und darf nicht in Logs, Screenshots, Issues oder Git landen.
4. Standard-Anreiseart auswählen: **Auto (CAR)**, **Fahrrad (BICYCLE)** oder
   **Zu Fuß (FEET)**. Vorgabe ist Auto.
   Erst die Aktion Einsatz zusagen sendet Anreiseart und Home-Assistant-Zuhause-Koordinaten
   an FF-Agent; das Speichern der Konfiguration sendet nichts.
5. Eigenen Webhook anzeigen lassen und den Dienst speichern. Für weitere
   Organisationen wiederholen; dieselbe Rückmelde-ID wird nicht doppelt angelegt.

Unter **Konfigurieren** lässt sich die Webhook-Adresse erneut anzeigen. Über
**Neu konfigurieren** im Menü des Dienstes können Name, ID und Anreiseart geändert
werden. Die geheime Webhook-ID bleibt bei Änderungen und Neustarts erhalten.
Entfernen oder Deaktivieren des Dienstes deaktiviert seinen Webhook.

### Alarm-Webhook vorbereiten und lokal prüfen

Der Dialog verwendet Home Assistants externe **HTTPS**-URL aus
**Einstellungen → System → Netzwerk**. Fehlt diese, wird die aktuelle Browseradresse
inklusive Port als Basis für die vollständige Webhook-URL verwendet. Ohne
aktuellen HTTP-Aufruf dient die konfigurierte/erkannte interne URL als Fallback.
Die Warnung hängt vom angezeigten Host ab, nicht davon, woher die URL stammt:
Lokale Hostnamen und nichtöffentliche IPv4-/IPv6-Adressen erhalten sie;
öffentliche Domains oder IPs nicht. DNS und externe Erreichbarkeit werden nicht
geprüft. Der Warnkasten verweist auf öffentlichen HTTPS-Zugang, etwa über Nabu Casa.
Nach Änderung der externen URL den Dialog erneut öffnen.
Eine konfigurierte URL allein schafft noch keine Erreichbarkeit: Dafür braucht es
einen geeigneten externen Zugang zu Home Assistant. Dieses Projekt richtet keinen
Tunnel, Router-Port oder öffentlichen Zugang ein; die Testinstanz bleibt lokal.

Im **generischen Webhook** von FF-Agent: **GET**, **HTTPS**, **kein Body**,
keine Basic-Authentifizierung oder zusätzlichen Header. Falls FF-Agent das Protokoll
separat auswählt, `https://` dort nicht nochmals im URL-Feld eintragen.
Die Webhook-Adresse ist ein Geheimnis: Wer sie kennt, kann Alarme auslösen.

Jeder GET erzeugt das lokale HA-Ereignis **`ff_agent_alarm`** mit
**`config_entry_id`** und aktiviert bei einem neuen Alarm den Binary-Sensor.
Dienste bleiben getrennt. Der Anfrageinhalt wird nicht
gelesen, gespeichert oder protokolliert. Keine Einsatzdetails oder automatischen
Rückmeldungen. Mehrfach zugestellte GETs erzeugen mehrere Ereignisse.
Schon Linkvorschauen können den GET auslösen; die geheime URL nicht teilen.
Der Handler bestätigt mit Klartext und `Cache-Control: no-store`.
POST wird mit 405 abgewiesen. HEAD beantwortet Home Assistant mit 200, ohne Alarm.

Zum lokalen Test unter **Entwicklerwerkzeuge → Ereignisse** auf `ff_agent_alarm`
lauschen und die angezeigte lokale URL in einem anderen Browser-Tab öffnen.
Alternativ im Terminal `curl --no-progress-meter '<lokale-webhook-url>'` verwenden.
Der Test prüft nicht den externen Weg von FF-Agent zu HA. Ein HTTP-200-Status allein
reicht nicht: Home Assistant antwortet auch für unbekannte Webhooks mit 200.
Immer den tatsächlichen Ereignisempfang prüfen. Kein Ersatz für offizielle Alarmierung.

### Zustände, Lebensdauer und Rückmeldeaktionen

Der Push-Coordinator hält pro Dienst einen UTC-Ablaufzeitpunkt und den Status
`pending`, `accepted` oder `rejected`. HA Store speichert beides pro Config Entry;
es werden weder UUID noch Koordinaten in diesem zusätzlichen Zustand abgelegt.
Beim Neuladen wird die ursprüngliche Frist wiederhergestellt. Abgelaufene Alarme
werden nicht erneut aktiviert. Nach vier Stunden endet der lokale Alarm über
einen nativen UTC-Timer; beim Entladen wird der Timer beendet und der Zustand
gespeichert. Entfernen des Dienstes löscht seinen zusätzlichen Zustand.

Weitere Hooks im aktiven Zeitfenster erzeugen Ereignisse, setzen aber weder die
Frist noch den Rückmeldestatus zurück. Ohne Einsatz-ID ist eine Unterscheidung
zwischen Wiederholung und neuem Einsatz nicht möglich; diese Einschränkung steht
auch in der Endnutzeranleitung. Ein neuer Alarm nach Ablauf/manuellem Ende startet
mit `pending`. Beenden erhält die letzte Rückmeldung.

Die Entity-Aktionen `ff_agent.accept`, `ff_agent.reject` und `ff_agent.end_alarm`
zielen auf den Einsatz-Binary-Sensor oder das zugehörige Organisationsgerät.
Das lokale Beenden sendet nichts und ist auch bei bereits beendetem Alarm möglich.
Zu-/Absagen setzen weder einen lokalen noch einen passenden FF-Agent-Einsatz
voraus. Zusagen ändern die Alarmaktivität nicht; eine per HTTP 2xx übermittelte
Absage ruft zusätzlich das lokale Beenden auf und behält `rejected` bei. Dies gilt
auch für die Antwort „kein passender Einsatz aktiv“. Fehler oder unbestätigte
Übertragungen lassen den bisherigen Zustand unverändert.

Die bestätigten persönlichen Weblinks aus der Gladys-Implementierung sind:

- Zusage: GET `https://www.ff-agent.com/app2/missionreplies/{UUID}/accept`,
  Query-Parameter `transport` (`CAR`/`BICYCLE`/`FEET`), `lat` und `lng` aus HA Core Config.
- Absage: GET `https://www.ff-agent.com/app2/missionreplies/{UUID}/reject`, ohne Query.

HA verwaltet den HTTPX-Client. Insgesamt fünf Sekunden Timeout, keine automatischen
Wiederholungen oder Weiterleitungen. HTTP 2xx setzt den lokalen Status unabhängig
vom Antworttext; das bestätigt nur die HTTP-Übermittlung, nicht die Zuordnung zu
einem FF-Agent-Einsatz. Fehler und unklare Übermittlung lassen den alten Status
stehen. Der Status ist kein zurückgelesener Providerstatus. Eine Antwort auf einen
inzwischen beendeten oder ersetzten Alarm darf dessen Nachfolger nicht überschreiben.

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
Werkzeugcontainer ausgeführt, Tests dagegen im exakten HA-Laufzeitimage.
Zusätzliche CI-Jobs verwenden die offiziellen Aktionen `home-assistant/actions/hassfest`
und `hacs/action` für Integrationsmetadaten und HACS-Kompatibilität. Diese Prüfungen
reichen das Repository nicht beim HACS-Standardkatalog ein.

Lokale Prüfungen:

```sh
docker compose config --quiet
docker compose run --rm ruff
docker compose run --rm ruff format --check --no-cache .
docker compose run --rm --no-deps --entrypoint python homeassistant -m unittest discover -s /tests -v
docker compose run --rm --no-deps --entrypoint python homeassistant -m homeassistant --script check_config --config /config
```

UI-Prüfungen erfolgen in der bestehenden Testinstanz, nicht in parallelen Instanzen.
Automatisierte Tests können auch direkt im laufenden Container ausgeführt werden:

```sh
docker compose exec -T homeassistant python -m unittest discover -s /tests -v
docker compose exec -T homeassistant python -m homeassistant --script check_config --config /config
```

Die Tests laden die gemountete Integration mit temporärem HA-Zustand und prüfen
mehrere Dienste, UUID-Validierung, Änderungen, Webhook-Zuordnung und Deaktivierung.
Zusätzlich werden die Vier-Stunden-Grenze, Wiederherstellung, manuelles Beenden,
Rückmeldeparameter, Fehlerantworten und verspätete Antworten geprüft. HTTPX
MockTransport verhindert echte Zu-/Absagen; Testkoordinaten und UUIDs sind synthetisch.
Die GET-/POST-/HEAD-Prüfung verwendet HTTP auf Loopback-Port 18123 innerhalb
des Containers; sie ändert weder Benutzer noch Dienste der laufenden Instanz.
Sie verwenden keine persönlichen Daten und senden keine FF-Agent-Anfragen.
`check_config` prüft die echte Dev-Konfiguration;
es startet keinen zweiten HTTP-Server. Die Befehle benötigen keinen Commit/Push.

Zum automatischen Formatieren den Quellordner einmal explizit schreibbar mounten
(der Standardmount des Werkzeugs bleibt absichtlich read-only):

```sh
docker compose run --rm --volume "$PWD:/edit:rw" --workdir /edit ruff format --no-cache .
```

Für spätere HA-Upgrades Image-Tag, Python-Zielversion und Mindestversion in
`hacs.json` gemeinsam prüfen. Keine produktiven Daten oder echten FF-Agent-Links
für automatisierte Tests verwenden.
