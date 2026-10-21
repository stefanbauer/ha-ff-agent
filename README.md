# FF Agent for Home Assistant

[English](#english) · [Deutsch](#deutsch)

<a id="english"></a>

## English

Connect multiple fire departments or organizations to Home Assistant, each with
its own name, personal reply UUID, default transport and alarm webhook.

**Work in progress:** Receive alarms, track local alarm/reply states, and explicitly
send acceptances or rejections. Incident details and a dedicated dashboard card
are **not implemented yet**. This integration does not replace official alarm systems.

### Installation

Requires **Home Assistant 2026.10.2 or newer**. Version **0.1.0** is an early
development version, not a finished alarm integration. HACS is optional.
Before testing on your main Home Assistant instance, create a backup. Keep your
official alarm channels enabled; test reply actions only when a real response is intended.

#### HACS — custom repository

The repository is public and can be added as a custom repository. It is **not
listed in the default HACS catalog**. HACS must already be installed.

[![Open FF Agent in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stefanbauer&repository=ha-ff-agent&category=integration)

With HACS installed, this button opens FF Agent and offers to add it
as a custom repository if necessary. Confirm the addition, choose **Download**,
then restart Home Assistant. The same button opens the repository again later.
It does not install anything without your confirmation.

Alternatively, add `https://github.com/stefanbauer/ha-ff-agent` under
**HACS → Custom repositories**, category **Integration**, then download it.

#### Manual installation

1. Copy the `ff_agent` folder from this repository's `custom_components` directory
   into your Home Assistant configuration directory's `custom_components` folder.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → FF Agent**.

For a production test, select your **production instance** in My Home Assistant,
not the local development instance. The setup button below works after either
HACS or manual installation.

After installing and restarting, you can also open setup directly:

[![Set up FF Agent in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ff_agent)

This second button starts configuration; it does not download the integration.
My Home Assistant asks for your instance address when needed. If a button opens
the wrong instance, correct that address; the menu paths above work without links.

If you are using the prepared local development instance, the integration is
already installed. Start with **Add integration** or **Add service** on its page.
No YAML configuration is needed to add your services.

### Add an organization

1. Enter a name, for example **Feuerwehr Berglern**.
2. In **FF-Agent → Personal profile → Weblinks für Einsatzmeldung**, find your
   personal reply link. Copy **only the UUID** between `/missionreplies/` and
   `/accept` or `/reject`. Enter it in **Reply UUID**.
   Use the format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` — no complete URL,
   slashes or query parameters.
3. Select **Car**, **Bicycle** or **On foot** for acceptances. The default is Car.
   Saving settings sends nothing. Explicit acceptance sends this choice and the
   home coordinates configured in Home Assistant.
4. Review the alarm webhook instructions and save the service.

Repeat for each organization. Every service has its own webhook; the same reply
UUID cannot be added twice. The interface uses English by default and German when
your Home Assistant language is German.

**Keep your reply UUID private.** Anyone who knows it can send FF-Agent replies
on your behalf. Do not include it in screenshots, support requests or public files.
Settings are stored in your Home Assistant instance.

### Set up incoming alarms

Open **Configure** on your FF Agent service to see its secret webhook address.
The dialog prefers your configured external **HTTPS** address. Without one,
it shows a full local test URL and a warning. You can open that local URL in
another browser tab after saving the service.

> [!WARNING]
> Do not enter a localhost or private network address in FF-Agent: its servers
> cannot reach it. For real delivery, arrange public HTTPS access, for example
> [Home Assistant Cloud by Nabu Casa](https://www.nabucasa.com/), and set the
> external URL under **Settings → System → Network**. Reopen **Configure** to
> get the updated webhook URL. This integration does not create public access.

In FF-Agent's **Generic webhook** form, use:

- **URL:** the address shown in Home Assistant.
- **Method:** GET.
- **Protocol:** HTTPS. If selected separately, omit `https://` from the URL field.
- **Body:** none.
- **Authentication:** no Basic authentication or additional headers.

Keep this address private too: anyone with it can trigger an alarm signal.
Simply opening it, or a service fetching a link preview, can trigger it. Do not
share it in chats or public screenshots. Responses are not cached.
To verify reception, open **Developer tools → Events**, listen for
`ff_agent_alarm`, then open the local webhook URL in another tab or send a test
from FF-Agent using the external URL. The event's `config_entry_id`
identifies the receiving service. Incident contents are ignored; repeated
deliveries produce repeated signals. A successful HTTP response alone is not
proof of reception. No reply is sent automatically.

### Alarm states and actions

Each organization has its own device with exactly two entities:

| Entity | Meaning |
| --- | --- |
| **Alarm active** (binary sensor) | On after a webhook, off after at most four hours, a successfully sent rejection or **End alarm**. The `expires_at` attribute shows the deadline. |
| **Reply status** (sensor) | **Open**, **Accepted** or **Rejected** (`pending`, `accepted`, `rejected` for automations). |

The four-hour deadline and reply survive restarts. Further hooks during an active
alarm still emit events, but do not extend the deadline or reset a sent reply.
Since the webhook contains no incident ID, the integration cannot distinguish a
repeat notification from a different incident during this window. End the local
alarm before treating another hook as a new incident. A new alarm starts **Open**.
When an alarm ends, the last reply is retained until the next alarm.

Under **Developer tools → Actions**, choose one of the following and target the
organization's **Alarm active** entity (or its FF-Agent device):

- **FF Agent: Accept** (`ff_agent.accept`): sends a real acceptance using the
  organization's saved UUID, transport and **Home Assistant home coordinates**.
  No phone tracking or current device location is used.
- **FF Agent: Reject** (`ff_agent.reject`): sends a real rejection using the UUID
  only; no transport or coordinates. A successfully sent rejection also ends the
  local alarm, retaining **Rejected** as the reply status.
- **FF Agent: End alarm** (`ff_agent.end_alarm`): turns the local binary sensor
  off immediately, retaining the reply status. **Sends nothing to FF-Agent.**

Accept and Reject require an active local alarm and are never triggered
automatically by a webhook. Acceptance leaves the alarm active; a failed or
unconfirmed rejection does not end it either. These are standard Home Assistant
actions, usable in automations, scripts and a future card; no scenes are needed.

> [!WARNING]
> **Accepted/Rejected records the last successfully HTTP-delivered action from
> this Home Assistant instance, not a status read back from FF-Agent.** Changes
> made in the FF-Agent app are not synchronized. Errors, timeouts, redirects and
> FF-Agent's “no matching active incident” response do not record a successful
> reply. Check FF-Agent before trying again: a failed/uncertain request might
> already have been processed. There are no automatic retries or redirects.

To test safely, trigger the local webhook and then use **End alarm**; neither
operation sends a reply. Only test Accept/Reject when you intend a real response.

### Change or remove a service

- **Reconfigure** in the service's menu changes its name, reply UUID or transport.
- **Configure** shows the webhook address again. It remains stable across
  setting changes and restarts.
- Disabling or removing the service disables its webhook. Removing and adding it
  again generates a new address; update FF-Agent accordingly.

### Troubleshooting

- **FF Agent is missing from Add integration:** check that the folder is named
  `custom_components/ff_agent`, restart Home Assistant and reload the browser page.
- **A complete reply URL is rejected:** enter only the UUID as described above.
- **No alarm arrives:** check the service is enabled, the webhook uses GET and
  the external HTTPS address is reachable. Use the event reception test above;
  there is no incident-details display or dedicated dashboard card yet.
- **No accept/reject card:** use the actions above; the dedicated card comes later.
- **A Forecast device appears:** this belongs to the separate Met.no weather
  integration, not FF Agent. The name “FF Agent Development” is the test instance's
  name, not the owner of every entity.

### License and FF-Agent logo

The integration's code and original documentation use the [MIT License](LICENSE).
The FF-Agent name and logo belong to FF-Agent and their respective rights holders
and are **not covered by the MIT License**. This is an independent community
integration, not an official FF-Agent product. See [third-party notices](NOTICES.md).

[Back to languages](#ff-agent-for-home-assistant) · [Deutsch](#deutsch)

<a id="deutsch"></a>

## Deutsch

Verbinde mehrere Feuerwehren oder Organisationen mit Home Assistant, jeweils mit
eigenem Namen, persönlicher Rückmelde-UUID, Standard-Anreiseart und Alarm-Webhook.

**In Entwicklung:** Alarme empfangen, lokale Einsatz-/Rückmeldestatus verfolgen
und ausdrücklich Zusagen oder Absagen senden. Einsatzdetails und eine eigene
Dashboard-Karte sind **noch nicht implementiert**. Die Integration ersetzt keine
offiziellen Alarmierungswege.

### Installation

Voraussetzung: **Home Assistant 2026.10.2 oder neuer**. Version **0.1.0** ist eine
frühe Entwicklungsversion, keine fertige Alarmintegration. HACS ist optional.
Erstelle vor einem Test in deiner produktiven Home-Assistant-Instanz ein Backup.
Lass die offiziellen Alarmierungswege aktiv; teste Rückmeldeaktionen nur, wenn
eine echte Antwort beabsichtigt ist.

#### HACS — benutzerdefiniertes Repository

Das Repository ist öffentlich und kann als benutzerdefiniertes Repository
hinzugefügt werden. Im HACS-Standardkatalog ist die Integration **nicht gelistet**.
HACS muss bereits installiert sein.

[![FF Agent in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stefanbauer&repository=ha-ff-agent&category=integration)

Mit installiertem HACS öffnet der Button
FF Agent und bietet bei Bedarf das Hinzufügen als benutzerdefiniertes Repository
an. Bestätige das Hinzufügen, wähle **Herunterladen** und starte Home Assistant
neu. Derselbe Button öffnet später wieder das Repository. Ohne deine Bestätigung
wird nichts installiert.

Alternativ unter **HACS → Benutzerdefinierte Repositorys** die Adresse
`https://github.com/stefanbauer/ha-ff-agent` mit Kategorie **Integration** hinzufügen
und anschließend herunterladen.

#### Manuell installieren

1. Kopiere den Ordner `ff_agent` aus `custom_components` dieses Repositorys in
   den Ordner `custom_components` deines Home-Assistant-Konfigurationsverzeichnisses.
2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen → FF Agent**.

Wähle für einen produktiven Test in My Home Assistant deine **produktive Instanz**
aus, nicht die lokale Entwicklungsinstanz. Der Einrichtungsbutton unten funktioniert
nach der Installation über HACS oder nach dem manuellen Kopieren der Dateien.

Nach Installation und Neustart kannst du die Einrichtung auch direkt öffnen:

[![FF Agent in Home Assistant einrichten](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ff_agent)

Dieser zweite Button startet die Einrichtung; er lädt keine Integration herunter.
My Home Assistant fragt bei Bedarf nach deiner Instanzadresse. Öffnet sich die
falsche Instanz, korrigiere diese Adresse. Die Menüwege oben funktionieren ohne Links.

In der vorbereiteten lokalen Entwicklungsinstanz ist die Integration bereits
installiert. Beginne direkt mit **Integration hinzufügen** oder **Dienst hinzufügen**
auf ihrer Seite. Zum Hinzufügen der Dienste ist keine YAML-Konfiguration nötig.

### Organisation hinzufügen

1. Gib einen Namen ein, zum Beispiel **Feuerwehr Berglern**.
2. Suche in **FF-Agent → Persönliches Profil → Weblinks für Einsatzmeldung**
   deinen persönlichen Rückmeldelink. Kopiere **nur die UUID** zwischen
   `/missionreplies/` und `/accept` oder `/reject` in das Feld **Rückmelde-UUID**.
   Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` — keine vollständige URL,
   Schrägstriche oder Parameter.
3. Wähle **Auto**, **Fahrrad** oder **Zu Fuß** für Zusagen. Vorgabe ist Auto.
   Das Speichern sendet nichts. Erst eine ausdrückliche Zusage sendet diese
   Auswahl und die in Home Assistant hinterlegten Zuhause-Koordinaten.
4. Lies die Hinweise zum Alarm-Webhook und speichere den Dienst.

Wiederhole das für jede Organisation. Jeder Dienst erhält seinen eigenen Webhook;
dieselbe Rückmelde-UUID kann nicht doppelt hinzugefügt werden. Die Oberfläche ist
standardmäßig Englisch, bei deutscher Home-Assistant-Sprache Deutsch.

**Halte deine Rückmelde-UUID geheim.** Wer sie kennt, kann in deinem Namen an
FF-Agent antworten. Nicht in Screenshots, Supportanfragen oder öffentlichen Dateien
teilen. Die Einstellungen werden in deiner Home-Assistant-Instanz gespeichert.

### Alarme empfangen

Öffne **Konfigurieren** an deinem FF-Agent-Dienst, um seine geheime Webhook-Adresse
anzuzeigen. Der Dialog bevorzugt deine hinterlegte externe **HTTPS**-Adresse.
Fehlt diese, siehst du eine vollständige lokale Testadresse mit Warnhinweis.
Nach dem Speichern des Dienstes kannst du sie in einem anderen Browser-Tab öffnen.

> [!WARNING]
> Keine localhost- oder private Netzwerkadresse in FF-Agent eintragen: Dessen
> Server können sie nicht erreichen. Richte für echte Zustellung einen öffentlichen
> HTTPS-Zugang ein, zum Beispiel [Home Assistant Cloud von Nabu Casa](https://www.nabucasa.com/),
> und hinterlege die externe URL unter **Einstellungen → System → Netzwerk**.
> Öffne danach **Konfigurieren** erneut, um die aktualisierte Webhook-URL zu sehen.
> Die Integration richtet keinen öffentlichen Zugang ein.

Im **generischen Webhook** von FF-Agent eintragen:

- **URL:** die in Home Assistant angezeigte Adresse.
- **Methode:** GET.
- **Protokoll:** HTTPS. Bei separater Auswahl `https://` im URL-Feld weglassen.
- **Inhalt:** kein Body.
- **Authentifizierung:** keine Basic-Authentifizierung oder zusätzlichen Header.

Auch diese Adresse geheim halten: Wer sie kennt, kann Alarmsignale auslösen.
Schon das Öffnen oder der Abruf einer Linkvorschau kann sie auslösen. Nicht in
Chats oder öffentlichen Screenshots teilen. Antworten werden nicht gecacht.
Zum Empfangstest unter **Entwicklerwerkzeuge → Ereignisse** auf `ff_agent_alarm`
lauschen und anschließend die lokale Webhook-Adresse in einem anderen Tab öffnen
oder mit der externen URL einen Test aus FF-Agent senden. Die `config_entry_id`
im Ereignis bezeichnet den empfangenden Dienst. Einsatzinhalte werden ignoriert;
mehrfache Zustellungen erzeugen mehrere Signale. Eine erfolgreiche HTTP-Antwort
allein bestätigt keinen Empfang. Es wird keine automatische Rückmeldung gesendet.

### Einsatzstatus und Aktionen

Jede Organisation bekommt ein eigenes Gerät mit genau zwei Entitäten:

| Entität | Bedeutung |
| --- | --- |
| **Einsatz aktiv** (Binary-Sensor) | Nach einem Webhook an, nach höchstens vier Stunden, einer erfolgreich gesendeten Absage oder **Einsatz beenden** aus. Das Attribut `expires_at` zeigt den Ablaufzeitpunkt. |
| **Rückmeldestatus** (Sensor) | **Offen**, **Zugesagt** oder **Abgesagt** (`pending`, `accepted`, `rejected` für Automationen). |

Vier-Stunden-Frist und Rückmeldung bleiben über Neustarts erhalten. Weitere Hooks
während eines aktiven Einsatzes erzeugen Ereignisse, verlängern aber weder die
Frist noch setzen sie eine gesendete Rückmeldung zurück. Da der Hook keine
Einsatz-ID enthält, kann die Integration in diesem Zeitraum eine Wiederholung
nicht von einem anderen Einsatz unterscheiden. Beende den lokalen Einsatz, bevor
ein weiterer Hook als neuer Einsatz behandelt werden soll. Ein neuer Einsatz
beginnt **Offen**. Beim Beenden bleibt die letzte Rückmeldung bis zum nächsten
Einsatz erhalten.

Unter **Entwicklerwerkzeuge → Aktionen** eine der folgenden Aktionen wählen und
die Entität **Einsatz aktiv** der Organisation (oder ihr FF-Agent-Gerät) als Ziel
auswählen:

- **FF Agent: Zusagen** (`ff_agent.accept`): sendet eine echte Zusage mit der
  gespeicherten UUID, Anreiseart und den **Zuhause-Koordinaten aus Home Assistant**.
  Kein Handy-Tracking und keine aktuelle Geräteposition.
- **FF Agent: Absagen** (`ff_agent.reject`): sendet eine echte Absage nur mit der
  UUID, ohne Anreiseart oder Koordinaten. Eine erfolgreich gesendete Absage beendet
  auch den lokalen Einsatz; der Rückmeldestatus bleibt **Abgesagt**.
- **FF Agent: Einsatz beenden** (`ff_agent.end_alarm`): schaltet den lokalen
  Binary-Sensor sofort aus und behält den Rückmeldestatus bei.
  **Sendet nichts an FF-Agent.**

Zusagen und Absagen erfordern einen aktiven lokalen Einsatz und werden nie
automatisch durch einen Webhook aufgerufen. Eine Zusage lässt den Einsatz aktiv;
eine fehlgeschlagene oder unbestätigte Absage beendet ihn ebenfalls nicht.
Das sind normale Home-Assistant-Aktionen für Automationen, Skripte und eine
spätere Karte; Szenen werden dafür nicht benötigt.

> [!WARNING]
> **Zugesagt/Abgesagt zeigt die letzte erfolgreich per HTTP übermittelte Aktion
> dieser Home-Assistant-Instanz, keinen aus FF-Agent zurückgelesenen Status.**
> Änderungen in der FF-Agent-App werden nicht synchronisiert. Fehler, Timeouts,
> Weiterleitungen und die FF-Agent-Antwort „kein passender Einsatz aktiv“ vermerken
> keine erfolgreiche Rückmeldung. Vor erneutem Senden FF-Agent prüfen: Eine
> fehlgeschlagene/unklare Anfrage könnte bereits verarbeitet worden sein.
> Es gibt keine automatischen Wiederholungen oder Weiterleitungen.

Gefahrloser Test: lokalen Webhook auslösen und **Einsatz beenden** aufrufen;
beides sendet keine Rückmeldung. Zusage/Absage nur testen, wenn du wirklich
antworten möchtest.

### Dienst ändern oder entfernen

- **Neu konfigurieren** im Menü des Dienstes ändert Name, Rückmelde-UUID oder Anreiseart.
- **Konfigurieren** zeigt die Webhook-Adresse erneut. Sie bleibt bei Änderungen
  und Neustarts erhalten.
- Deaktivieren oder Entfernen des Dienstes deaktiviert seinen Webhook. Beim
  erneuten Hinzufügen entsteht eine neue Adresse, die du auch in FF-Agent ändern musst.

### Häufige Fragen

- **FF Agent fehlt unter Integration hinzufügen:** Prüfe den Ordner
  `custom_components/ff_agent`, starte Home Assistant neu und lade die Browserseite neu.
- **Die Rückmelde-URL wird abgelehnt:** Gib nur die UUID wie oben beschrieben ein.
- **Kein Alarm kommt an:** Prüfe, ob der Dienst aktiviert ist, der Webhook GET
  verwendet und die externe HTTPS-Adresse erreichbar ist. Nutze den Ereignistest
  oben; es gibt noch keine Einsatzdetailanzeige oder eigene Dashboard-Karte.
- **Keine Zusage-/Absage-Karte:** Nutze die Aktionen oben; die eigene Karte folgt später.
- **Ein Gerät Forecast erscheint:** Es gehört zur separaten Wetterintegration
  Met.no, nicht zu FF Agent. „FF Agent Development“ ist der Name der Testinstanz,
  nicht die zuständige Integration jeder Entität.

### Lizenz und FF-Agent-Logo

Quellcode und eigene Dokumentation der Integration stehen unter der
[MIT-Lizenz](LICENSE). Der Name und das Logo von FF-Agent gehören FF-Agent und
den jeweiligen Rechteinhabern und sind **nicht von der MIT-Lizenz umfasst**.
Dies ist eine unabhängige Community-Integration, kein offizielles FF-Agent-Produkt.
Siehe die [Hinweise zu Rechten Dritter](NOTICES.md).

[Zur Sprachauswahl](#ff-agent-for-home-assistant) · [English](#english)

---

For contributors / Für Entwickler: [Local development / Lokale Entwicklung](dev/README.md).
